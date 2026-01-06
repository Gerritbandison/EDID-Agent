#!/bin/bash
#
# Device Inventory Agent - Linux Installer
#

set -e

INSTALL_DIR="/opt/inventory-agent"
CONFIG_DIR="/etc/inventory-agent"
LOG_DIR="/var/log/inventory-agent"
SERVICE_NAME="inventory-agent"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}Device Inventory Agent Installer${NC}"
echo "=================================="

# Check root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run as root or with sudo${NC}"
    exit 1
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is required but not installed.${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "Python version: $PYTHON_VERSION"

# Get API configuration
echo ""
read -p "API Server URL [http://localhost:5000]: " API_URL
API_URL=${API_URL:-http://localhost:5000}

read -p "API Key: " API_KEY

read -p "Check-in interval (seconds) [1800]: " CHECK_IN_INTERVAL
CHECK_IN_INTERVAL=${CHECK_IN_INTERVAL:-1800}

# Create directories
echo ""
echo "Creating directories..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$CONFIG_DIR"
mkdir -p "$LOG_DIR"

# Copy files
echo "Installing agent files..."
cp -r src/* "$INSTALL_DIR/"
cp requirements.txt "$INSTALL_DIR/"

# Install dependencies
echo "Installing Python dependencies..."
pip3 install -r "$INSTALL_DIR/requirements.txt" --quiet

# Create configuration
echo "Creating configuration..."
cat > "$CONFIG_DIR/config.json" << EOF
{
  "api_url": "$API_URL",
  "api_key": "$API_KEY",
  "check_in_interval": $CHECK_IN_INTERVAL,
  "max_retries": 3,
  "retry_delay": 5,
  "request_timeout": 30,
  "log_level": "INFO"
}
EOF

chmod 600 "$CONFIG_DIR/config.json"

# Create environment file
cat > "$CONFIG_DIR/environment" << EOF
INVENTORY_API_URL=$API_URL
INVENTORY_API_KEY=$API_KEY
INVENTORY_CHECK_IN_INTERVAL=$CHECK_IN_INTERVAL
EOF

chmod 600 "$CONFIG_DIR/environment"

# Install systemd service
echo "Installing systemd service..."
cp installers/linux/inventory-agent.service /etc/systemd/system/

# Reload systemd
systemctl daemon-reload

# Enable service
systemctl enable "$SERVICE_NAME"

echo ""
echo -e "${GREEN}Installation complete!${NC}"
echo ""
echo "To start the service:"
echo "  sudo systemctl start $SERVICE_NAME"
echo ""
echo "To check status:"
echo "  sudo systemctl status $SERVICE_NAME"
echo ""
echo "Configuration file: $CONFIG_DIR/config.json"
echo "Log file: $LOG_DIR/agent.log"
