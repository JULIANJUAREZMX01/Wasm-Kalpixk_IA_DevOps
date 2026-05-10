use sysinfo::{CpuExt, ProcessExt, System, SystemExt};

pub struct ProcessCollector {
    sys: System,
}

#[derive(Default, Clone)]
pub struct ProcessMetrics {
    pub cpu_usage: f32,
    pub process_injection_detected: bool,
    pub parent_child_anomaly: bool,
    pub lsass_access: bool,
}

impl ProcessCollector {
    pub fn new() -> Self {
        let mut sys = System::new_all();
        sys.refresh_all();
        Self { sys }
    }

    pub fn collect(&mut self) -> ProcessMetrics {
        self.sys.refresh_all();
        let mut metrics = ProcessMetrics {
            cpu_usage: self.sys.global_cpu_info().cpu_usage(),
            ..ProcessMetrics::default()
        };

        for process in self.sys.processes().values() {
            let name = process.name().to_lowercase();

            // [18] parent_child_anomaly: detect cmd.exe spawned by non-shell
            if name == "cmd.exe" || name == "powershell.exe" {
                if let Some(parent_pid) = process.parent() {
                    if let Some(parent) = self.sys.process(parent_pid) {
                        let p_name = parent.name().to_lowercase();
                        let is_shell = p_name == "explorer.exe"
                            || p_name == "cmd.exe"
                            || p_name == "powershell.exe"
                            || p_name == "services.exe";
                        if !is_shell {
                            metrics.parent_child_anomaly = true;
                        }
                    }
                }
            }

            // [16] process_injection: suspicious parent PID
            if let Some(parent_pid) = process.parent() {
                if self.sys.process(parent_pid).is_none() {
                    metrics.process_injection_detected = true;
                }
            }
        }

        metrics
    }
}
