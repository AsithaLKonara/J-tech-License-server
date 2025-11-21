%define name upload-bridge
%define version 3.0.0
%define release 1

Summary: Upload Bridge - LED Pattern Designer
Name: %{name}
Version: %{version}
Release: %{release}%{?dist}
License: Proprietary
Group: Applications/Graphics
URL: https://uploadbridge.com
Source0: %{name}-%{version}.tar.gz
BuildArch: x86_64

Requires: python3 >= 3.10
Requires: python3-PySide6
Requires: python3-pip
Requires: python3-pyserial
Requires: python3-Pillow
Requires: python3-opencv-python
Requires: python3-numpy

%description
Upload Bridge is a comprehensive tool for designing and uploading
LED matrix patterns to various microcontrollers.

Features:
- Visual pattern editor
- Multi-layer support
- Multiple export formats
- Support for ESP32, STM32, AVR, PIC, and Nuvoton chips
- Hardware verification

%prep
%setup -q

%build
# No build step needed for Python application

%install
mkdir -p %{buildroot}/opt/upload-bridge
cp -r * %{buildroot}/opt/upload-bridge/
mkdir -p %{buildroot}/usr/bin
ln -s /opt/upload-bridge/main.py %{buildroot}/usr/bin/upload-bridge

%files
/opt/upload-bridge/*
/usr/bin/upload-bridge

%changelog
* Tue Nov 10 2024 Upload Bridge Team <support@uploadbridge.com> - 3.0.0-1
- Initial enterprise release

