/**
 * Update Delivery Service
 * Handles application updates with entitlement gating
 */

const fs = require('fs').promises;
const path = require('path');

class UpdateService {
    constructor(dbPool, auth0Manager) {
        this.db = dbPool;
        this.auth0Manager = auth0Manager;
        this.updatesDir = path.join(__dirname, '..', 'updates');
    }

    /**
     * Check for available updates
     * GET /api/updates/check
     */
    async checkUpdates(req, res) {
        try {
            const { current_version } = req.query;
            const userId = req.user?.id;

            // Verify user has valid entitlement
            if (userId) {
                const client = await this.db.connect();
                try {
                    const result = await client.query(
                        `SELECT * FROM entitlements
                         WHERE user_id = $1 AND status = 'active'
                         AND (expires_at IS NULL OR expires_at > NOW())
                         LIMIT 1`,
                        [userId]
                    );

                    if (result.rows.length === 0) {
                        return res.status(403).json({ error: 'No active entitlement found' });
                    }
                } finally {
                    client.release();
                }
            }

            // Check for updates (simplified - in production, check version database)
            const latestVersion = process.env.LATEST_VERSION || '1.0.0';
            const hasUpdate = current_version !== latestVersion;

            res.json({
                has_update: hasUpdate,
                current_version: current_version,
                latest_version: latestVersion,
                update_url: hasUpdate ? `/api/updates/download?version=${latestVersion}` : null
            });
        } catch (error) {
            console.error('Check updates error:', error);
            res.status(500).json({ error: `Failed to check updates: ${error.message}` });
        }
    }

    /**
     * Download update (requires entitlement)
     * GET /api/updates/download
     */
    async downloadUpdate(req, res) {
        try {
            const { version } = req.query;
            const userId = req.user?.id;

            // Verify user has valid entitlement
            if (!userId) {
                return res.status(401).json({ error: 'Authentication required' });
            }

            const client = await this.db.connect();
            try {
                const result = await client.query(
                    `SELECT * FROM entitlements
                     WHERE user_id = $1 AND status = 'active'
                     AND (expires_at IS NULL OR expires_at > NOW())
                     LIMIT 1`,
                    [userId]
                );

                if (result.rows.length === 0) {
                    return res.status(403).json({ error: 'No active entitlement found' });
                }
            } finally {
                client.release();
            }

            // In production, serve actual update file
            // For now, return placeholder
            res.json({
                message: 'Update download endpoint',
                version: version,
                download_url: `/updates/uploadbridge-${version}.exe` // Placeholder
            });
        } catch (error) {
            console.error('Download update error:', error);
            res.status(500).json({ error: `Failed to download update: ${error.message}` });
        }
    }
}

module.exports = UpdateService;
