use crate::collectors::{
    FsCollector, NetworkCollector, ProcessCollector, RegistryCollector, TelemetryBatch,
};
use crate::config::Config;
use crate::features::extract_features;
use serde::{Deserialize, Serialize};
use std::time::{Duration, Instant};
use tracing::{error, info};

#[derive(Serialize)]
struct DetectRequest {
    features: Vec<Vec<f32>>,
}

#[derive(Deserialize)]
struct DetectResponse {
    results: Vec<DetectionResult>,
}

#[derive(Deserialize)]
struct DetectionResult {
    anomaly_score: f32,
    technique: String,
}

pub struct TelemetrySender {
    config: Config,
    fs_collector: FsCollector,
    process_collector: ProcessCollector,
    network_collector: NetworkCollector,
    registry_collector: RegistryCollector,
    start_time: Instant,
}

impl TelemetrySender {
    pub fn new(config: Config) -> Result<Self, Box<dyn std::error::Error>> {
        let fs_collector = FsCollector::new(&config.watch_dir)?;
        let process_collector = ProcessCollector::new();
        let network_collector = NetworkCollector::new();
        let registry_collector = RegistryCollector::new();

        Ok(Self {
            config,
            fs_collector,
            process_collector,
            network_collector,
            registry_collector,
            start_time: Instant::now(),
        })
    }

    pub async fn run(&mut self) {
        let client = reqwest::Client::new();
        let url = format!("{}/api/detect", self.config.api_url);
        let mut interval = tokio::time::interval(Duration::from_secs(self.config.interval_secs));

        info!("Starting telemetry loop, sending to {}", url);

        loop {
            interval.tick().await;

            let batch = TelemetryBatch {
                fs: self.fs_collector.take_metrics(),
                process: self.process_collector.collect(),
                network: self.network_collector.collect(),
                registry: self.registry_collector.collect(),
            };

            let uptime_s = self.start_time.elapsed().as_secs();
            let features = extract_features(&batch, self.config.interval_secs, uptime_s);

            let req_body = DetectRequest {
                features: vec![features.to_vec()],
            };

            match client
                .post(&url)
                .header("x-api-key", &self.config.api_key)
                .json(&req_body)
                .send()
                .await
            {
                Ok(resp) => {
                    if resp.status().is_success() {
                        if let Ok(det_resp) = resp.json::<DetectResponse>().await {
                            for result in det_resp.results {
                                self.handle_anomaly(result.anomaly_score, &result.technique)
                                    .await;
                            }
                        }
                    } else {
                        error!("API error: {}", resp.status());
                    }
                }
                Err(e) => {
                    error!("Failed to send telemetry: {}", e);
                }
            }
        }
    }

    async fn handle_anomaly(&self, score: f32, technique: &str) {
        if score > 0.85 {
            let msg = format!(
                "!!! CRITICAL ALERT !!! Anomaly Score: {:.4}, Technique: {}",
                score, technique
            );
            println!("\x1b[31;1m{}\x1b[0m", msg);
            if let Err(e) = self.log_to_file(&msg) {
                error!("Failed to write to log file: {}", e);
            }
        } else if score > 0.5 {
            println!(
                "\x1b[33mWarning: Anomaly detected ({:.4}) - {}\x1b[0m",
                score, technique
            );
        }
    }

    fn log_to_file(&self, msg: &str) -> std::io::Result<()> {
        use std::fs::OpenOptions;
        use std::io::Write;
        let mut file = OpenOptions::new()
            .create(true)
            .append(true)
            .open(&self.config.log_file)?;
        writeln!(file, "[{}] {}", chrono::Local::now(), msg)?;
        Ok(())
    }
}
