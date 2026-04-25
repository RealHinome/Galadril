use scribe::ScribeReport;
use scribe::engine::ScribeConfig;
use scribe::tools::database::NoOpProvider;
use tracing_subscriber::layer::SubscriberExt;
use tracing_subscriber::util::SubscriberInitExt;
use tracing_subscriber::{EnvFilter, fmt};

const PROMPT: &str = "Synthetic report about DSGE model in macroeconomy. No graph. Rely on your knowledge--database is not connected.";

#[tokio::main]
async fn main() {
    tracing_subscriber::registry()
        .with(
            EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| EnvFilter::new("trace")),
        )
        .with(fmt::layer())
        .init();

    let config = ScribeConfig::new()
        .expect("cannot generate config")
        .with_max_iterations(5)
        .with_max_seq_len(4096);

    // We pass NoOpProvider here, but you can swap this with a real DB
    // implementation.
    let engine = ScribeReport::new(config, NoOpProvider)
        .await
        .expect("cannot initialize mistralrs engine");

    tracing::info!("generating report...");
    let pdf = engine
        .generate_pdf(PROMPT)
        .await
        .expect("cannot generate report");

    std::fs::write("report.pdf", pdf)
        .expect("failed to write generated PDF to disk");
    tracing::info!(path = "report.pdf", "report saved successfully");
}
