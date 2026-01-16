# 🛠️ J-Tech Pixel LED Upload Bridge - Developer Guide

This guide details the technical architecture and extension points of the Upload Bridge for developers.

---

## 🏗️ Architecture Overview

The project is built as a **PyQt6** desktop application that interacts with a **Laravel-based** license server.

### Core Modules (`apps/upload-bridge/core`)
- **`gradient.py`**: A specialized engine for interpolating multi-stop colors.
- **`auth_manager.py`**: Handles device-bound encryption and license validation.
- **`automation/`**: Contains the protocol logic for converting UI instructions into hardware-ready patterns.

### UI Components (`apps/upload-bridge/ui`)
- **`matrix_design_canvas.py`**: The primary painting surface. It uses a coordinate-based pixel grid and supports custom drawing modes.

---

## 🎨 Extending the Canvas

To add a new drawing tool:
1. Add a new member to the `DrawingMode` enum in `matrix_design_canvas.py`.
2. Implement the tool's behavior in `mousePressEvent` and `mouseMoveEvent`.
3. If the tool requires a visual ghost/preview, update the `paintEvent`.

### Example: Custom Brush
```python
if self._drawing_mode == DrawingMode.MY_CUSTOM_TOOL:
    # Coordinate logic here
    self._set_pixel(x, y, self._primary_color)
```

---

## 📡 API Integration

The Desktop app communicates with the Web Dashboard via a REST API.

- **Check Entitlement**: `GET /api/v2/entitlement`
- **Device Registration**: `POST /api/v2/devices/register`
- **Heartbeat**: Automated token refresh every 1 hour.

---

## 🧪 Testing

Run the full test suite from the root directory:
```bash
pytest apps/upload-bridge/tests/ -v
```

For End-to-End tests involving the web server:
```powershell
.\run_complete_e2e_tests.ps1
```

---

**Contact**: Lead Architect
