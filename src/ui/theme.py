"""
Kalpixk Visual Theme — portado del sistema dhell/SACITY
Paleta: Rojo/Negro/Gris + Verde Virus + Azul Cyber (estética hacker-AMD)
"""

class ANSI:
    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    DIM    = "\033[2m"
    BLINK  = "\033[5m"

    # Rojos (dominantes — identidad Kalpixk/SACITY)
    RED        = "\033[31m"
    RED_BRIGHT = "\033[91m"
    RED_BOLD   = "\033[1;31m"
    RED_BG     = "\033[41m"

    # Acento AMD
    ORANGE     = "\033[38;2;255;100;0m"   # Naranja fuego AMD
    AMD_RED    = "\033[38;2;237;28;36m"   # Rojo oficial AMD

    # Estados del sistema
    GREEN      = "\033[38;2;50;255;50m"   # Verde virus — OK
    CYAN       = "\033[38;2;0;200;255m"   # Azul cyber — info
    YELLOW     = "\033[33m"               # Advertencia
    GRAY       = "\033[38;2;100;100;100m" # Secundario

    # Fondos
    BG_BLACK   = "\033[40m"
    BG_RED     = "\033[41m"


class KalpixkTheme:
    """Arte ASCII y banners del sistema Kalpixk."""

    BANNER = f"""
{ANSI.RED_BRIGHT}{ANSI.BOLD}
██╗  ██╗ █████╗ ██╗     ██████╗ ██╗██╗  ██╗██╗  ██╗
██║ ██╔╝██╔══██╗██║     ██╔══██╗██║╚██╗██╔╝██║ ██╔╝
█████╔╝ ███████║██║     ██████╔╝██║ ╚███╔╝ █████╔╝
██╔═██╗ ██╔══██║██║     ██╔═══╝ ██║ ██╔██╗ ██╔═██╗
██║  ██╗██║  ██║███████╗██║     ██║██╔╝ ██╗██║  ██╗
╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝
{ANSI.RESET}{ANSI.AMD_RED}  ⚡ WASM Anomaly Detection Engine — AMD MI300X{ANSI.RESET}
{ANSI.GRAY}  del náhuatl: "el que cuenta" | by JULIANJUAREZMX01{ANSI.RESET}
"""

    BOOT_MSGS = [
        "INITIALIZING KALPIXK ANOMALY ENGINE...",
        "LOADING AMD MI300X NEURAL CORES...",
        "WASM RUNTIME MONITOR ONLINE...",
        "CONNECTING TO KYNIC NETWORK...",
        "ANOMALY DETECTION ARMED ✓",
    ]

    STATUS = {
        "ok":      f"{ANSI.GREEN}[  OK  ]{ANSI.RESET}",
        "error":   f"{ANSI.RED_BRIGHT}[ FAIL ]{ANSI.RESET}",
        "warn":    f"{ANSI.YELLOW}[ WARN ]{ANSI.RESET}",
        "info":    f"{ANSI.CYAN}[ INFO ]{ANSI.RESET}",
        "anomaly": f"{ANSI.RED_BG}{ANSI.BOLD}[ANOMALY]{ANSI.RESET}",
    }

    @staticmethod
    def print_banner():
        print(KalpixkTheme.BANNER)

    @staticmethod
    def print_boot():
        import time
        for msg in KalpixkTheme.BOOT_MSGS:
            print(f"{ANSI.RED_BRIGHT}>{ANSI.RESET} {ANSI.DIM}{msg}{ANSI.RESET}")
            time.sleep(0.15)
        print()

    @staticmethod
    def status_line(label: str, value: str, status: str = "ok") -> str:
        tag = KalpixkTheme.STATUS.get(status, "")
        return f"{tag} {ANSI.CYAN}{label:<20}{ANSI.RESET} {value}"
