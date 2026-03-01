use std::collections::HashMap;
use std::str::FromStr;
use std::sync::{Arc, Mutex};

use anyhow::Result;
use ollama_rs::generation::tools::implementations::{
    Calculator, DDGSearcher, Scraper,
};
use ollama_rs::generation::tools::{self, Tool};
use ollama_rs::models::create::CreateModelRequest;
use schemars::JsonSchema;
use serde::{Deserialize, Serialize};
use tera::{Tera, Value, to_value, try_get_value};

/// A section produced by the model via `add_section(title, content)`.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Section {
    pub title: String,
    pub content: String,
}

use ollama_rs::Ollama;
use ollama_rs::coordinator::Coordinator;
use ollama_rs::generation::chat::ChatMessage;
use ollama_rs::models::ModelOptions;

use crate::database::DatabaseProvider;

const MODEL_NAME: &str = "report-latex";
const DEFAULT_MODEL: &str = "ministral-3:14b";
const DEFAULT_SYSTEM_PROMPT: &str = include_str!("../templates/system.txt");

fn resolve_model() -> String {
    std::env::var("BASE_MODEL").unwrap_or_else(|_| DEFAULT_MODEL.to_string())
}

fn resolve_system_prompt() -> Result<String> {
    match std::env::var("SYSTEM_PROMPT") {
        Ok(path) => {
            tracing::info!(path = %path, "loading system prompt from env path");
            Ok(std::fs::read_to_string(&path)?)
        },
        Err(_) => Ok(DEFAULT_SYSTEM_PROMPT.to_string()),
    }
}

/// Configuration for the report generation engine.
#[derive(Debug, Clone)]
pub struct ScribeConfig {
    pub host: String,
    pub port: u16,
    pub model: String,
    pub system_prompt: String,
    pub custom_template: Option<String>,
}

impl ScribeConfig {
    pub fn new() -> Result<Self> {
        let url = url::Url::from_str(
            &std::env::var("OLLAMA_HOST")
                .unwrap_or_else(|_| "http://localhost:11434".to_string()),
        )?;
        let host = format!(
            "{}://{}",
            url.scheme(),
            url.host_str().unwrap_or("http://localhost")
        );

        Ok(Self {
            host,
            port: url.port().unwrap_or(11434),
            model: resolve_model(),
            system_prompt: resolve_system_prompt()
                .unwrap_or_else(|_| DEFAULT_SYSTEM_PROMPT.to_string()),
            custom_template: None,
        })
    }
}

/// Parameters accepted by the `add_section` tool.
#[derive(Debug, Clone, Deserialize, JsonSchema)]
struct AddSectionParams {
    /// The section title (will be rendered as \section{TITLE}).
    #[schemars(
        description = "The section title (will be rendered as \\section{TITLE})."
    )]
    title: String,
    /// The LaTeX body content of the section.
    #[schemars(description = "The LaTeX body content of the section.")]
    content: String,
}

/// A tool that appends a section to a shared `Vec<Section>`.
struct AddSectionTool {
    sections: Arc<Mutex<Vec<Section>>>,
}

impl Tool for AddSectionTool {
    type Params = AddSectionParams;

    fn name() -> &'static str {
        "add_section"
    }

    fn description() -> &'static str {
        "Add a section to the LaTeX report. The content must be raw LaTeX body \
         (no \\section command, no preamble). Use \\subsection, \\subsubsection, \
         math environments, and TikZ as needed."
    }

    async fn call(&mut self, params: Self::Params) -> tools::Result<String> {
        tracing::debug!(title = ?params.title, content = ?params.content, "add_section called");
        self.sections
            .lock()
            .map_err(|_| "poisoned mutex")?
            .push(Section {
                title: params.title,
                content: params.content,
            });
        Ok(String::new())
    }
}

/// Query an external database to retrieve context data before writing a
/// section. Use this when you need facts, metrics, or structured data that
/// you do not already have. It uses PostgreSQL with Apache AGE and
/// pgvectorscale on intern, to find the best elements with a raw query.
///
/// * query - A natural-language query describing the data needed.
#[ollama_rs::function]
async fn from_database(query: String) -> Result<String> {
    tracing::error!(?query, "function from_database called");
    Ok(String::default())
}

/// The main engine that orchestrates NLP generation and LaTeX rendering.
pub struct Scribe<D: DatabaseProvider + 'static> {
    config: ScribeConfig,
    ollama: Ollama,
    db: D,
}

impl<D: DatabaseProvider> Scribe<D> {
    /// Create a new [`Scribe`] instance.
    pub fn new(config: ScribeConfig, db: D) -> Self {
        println!("{:?} and {:?}", &config.host, config.port);
        let ollama = Ollama::new(&config.host, config.port);
        Self { config, ollama, db }
    }

    /// Create the LaTeX technical writer model.
    pub async fn create_custom_model(&self) -> Result<()> {
        self.ollama
            .create_model(
                CreateModelRequest::new(MODEL_NAME.to_string())
                    .system(self.config.system_prompt.clone())
                    .from_model(self.config.model.clone()),
            )
            .await?;
        Ok(())
    }

    /// Generate LaTeX sections from a user prompt.
    pub async fn generate_sections(
        &mut self,
        user_prompt: &str,
    ) -> Result<Vec<Section>> {
        // Shared buffer.
        let sections = Arc::new(Mutex::new(Vec::<Section>::new()));

        {
            let tool = AddSectionTool {
                sections: Arc::clone(&sections),
            };

            let mut coordinator = Coordinator::new(
                self.ollama.clone(),
                MODEL_NAME.to_string(),
                Vec::new(),
            )
            .options(
                ModelOptions::default()
                    .temperature(0.2)
                    .top_p(0.9)
                    .top_k(20)
                    .repeat_penalty(1.01)
                    .num_ctx(16384)
                    .seed(42),
            )
            // .add_tool(DDGSearcher::new())
            // .add_tool(Scraper {})
            // .add_tool(Calculator {})
            .add_tool(tool)
            // .add_tool(from_database)
            .think(false);

            let user_message = ChatMessage::user(user_prompt.to_string());
            let _ = coordinator.chat(vec![user_message]).await?;
        }

        let result = Arc::try_unwrap(sections)
            .map_err(|_| anyhow::anyhow!("Arc still has multiple owners"))?
            .into_inner()?;

        Ok(result)
    }

    pub fn generate_raw_latex(sections: Vec<Section>) -> Result<String> {
        let mut tera = Tera::new("templates/**/*.tex")?;
        tera.register_filter("latex_escape", Self::latex_escape);
        let mut context = tera::Context::new();
        context.insert("sections", &sections);
        let raw = tera.render("report.tex", &context)?;
        Ok(raw)
    }

    fn latex_escape(
        value: &Value,
        _: &HashMap<String, Value>,
    ) -> tera::Result<Value> {
        let s = try_get_value!("latex_escape", "value", String, value);

        let escaped = s
            .replace('\\', "\\textbackslash ")
            .replace('&', "\\&")
            .replace('%', "\\%")
            .replace('$', "\\$")
            .replace('#', "\\#")
            .replace('_', "\\_")
            .replace('{', "\\{")
            .replace('}', "\\}")
            .replace('~', "\\textasciitilde ")
            .replace('^', "\\textasciicircum ");

        Ok(to_value(escaped).unwrap())
    }

    /// Generate bytes of PDF of LaTeX article using a prompt.
    pub async fn generate_pdf(
        &mut self,
        user_prompt: &str,
    ) -> Result<Vec<u8>> {
        let sections = self.generate_sections(user_prompt).await?;
        let raw_latex = Self::generate_raw_latex(sections)?;
        Ok(tectonic::latex_to_pdf(raw_latex).unwrap())
    }
}
