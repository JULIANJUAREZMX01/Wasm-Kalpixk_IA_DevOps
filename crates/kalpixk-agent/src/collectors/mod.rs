pub mod fs;
pub mod network;
pub mod process;
pub mod registry;

pub use fs::{FsCollector, FsMetrics};
pub use network::{NetworkCollector, NetworkMetrics};
pub use process::{ProcessCollector, ProcessMetrics};
pub use registry::{RegistryCollector, RegistryMetrics};

#[derive(Clone)]
pub struct TelemetryBatch {
    pub fs: FsMetrics,
    pub process: ProcessMetrics,
    pub network: NetworkMetrics,
    pub registry: RegistryMetrics,
}
