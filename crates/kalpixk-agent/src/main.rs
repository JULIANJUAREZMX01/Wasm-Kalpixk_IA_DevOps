mod collectors;
mod config;
mod features;
mod sender;

use crate::config::Config;
use crate::sender::TelemetrySender;
use clap::Parser;
use std::path::PathBuf;
use tracing::info;

#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// Path to the configuration file
    #[arg(short, long, value_name = "FILE")]
    config: Option<PathBuf>,
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Initialize logging
    tracing_subscriber::fmt::init();

    let args = Args::parse();

    let config = if let Some(config_path) = args.config {
        info!("Loading config from {:?}", config_path);
        Config::load(&config_path)?
    } else {
        info!("Loading config from environment");
        Config::from_env()
    };

    info!("Kalpixk Agent v{} starting...", env!("CARGO_PKG_VERSION"));

    let mut sender = TelemetrySender::new(config)?;
    sender.run().await;

    Ok(())
}
