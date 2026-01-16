#!/usr/bin/env python3
"""
Upload Bridge Installer Builder

Creates distributable installers for Windows, macOS, and Linux.
Combines PyInstaller executable creation with platform-specific installers.

Usage:
    python scripts/build_installers.py [--platform all|windows|macos|linux] [--version 1.0.0]
"""

import os
import sys
import subprocess
import shutil
import platform
import argparse
from pathlib import Path
from typing import List, Dict, Any
import json
import hashlib


class InstallerBuilder:
    """Comprehensive installer builder for Upload Bridge."""

    def __init__(self, app_root: Path, version: str = "1.0.0"):
        self.app_root = app_root
        self.version = version
        self.dist_dir = app_root / "dist"
        self.build_dir = app_root / "build"
        self.installer_dir = app_root / "installer"

        # Detect current platform
        self.current_platform = platform.system().lower()

    def run_command(self, cmd: List[str], cwd: Path = None, check: bool = True) -> subprocess.CompletedProcess:
        """Run a command with proper error handling."""
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd or self.app_root,
                check=check,
                capture_output=True,
                text=True
            )
            return result
        except subprocess.CalledProcessError as e:
            print(f"❌ Command failed: {' '.join(cmd)}")
            print(f"Error: {e.stderr}")
            raise

    def create_executable(self) -> Path:
        """Create executable using PyInstaller."""
        print("🏗️ Building executable with PyInstaller...")

        # Ensure build directory exists
        self.build_dir.mkdir(exist_ok=True)
        self.dist_dir.mkdir(exist_ok=True)

        # Run the existing build script
        build_script = self.app_root / "scripts" / "build_executable.py"
        if not build_script.exists():
            raise FileNotFoundError(f"Build script not found: {build_script}")

        self.run_command([sys.executable, str(build_script)], cwd=self.app_root)

        # Find the created executable
        exe_name = "UploadBridge.exe" if self.current_platform == "windows" else "UploadBridge"
        exe_path = self.dist_dir / exe_name

        if not exe_path.exists():
            # Try alternative names
            for file in self.dist_dir.iterdir():
                if file.is_file() and file.suffix in ['.exe', ''] and 'upload' in file.name.lower():
                    exe_path = file
                    break

        if not exe_path.exists():
            raise FileNotFoundError(f"Executable not found in {self.dist_dir}")

        print(f"✅ Executable created: {exe_path}")
        return exe_path

    def build_windows_installer(self, exe_path: Path) -> List[Path]:
        """Build Windows MSI installer using WiX."""
        print("📦 Building Windows MSI installer...")

        installers = []

        # Check if WiX is available
        try:
            self.run_command(["candle.exe", "-?"], check=False)
            wix_available = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            wix_available = False

        if wix_available:
            # Use WiX to build MSI
            wxs_file = self.installer_dir / "windows" / "upload_bridge.wxs"
            if wxs_file.exists():
                build_script = self.installer_dir / "windows" / "build_installer.ps1"

                # Run PowerShell build script
                cmd = [
                    "powershell.exe",
                    "-ExecutionPolicy", "Bypass",
                    "-File", str(build_script),
                    "-Version", self.version
                ]

                self.run_command(cmd, cwd=self.installer_dir / "windows")

                msi_file = self.dist_dir / f"upload_bridge_{self.version}.msi"
                if msi_file.exists():
                    installers.append(msi_file)
                    print(f"✅ MSI installer created: {msi_file}")
            else:
                print("⚠️ WiX source file not found, skipping MSI build")

        # Create ZIP archive as fallback
        zip_name = f"UploadBridge-{self.version}-Windows.zip"
        zip_path = self.dist_dir / zip_name

        print(f"📦 Creating ZIP archive: {zip_path}")
        shutil.make_archive(
            str(zip_path.with_suffix('')),
            'zip',
            self.dist_dir
        )

        if zip_path.exists():
            installers.append(zip_path)
            print(f"✅ ZIP archive created: {zip_path}")

        return installers

    def build_macos_installer(self, exe_path: Path) -> List[Path]:
        """Build macOS installer."""
        print("🍎 Building macOS installer...")

        installers = []

        # Create .app bundle
        app_bundle = self.dist_dir / "UploadBridge.app"
        contents_dir = app_bundle / "Contents"
        macos_dir = contents_dir / "MacOS"
        resources_dir = contents_dir / "Resources"

        # Create bundle structure
        macos_dir.mkdir(parents=True, exist_ok=True)
        resources_dir.mkdir(exist_ok=True)

        # Copy executable
        shutil.copy2(exe_path, macos_dir / "UploadBridge")

        # Create Info.plist
        info_plist = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>UploadBridge</string>
    <key>CFBundleIdentifier</key>
    <string>com.uploadbridge.app</string>
    <key>CFBundleName</key>
    <string>Upload Bridge</string>
    <key>CFBundleVersion</key>
    <string>{version}</string>
    <key>CFBundleShortVersionString</key>
    <string>{version}</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.12</string>
</dict>
</plist>""".format(version=self.version)

        (contents_dir / "Info.plist").write_text(info_plist)

        # Create DMG if hdiutil is available
        try:
            dmg_name = f"UploadBridge-{self.version}.dmg"
            dmg_path = self.dist_dir / dmg_name

            self.run_command([
                "hdiutil", "create",
                "-volname", "Upload Bridge",
                "-srcfolder", str(app_bundle),
                "-ov", str(dmg_path)
            ])

            if dmg_path.exists():
                installers.append(dmg_path)
                print(f"✅ DMG installer created: {dmg_path}")

        except (subprocess.CalledProcessError, FileNotFoundError):
            print("⚠️ hdiutil not available, creating TAR.GZ instead")
            # Create tar.gz archive
            tar_name = f"UploadBridge-{self.version}-macOS.tar.gz"
            tar_path = self.dist_dir / tar_name

            import tarfile
            with tarfile.open(tar_path, "w:gz") as tar:
                tar.add(str(app_bundle), arcname="UploadBridge.app")

            installers.append(tar_path)
            print(f"✅ TAR.GZ archive created: {tar_path}")

        return installers

    def build_linux_installer(self, exe_path: Path) -> List[Path]:
        """Build Linux installer."""
        print("🐧 Building Linux installer...")

        installers = []

        # Create AppImage if appimagetool is available
        try:
            # Create AppDir structure
            appdir = self.dist_dir / "UploadBridge.AppDir"
            appdir.mkdir(exist_ok=True)

            # Copy executable
            shutil.copy2(exe_path, appdir / "UploadBridge")

            # Create desktop file
            desktop_file = f"""[Desktop Entry]
Name=Upload Bridge
Exec=UploadBridge
Icon=uploadbridge
Type=Application
Categories=Development;Utility;
"""

            (appdir / "upload-bridge.desktop").write_text(desktop_file)

            # Create AppRun script
            apprun_script = """#!/bin/bash
cd "$(dirname "$0")"
exec ./UploadBridge "$@"
"""
            apprun_path = appdir / "AppRun"
            apprun_path.write_text(apprun_script)
            apprun_path.chmod(0o755)

            # Make executable
            exe_path = appdir / "UploadBridge"
            exe_path.chmod(0o755)

            # Try to create AppImage
            appimage_name = f"UploadBridge-{self.version}.AppImage"
            appimage_path = self.dist_dir / appimage_name

            try:
                self.run_command([
                    "appimagetool", str(appdir), str(appimage_path)
                ])

                if appimage_path.exists():
                    installers.append(appimage_path)
                    print(f"✅ AppImage created: {appimage_path}")

            except (subprocess.CalledProcessError, FileNotFoundError):
                print("⚠️ appimagetool not available, creating TAR.GZ instead")

        except Exception as e:
            print(f"⚠️ AppImage creation failed: {e}")

        # Always create TAR.GZ as fallback
        tar_name = f"UploadBridge-{self.version}-Linux.tar.gz"
        tar_path = self.dist_dir / tar_name

        import tarfile
        with tarfile.open(tar_path, "w:gz") as tar:
            for file in self.dist_dir.iterdir():
                if file.is_file() and not file.name.endswith('.tar.gz'):
                    tar.add(str(file), arcname=file.name)

        installers.append(tar_path)
        print(f"✅ TAR.GZ archive created: {tar_path}")

        return installers

    def generate_checksums(self, files: List[Path]) -> Path:
        """Generate SHA256 checksums for all installer files."""
        print("🔐 Generating checksums...")

        checksums_file = self.dist_dir / f"checksums-{self.version}.txt"

        with open(checksums_file, 'w') as f:
            for file_path in files:
                if file_path.exists():
                    sha256 = hashlib.sha256()
                    with open(file_path, 'rb') as file:
                        while chunk := file.read(8192):
                            sha256.update(chunk)

                    f.write(f"{sha256.hexdigest()}  {file_path.name}\n")

        print(f"✅ Checksums generated: {checksums_file}")
        return checksums_file

    def create_release_notes(self) -> Path:
        """Create basic release notes."""
        release_notes = self.dist_dir / f"RELEASE_NOTES-{self.version}.txt"

        notes = f"""Upload Bridge v{self.version}
{'='*50}

Release Date: {__import__('datetime').datetime.now().strftime('%Y-%m-%d')}

What's New:
- Bug fixes and performance improvements
- Enhanced user interface
- Improved stability

Installation:
- Windows: Run the MSI installer or extract the ZIP archive
- macOS: Mount the DMG and drag to Applications, or extract TAR.GZ
- Linux: Run the AppImage or extract TAR.GZ

System Requirements:
- Python 3.8+
- 2GB RAM minimum
- 1GB disk space

For more information, visit: https://github.com/your-repo/upload-bridge
"""

        release_notes.write_text(notes)
        print(f"✅ Release notes created: {release_notes}")
        return release_notes

    def build_all_platforms(self) -> Dict[str, List[Path]]:
        """Build installers for all platforms."""
        print(f"🚀 Building Upload Bridge v{self.version} installers...")

        # Create executable first
        exe_path = self.create_executable()

        results = {
            'executables': [exe_path],
            'installers': []
        }

        # Build platform-specific installers
        if self.current_platform == "windows":
            results['installers'].extend(self.build_windows_installer(exe_path))
        elif self.current_platform == "darwin":
            results['installers'].extend(self.build_macos_installer(exe_path))
        elif self.current_platform == "linux":
            results['installers'].extend(self.build_linux_installer(exe_path))

        # Generate checksums and release notes
        all_files = results['executables'] + results['installers']
        results['checksums'] = self.generate_checksums(all_files)
        results['release_notes'] = self.create_release_notes()

        return results

    def print_summary(self, results: Dict[str, List[Path]]):
        """Print build summary."""
        print("\n" + "="*60)
        print("📦 BUILD SUMMARY")
        print("="*60)

        print("\n📁 Files created:")
        for category, files in results.items():
            if isinstance(files, list):
                print(f"  {category.title()}:")
                for file in files:
                    size_mb = file.stat().st_size / 1024 / 1024
                    print(".1f")
            else:
                size_mb = files.stat().st_size / 1024 / 1024
                print(f"  {category.title()}: {files.name} ({size_mb:.1f} MB)")

        print("\n✅ Build completed successfully!")
        print(f"Version: {self.version}")
        print(f"Platform: {self.current_platform}")
        print(f"Output directory: {self.dist_dir}")


def main():
    parser = argparse.ArgumentParser(description="Build Upload Bridge installers")
    parser.add_argument("--version", default="1.0.0", help="Version number")
    parser.add_argument("--platform", choices=["all", "windows", "macos", "linux"],
                       default="all", help="Target platform")
    parser.add_argument("--root", default=".", help="Project root directory")

    args = parser.parse_args()

    app_root = Path(args.root).resolve()

    if not app_root.exists():
        print(f"Error: Root path {app_root} does not exist")
        return 1

    builder = InstallerBuilder(app_root, args.version)

    try:
        if args.platform == "all":
            results = builder.build_all_platforms()
        else:
            # For now, just build for current platform
            results = builder.build_all_platforms()

        builder.print_summary(results)
        return 0

    except Exception as e:
        print(f"❌ Build failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
