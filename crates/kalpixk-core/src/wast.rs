//! WAST — WebAssembly Test Format
//! 
//! Testing framework for Kalpixk WASM modules:
//! - Test cases definition
//! - Expected results validation
//! - Test suite execution

use serde::{Deserialize, Serialize};

/// Test case definition
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WastTestCase {
    pub name: String,
    pub input: String,
    pub expected: WastExpectedOutput,
    pub timeout_ms: Option<u64>,
}

/// Expected output for a test
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WastExpectedOutput {
    pub event_type: Option<String>,
    pub severity_min: f64,
    pub severity_max: f64,
    pub should_parse: bool,
}

/// Test result
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WastTestResult {
    pub name: String,
    pub passed: bool,
    pub actual_severity: f64,
    pub expected_severity: f64,
    pub error: Option<String>,
    pub duration_ms: u64,
}

/// Test suite result
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WastSuiteResult {
    pub total: usize,
    pub passed: usize,
    pub failed: usize,
    pub results: Vec<WastTestResult>,
    pub duration_ms: u64,
}

/// Run a test case
pub fn run_test_case(
    case: &WastTestCase,
    parse_fn: fn(&str) -> Result<(String, f64), String>,
) -> WastTestResult {
    let start = std::time::Instant::now();
    
    let result = parse_fn(&case.input);
    let duration_ms = start.elapsed().as_millis() as u64;
    
    match result {
        Ok((event_type, severity)) => {
            let passed = case.expected.should_parse
                && severity >= case.expected.severity_min
                && severity <= case.expected.severity_max;
            
            WastTestResult {
                name: case.name.clone(),
                passed,
                actual_severity: severity,
                expected_severity: (case.expected.severity_min + case.expected.severity_max) / 2.0,
                error: if passed {
                    None
                } else {
                    Some(format!("Severity {} not in range [{}, {}]",
                        severity, case.expected.severity_min, case.expected.severity_max))
                },
                duration_ms,
            }
        }
        Err(e) => {
            WastTestResult {
                name: case.name.clone(),
                passed: !case.expected.should_parse,
                actual_severity: 0.0,
                expected_severity: 0.0,
                error: Some(e),
                duration_ms,
            }
        }
    }
}

/// Run a full test suite
pub fn run_test_suite(
    cases: &[WastTestCase],
    parse_fn: fn(&str) -> Result<(String, f64), String>,
) -> WastSuiteResult {
    let start = std::time::Instant::now();
    
    let results: Vec<WastTestResult> = cases.iter()
        .map(|c| run_test_case(c, parse_fn))
        .collect();
    
    let passed = results.iter().filter(|r| r.passed).count();
    let failed = results.len() - passed;
    let duration_ms = start.elapsed().as_millis() as u64;
    
    WastSuiteResult {
        total: results.len(),
        passed,
        failed,
        results,
        duration_ms,
    }
}

/// Predefined test cases for Kalpixk parsers
pub mod test_cases {
    use super::*;
    
    /// Syslog parser test cases
    pub fn syslog_tests() -> Vec<WastTestCase> {
        vec![
            WastTestCase {
                name: "syslog_ssh_failed_password".to_string(),
                input: "Apr  8 18:00:00 server sshd[123]: Failed password for root from 192.168.1.100 port 22".to_string(),
                expected: WastExpectedOutput {
                    event_type: Some("login_failure".to_string()),
                    severity_min: 0.35,
                    severity_max: 0.55,
                    should_parse: true,
                },
                timeout_ms: Some(100),
            },
            WastTestCase {
                name: "syslog_ssh_success".to_string(),
                input: "Apr  8 18:00:00 server sshd[124]: Accepted password for admin from 192.168.1.50 port 44321".to_string(),
                expected: WastExpectedOutput {
                    event_type: Some("login_success".to_string()),
                    severity_min: 0.05,
                    severity_max: 0.20,
                    should_parse: true,
                },
                timeout_ms: Some(100),
            },
            WastTestCase {
                name: "syslog_sudo_command".to_string(),
                input: "Apr  8 18:00:00 server sudo[456]: user : TTY=pts/0 ; PWD=/home/user ; USER=root ; COMMAND=/bin/rm -rf /tmp/*".to_string(),
                expected: WastExpectedOutput {
                    event_type: Some("process_execution".to_string()),
                    severity_min: 0.40,
                    severity_max: 0.60,
                    should_parse: true,
                },
                timeout_ms: Some(100),
            },
            WastTestCase {
                name: "syslog_user_creation".to_string(),
                input: "Apr  8 18:00:00 server useradd[789]: new user: name=hacker uid=1005 gid=1005".to_string(),
                expected: WastExpectedOutput {
                    event_type: Some("user_creation".to_string()),
                    severity_min: 0.60,
                    severity_max: 0.80,
                    should_parse: true,
                },
                timeout_ms: Some(100),
            },
        ]
    }
    
    /// JSON parser test cases
    pub fn json_tests() -> Vec<WastTestCase> {
        vec![
            WastTestCase {
                name: "json_login_success".to_string(),
                input: r#"{"event_type": "login_success", "user": "admin", "src_ip": "192.168.1.50", "severity": 0.15}"#.to_string(),
                expected: WastExpectedOutput {
                    event_type: Some("login_success".to_string()),
                    severity_min: 0.10,
                    severity_max: 0.20,
                    should_parse: true,
                },
                timeout_ms: Some(100),
            },
            WastTestCase {
                name: "json_db_query_dangerous".to_string(),
                input: r#"{"event_type": "db_query", "sql": "DROP TABLE users", "src_ip": "10.0.0.5"}"#.to_string(),
                expected: WastExpectedOutput {
                    event_type: Some("db_anomalous_query".to_string()),
                    severity_min: 0.70,
                    severity_max: 0.95,
                    should_parse: true,
                },
                timeout_ms: Some(100),
            },
        ]
    }
    
    /// Windows Event parser test cases
    pub fn windows_tests() -> Vec<WastTestCase> {
        vec![
            WastTestCase {
                name: "windows_login_success_4624".to_string(),
                input: "EventID: 4624 SubjectUserName: ADMINISTRATOR".to_string(),
                expected: WastExpectedOutput {
                    event_type: Some("login_success".to_string()),
                    severity_min: 0.05,
                    severity_max: 0.20,
                    should_parse: true,
                },
                timeout_ms: Some(100),
            },
            WastTestCase {
                name: "windows_privilege_escalation_4672".to_string(),
                input: "EventID: 4672 SubjectUserName: HACKER".to_string(),
                expected: WastExpectedOutput {
                    event_type: Some("privilege_escalation".to_string()),
                    severity_min: 0.65,
                    severity_max: 0.85,
                    should_parse: true,
                },
                timeout_ms: Some(100),
            },
            WastTestCase {
                name: "windows_user_creation_4720".to_string(),
                input: "EventID: 4720 SubjectUserName: ADMIN".to_string(),
                expected: WastExpectedOutput {
                    event_type: Some("user_creation".to_string()),
                    severity_min: 0.60,
                    severity_max: 0.80,
                    should_parse: true,
                },
                timeout_ms: Some(100),
            },
        ]
    }
    
    /// DB2 parser test cases
    pub fn db2_tests() -> Vec<WastTestCase> {
        vec![
            WastTestCase {
                name: "db2_drop_table".to_string(),
                input: "AUTHID=ADMIN HOSTNAME=DB2SERV DROP TABLE INVENTORY".to_string(),
                expected: WastExpectedOutput {
                    event_type: Some("db_anomalous_query".to_string()),
                    severity_min: 0.75,
                    severity_max: 0.95,
                    should_parse: true,
                },
                timeout_ms: Some(100),
            },
            WastTestCase {
                name: "db2_data_exfiltration".to_string(),
                input: "AUTHID=APP_HOST HOSTNAME=WMS EXPORT TO /tmp/data.csv".to_string(),
                expected: WastExpectedOutput {
                    event_type: Some("db_anomalous_query".to_string()),
                    severity_min: 0.60,
                    severity_max: 0.85,
                    should_parse: true,
                },
                timeout_ms: Some(100),
            },
        ]
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    fn mock_parse(input: &str) -> Result<(String, f64), String> {
        let lower = input.to_lowercase();
        if lower.contains("failed") || lower.contains("failure") {
            Ok(("login_failure".to_string(), 0.45))
        } else if lower.contains("drop") || lower.contains("truncate") {
            Ok(("db_anomalous_query".to_string(), 0.85))
        } else {
            Ok(("login_success".to_string(), 0.15))
        }
    }
    
    #[test]
    fn test_run_single_test() {
        let case = WastTestCase {
            name: "test_basic".to_string(),
            input: "Failed password".to_string(),
            expected: WastExpectedOutput {
                event_type: Some("login_failure".to_string()),
                severity_min: 0.3,
                severity_max: 0.5,
                should_parse: true,
            },
            timeout_ms: None,
        };
        
        let result = run_test_case(&case, mock_parse);
        assert!(result.passed);
    }
    
    #[test]
    fn test_run_suite() {
        let cases = test_cases::syslog_tests();
        let result = run_test_suite(&cases, mock_parse);
        
        println!("Total: {}, Passed: {}, Failed: {}", 
            result.total, result.passed, result.failed);
        
        // Most should pass
        assert!(result.passed >= result.total / 2);
    }
}