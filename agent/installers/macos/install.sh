#!/bin/bash
#
# Device Inventory Agent - macOS Installer
#

set -e

INSTALL_DIR="/Library/InventoryAgent"
LOG_DIR="/Library/Logs/InventoryAgent"
LAUNCH_DAEMON="/Library/LaunchDaemons/com.inventory.agent.plist"
SERVICE_LABEL="com.inventory.agent"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${GREEN}Device Inventory Agent Installer for macOS${NC}"
echo "============================================="

# Check root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run as root: sudo ./install.sh${NC}"
    exit 1
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is required. Install from python.org or use Homebrew.${NC}"
    exit 1
fi

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
cat > "$INSTALL_DIR/config.json" << EOF
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

chmod 600 "$INSTALL_DIR/config.json"

# Install LaunchDaemon
echo "Installing LaunchDaemon..."
cp installers/macos/com.inventory.agent.plist "$LAUNCH_DAEMON"
chmod 644 "$LAUNCH_DAEMON"
chown root:wheel "$LAUNCH_DAEMON"

# Load service
echo "Loading service..."
launchctl unload "$LAUNCH_DAEMON" 2>/dev/null || true
launchctl load "$LAUNCH_DAEMON"

echo ""
echo -e "${GREEN}Installation complete!${NC}"
echo ""
echo "Service is now running."
echo ""
echo "To check status:"
echo "  sudo launchctl list | grep inventory"
echo ""
echo "To stop:"
echo "  sudo launchctl unload $LAUNCH_DAEMON"
echo ""
echo "Configuration: $INSTALL_DIR/config.json"
echo "Logs: $LOG_DIR/"
