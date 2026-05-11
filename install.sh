#!/bin/bash

# Kalpixk Agent Installer (Linux/macOS)
# ATLATL-ORDNANCE Protocol v5.0

set -e

echo "🏹 Kalpixk Agent Installer Starting..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (use sudo)"
  exit 1
fi

# 1. Download binary
BINARY_URL="https://github.com/JULIANJUAREZMX01/Wasm-Kalpixk_IA_DevOps/releases/latest/download/kalpixk-agent-linux"
INSTALL_PATH="/usr/local/bin/kalpixk-agent"

echo "Downloading binary from $BINARY_URL..."
curl -sL "$BINARY_URL" -o "$INSTALL_PATH"
chmod +x "$INSTALL_PATH"

# 2. Prompt for configuration
# Using /dev/tty to allow reading input when script is piped (e.g. curl | bash)
read -p "Enter API_URL [http://localhost:8000]: " API_URL < /dev/tty
API_URL=${API_URL:-http://localhost:8000}

read -p "Enter API_KEY: " API_KEY < /dev/tty

# 3. Create configuration file
CONFIG_PATH="/etc/kalpixk-agent.toml"
echo "Creating configuration at $CONFIG_PATH..."

cat <<EOF > "$CONFIG_PATH"
api_url = "$API_URL"
api_key = "$API_KEY"
watch_dir = "/tmp"
interval_secs = 2
log_file = "/var/log/kalpixk-agent.log"
EOF

# 4. Create systemd service
SERVICE_PATH="/etc/systemd/system/kalpixk-agent.service"
echo "Creating systemd service at $SERVICE_PATH..."

cat <<EOF > "$SERVICE_PATH"
[Unit]
Description=Kalpixk Agent - OS Monitoring
After=network.target

[Service]
ExecStart=$INSTALL_PATH --config $CONFIG_PATH
Restart=always
User=root

[Install]
WantedBy=multi-user.target
EOF

# 5. Start service
echo "Starting kalpixk-agent service..."
systemctl daemon-reload
systemctl enable kalpixk-agent
systemctl start kalpixk-agent

echo "✅ Kalpixk Agent installed and started successfully!"
systemctl status kalpixk-agent --no-pager
