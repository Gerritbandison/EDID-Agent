#!/bin/bash
# Device Inventory Agent Uninstaller

set -e

INSTALL_DIR="/opt/inventory-agent"
CONFIG_DIR="/etc/inventory-agent"
SERVICE_NAME="inventory-agent"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${RED}========================================${NC}"
echo -e "${RED}  Device Inventory Agent Uninstaller${NC}"
echo -e "${RED}========================================${NC}"

if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run as root (use sudo)${NC}"
    exit 1
fi

echo -e "${YELLOW}Stopping service...${NC}"
systemctl stop ${SERVICE_NAME} 2>/dev/null || true
systemctl disable ${SERVICE_NAME} 2>/dev/null || true

echo -e "${YELLOW}Removing service file...${NC}"
rm -f /etc/systemd/system/${SERVICE_NAME}.service
systemctl daemon-reload

echo -e "${YELLOW}Removing installation directory...${NC}"
rm -rf "$INSTALL_DIR"

read -p "Remove configuration files? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -rf "$CONFIG_DIR"
    echo -e "${GREEN}Configuration removed.${NC}"
else
    echo -e "${YELLOW}Configuration kept at: $CONFIG_DIR${NC}"
fi

echo ""
echo -e "${GREEN}Uninstallation complete!${NC}"
