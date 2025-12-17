/**
 * Preset Library Service
 * Handles curated and user-contributed presets
 */

class PresetLibraryService {
    constructor(dbPool, auth0Manager) {
        this.db = dbPool;
        this.auth0Manager = auth0Manager;
    }

    /**
     * List presets (curated and public)
     * GET /api/presets
     */
    async listPresets(req, res) {
        try {
            const { category, curated_only, search } = req.query;
            const client = await this.db.connect();
            
            try {
                let query = `SELECT id, name, description, category, is_curated, is_public, download_count, created_at
                             FROM presets
                             WHERE is_public = true`;
                const params = [];
                let paramCount = 1;

                if (curated_only === 'true') {
                    query += ` AND is_curated = true`;
                }

                if (category) {
                    query += ` AND category = $${paramCount}`;
                    params.push(category);
                    paramCount++;
                }

                if (search) {
                    query += ` AND (name ILIKE $${paramCount} OR description ILIKE $${paramCount})`;
                    params.push(`%${search}%`);
                    paramCount++;
                }

                query += ` ORDER BY is_curated DESC, download_count DESC, created_at DESC`;

                const result = await client.query(query, params);

                res.json({
                    presets: result.rows
                });
            } finally {
                client.release();
            }
        } catch (error) {
            console.error('List presets error:', error);
            res.status(500).json({ error: `Failed to list presets: ${error.message}` });
        }
    }

    /**
     * Get preset details
     * GET /api/presets/:id
     */
    async getPreset(req, res) {
        try {
            const presetId = req.params.id;
            const client = await this.db.connect();
            
            try {
                const result = await client.query(
                    `SELECT * FROM presets
                     WHERE id = $1 AND (is_public = true OR user_id = $2)`,
                    [presetId, req.user?.id]
                );

                if (result.rows.length === 0) {
                    return res.status(404).json({ error: 'Preset not found' });
                }

                const preset = result.rows[0];
                const presetData = typeof preset.preset_data === 'string'
                    ? JSON.parse(preset.preset_data)
                    : preset.preset_data;

                // Increment download count
                await client.query(
                    'UPDATE presets SET download_count = download_count + 1 WHERE id = $1',
                    [presetId]
                );

                res.json({
                    id: preset.id,
                    name: preset.name,
                    description: preset.description,
                    category: preset.category,
                    preset_data: presetData,
                    is_curated: preset.is_curated,
                    download_count: preset.download_count + 1
                });
            } finally {
                client.release();
            }
        } catch (error) {
            console.error('Get preset error:', error);
            res.status(500).json({ error: `Failed to get preset: ${error.message}` });
        }
    }

    /**
     * Upload user-contributed preset
     * POST /api/presets
     */
    async uploadPreset(req, res) {
        try {
            const userId = req.user.id;
            const { name, description, category, preset_data, is_public } = req.body;

            if (!name || !preset_data) {
                return res.status(400).json({ error: 'Name and preset_data are required' });
            }

            const client = await this.db.connect();
            try {
                const result = await client.query(
                    `INSERT INTO presets (user_id, name, description, category, preset_data, is_public, created_at, updated_at)
                     VALUES ($1, $2, $3, $4, $5, $6, NOW(), NOW())
                     RETURNING *`,
                    [userId, name, description || '', category || 'general', JSON.stringify(preset_data), is_public || false]
                );

                res.json({
                    success: true,
                    preset: {
                        id: result.rows[0].id,
                        name: result.rows[0].name,
                        created_at: result.rows[0].created_at
                    }
                });
            } finally {
                client.release();
            }
        } catch (error) {
            console.error('Upload preset error:', error);
            res.status(500).json({ error: `Failed to upload preset: ${error.message}` });
        }
    }
}

module.exports = PresetLibraryService;
