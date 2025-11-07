/**
 * Upload Bridge License Server - Test Client
 * Demonstrates license generation, activation, and validation
 */

const axios = require('axios');

const SERVER_URL = 'http://localhost:3000';

class LicenseTestClient {
    constructor(serverUrl = SERVER_URL) {
        this.serverUrl = serverUrl;
    }

    async testHealth() {
        console.log('🏥 Testing server health...');
        try {
            const response = await axios.get(`${this.serverUrl}/api/health`);
            console.log('✅ Server is healthy:', response.data);
            return true;
        } catch (error) {
            console.error('❌ Server health check failed:', error.message);
            return false;
        }
    }

    async generateLicense(email, options = {}) {
        console.log(`🔑 Generating license for: ${email}`);
        
        const licenseData = {
            email: email,
            product_id: options.product_id || 'upload_bridge_pro',
            features: options.features || ['pattern_upload', 'wifi_upload', 'advanced_controls'],
            expires_at: options.expires_at || new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toISOString(),
            max_devices: options.max_devices || 1,
            chip_id: options.chip_id || null
        };

        try {
            const response = await axios.post(`${this.serverUrl}/api/generate-license`, licenseData);
            console.log('✅ License generated successfully');
            console.log('   License ID:', response.data.license_id);
            console.log('   Features:', response.data.license_file.license.features);
            console.log('   Expires:', response.data.license_file.license.expires_at);
            
            return response.data;
        } catch (error) {
            console.error('❌ License generation failed:', error.response?.data || error.message);
            return null;
        }
    }

    async activateLicense(licenseFile, chipId, deviceInfo = {}) {
        console.log(`🔗 Activating license for chip: ${chipId}`);
        
        const activationData = {
            license_token: JSON.stringify(licenseFile),
            chip_id: chipId,
            device_info: {
                firmware_version: '1.0.0',
                hardware_version: 'ESP8266',
                ...deviceInfo
            }
        };

        try {
            const response = await axios.post(`${this.serverUrl}/api/activate`, activationData);
            console.log('✅ License activated successfully');
            console.log('   Device bound:', response.data.device);
            
            return response.data;
        } catch (error) {
            console.error('❌ License activation failed:', error.response?.data || error.message);
            return null;
        }
    }

    async validateLicense(licenseId, chipId) {
        console.log(`🔍 Validating license: ${licenseId} for chip: ${chipId}`);
        
        const validationData = {
            license_id: licenseId,
            chip_id: chipId
        };

        try {
            const response = await axios.post(`${this.serverUrl}/api/validate`, validationData);
            console.log('✅ License validation result:', response.data);
            
            return response.data;
        } catch (error) {
            console.error('❌ License validation failed:', error.response?.data || error.message);
            return null;
        }
    }

    async revokeLicense(licenseId, reason = 'Test revocation') {
        console.log(`🚫 Revoking license: ${licenseId}`);
        
        const revocationData = {
            license_id: licenseId,
            reason: reason
        };

        try {
            const response = await axios.post(`${this.serverUrl}/api/revoke`, revocationData);
            console.log('✅ License revoked successfully');
            
            return response.data;
        } catch (error) {
            console.error('❌ License revocation failed:', error.response?.data || error.message);
            return null;
        }
    }

    async getLicenseStatus(licenseId) {
        console.log(`📊 Getting license status: ${licenseId}`);
        
        try {
            const response = await axios.get(`${this.serverUrl}/api/license/${licenseId}`);
            console.log('✅ License status retrieved');
            console.log('   License:', response.data.license);
            console.log('   Revoked:', response.data.revoked);
            
            return response.data;
        } catch (error) {
            console.error('❌ Failed to get license status:', error.response?.data || error.message);
            return null;
        }
    }

    async listAllLicenses() {
        console.log('📋 Listing all licenses...');
        
        try {
            const response = await axios.get(`${this.serverUrl}/api/licenses`);
            console.log('✅ Licenses retrieved');
            console.log('   Total licenses:', response.data.total);
            
            response.data.licenses.forEach((license, index) => {
                console.log(`   ${index + 1}. ${license.license_id} - ${license.issued_to_email}`);
            });
            
            return response.data;
        } catch (error) {
            console.error('❌ Failed to list licenses:', error.response?.data || error.message);
            return null;
        }
    }

    async runCompleteTest() {
        console.log('🧪 Running complete license system test...\n');
        
        // Test 1: Health check
        const healthOk = await this.testHealth();
        if (!healthOk) {
            console.log('❌ Server health check failed, aborting tests');
            return;
        }
        
        console.log('\n' + '='.repeat(50) + '\n');
        
        // Test 2: Generate license
        const licenseResult = await this.generateLicense('test@example.com', {
            features: ['pattern_upload', 'wifi_upload', 'advanced_controls'],
            expires_at: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString() // 30 days
        });
        
        if (!licenseResult) {
            console.log('❌ License generation failed, aborting tests');
            return;
        }
        
        const licenseId = licenseResult.license_id;
        const licenseFile = licenseResult.license_file;
        
        console.log('\n' + '='.repeat(50) + '\n');
        
        // Test 3: Activate license
        const chipId = 'ESP8266_' + Math.random().toString(36).substr(2, 8).toUpperCase();
        const activationResult = await this.activateLicense(licenseFile, chipId);
        
        if (!activationResult) {
            console.log('❌ License activation failed, aborting tests');
            return;
        }
        
        console.log('\n' + '='.repeat(50) + '\n');
        
        // Test 4: Validate license
        const validationResult = await this.validateLicense(licenseId, chipId);
        
        if (!validationResult || !validationResult.valid) {
            console.log('❌ License validation failed');
        }
        
        console.log('\n' + '='.repeat(50) + '\n');
        
        // Test 5: Get license status
        await this.getLicenseStatus(licenseId);
        
        console.log('\n' + '='.repeat(50) + '\n');
        
        // Test 6: List all licenses
        await this.listAllLicenses();
        
        console.log('\n' + '='.repeat(50) + '\n');
        
        // Test 7: Revoke license
        await this.revokeLicense(licenseId, 'Test revocation');
        
        console.log('\n' + '='.repeat(50) + '\n');
        
        // Test 8: Validate revoked license
        const revokedValidation = await this.validateLicense(licenseId, chipId);
        
        if (revokedValidation && !revokedValidation.valid) {
            console.log('✅ Revoked license correctly shows as invalid');
        }
        
        console.log('\n🎉 Complete license system test finished!');
    }
}

// Example usage
async function main() {
    const client = new LicenseTestClient();
    
    // Run complete test suite
    await client.runCompleteTest();
    
    // Individual test examples
    console.log('\n' + '='.repeat(50));
    console.log('📝 Individual test examples:');
    console.log('='.repeat(50));
    
    // Generate trial license
    const trialLicense = await client.generateLicense('trial@example.com', {
        features: ['pattern_upload'],
        expires_at: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(), // 7 days
        max_devices: 1
    });
    
    if (trialLicense) {
        console.log('✅ Trial license generated');
    }
    
    // Generate enterprise license
    const enterpriseLicense = await client.generateLicense('enterprise@company.com', {
        features: ['pattern_upload', 'wifi_upload', 'advanced_controls', 'batch_processing'],
        expires_at: new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toISOString(), // 1 year
        max_devices: 10
    });
    
    if (enterpriseLicense) {
        console.log('✅ Enterprise license generated');
    }
}

// Run if called directly
if (require.main === module) {
    main().catch(console.error);
}

module.exports = LicenseTestClient;

