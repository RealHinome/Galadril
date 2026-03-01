use scribe::database::NoOpProvider;
use scribe::ollama::{Scribe, ScribeConfig};
use tracing_subscriber::layer::SubscriberExt;
use tracing_subscriber::util::SubscriberInitExt;
use tracing_subscriber::{EnvFilter, fmt};

const PROMPT: &str = "Generate one-section report for sample with tikz graphs";

#[tokio::main]
async fn main() {
    tracing_subscriber::registry()
        .with(
            EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| EnvFilter::new("trace")),
        )
        .with(fmt::layer())
        .init();

    let config = ScribeConfig::new().expect("cannot generate config");

    let mut engine = Scribe::new(config, NoOpProvider);
    engine.create_custom_model().await.unwrap();
    let pdf = engine
        .generate_pdf(PROMPT)
        .await
        .expect("cannot generate report");
    std::fs::write("report.pdf", pdf).unwrap();
    tracing::info!("report generated");
}
