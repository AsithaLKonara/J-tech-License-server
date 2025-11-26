#!/bin/bash
# Upload Bridge Linux RPM Package Build Script
# Requires rpmbuild

set -e

VERSION="${1:-3.0.0}"
OUTPUT_DIR="${2:-dist}"

echo "Building Upload Bridge RPM package..."

# Check for required tools
if ! command -v rpmbuild &> /dev/null; then
    echo "ERROR: rpmbuild not found!"
    echo "Please install: sudo yum install rpm-build rpmdevtools"
    exit 1
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Setup RPM build directories
RPMBUILD_DIR="$HOME/rpmbuild"
mkdir -p "$RPMBUILD_DIR"/{BUILD,BUILDROOT,RPMS,SOURCES,SPECS,SRPMS}

# Copy spec file
cp "rpm/upload_bridge.spec" "$RPMBUILD_DIR/SPECS/"

# Update version in spec file
sed -i "s/Version:.*/Version:        $VERSION/" "$RPMBUILD_DIR/SPECS/upload_bridge.spec"

# Create source tarball (if needed)
# tar -czf "$RPMBUILD_DIR/SOURCES/upload-bridge-${VERSION}.tar.gz" \
#     --exclude='.git' --exclude='*.pyc' --exclude='__pycache__' \
#     -C .. upload-bridge

# Build RPM
echo "Building RPM package..."
rpmbuild -ba "$RPMBUILD_DIR/SPECS/upload_bridge.spec"

# Copy built RPM to output directory
cp "$RPMBUILD_DIR/RPMS"/*/upload-bridge-*.rpm "$OUTPUT_DIR/" 2>/dev/null || true
cp "$RPMBUILD_DIR/SRPMS"/*/upload-bridge-*.src.rpm "$OUTPUT_DIR/" 2>/dev/null || true

echo ""
echo "✅ RPM package built successfully"
echo "Packages are in: $OUTPUT_DIR"
echo ""
echo "To install, run: sudo rpm -ivh upload-bridge-*.rpm"

