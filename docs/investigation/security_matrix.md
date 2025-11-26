# Security & Permissions Matrix – Upload Bridge

This matrix captures access control, safety constraints, and handling of sensitive operations and data.

## Columns

- **ID**: Security identifier (e.g., SEC-WiFi-1).
- **Resource Type**: `Feature`, `Script`, `Config`, `Data`, etc.
- **Resource Name**: What is being protected or controlled.
- **Expected Access Rules**: From docs or design intent.
- **Actual Access Rules**: As implemented.
- **Sensitive Data Involved**: Tokens, license keys, device identifiers, etc.
- **Transport Security**: Encryption, secure protocols, etc.
- **Storage Security**: How data is stored and protected.
- **Audit / Logging**: What is logged and where.
- **Issues / Gaps**: Observed issues or concerns.
- **Severity / Risk**: `Low`, `Medium`, `High`, `Critical`.
- **Next Actions**: Follow-up investigations or fixes.

## Seed Security Rows

| ID | Resource Type | Resource Name | Expected Access Rules | Actual Access Rules | Sensitive Data Involved | Transport Security | Storage Security | Audit / Logging | Issues / Gaps | Severity / Risk | Next Actions |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SEC-License-1 | Feature | Licensing & activation | Only licensed users should access full features; license keys validated. | License activation requires keys from `LICENSE_KEYS.txt` or server-issued licenses; runtime validation follows `LICENSE_VALIDATION_FLOW.md`. | License keys, activation tokens, device IDs, signed license blobs | License server uses HTTPS/TLS when deployed behind a proper reverse proxy; firmware/device traffic uses signed tokens over HTTP or HTTPS depending on deployment. | Cached licenses stored encrypted on disk (`~/.upload_bridge/license/license.enc`); license server keys stored in `license_server/keys` on server. Offline license keys are plain text in `LICENSE_KEYS.txt`. | License server logs access; client app can log license validation outcomes. | Offline keys are bundled as plain text and may be considered sensitive; local cache path must have proper OS permissions; server uses in-memory DB by default (no persistence/hardening guidance). | Medium | Consider not shipping production-grade keys in plaintext; document best practices for protecting `LICENSE_KEYS.txt` and server keys; enforce secure file permissions for local cache. |
| SEC-WiFi-1 | Feature / Script | Wi-Fi upload & device control | Only authorized users/devices; safe uploads; no credential leakage. | Wi-Fi Upload tab (`ui/tabs/wifi_upload_tab.py`) and `wifi_upload/wifi_uploader.py` send uploads over HTTP to `/api/status` and `/api/upload` with no authentication beyond network access; UI fields expose SSID/password but do not persist them. | Wi-Fi credentials (SSID/password), device IPs, pattern file contents | Plain HTTP to local ESP8266/ESP32 endpoints (no TLS); assumes private, trusted network. | No long-term credential storage beyond runtime UI fields; logs may contain device IPs and status info. | Console/UI logs show connection status, upload success/failure messages; no structured security logging. | Lack of authentication and encryption on Wi-Fi endpoints means anyone on the same network could potentially upload patterns or query device status; default password (`ledmatrix123`) is weak and visible in UI. | Medium–High (depending on deployment environment) | Recommend securing Wi-Fi network (WPA2+), allowing users to change default password, and documenting that APIs are HTTP-only; optionally add an authentication token and HTTPS support for more sensitive deployments. |
| SEC-Package-1 | Script | Package creation scripts | Packages should not leak internal secrets or dev-only files. | `create_complete_package.py` includes core app, docs, diagnostics, `wifi_upload`, `config`, and `docs` recursively; by default it also packages `LICENSE_KEYS.txt` and many internal docs. | Potential inclusion of license keys, internal test scripts, and configuration defaults. | N/A (local packaging) | ZIP file contents reflect repo state; any sensitive files in included directories will be shipped. | Packaging script prints included/missing files; no automated secret scanning. | Packaging currently includes `LICENSE_KEYS.txt` and the entire `config` directory, which may not be appropriate for all distributions. | Medium | Clarify distribution profiles (dev vs production) and exclude sensitive files (e.g., offline keys, internal configs) from production packages; add a simple allowlist/denylist or secret-scan step before packaging. |


