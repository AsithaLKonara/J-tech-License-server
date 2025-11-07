# Packaging Notes (Windows EXE)

If you build a standalone EXE (e.g., PyInstaller), include non-Python resources:

## PyInstaller

Recommended flags:

```
pyinstaller --noconsole --name UploadBridge \
  --icon LEDMatrixStudio_icon.ico \
  --add-data "firmware/templates;firmware/templates" \
  --add-data "config;config" \
  --add-data "LEDMatrixStudio_icon.ico;." \
  main.py
```

Notes:
- Use `;` on Windows, `:` on Linux/macOS for `--add-data`.
- `firmware/templates` is required for chip templates.
- `config` is recommended if you distribute public_key.pem or license_keys.yaml.
- `--icon LEDMatrixStudio_icon.ico` sets the EXE icon; the runtime window icon is also set in code.

## Inno Setup / Other Installers
- Ensure the `firmware/templates/**` directory and `config/**` are copied next to the EXE (or inside the app directory) if not embedding with PyInstaller.

## Runtime Fallback
- The app now attempts to load templates as package resources when embedded and will extract them to a temporary directory.
- Including the directories explicitly reduces startup overhead.


