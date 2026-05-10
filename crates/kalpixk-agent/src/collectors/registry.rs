#[cfg(windows)]
use winreg::enums::*;
#[cfg(windows)]
use winreg::RegKey;

#[derive(Default, Clone)]
pub struct RegistryMetrics {
    pub autorun_write: bool,
}

pub struct RegistryCollector {}

impl RegistryCollector {
    pub fn new() -> Self {
        Self {}
    }

    #[cfg(windows)]
    pub fn collect(&self) -> RegistryMetrics {
        let mut metrics = RegistryMetrics::default();
        let hkcu = RegKey::predef(HKEY_CURRENT_USER);
        if let Ok(_run_key) = hkcu.open_subkey("Software\\Microsoft\\Windows\\CurrentVersion\\Run")
        {
            // In a real agent, we'd watch for changes.
            // For now, just returning default.
        }
        metrics
    }

    #[cfg(not(windows))]
    pub fn collect(&self) -> RegistryMetrics {
        RegistryMetrics::default()
    }
}
