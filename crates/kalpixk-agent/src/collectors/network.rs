use std::collections::HashSet;
use sysinfo::{NetworkExt, System, SystemExt};

pub struct NetworkCollector {
    sys: System,
}

#[derive(Default, Clone)]
pub struct NetworkMetrics {
    pub outbound_connections: u64,
    pub dst_port_diversity: usize,
}

impl NetworkCollector {
    pub fn new() -> Self {
        let mut sys = System::new_all();
        sys.refresh_networks_list();
        Self { sys }
    }

    pub fn collect(&mut self) -> NetworkMetrics {
        self.sys.refresh_networks();

        let mut metrics = NetworkMetrics::default();
        let mut ports = HashSet::new();

        for (_interface_name, data) in self.sys.networks() {
            metrics.outbound_connections += data.packets_transmitted();
            if data.transmitted() > 0 {
                ports.insert((data.transmitted() % 1024) as u16);
            }
        }

        metrics.dst_port_diversity = ports.len();

        metrics
    }
}
