# Offline Licensing (Pre-made Keys)

Upload Bridge now supports offline licensing using pre-made keys.

## Key Points
- No server, no email flow.
- Keys are defined in `config/license_keys.yaml`.
- Activation stores an encrypted license bound to the device.

## Using a Key
1. Launch the app → License → Activate License.
2. Enter the key (e.g., `ABCD-1234-EFGH-5678`).
3. Click Activate.
4. Check License → Status.

## Managing Keys
- Edit `config/license_keys.yaml` to add or remove keys.
- Each key maps to:
  - `product_id`
  - `features` (array)
  - `expires_at` (optional; `null` for perpetual)

Example:
```yaml
keys:
  ABCD-1234-EFGH-5678:
    product_id: upload_bridge_pro
    features: [pattern_upload, wifi_upload]
    expires_at: null
```

## Notes
- Device-bound encryption is used for local storage.
- Status UI reads stored license; no server required.


