use notify::{Event, EventKind, RecursiveMode, Watcher};
use std::collections::HashSet;
use std::path::Path;
use std::sync::{Arc, Mutex};
use std::time::Instant;

#[derive(Debug, Clone, Default)]
pub struct FsMetrics {
    pub bytes_written: u64,
    pub files_opened: u64,
    pub entropy_sum: f64,
    pub entropy_max: f64,
    pub entropy_count: u64,
    pub reads: u64,
    pub writes: u64,
    pub unique_extensions: HashSet<String>,
    pub deletes: u64,
    pub renames: u64,
    pub max_depth: usize,
    pub total_ops: u64,
}

pub struct FsCollector {
    metrics: Arc<Mutex<FsMetrics>>,
    _watcher: Box<dyn Watcher>,
    _start_time: Instant,
}

impl FsCollector {
    pub fn new(watch_dir: &str) -> Result<Self, Box<dyn std::error::Error>> {
        let metrics = Arc::new(Mutex::new(FsMetrics::default()));
        let m_clone = metrics.clone();

        let mut watcher = notify::recommended_watcher(move |res: notify::Result<Event>| {
            if let Ok(event) = res {
                let mut m = m_clone.lock().unwrap();
                m.total_ops += 1;

                match event.kind {
                    EventKind::Access(_) => {
                        m.files_opened += 1;
                        m.reads += 1;
                    }
                    EventKind::Create(_) => {
                        m.writes += 1;
                    }
                    EventKind::Modify(mod_kind) => {
                        m.writes += 1;
                        if let notify::event::ModifyKind::Data(_) = mod_kind {
                            for path in &event.paths {
                                if let Ok(data) = std::fs::read(path) {
                                    m.bytes_written += data.len() as u64;
                                    let entropy = calculate_entropy(&data);
                                    m.entropy_sum += entropy;
                                    m.entropy_max = m.entropy_max.max(entropy);
                                    m.entropy_count += 1;
                                }
                            }
                        }
                        if let notify::event::ModifyKind::Name(_) = mod_kind {
                            m.renames += 1;
                        }
                    }
                    EventKind::Remove(_) => {
                        m.deletes += 1;
                    }
                    _ => {}
                }

                for path in &event.paths {
                    if let Some(ext) = path.extension().and_then(|e| e.to_str()) {
                        m.unique_extensions.insert(ext.to_string());
                    }
                    let depth = path.components().count();
                    m.max_depth = m.max_depth.max(depth);
                }
            }
        })?;

        watcher.watch(Path::new(watch_dir), RecursiveMode::Recursive)?;

        Ok(Self {
            metrics,
            _watcher: Box::new(watcher),
            _start_time: Instant::now(),
        })
    }

    pub fn take_metrics(&self) -> FsMetrics {
        let mut m = self.metrics.lock().unwrap();
        let current = m.clone();

        let reset = FsMetrics {
            unique_extensions: current.unique_extensions.clone(),
            max_depth: current.max_depth,
            ..FsMetrics::default()
        };
        *m = reset;

        current
    }
}

fn calculate_entropy(data: &[u8]) -> f64 {
    if data.is_empty() {
        return 0.0;
    }
    let mut frequencies = [0usize; 256];
    for &b in data {
        frequencies[b as usize] += 1;
    }
    let len = data.len() as f64;
    let mut entropy = 0.0;
    for &count in &frequencies {
        if count > 0 {
            let p = count as f64 / len;
            entropy -= p * p.log2();
        }
    }
    entropy / 8.0 // Normalize to 0.0 - 1.0
}
