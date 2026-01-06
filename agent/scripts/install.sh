#!/bin/bash
# Device Inventory Agent Installer
# Supports: Ubuntu, Debian, Pop!_OS, and other Debian-based distros

set -e

INSTALL_DIR="/opt/inventory-agent"
CONFIG_DIR="/etc/inventory-agent"
SERVICE_NAME="inventory-agent"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Device Inventory Agent Installer${NC}"
echo -e "${GREEN}========================================${NC}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run as root (use sudo)${NC}"
    exit 1
fi

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${YELLOW}Installing from: $AGENT_DIR${NC}"

# Install Python dependencies
echo -e "${GREEN}[1/5] Installing system dependencies...${NC}"
apt-get update -qq
apt-get install -y -qq python3 python3-pip python3-venv > /dev/null

# Create installation directory
echo -e "${GREEN}[2/5] Creating installation directory...${NC}"
mkdir -p "$INSTALL_DIR"
mkdir -p "$CONFIG_DIR"

# Copy agent files
echo -e "${GREEN}[3/5] Copying agent files...${NC}"
cp -r "$AGENT_DIR/src" "$INSTALL_DIR/"
cp "$AGENT_DIR/requirements.txt" "$INSTALL_DIR/"
cp "$AGENT_DIR/run.py" "$INSTALL_DIR/"

# Create virtual environment and install dependencies
echo -e "${GREEN}[4/5] Setting up Python environment...${NC}"
python3 -m venv "$INSTALL_DIR/venv"
"$INSTALL_DIR/venv/bin/pip" install --quiet --upgrade pip
"$INSTALL_DIR/venv/bin/pip" install --quiet -r "$INSTALL_DIR/requirements.txt"

# Create default config if not exists
if [ ! -f "$CONFIG_DIR/agent.json" ]; then
    echo -e "${GREEN}[5/5] Creating default configuration...${NC}"
    cat > "$CONFIG_DIR/agent.json" << 'EOF'
{
  "api_url": "http://localhost:5000",
  "api_key": "default-api-key-change-in-production",
  "check_in_interval": 300,
  "max_retries": 3,
  "retry_delay": 5,
  "request_timeout": 30,
  "log_level": "INFO"
}
EOF
    echo -e "${YELLOW}NOTE: Edit /etc/inventory-agent/agent.json to configure the agent${NC}"
else
    echo -e "${GREEN}[5/5] Keeping existing configuration...${NC}"
fi

# Create systemd service
cat > /etc/systemd/system/${SERVICE_NAME}.service << EOF
[Unit]
Description=Device Inventory Agent
After=network.target

[Service]
Type=simple
ExecStart=${INSTALL_DIR}/venv/bin/python ${INSTALL_DIR}/run.py
WorkingDirectory=${INSTALL_DIR}
Environment=INVENTORY_CONFIG_PATH=${CONFIG_DIR}/agent.json
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
systemctl daemon-reload

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Installation Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "Configuration file: ${YELLOW}/etc/inventory-agent/agent.json${NC}"
echo ""
echo -e "Commands:"
echo -e "  Start agent:   ${YELLOW}sudo systemctl start inventory-agent${NC}"
echo -e "  Stop agent:    ${YELLOW}sudo systemctl stop inventory-agent${NC}"
echo -e "  View status:   ${YELLOW}sudo systemctl status inventory-agent${NC}"
echo -e "  View logs:     ${YELLOW}sudo journalctl -u inventory-agent -f${NC}"
echo -e "  Enable on boot: ${YELLOW}sudo systemctl enable inventory-agent${NC}"
echo ""
echo -e "${YELLOW}Don't forget to edit the config file with your server URL!${NC}"
