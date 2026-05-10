use serde::Deserialize;
use std::fs;
use std::path::Path;

#[derive(Debug, Deserialize, Clone)]
pub struct Config {
    pub api_url: String,
    pub api_key: String,
    pub watch_dir: String,
    pub interval_secs: u64,
    pub log_file: String,
}

impl Config {
    pub fn load(path: &Path) -> Result<Self, Box<dyn std::error::Error>> {
        let content = fs::read_to_string(path)?;
        let config: Config = toml::from_str(&content)?;
        Ok(config)
    }

    pub fn from_env() -> Self {
        Config {
            api_url: std::env::var("KALPIXK_API_URL")
                .unwrap_or_else(|_| "http://localhost:8000".to_string()),
            api_key: std::env::var("KALPIXK_API_KEY").unwrap_or_default(),
            watch_dir: std::env::var("KALPIXK_WATCH_DIR").unwrap_or_else(|_| "/tmp".to_string()),
            interval_secs: std::env::var("KALPIXK_INTERVAL_SECS")
                .unwrap_or_else(|_| "2".to_string())
                .parse()
                .unwrap_or(2),
            log_file: std::env::var("KALPIXK_LOG_FILE")
                .unwrap_or_else(|_| "kalpixk-alerts.log".to_string()),
        }
    }
}
