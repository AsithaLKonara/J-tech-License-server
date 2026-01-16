#!/bin/bash
# Upload Bridge macOS Installer Build Script
# Requires pkgbuild and productbuild

set -e

VERSION="${1:-3.0.0}"
OUTPUT_DIR="${2:-dist}"
SIGN_IDENTITY="${3:-}"

echo "Building Upload Bridge macOS Installer..."

# Check for required tools
if ! command -v pkgbuild &> /dev/null; then
    echo "ERROR: pkgbuild not found!"
    echo "Please install Xcode Command Line Tools: xcode-select --install"
    exit 1
fi

if ! command -v productbuild &> /dev/null; then
    echo "ERROR: productbuild not found!"
    echo "Please install Xcode Command Line Tools: xcode-select --install"
    exit 1
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Build component package
COMPONENT_PKG="$OUTPUT_DIR/upload_bridge_component.pkg"
echo "Building component package..."

PKGBUILD_ARGS=(
    --root "."
    --identifier "com.uploadbridge.pkg"
    --version "$VERSION"
    --install-location "/Applications/UploadBridge"
    --component-plist "macos/component.plist"
    "$COMPONENT_PKG"
)

if [ -n "$SIGN_IDENTITY" ]; then
    PKGBUILD_ARGS+=(--sign "$SIGN_IDENTITY")
fi

pkgbuild "${PKGBUILD_ARGS[@]}"

# Build distribution package
DIST_PKG="$OUTPUT_DIR/upload_bridge_${VERSION}.pkg"
echo "Building distribution package..."

PRODUCTBUILD_ARGS=(
    --distribution "macos/upload_bridge.pkgproj"
    --package-path "$OUTPUT_DIR"
    --resources "macos/resources"
    "$DIST_PKG"
)

if [ -n "$SIGN_IDENTITY" ]; then
    PRODUCTBUILD_ARGS+=(--sign "$SIGN_IDENTITY")
fi

productbuild "${PRODUCTBUILD_ARGS[@]}"

echo ""
echo "✅ Installer built successfully: $DIST_PKG"
echo ""
echo "To install, run: sudo installer -pkg \"$DIST_PKG\" -target /"

