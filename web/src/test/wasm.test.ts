import { describe, it, expect, beforeAll } from 'vitest'
import { initWasm, parse_log_line, process_batch, version, health_check } from '../wasm/index'

beforeAll(async () => {
  await initWasm()
})

describe('Kalpixk WASM engine', () => {
  it('version() retorna string no vacío', () => {
    expect(version()).toBeTruthy()
    expect(typeof version()).toBe('string')
  })

  it('health_check() retorna feature_dim=32', () => {
    const health = JSON.parse(health_check());
    expect(health.status).toBe('ok');
    expect(health.feature_dim).toBe(32);
  })

  it('parse_log_line detecta SSH brute force', () => {
    const raw = 'Apr 5 02:14:22 server sshd[123]: Failed password for root from 45.33.32.156 port 22'
    const result = parse_log_line(raw, 'syslog')
    expect(result).toBeTruthy()
    const event = JSON.parse(result!)
    expect(event.event_type).toBe('login_failure')
    expect(event.local_severity).toBeGreaterThan(0.3)
  })

  it('parse_log_line detecta DROP TABLE en DB2', () => {
    const raw = 'TIMESTAMP=2026-04-05-02.15.00 AUTHID=CEDIS_USR STATEMENT=DROP TABLE NOMINAS'
    const result = parse_log_line(raw, 'db2')
    expect(result).toBeTruthy()
    const event = JSON.parse(result!)
    expect(event.event_type).toBe('db_anomalous_query')
    expect(event.local_severity).toBeGreaterThan(0.8)
  })

  it('process_batch retorna feature matrix con 32 dimensiones', () => {
    const logs = JSON.stringify([
      'Apr 5 10:00:00 server sshd[1]: Accepted publickey for jjuarez from 192.168.1.50',
      'Apr 5 02:00:00 server sshd[2]: Failed password for root from 45.33.32.156'
    ])
    const result = process_batch(logs, 'syslog')
    const batch = JSON.parse(result)
    expect(batch.parsed_count).toBe(2)
    expect(batch.feature_matrix).toHaveLength(2)
    expect(batch.feature_matrix[0]).toHaveLength(32)
  })
})
