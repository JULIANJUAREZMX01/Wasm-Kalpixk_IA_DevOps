#!/usr/bin/env python3
"""
Kalpixk Attack Simulator — Ransomware Demo
Simulates benign activity → ransomware entropy spike for AMD Hackathon demo.

Usage:
    python scripts/simulate_attack.py
    python scripts/simulate_attack.py --backend-url http://localhost:8000
"""

import argparse
import math
import os
import random
import sys
import time
from collections.abc import Generator
from pathlib import Path

import requests

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import track

    RICH = True
    console = Console()
except ImportError:
    RICH = False

TARGET_DIR = Path("/tmp/kalpixk_target")
NUM_FILES = 50

BENIGN_TEXTS = [
    "2026-05-11 10:23:41 INFO  [kernel] systemd: Started Session 5 of user root.\n",
    "2026-05-11 10:24:05 WARN  [sshd] pam_unix(sshd:auth): authentication failure; user=admin\n",
    "2026-05-11 10:24:22 INFO  [nginx] 192.168.1.1 - GET /api/health HTTP/1.1 200 42\n",
    "2026-05-11 10:25:01 INFO  [cron] kalpixk-agent started, monitoring /var/log\n",
    "2026-05-11 10:25:44 DEBUG [kalpixk] entropy=0.12 files_per_sec=2.1 cpu=18.4\n",
]


def log(msg: str, level: str = "INFO") -> None:
    if RICH:
        color = {"INFO": "cyan", "WARN": "yellow", "CRIT": "red bold"}.get(level, "white")
        console.print(f"[{color}][{level}][/{color}] {msg}")
    else:
        print(f"[{level}] {msg}", flush=True)


def shannon_entropy(data: bytes) -> float:
    if not data:
        return 0.0
    freq: dict[int, int] = {}
    for b in data:
        freq[b] = freq.get(b, 0) + 1
    n = len(data)
    return -sum((c / n) * math.log2(c / n) for c in freq.values() if c > 0) / 8.0


def build_features(
    write_entropy: float,
    files_per_sec: float,
    unique_ext: int,
    cpu: float,
    mem_mb: float,
    phase: str,
) -> list[float]:
    """Build a 32-float feature vector compatible with the Kalpixk detection model."""
    base: list[float] = [
        write_entropy,       # [0] write_entropy
        files_per_sec,       # [1] files_modified_per_sec
        float(unique_ext),   # [2] unique_extensions_written
        cpu,                 # [3] cpu_usage_percent
        mem_mb,              # [4] memory_usage_mb
        float(phase == "attack") * 4.0,  # [5] process_tree_depth proxy
    ]
    # Pad to 32 with realistic noise
    rng = random.Random(42 if phase == "attack" else 7)
    while len(base) < 32:
        base.append(round(rng.uniform(0.01, 0.3 if phase == "normal" else 0.9), 4))
    return base[:32]


def send_event(backend_url: str, features: list[float], source: str = "simulator") -> dict:
    try:
        resp = requests.post(
            f"{backend_url}/api/detect",
            json={"features": features, "source": source, "raw_log": None},
            timeout=3,
        )
        return resp.json() if resp.ok else {"error": resp.status_code}
    except Exception as exc:
        return {"error": str(exc)}


def setup_target_dir() -> None:
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    for i in range(NUM_FILES):
        fpath = TARGET_DIR / f"syslog_{i:04d}.txt"
        content = "".join(random.choices(BENIGN_TEXTS, k=20))
        fpath.write_text(content, encoding="utf-8")
    log(f"Created {NUM_FILES} target files in {TARGET_DIR}")


def run_benign_phase(backend_url: str, duration: int = 30) -> None:
    log("Phase 1: Benign activity (30s)...", "INFO")
    start = time.time()
    file_list = list(TARGET_DIR.glob("*.txt"))
    count = 0
    while time.time() - start < duration:
        # Write 2-3 files per second
        for _ in range(random.randint(2, 3)):
            f = random.choice(file_list)
            f.write_text(
                "".join(random.choices(BENIGN_TEXTS, k=15)),
                encoding="utf-8",
            )
            count += 1
        features = build_features(
            write_entropy=round(random.uniform(0.08, 0.15), 3),
            files_per_sec=round(random.uniform(2.0, 3.0), 2),
            unique_ext=1,
            cpu=round(random.uniform(15.0, 25.0), 1),
            mem_mb=round(random.uniform(180.0, 220.0), 1),
            phase="normal",
        )
        result = send_event(backend_url, features)
        score = result.get("anomaly_score", result.get("score", "?"))
        log(f"entropy=0.11 files/s=2.4 | anomaly_score={score}", "INFO")
        time.sleep(1)
    log(f"Benign phase done. Files modified: {count}")


def run_attack_phase(backend_url: str) -> None:
    log("☠  Phase 2: RANSOMWARE DETECTED — mass encryption starting...", "CRIT")
    file_list = list(TARGET_DIR.glob("*.txt"))
    t0 = time.time()

    # Overwrite all files with random bytes in <5 seconds
    for f in file_list:
        f.write_bytes(os.urandom(random.randint(512, 4096)))

    elapsed = time.time() - t0
    fps = len(file_list) / max(elapsed, 0.01)
    log(f"Encrypted {len(file_list)} files in {elapsed:.2f}s ({fps:.0f} files/sec)", "CRIT")

    # Send high-entropy feature vector
    features = build_features(
        write_entropy=0.974,
        files_per_sec=round(fps, 1),
        unique_ext=3,
        cpu=87.4,
        mem_mb=512.0,
        phase="attack",
    )
    result = send_event(backend_url, features, source="ransomware_sim")
    score = result.get("anomaly_score", result.get("score", "?"))
    if RICH:
        console.print(
            Panel.fit(
                f"[red bold]⚠ ANOMALY SCORE: {score}[/red bold]\n"
                f"[red]write_entropy=0.974 | files/sec={fps:.0f} | CRITICAL[/red]",
                title="[red bold]KALPIXK ALERT[/red bold]",
            )
        )
    else:
        log(f"⚠  ANOMALY SCORE: {score} | write_entropy=0.974 | CRITICAL", "CRIT")


def cleanup() -> None:
    if TARGET_DIR.exists():
        import shutil
        shutil.rmtree(TARGET_DIR)
        log(f"Cleaned up {TARGET_DIR}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Kalpixk Ransomware Attack Simulator")
    parser.add_argument("--backend-url", default="http://localhost:8000", help="Backend API URL")
    parser.add_argument("--no-cleanup", action="store_true", help="Keep target directory after run")
    args = parser.parse_args()

    if RICH:
        console.print(Panel.fit(
            "[cyan bold]KALPIXK — Attack Simulator[/cyan bold]\n"
            "[dim]AMD Hackathon Demo | Ransomware Detection[/dim]",
        ))

    log(f"Backend: {args.backend_url}")

    try:
        setup_target_dir()
        run_benign_phase(args.backend_url, duration=30)
        run_attack_phase(args.backend_url)
    finally:
        if not args.no_cleanup:
            cleanup()

    log("Simulation complete.", "INFO")


if __name__ == "__main__":
    main()
