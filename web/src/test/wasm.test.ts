import { describe, it, expect, beforeAll } from "vitest";
import { initWasm, parse_log_line, process_batch, version, health_check } from "../wasm/index";
import * as fs from "fs";
import * as path from "path";

beforeAll(async () => {
  const wasmPath = path.resolve(__dirname, "../../../crates/kalpixk-core/pkg/kalpixk_core_bg.wasm");
  const wasmBuffer = fs.readFileSync(wasmPath);
  global.fetch = async () => new Response(wasmBuffer, { headers: { 'Content-Type': 'application/wasm' } });
  await initWasm();
});

describe("Kalpixk WASM engine", () => {
  it("version() retorna string no vacío", () => {
    const v = version();
    expect(v).toBeTruthy();
    expect(typeof v).toBe("string");
    expect(v).toContain("kalpixk-core");
  });

  it("health_check() retorna feature_dim=32", () => {
    const h = JSON.parse(health_check());
    expect(h.status).toBe("ok");
    expect(h.feature_dim).toBe(32);
  });

  it("parse_log_line detecta SSH brute force", () => {
    const raw =
      "Apr  5 02:14:22 server sshd[123]: Failed password for root from 45.33.32.156 port 22";
    const result = parse_log_line(raw, "syslog");
    expect(result).toBeTruthy();
    const event = JSON.parse(result!);
    expect(event.event_type).toMatch(/login_failure|LoginFailure/i);
    expect(event.local_severity).toBeGreaterThan(0.3);
  });

  it("parse_log_line detecta DROP TABLE en DB2", () => {
    const raw =
      "TIMESTAMP=2026-04-05-02.15.00 AUTHID=CEDIS_USR HOSTNAME=185.220.101.35 OPERATION=DDL STATEMENT=DROP TABLE NOMINAS";
    const result = parse_log_line(raw, "db2");
    expect(result).toBeTruthy();
    const event = JSON.parse(result!);
    expect(event.local_severity).toBeGreaterThan(0.7);
  });

  it("process_batch retorna feature matrix con 32 dimensiones", () => {
    const logs = JSON.stringify([
      "Apr  5 10:00:00 server sshd[1]: Accepted publickey for jjuarez from 192.168.1.50 port 44321",
      "Apr  5 02:00:00 server sshd[2]: Failed password for root from 45.33.32.156 port 22",
    ]);
    const result = process_batch(logs, "syslog");
    const batch = JSON.parse(result);
    expect(batch.parsed_count).toBe(2);
    expect(batch.feature_matrix).toHaveLength(2);
    expect(batch.feature_matrix[0]).toHaveLength(32);
  });

  it("feature matrix contiene exactamente 32 dimensiones", () => {
    const logs = JSON.stringify([
      "Apr  5 10:00:00 server cron[1]: (root) CMD (/bin/backup.sh)",
    ]);
    const result = process_batch(logs, "syslog");
    const batch = JSON.parse(result);
    expect(batch.feature_matrix[0].length).toBe(32);
    // Todos los valores deben estar en [0, 1]
    for (const v of batch.feature_matrix[0]) {
      expect(v).toBeGreaterThanOrEqual(0);
      expect(v).toBeLessThanOrEqual(1.01); // pequeño margen
    }
  });
});
