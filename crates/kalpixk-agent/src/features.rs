use crate::collectors::TelemetryBatch;
use std::time::{SystemTime, UNIX_EPOCH};

pub fn extract_features(batch: &TelemetryBatch, interval_secs: u64, uptime_s: u64) -> [f32; 32] {
    let mut f = [0.0f32; 32];

    // [0] bytes_written_per_sec
    f[0] = batch.fs.bytes_written as f32 / interval_secs as f32;
    // [1] files_opened_per_sec
    f[1] = batch.fs.files_opened as f32 / interval_secs as f32;
    // [2] entropy_avg
    f[2] = if batch.fs.entropy_count > 0 {
        (batch.fs.entropy_sum / batch.fs.entropy_count as f64) as f32
    } else {
        0.0
    };
    // [3] entropy_max
    f[3] = batch.fs.entropy_max as f32;
    // [4] read_write_ratio
    f[4] = if batch.fs.writes > 0 {
        batch.fs.reads as f32 / batch.fs.writes as f32
    } else {
        batch.fs.reads as f32
    };
    // [5] unique_extensions
    f[5] = batch.fs.unique_extensions.len() as f32;
    // [6] delete_rename_ratio
    f[6] = if batch.fs.total_ops > 0 {
        (batch.fs.deletes + batch.fs.renames) as f32 / batch.fs.total_ops as f32
    } else {
        0.0
    };
    // [7] dir_traversal_depth
    f[7] = batch.fs.max_depth as f32;
    // [8] outbound_connections
    f[8] = batch.network.outbound_connections as f32;
    // [9] dst_port_diversity
    f[9] = batch.network.dst_port_diversity as f32;
    // [10] dns_query_anomaly
    f[10] = 0.0;
    // [11] beaconing_detected
    f[11] = 0.0;
    // [12] payload_size_bytes
    f[12] = if batch.fs.writes > 0 {
        batch.fs.bytes_written as f32 / batch.fs.writes as f32
    } else {
        0.0
    };
    // [13] ttl_avg
    f[13] = 64.0;
    // [14] failed_auth_count
    f[14] = 0.0;
    // [15] tls_fingerprint_score
    f[15] = 0.0;
    // [16] process_injection
    f[16] = if batch.process.process_injection_detected {
        1.0
    } else {
        0.0
    };
    // [17] hollow_process
    f[17] = 0.0;
    // [18] parent_child_anomaly
    f[18] = if batch.process.parent_child_anomaly {
        1.0
    } else {
        0.0
    };
    // [19] lsass_access
    f[19] = if batch.process.lsass_access { 1.0 } else { 0.0 };
    // [20] cpu_spike_pct
    f[20] = batch.process.cpu_usage;
    // [21] scheduled_task_created
    f[21] = 0.0;
    // [22] registry_autorun_write
    f[22] = if batch.registry.autorun_write {
        1.0
    } else {
        0.0
    };
    // [23] wmi_event_consumer
    f[23] = 0.0;

    let now = SystemTime::now().duration_since(UNIX_EPOCH).unwrap();
    let seconds_since_midnight = now.as_secs() % 86400;
    let ms_since_midnight = (seconds_since_midnight * 1000) + (now.subsec_millis() as u64);

    // [24] time_of_day_ms
    f[24] = ms_since_midnight as f32;
    // [25] user_behavior_deviation
    f[25] = 0.0;
    // [26] after_hours_activity
    let hour = seconds_since_midnight / 3600;
    // Requirements: < 6h or > 22h.
    // If hour is 22, it's between 22:00:00 and 22:59:59, which is > 22h.
    f[26] = if !(6..22).contains(&hour) { 1.0 } else { 0.0 };
    // [27] session_duration_s
    f[27] = uptime_s as f32;
    // [28] geo_anomaly_score
    f[28] = 0.0;
    // [29] lateral_movement_graph
    f[29] = 0.0;
    // [30] privilege_escalation_score
    f[30] = 0.0;
    // [31] composite_threat_score
    f[31] = f[2] * 0.4 + (f[20] / 100.0) * 0.3 + (f[8] / 1000.0) * 0.3;

    f
}
