//! Custom engine of Scribe.
//! Use any model you want.

use std::collections::HashMap;
use std::sync::{Arc, Mutex};

use anyhow::{Result, anyhow};
use chrono::{Datelike, Local};
use mistralrs::{
    Agent, AgentBuilder, AgentStopReason, AnyMoeConfig, AnyMoeModelBuilder,
    AutoDeviceMapParams, DeviceMapSetting, GgufModelBuilder, IsqBits,
    MemoryGpuConfig, PagedAttentionMetaBuilder, TextModelBuilder,
    XLoraModelBuilder,
};
use tera::{Tera, Value, to_value, try_get_value};

use crate::tools::add_section::{
    SECTIONS, Section, add_section_tool_with_callback,
};
use crate::tools::calculator::calculator_tool_with_callback;
use crate::tools::database::{
    DatabaseProvider, from_database_tool_with_callback, set_database_provider,
};

const DEFAULT_GGUF_REPO: &str = "MaziyarPanahi/Mistral-7B-Instruct-v0.3-GGUF";
const DEFAULT_GGUF_FILE: &str = "Mistral-7B-Instruct-v0.3.Q4_K_M.gguf";
const DEFAULT_TEXT_MODEL: &str = "Qwen/Qwen3-4B";
const DEFAULT_SYSTEM_PROMPT: &str = include_str!("../templates/system.txt");

fn resolve_gguf_model() -> String {
    std::env::var("BASE_MODEL")
        .unwrap_or_else(|_| DEFAULT_GGUF_REPO.to_string())
}

fn resolve_text_model() -> String {
    std::env::var("TEXT_MODEL")
        .unwrap_or_else(|_| DEFAULT_TEXT_MODEL.to_string())
}

fn resolve_system_prompt() -> Result<String> {
    match std::env::var("SYSTEM_PROMPT") {
        Ok(path) => {
            tracing::info!(?path, "loading system prompt from env path");
            std::fs::read_to_string(&path).map_err(Into::into)
        },
        Err(_) => Ok(DEFAULT_SYSTEM_PROMPT.to_string()),
    }
}

/// Configuration for the report generation engine.
/// Provides a builder pattern to optionally enable MoE, X-LoRa, and configure
/// the Agent.
#[derive(Clone)]
pub struct ScribeConfig {
    pub model_id: String,
    pub text_model_id: String,
    pub gguf_files: Vec<String>,
    pub system_prompt: String,
    pub custom_template: Option<String>,
    pub max_iterations: usize,
    pub max_seq_len: usize,
    pub xlora_model_id: Option<String>,
    pub xlora_ordering_file: Option<String>,
    pub anymoe_config: Option<AnyMoeConfig>,
    pub anymoe_experts: Option<Vec<String>>,
    pub anymoe_routing_map: Option<String>,
    pub use_text_model_only: bool,
}

impl ScribeConfig {
    /// Creates a default configuration.
    pub fn new() -> Result<Self> {
        Ok(Self {
            model_id: resolve_gguf_model(),
            text_model_id: resolve_text_model(),
            gguf_files: vec![DEFAULT_GGUF_FILE.to_string()],
            system_prompt: resolve_system_prompt()?,
            custom_template: None,
            max_iterations: 20,
            max_seq_len: 4096,
            xlora_model_id: None,
            xlora_ordering_file: None,
            anymoe_config: None,
            anymoe_experts: None,
            anymoe_routing_map: None,
            use_text_model_only: false,
        })
    }

    /// Set a custom number of max iterations for the Agentic loop.
    pub fn with_max_iterations(mut self, iterations: usize) -> Self {
        self.max_iterations = iterations;
        self
    }

    /// Set a custom maximum sequence length.
    pub fn with_max_seq_len(mut self, max_seq_len: usize) -> Self {
        self.max_seq_len = max_seq_len;
        self
    }

    /// Enable and configure X-LoRA.
    pub fn with_xlora(
        mut self,
        model_id: impl Into<String>,
        ordering_file: impl Into<String>,
    ) -> Self {
        self.xlora_model_id = Some(model_id.into());
        self.xlora_ordering_file = Some(ordering_file.into());
        self
    }

    /// Enable and configure AnyMoE (Mixture of Experts).
    pub fn with_anymoe(
        mut self,
        config: AnyMoeConfig,
        experts: Vec<String>,
        routing_map_path: impl Into<String>,
    ) -> Self {
        self.anymoe_config = Some(config);
        self.anymoe_experts = Some(experts);
        self.anymoe_routing_map = Some(routing_map_path.into());
        self
    }

    /// Use text model instead of GGUF model.
    pub fn with_text_model(mut self) -> Self {
        self.use_text_model_only = true;
        self
    }
}

/// The main engine that orchestrates NLP generation and LaTeX rendering.
pub struct Scribe {
    config: ScribeConfig,
    agent: Agent,
}

impl Scribe {
    /// Create a new [`Scribe`] instance and initialize the mistralrs agent.
    pub async fn new(
        config: ScribeConfig,
        db_provider: impl DatabaseProvider + 'static,
    ) -> Result<Self> {
        if let Err(err) = set_database_provider(db_provider) {
            tracing::warn!(?err, "failed to set database provider");
        }

        let paged_attn_meta = PagedAttentionMetaBuilder::default()
            .with_block_size(32)
            .with_gpu_memory(MemoryGpuConfig::ContextSize(32_768))
            .build()?;

        let device_map = DeviceMapSetting::Auto(AutoDeviceMapParams::Text {
            max_seq_len: config.max_seq_len,
            max_batch_size: AutoDeviceMapParams::DEFAULT_MAX_BATCH_SIZE,
        });

        let model = if let (Some(cfg), Some(experts), Some(map_path)) = (
            &config.anymoe_config,
            &config.anymoe_experts,
            &config.anymoe_routing_map,
        ) {
            tracing::info!(
                text_model_id = ?config.text_model_id,
                ?experts,
                "applying AnyMoE with experts (requires ISQ quantization instead of GGUF)"
            );

            let base_builder = TextModelBuilder::new(&config.text_model_id)
                .with_logging()
                .with_auto_isq(IsqBits::Four)
                .with_paged_attn(paged_attn_meta)
                .with_device_mapping(device_map);

            AnyMoeModelBuilder::from_text_builder(
                base_builder,
                cfg.clone(),
                "model.layers",
                "mlp",
                map_path,
                experts.clone(),
                (0..32).collect(),
            )
            .build()
            .await?
        } else if let (Some(xlora_id), Some(ordering_file)) =
            (&config.xlora_model_id, &config.xlora_ordering_file)
        {
            tracing::info!(
                text_model_id = ?config.text_model_id,
                ?xlora_id,
                ?ordering_file,
                "applying X-LoRA adapter mixing (requires ISQ quantization instead of GGUF)"
            );

            let base_builder = TextModelBuilder::new(&config.text_model_id)
                .with_logging()
                .with_auto_isq(IsqBits::Four)
                .with_paged_attn(paged_attn_meta)
                .with_device_mapping(device_map);

            let ordering_data = std::fs::read_to_string(ordering_file)
                .map_err(|e| {
                    anyhow!("could not read X-LoRA ordering file: {}", e)
                })?;

            let ordering =
                serde_json::from_str(&ordering_data).map_err(|e| {
                    anyhow!("invalid JSON in X-LoRA ordering file: {}", e)
                })?;

            XLoraModelBuilder::from_text_model_builder(
                base_builder,
                xlora_id,
                ordering,
            )
            .build()
            .await?
        } else if config.use_text_model_only {
            tracing::info!(
                text_model_id = ?config.text_model_id,
                "initializing standard Text model with ISQ"
            );

            TextModelBuilder::new(&config.text_model_id)
                .with_logging()
                .with_auto_isq(IsqBits::Four)
                .with_paged_attn(paged_attn_meta)
                .with_device_mapping(device_map)
                .build()
                .await?
        } else {
            tracing::info!(
                gguf_model_id = ?config.model_id,
                "initializing standard GGUF model (No MoE / X-LoRA)"
            );

            let base_builder = GgufModelBuilder::new(
                &config.model_id,
                config.gguf_files.clone(),
            )
            .with_tok_model_id(&config.text_model_id)
            .with_logging()
            .with_paged_attn(paged_attn_meta)
            .with_device_mapping(device_map);

            base_builder.build().await?
        };

        let agent = AgentBuilder::new(model)
            .with_system_prompt(&config.system_prompt)
            .with_max_iterations(config.max_iterations)
            .with_parallel_tool_execution(true)
            .register_tool(add_section_tool_with_callback())
            .register_tool(from_database_tool_with_callback())
            .register_tool(calculator_tool_with_callback())
            .build();

        Ok(Self { config, agent })
    }

    /// Generate LaTeX sections from a user prompt using the Agentic loop.
    pub async fn generate_sections(
        &self,
        user_prompt: &str,
    ) -> Result<Vec<Section>> {
        let sections = Arc::new(Mutex::new(Vec::new()));
        let sections_clone = sections.clone();

        let response = SECTIONS
            .scope(
                sections_clone,
                async move { self.agent.run(user_prompt).await },
            )
            .await?;

        tracing::debug!(?response, "llm generation ended");

        if let AgentStopReason::Error(err) = response.stop_reason {
            anyhow::bail!("Agent encountered an error: {}", err);
        }

        let result = {
            let guard = sections
                .lock()
                .map_err(|err| anyhow!("Mutex poisoned: {}", err))?;
            guard.clone()
        };
        Ok(result)
    }

    /// Takes the generated sections and applies the Tera LaTeX template.
    pub fn generate_raw_latex(sections: Vec<Section>) -> Result<String> {
        let mut tera = Tera::default();
        let report_template = include_str!("../templates/report.tex");
        tera.add_raw_template("report.tex", report_template)?;
        tera.register_filter("latex_escape", Self::latex_escape);

        let mut context = tera::Context::new();
        context.insert("sections", &sections);

        let now = Local::now();
        context.insert("year", &now.year());
        context.insert("month", &now.month());
        context.insert("day", &now.day());

        let raw = tera.render("report.tex", &context)?;
        Ok(raw)
    }

    /// Tera filter to escape LaTeX special characters from user/model input.
    fn latex_escape(
        value: &Value,
        _: &HashMap<String, Value>,
    ) -> tera::Result<Value> {
        let s = try_get_value!("latex_escape", "value", String, value);

        let escaped = s.replace('&', "\\&").replace('%', "\\%");
        match to_value(escaped) {
            Ok(val) => Ok(val),
            Err(err) => Err(tera::Error::msg(format!(
                "Failed to parse escaped value: {}",
                err
            ))),
        }
    }

    /// Generate bytes of PDF of LaTeX article using a prompt via tectonic.
    pub async fn generate_pdf(&self, user_prompt: &str) -> Result<Vec<u8>> {
        let sections = self.generate_sections(user_prompt).await?;
        let raw_latex = Self::generate_raw_latex(sections)?;

        let pdf_bytes = tokio::task::spawn_blocking(move || {
            tectonic::latex_to_pdf(raw_latex).map_err(|err| {
                anyhow!("Tectonic PDF compilation error: {:?}", err)
            })
        })
        .await??;

        Ok(pdf_bytes)
    }
}
