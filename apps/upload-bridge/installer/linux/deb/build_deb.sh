#!/bin/bash
# Upload Bridge Linux DEB Package Build Script
# Requires dpkg-deb

set -e

VERSION="${1:-3.0.0}"
OUTPUT_DIR="${2:-dist}"
ARCH="${3:-amd64}"

echo "Building Upload Bridge DEB package..."

# Check for required tools
if ! command -v dpkg-deb &> /dev/null; then
    echo "ERROR: dpkg-deb not found!"
    echo "Please install: sudo apt-get install dpkg-dev"
    exit 1
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Create package directory structure
PKG_DIR="$OUTPUT_DIR/upload-bridge_${VERSION}_${ARCH}"
mkdir -p "$PKG_DIR/DEBIAN"
mkdir -p "$PKG_DIR/usr/bin"
mkdir -p "$PKG_DIR/usr/share/upload-bridge"
mkdir -p "$PKG_DIR/usr/share/applications"
mkdir -p "$PKG_DIR/usr/share/doc/upload-bridge"

# Copy control file
cp "deb/control" "$PKG_DIR/DEBIAN/control"

# Update version in control file
sed -i "s/Version: .*/Version: $VERSION/" "$PKG_DIR/DEBIAN/control"
sed -i "s/Architecture: .*/Architecture: $ARCH/" "$PKG_DIR/DEBIAN/control"

# Copy application files (adjust paths as needed)
# cp -r ../.. "$PKG_DIR/usr/share/upload-bridge/" 2>/dev/null || true

# Create launcher script
cat > "$PKG_DIR/usr/bin/upload-bridge" << 'EOF'
#!/bin/bash
cd /usr/share/upload-bridge
python3 main.py "$@"
EOF
chmod +x "$PKG_DIR/usr/bin/upload-bridge"

# Create desktop file
cat > "$PKG_DIR/usr/share/applications/upload-bridge.desktop" << EOF
[Desktop Entry]
Name=Upload Bridge
Comment=LED Pattern Designer
Exec=/usr/bin/upload-bridge
Icon=upload-bridge
Terminal=false
Type=Application
Categories=Graphics;Development;
EOF

# Build DEB package
DEB_FILE="$OUTPUT_DIR/upload-bridge_${VERSION}_${ARCH}.deb"
echo "Building DEB package..."
dpkg-deb --build "$PKG_DIR" "$DEB_FILE"

echo ""
echo "✅ DEB package built successfully: $DEB_FILE"
echo ""
echo "To install, run: sudo dpkg -i \"$DEB_FILE\""
echo "To fix dependencies, run: sudo apt-get install -f"

