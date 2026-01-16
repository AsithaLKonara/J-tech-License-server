/**
 * Test Database Cleanup Utility
 * Cleans up test devices from the database to prevent device limit issues
 */

const ApiClient = require('../helpers/api-client');

const BASE_URL = process.env.LICENSE_SERVER_URL || process.env.API_URL || 'http://localhost:8000';
const TEST_USER_EMAIL = process.env.TEST_USER_EMAIL || 'test@example.com';
const TEST_USER_PASSWORD = process.env.TEST_USER_PASSWORD || 'testpassword123';

/**
 * Clean up all devices for the test user
 */
async function cleanupDevices() {
    const apiClient = new ApiClient(BASE_URL, { logging: false });
    
    try {
        // Login as test user
        const loginResponse = await apiClient.login(
            TEST_USER_EMAIL,
            TEST_USER_PASSWORD,
            'CLEANUP_DEVICE',
            'Cleanup Device'
        );
        
        if (loginResponse.status !== 200) {
            console.warn(`[Cleanup] Failed to login: ${loginResponse.status}`);
            return { success: false, error: 'Login failed', deleted: 0 };
        }
        
        // List all devices
        const listResponse = await apiClient.listDevices();
        
        if (listResponse.status !== 200) {
            console.warn(`[Cleanup] Failed to list devices: ${listResponse.status}`);
            return { success: false, error: 'List devices failed', deleted: 0 };
        }
        
        const devices = listResponse.data.devices || [];
        let deleted = 0;
        const errors = [];
        
        // Delete all devices
        for (const device of devices) {
            try {
                // Skip the cleanup device itself
                if (device.device_id === 'CLEANUP_DEVICE') {
                    continue;
                }
                
                const deleteResponse = await apiClient.deleteDevice(device.id);
                if (deleteResponse.status === 200) {
                    deleted++;
                } else {
                    errors.push(`Failed to delete device ${device.id}: ${deleteResponse.status}`);
                }
            } catch (error) {
                errors.push(`Error deleting device ${device.id}: ${error.message}`);
            }
        }
        
        // Also delete the cleanup device
        const cleanupDevice = devices.find(d => d.device_id === 'CLEANUP_DEVICE');
        if (cleanupDevice) {
            try {
                await apiClient.deleteDevice(cleanupDevice.id);
            } catch (error) {
                // Ignore errors for cleanup device
            }
        }
        
        if (errors.length > 0) {
            console.warn(`[Cleanup] Some errors occurred:`, errors);
        }
        
        return { success: true, deleted, errors };
    } catch (error) {
        console.error(`[Cleanup] Error during cleanup:`, error.message);
        return { success: false, error: error.message, deleted: 0 };
    }
}

/**
 * Clean up devices matching a pattern (e.g., all test devices)
 */
async function cleanupDevicesByPattern(pattern) {
    const apiClient = new ApiClient(BASE_URL, { logging: false });
    
    try {
        const loginResponse = await apiClient.login(
            TEST_USER_EMAIL,
            TEST_USER_PASSWORD,
            'CLEANUP_DEVICE',
            'Cleanup Device'
        );
        
        if (loginResponse.status !== 200) {
            return { success: false, error: 'Login failed', deleted: 0 };
        }
        
        const listResponse = await apiClient.listDevices();
        
        if (listResponse.status !== 200) {
            return { success: false, error: 'List devices failed', deleted: 0 };
        }
        
        const devices = listResponse.data.devices || [];
        const regex = new RegExp(pattern);
        let deleted = 0;
        
        for (const device of devices) {
            if (regex.test(device.device_id)) {
                try {
                    const deleteResponse = await apiClient.deleteDevice(device.id);
                    if (deleteResponse.status === 200) {
                        deleted++;
                    }
                } catch (error) {
                    // Continue with other devices
                }
            }
        }
        
        return { success: true, deleted };
    } catch (error) {
        return { success: false, error: error.message, deleted: 0 };
    }
}

// Export for use in test files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        cleanupDevices,
        cleanupDevicesByPattern,
    };
}

// Run cleanup if called directly
if (require.main === module) {
    const pattern = process.argv[2];
    
    if (pattern) {
        cleanupDevicesByPattern(pattern).then(result => {
            console.log(`Cleaned up ${result.deleted} devices matching pattern: ${pattern}`);
            process.exit(result.success ? 0 : 1);
        });
    } else {
        cleanupDevices().then(result => {
            console.log(`Cleaned up ${result.deleted} devices`);
            process.exit(result.success ? 0 : 1);
        });
    }
}
