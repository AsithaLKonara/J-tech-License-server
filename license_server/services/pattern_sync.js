/**
 * Pattern Sync Service
 * Handles cloud pattern storage and synchronization
 */

class PatternSyncService {
    constructor(dbPool, auth0Manager) {
        this.db = dbPool;
        this.auth0Manager = auth0Manager;
    }

    /**
     * Upload pattern to cloud
     * POST /api/sync/upload
     */
    async uploadPattern(req, res) {
        try {
            const userId = req.user.id;
            const { name, pattern_data } = req.body;

            if (!name || !pattern_data) {
                return res.status(400).json({ error: 'Name and pattern_data are required' });
            }

            // Calculate file size
            const fileSize = JSON.stringify(pattern_data).length;

            const client = await this.db.connect();
            try {
                const result = await client.query(
                    `INSERT INTO cloud_patterns (user_id, name, pattern_data, file_size, created_at, updated_at)
                     VALUES ($1, $2, $3, $4, NOW(), NOW())
                     RETURNING *`,
                    [userId, name, JSON.stringify(pattern_data), fileSize]
                );

                res.json({
                    success: true,
                    pattern: {
                        id: result.rows[0].id,
                        name: result.rows[0].name,
                        created_at: result.rows[0].created_at
                    }
                });
            } finally {
                client.release();
            }
        } catch (error) {
            console.error('Upload pattern error:', error);
            res.status(500).json({ error: `Failed to upload pattern: ${error.message}` });
        }
    }

    /**
     * List user's cloud patterns
     * GET /api/sync/list
     */
    async listPatterns(req, res) {
        try {
            const userId = req.user.id;
            const client = await this.db.connect();
            
            try {
                const result = await client.query(
                    `SELECT id, name, file_size, created_at, updated_at
                     FROM cloud_patterns
                     WHERE user_id = $1
                     ORDER BY updated_at DESC`,
                    [userId]
                );

                res.json({
                    patterns: result.rows
                });
            } finally {
                client.release();
            }
        } catch (error) {
            console.error('List patterns error:', error);
            res.status(500).json({ error: `Failed to list patterns: ${error.message}` });
        }
    }

    /**
     * Download pattern from cloud
     * GET /api/sync/download/:id
     */
    async downloadPattern(req, res) {
        try {
            const userId = req.user.id;
            const patternId = req.params.id;
            const client = await this.db.connect();
            
            try {
                const result = await client.query(
                    `SELECT * FROM cloud_patterns
                     WHERE id = $1 AND user_id = $2`,
                    [patternId, userId]
                );

                if (result.rows.length === 0) {
                    return res.status(404).json({ error: 'Pattern not found' });
                }

                const pattern = result.rows[0];
                const patternData = typeof pattern.pattern_data === 'string' 
                    ? JSON.parse(pattern.pattern_data)
                    : pattern.pattern_data;

                res.json({
                    id: pattern.id,
                    name: pattern.name,
                    pattern_data: patternData,
                    created_at: pattern.created_at,
                    updated_at: pattern.updated_at
                });
            } finally {
                client.release();
            }
        } catch (error) {
            console.error('Download pattern error:', error);
            res.status(500).json({ error: `Failed to download pattern: ${error.message}` });
        }
    }

    /**
     * Delete pattern from cloud
     * DELETE /api/sync/:id
     */
    async deletePattern(req, res) {
        try {
            const userId = req.user.id;
            const patternId = req.params.id;
            const client = await this.db.connect();
            
            try {
                // Verify pattern belongs to user
                const checkResult = await client.query(
                    'SELECT * FROM cloud_patterns WHERE id = $1 AND user_id = $2',
                    [patternId, userId]
                );

                if (checkResult.rows.length === 0) {
                    return res.status(404).json({ error: 'Pattern not found' });
                }

                await client.query(
                    'DELETE FROM cloud_patterns WHERE id = $1 AND user_id = $2',
                    [patternId, userId]
                );

                res.json({
                    success: true,
                    message: 'Pattern deleted successfully'
                });
            } finally {
                client.release();
            }
        } catch (error) {
            console.error('Delete pattern error:', error);
            res.status(500).json({ error: `Failed to delete pattern: ${error.message}` });
        }
    }
}

module.exports = PatternSyncService;
