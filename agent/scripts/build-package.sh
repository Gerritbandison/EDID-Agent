#!/bin/bash
# Build a distributable package for the Device Inventory Agent

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_DIR="$(dirname "$SCRIPT_DIR")"
VERSION="1.0.0"
PACKAGE_NAME="inventory-agent-${VERSION}"
BUILD_DIR="${AGENT_DIR}/build"
DIST_DIR="${AGENT_DIR}/dist"

echo "Building ${PACKAGE_NAME}..."

# Clean previous builds
rm -rf "$BUILD_DIR" "$DIST_DIR"
mkdir -p "$BUILD_DIR/$PACKAGE_NAME"
mkdir -p "$DIST_DIR"

# Copy source files
cp -r "$AGENT_DIR/src" "$BUILD_DIR/$PACKAGE_NAME/"
cp "$AGENT_DIR/requirements.txt" "$BUILD_DIR/$PACKAGE_NAME/"
cp "$AGENT_DIR/run.py" "$BUILD_DIR/$PACKAGE_NAME/"

# Copy scripts
mkdir -p "$BUILD_DIR/$PACKAGE_NAME/scripts"
cp "$AGENT_DIR/scripts/install.sh" "$BUILD_DIR/$PACKAGE_NAME/scripts/"
cp "$AGENT_DIR/scripts/uninstall.sh" "$BUILD_DIR/$PACKAGE_NAME/scripts/"

# Copy config example
mkdir -p "$BUILD_DIR/$PACKAGE_NAME/config"
cp "$AGENT_DIR/config/agent.json.example" "$BUILD_DIR/$PACKAGE_NAME/config/"

# Create README
cat > "$BUILD_DIR/$PACKAGE_NAME/README.txt" << 'EOF'
Device Inventory Agent v1.0.0
=============================

Installation (Linux):
  sudo ./scripts/install.sh

After installation:
  1. Edit /etc/inventory-agent/agent.json with your server URL
  2. Start the service: sudo systemctl start inventory-agent
  3. Enable on boot: sudo systemctl enable inventory-agent

Uninstallation:
  sudo /opt/inventory-agent/scripts/uninstall.sh

  Or run: sudo ./scripts/uninstall.sh

Manual Run (without installing):
  pip install -r requirements.txt
  python3 run.py
EOF

# Make scripts executable
chmod +x "$BUILD_DIR/$PACKAGE_NAME/scripts/"*.sh

# Create tarball
cd "$BUILD_DIR"
tar -czf "$DIST_DIR/${PACKAGE_NAME}-linux.tar.gz" "$PACKAGE_NAME"

echo ""
echo "Package created: $DIST_DIR/${PACKAGE_NAME}-linux.tar.gz"
echo ""
echo "To install on another machine:"
echo "  1. Copy the tar.gz file to the target machine"
echo "  2. Extract: tar -xzf ${PACKAGE_NAME}-linux.tar.gz"
echo "  3. Install: cd ${PACKAGE_NAME} && sudo ./scripts/install.sh"
