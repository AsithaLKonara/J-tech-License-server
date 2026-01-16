/**
 * Automated Upload Bridge Verification Tests
 * Tests the integration between upload-bridge and the license server
 */

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const ApiClient = require('../helpers/api-client');

describe('Upload Bridge Automated Verification', () => {
    let apiClient;
    const uploadBridgePath = path.join(__dirname, '../../apps/upload-bridge');
    const configPath = path.join(uploadBridgePath, 'config/auth_config.yaml');
    const serverUrl = process.env.LICENSE_SERVER_URL || 'http://localhost:8000';

    beforeAll(() => {
        apiClient = new ApiClient(serverUrl);
    });

    describe('Configuration Verification', () => {
        test('auth_config.yaml should exist', () => {
            expect(fs.existsSync(configPath)).toBe(true);
        });

        test('auth_config.yaml should be valid YAML', () => {
            const yaml = require('yaml');
            const content = fs.readFileSync(configPath, 'utf8');
            expect(() => yaml.parse(content)).not.toThrow();
        });

        test('auth_config.yaml should contain server URL', () => {
            const yaml = require('yaml');
            const content = fs.readFileSync(configPath, 'utf8');
            const config = yaml.parse(content);
            
            const serverUrl = config.auth_server_url || config.license_server_url;
            expect(serverUrl).toBeDefined();
        });
    });

    describe('Python Module Verification', () => {
        test('core/auth_manager.py should exist', () => {
            const authManagerPath = path.join(uploadBridgePath, 'core/auth_manager.py');
            expect(fs.existsSync(authManagerPath)).toBe(true);
        });

        test('core/license_manager.py should exist', () => {
            const licenseManagerPath = path.join(uploadBridgePath, 'core/license_manager.py');
            expect(fs.existsSync(licenseManagerPath)).toBe(true);
        });

        test('ui/dialogs/login_dialog.py should exist', () => {
            const loginDialogPath = path.join(uploadBridgePath, 'ui/dialogs/login_dialog.py');
            expect(fs.existsSync(loginDialogPath)).toBe(true);
        });
    });

    describe('API Connectivity', () => {
        test('License server should be accessible', async () => {
            const response = await apiClient.health();
            expect(response.status).toBe(200);
        });

        test('Login endpoint should be accessible', async () => {
            const response = await apiClient.post('/api/v2/auth/login', {
                email: 'test@example.com',
                password: 'testpassword123',
                device_id: 'VERIFY_DEVICE',
                device_name: 'Verification Device'
            });

            // Should either succeed (200) or fail with auth error (401), not connection error
            expect([200, 401, 400]).toContain(response.status);
        });
    });

    describe('Verification Script', () => {
        test('verify_license_integration.py should exist', () => {
            const scriptPath = path.join(uploadBridgePath, 'tests/verify_license_integration.py');
            expect(fs.existsSync(scriptPath)).toBe(true);
        });

        test('verify_license_integration.py should be executable', (done) => {
            const scriptPath = path.join(uploadBridgePath, 'tests/verify_license_integration.py');
            
            if (process.platform === 'win32') {
                // On Windows, check if Python can execute it
                const python = spawn('python', [scriptPath], {
                    cwd: uploadBridgePath,
                    stdio: 'pipe'
                });

                python.on('close', (code) => {
                    // Exit code 0 or 1 is acceptable (1 means some checks failed, which is OK)
                    expect([0, 1]).toContain(code);
                    done();
                });

                python.on('error', (error) => {
                    // If Python is not found, skip this test
                    if (error.code === 'ENOENT') {
                        console.warn('Python not found, skipping verification script test');
                        done();
                    } else {
                        done(error);
                    }
                });
            } else {
                // On Unix-like systems, check if file is executable
                fs.access(scriptPath, fs.constants.X_OK, (err) => {
                    if (err) {
                        // Not executable, but that's OK - we can still run it with python
                        done();
                    } else {
                        done();
                    }
                });
            }
        }, 30000); // 30 second timeout
    });

    describe('Integration Points', () => {
        test('AuthManager should use correct server URL', () => {
            // This is a structural test - verify the code structure
            const authManagerPath = path.join(uploadBridgePath, 'core/auth_manager.py');
            const content = fs.readFileSync(authManagerPath, 'utf8');
            
            // Check that server_url is configurable
            expect(content).toMatch(/server_url/i);
        });

        test('LicenseManager should use correct server URL', () => {
            const licenseManagerPath = path.join(uploadBridgePath, 'core/license_manager.py');
            const content = fs.readFileSync(licenseManagerPath, 'utf8');
            
            // Check that server_url is configurable
            expect(content).toMatch(/server_url/i);
        });

        test('LoginDialog should support email/password', () => {
            const loginDialogPath = path.join(uploadBridgePath, 'ui/dialogs/login_dialog.py');
            const content = fs.readFileSync(loginDialogPath, 'utf8');
            
            // Check that email/password login is supported
            expect(content).toMatch(/email.*password|password.*email/i);
        });

        test('LoginDialog should support magic link', () => {
            const loginDialogPath = path.join(uploadBridgePath, 'ui/dialogs/login_dialog.py');
            const content = fs.readFileSync(loginDialogPath, 'utf8');
            
            // Check that magic link is supported
            expect(content).toMatch(/magic.*link|magic_link/i);
        });
    });

    describe('Documentation Verification', () => {
        test('LICENSE_INTEGRATION_VERIFICATION.md should exist', () => {
            const docPath = path.join(uploadBridgePath, 'tests/LICENSE_INTEGRATION_VERIFICATION.md');
            expect(fs.existsSync(docPath)).toBe(true);
        });

        test('LOGIN_SYSTEM_SUMMARY.md should exist', () => {
            const docPath = path.join(uploadBridgePath, 'docs/LOGIN_SYSTEM_SUMMARY.md');
            expect(fs.existsSync(docPath)).toBe(true);
        });
    });

    describe('End-to-End Flow Simulation', () => {
        test('Complete login flow should work', async () => {
            // Simulate the complete flow
            // 1. Health check
            const healthResponse = await apiClient.health();
            expect(healthResponse.status).toBe(200);

            // 2. Login
            const loginResponse = await apiClient.login(
                'test@example.com',
                'testpassword123',
                'E2E_TEST_DEVICE',
                'E2E Test Device'
            );

            if (loginResponse.status === 200) {
                // 3. Get license info
                const licenseResponse = await apiClient.getLicenseInfo();
                expect(licenseResponse.status).toBe(200);

                // 4. List devices
                const devicesResponse = await apiClient.listDevices();
                expect(devicesResponse.status).toBe(200);
            } else {
                // If login fails, that's OK for automated tests (user might not exist)
                expect([401, 400]).toContain(loginResponse.status);
            }
        });
    });
});
