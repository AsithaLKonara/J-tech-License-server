# Local Database for Desktop App

The desktop app now uses a local SQLite database for session management and login details storage.

## Location

The database is stored at:
- **Linux/macOS**: `~/.upload_bridge/local.db`
- **Windows**: `C:\Users\<username>\.upload_bridge\local.db`

## Schema

The database includes the following tables:

### `sessions`
Stores active user sessions with tokens and expiration times.

### `users`
Stores user login information and credentials.

### `license_cache`
Caches license information for offline validation.

### `device_info`
Stores device fingerprint and registration information.

### `validation_log`
Logs license validation attempts for debugging.

## Usage

The `LocalDatabase` class in `local_db.py` provides methods to:

- Save/load user sessions
- Store user login information
- Cache licenses for offline validation
- Track device information
- Log validation attempts

## Migration from File-Based Storage

The previous file-based storage (encrypted token files) has been replaced with the SQLite database. The database provides:

- Better organization
- Query capabilities
- Easier debugging
- Structured data storage

## Privacy & Security

- User credentials are still encrypted when stored
- Database is stored locally on the user's machine
- No sensitive data is sent to external servers
- Sessions can be invalidated securely

## Maintenance

The database automatically creates tables on first use. You can call `cleanup_old_data()` to remove old sessions and logs periodically.
