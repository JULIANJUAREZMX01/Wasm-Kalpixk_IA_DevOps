import time
import os
import socket
import psutil
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.console import Console
from rich.text import Text
from datetime import datetime

class KalpixkTUI:
    def __init__(self, detector=None, monitor=None):
        self.console = Console()
        self.detector = detector
        self.monitor = monitor
        self.start_time = time.time()
        self.logs = []

    def get_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"

    def make_layout(self) -> Layout:
        layout = Layout()
        layout.split(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=3)
        )
        layout["main"].split_row(
            Layout(name="left", ratio=1),
            Layout(name="right", ratio=2)
        )
        return layout

    def generate_header(self) -> Panel:
        grid = Table.grid(expand=True)
        grid.add_column(justify="left", ratio=1)
        grid.add_column(justify="center", ratio=1)
        grid.add_column(justify="right", ratio=1)

        title = Text("██ KALPIXK SIEM — DEFENSE GRID", style="bold red")
        status = Text(f"● SYSTEM ARMOURED", style="bold green blink")
        clock = Text(datetime.now().strftime("%H:%M:%S"), style="cyan")

        grid.add_row(title, status, clock)
        return Panel(grid, style="red")

    def generate_system_stats(self) -> Panel:
        table = Table.grid(padding=(0, 1))
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory().percent

        table.add_row("CPU Usage:", f"[bold {'red' if cpu > 80 else 'green'}]{cpu}%[/]")
        table.add_row("RAM Usage:", f"[bold {'red' if mem > 80 else 'green'}]{mem}%[/]")
        table.add_row("Uptime:", f"{int(time.time() - self.start_time)}s")

        device = "CPU"
        trained = "No"
        if self.detector:
            device = str(self.detector.device)
            trained = "Yes" if self.detector.is_trained else "No"

        table.add_row("AI Engine:", f"[cyan]{device}[/]")
        table.add_row("Model Trained:", f"[bold {'green' if trained == 'Yes' else 'yellow'}]{trained}[/]")

        return Panel(table, title="System Telemetry", border_style="cyan")

    def add_log(self, vector, score, status):
        ts = datetime.now().strftime("%H:%M:%S")
        self.logs.append((ts, vector, score, status))
        if len(self.logs) > 15:
            self.logs.pop(0)

    def generate_threat_log(self) -> Panel:
        table = Table(box=None, expand=True)
        table.add_column("Time", style="dim", width=10)
        table.add_column("Vector", style="bold")
        table.add_column("Score", justify="right")
        table.add_column("Status")

        if not self.logs:
            table.add_row("-", "Initializing sensors...", "-", "WAITING")
        else:
            for log in reversed(self.logs):
                table.add_row(*log)

        return Panel(table, title="Live Engagement Log", border_style="red")

    def generate_footer(self) -> Panel:
        ip = self.get_ip()
        port = os.getenv("PORT", "8000")
        msg = Text.assemble(
            ("WEB DASHBOARD: ", "cyan"),
            (f"http://{ip}:{port}", "bold white underline"),
            (" | API DOCS: ", "cyan"),
            (f"http://localhost:{port}/docs", "bold white")
        )
        return Panel(msg, style="blue")

    def run(self):
        layout = self.make_layout()
        with Live(layout, refresh_per_second=4, screen=True):
            try:
                while True:
                    if self.monitor and self.detector:
                        m = self.monitor.capture_metrics()
                        res = self.detector.predict(m.to_array())
                        score = res["reconstruction_errors"][0]
                        is_anomaly = res["anomalies"][0]
                        status = "[bold red]THREAT![/]" if is_anomaly else "[green]CLEAN[/]"
                        self.add_log("Runtime Metrics", f"{score:.6f}", status)

                    layout["header"].update(self.generate_header())
                    layout["left"].update(self.generate_system_stats())
                    layout["right"].update(self.generate_threat_log())
                    layout["footer"].update(self.generate_footer())
                    time.sleep(1.0)
            except KeyboardInterrupt:
                pass

if __name__ == "__main__":
    from src.detector import AnomalyDetector
    from src.runtime import WasmRuntimeMonitor
    d = AnomalyDetector()
    m = WasmRuntimeMonitor()
    tui = KalpixkTUI(detector=d, monitor=m)
    tui.run()
