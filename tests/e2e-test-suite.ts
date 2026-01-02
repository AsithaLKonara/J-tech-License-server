/**
 * Comprehensive End-to-End Test Suite for License Server
 * 
 * This test suite covers:
 * 1. License Server API endpoints (health, login, refresh)
 * 2. Auth0 OAuth integration
 * 3. Token validation and error handling
 * 4. Edge cases and performance
 * 
 * Usage:
 *   npx ts-node tests/e2e-test-suite.ts
 * 
 * Environment Variables:
 *   LICENSE_SERVER_URL - License server URL (default: Railway production)
 *   AUTH0_DOMAIN - Auth0 domain
 *   AUTH0_AUDIENCE - Auth0 audience
 *   TEST_AUTH0_TOKEN - Optional real Auth0 token for full E2E test
 */

import { verifyAuth0Token, extractUserInfo } from '../lib/jwt-validator';

interface TestResult {
  name: string;
  passed: boolean;
  message: string;
  details?: any;
  duration?: number;
}

class E2ETestSuite {
  private results: TestResult[] = [];
  private licenseServerUrl: string;
  private auth0Domain: string | undefined;
  private auth0Audience: string | undefined;
  private sessionToken: string | null = null;
  private entitlementToken: any = null;
  private userId: string | null = null;

  constructor() {
    this.licenseServerUrl = process.env.LICENSE_SERVER_URL || 'https://j-tech-license-server-production.up.railway.app';
    this.auth0Domain = process.env.AUTH0_DOMAIN;
    this.auth0Audience = process.env.AUTH0_AUDIENCE;
  }

  private addResult(name: string, passed: boolean, message: string, details?: any, duration?: number) {
    this.results.push({ name, passed, message, details, duration });
    const icon = passed ? '✅' : '❌';
    const durationStr = duration ? ` (${duration}ms)` : '';
    console.log(`${icon} ${name}: ${message}${durationStr}`);
    if (details && !passed) {
      console.log(`   Details: ${JSON.stringify(details, null, 2)}`);
    }
  }

  private async timeTest<T>(name: string, testFn: () => Promise<T>): Promise<T> {
    const start = Date.now();
    try {
      const result = await testFn();
      const duration = Date.now() - start;
      return result;
    } catch (error) {
      const duration = Date.now() - start;
      throw { error, duration };
    }
  }

  /**
   * Phase 1: License Server API Tests
   */

  async testHealthEndpoint(): Promise<void> {
    await this.timeTest('Health Endpoint', async () => {
      const response = await fetch(`${this.licenseServerUrl}/api/health`);
      
      if (!response.ok) {
        this.addResult('Health Endpoint', false, `HTTP ${response.status}: ${response.statusText}`);
        return;
      }

      const data = await response.json() as { status: string; service: string; version?: string; timestamp?: string };
      
      if (data.status === 'ok' && data.service === 'upload-bridge-license-server') {
        this.addResult('Health Endpoint', true, 'Server is healthy and responding', {
          service: data.service,
          version: data.version,
          timestamp: data.timestamp
        });
      } else {
        this.addResult('Health Endpoint', false, 'Unexpected response structure', { received: data });
      }
    });
  }

  async testHealthEndpointCors(): Promise<void> {
    await this.timeTest('Health Endpoint CORS', async () => {
      const response = await fetch(`${this.licenseServerUrl}/api/health`, {
        method: 'OPTIONS',
      });

      const corsHeader = response.headers.get('Access-Control-Allow-Origin');
      const corsMethods = response.headers.get('Access-Control-Allow-Methods');
      
      if (corsHeader && corsMethods) {
        this.addResult('Health Endpoint CORS', true, 'CORS headers are present', {
          'Access-Control-Allow-Origin': corsHeader,
          'Access-Control-Allow-Methods': corsMethods,
        });
      } else {
        this.addResult('Health Endpoint CORS', false, 'CORS headers missing or incomplete', {
          headers: Object.fromEntries(response.headers.entries())
        });
      }
    });
  }

  async testLoginEndpointMissingToken(): Promise<void> {
    await this.timeTest('Login Endpoint - Missing Token', async () => {
      const response = await fetch(`${this.licenseServerUrl}/api/v2/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      });

      const data = await response.json() as { error?: string };
      
      if (response.status === 400 && data.error && data.error.includes('token')) {
        this.addResult('Login Endpoint - Missing Token', true, 'Correctly validates missing token', {
          status: response.status,
          error: data.error
        });
      } else {
        this.addResult('Login Endpoint - Missing Token', false, 'Unexpected response', {
          status: response.status,
          data
        });
      }
    });
  }

  async testLoginEndpointInvalidToken(): Promise<void> {
    await this.timeTest('Login Endpoint - Invalid Token', async () => {
      const response = await fetch(`${this.licenseServerUrl}/api/v2/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          auth0_token: 'invalid.token.here',
          device_id: 'test-device-123',
          device_name: 'Test Device',
        }),
      });

      const data = await response.json() as { error?: string };
      
      if (response.status === 401 && data.error) {
        this.addResult('Login Endpoint - Invalid Token', true, 'Correctly rejects invalid token', {
          status: response.status,
          error: data.error
        });
      } else {
        this.addResult('Login Endpoint - Invalid Token', false, 'Unexpected response', {
          status: response.status,
          data
        });
      }
    });
  }

  async testLoginEndpointValidToken(): Promise<void> {
    const testToken = process.env.TEST_AUTH0_TOKEN;
    
    if (!testToken) {
      this.addResult('Login Endpoint - Valid Token', false, 'TEST_AUTH0_TOKEN not provided (skipping)', {
        skip: true,
        hint: 'Set TEST_AUTH0_TOKEN environment variable to test with real token'
      });
      return;
    }

    await this.timeTest('Login Endpoint - Valid Token', async () => {
      const response = await fetch(`${this.licenseServerUrl}/api/v2/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          auth0_token: testToken,
          device_id: 'test-device-e2e',
          device_name: 'E2E Test Device',
        }),
      });

      const data = await response.json() as {
        session_token?: string;
        entitlement_token?: any;
        user?: { id?: string; email?: string };
        error?: string;
      };

      if (response.status === 200) {
        if (data.session_token && data.entitlement_token && data.user) {
          // Store for refresh test
          this.sessionToken = data.session_token;
          this.entitlementToken = data.entitlement_token;
          this.userId = data.user.id || null;

          this.addResult('Login Endpoint - Valid Token', true, 'Successfully authenticated', {
            hasSessionToken: !!data.session_token,
            hasEntitlementToken: !!data.entitlement_token,
            userEmail: data.user.email,
            plan: data.entitlement_token.plan,
            features: data.entitlement_token.features,
          });
        } else {
          this.addResult('Login Endpoint - Valid Token', false, 'Response missing required fields', { data });
        }
      } else {
        this.addResult('Login Endpoint - Valid Token', false, `Authentication failed: ${data.error || 'Unknown error'}`, {
          status: response.status,
          data
        });
      }
    });
  }

  async testLoginEndpointCors(): Promise<void> {
    await this.timeTest('Login Endpoint CORS', async () => {
      const response = await fetch(`${this.licenseServerUrl}/api/v2/auth/login`, {
        method: 'OPTIONS',
      });

      const corsHeader = response.headers.get('Access-Control-Allow-Origin');
      const corsMethods = response.headers.get('Access-Control-Allow-Methods');
      
      if (corsHeader && corsMethods) {
        this.addResult('Login Endpoint CORS', true, 'CORS headers are present', {
          'Access-Control-Allow-Origin': corsHeader,
          'Access-Control-Allow-Methods': corsMethods,
        });
      } else {
        this.addResult('Login Endpoint CORS', false, 'CORS headers missing', {
          headers: Object.fromEntries(response.headers.entries())
        });
      }
    });
  }

  async testRefreshEndpointMissingToken(): Promise<void> {
    await this.timeTest('Refresh Endpoint - Missing Token', async () => {
      const response = await fetch(`${this.licenseServerUrl}/api/v2/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      });

      const data = await response.json() as { error?: string };
      
      if (response.status === 400 && data.error && data.error.includes('token')) {
        this.addResult('Refresh Endpoint - Missing Token', true, 'Correctly validates missing token', {
          status: response.status,
          error: data.error
        });
      } else {
        this.addResult('Refresh Endpoint - Missing Token', false, 'Unexpected response', {
          status: response.status,
          data
        });
      }
    });
  }

  async testRefreshEndpointInvalidToken(): Promise<void> {
    await this.timeTest('Refresh Endpoint - Invalid Token', async () => {
      const response = await fetch(`${this.licenseServerUrl}/api/v2/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_token: 'invalid_session_token',
          device_id: 'test-device-123',
        }),
      });

      const data = await response.json() as { error?: string };
      
      if (response.status === 401 && data.error) {
        this.addResult('Refresh Endpoint - Invalid Token', true, 'Correctly rejects invalid token', {
          status: response.status,
          error: data.error
        });
      } else {
        this.addResult('Refresh Endpoint - Invalid Token', false, 'Unexpected response', {
          status: response.status,
          data
        });
      }
    });
  }

  async testRefreshEndpointValidToken(): Promise<void> {
    if (!this.sessionToken) {
      this.addResult('Refresh Endpoint - Valid Token', false, 'No session token available (skipping)', {
        skip: true,
        hint: 'Run login test first to get session token'
      });
      return;
    }

    await this.timeTest('Refresh Endpoint - Valid Token', async () => {
      const response = await fetch(`${this.licenseServerUrl}/api/v2/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_token: this.sessionToken,
          device_id: 'test-device-e2e',
        }),
      });

      const data = await response.json() as {
        session_token?: string;
        entitlement_token?: any;
        error?: string;
      };

      if (response.status === 200) {
        if (data.session_token && data.entitlement_token) {
          // Update stored tokens
          this.sessionToken = data.session_token;
          this.entitlementToken = data.entitlement_token;

          this.addResult('Refresh Endpoint - Valid Token', true, 'Successfully refreshed tokens', {
            hasNewSessionToken: !!data.session_token,
            hasEntitlementToken: !!data.entitlement_token,
            plan: data.entitlement_token.plan,
          });
        } else {
          this.addResult('Refresh Endpoint - Valid Token', false, 'Response missing required fields', { data });
        }
      } else {
        this.addResult('Refresh Endpoint - Valid Token', false, `Refresh failed: ${data.error || 'Unknown error'}`, {
          status: response.status,
          data
        });
      }
    });
  }

  /**
   * Phase 2: Auth0 Configuration Tests
   */

  async testAuth0Configuration(): Promise<void> {
    if (!this.auth0Domain) {
      this.addResult('Auth0 Configuration', false, 'AUTH0_DOMAIN environment variable is not set', {
        hint: 'Set AUTH0_DOMAIN in your environment or .env file'
      });
      return;
    }

    await this.timeTest('Auth0 Configuration', async () => {
      this.addResult('Auth0 Configuration', true, 'AUTH0_DOMAIN is configured', {
        domain: this.auth0Domain,
        audience: this.auth0Audience || 'not set'
      });

      // Test JWKS endpoint accessibility
      const jwksUrl = `https://${this.auth0Domain}/.well-known/jwks.json`;
      try {
        const response = await fetch(jwksUrl);
        
        if (response.ok) {
          const data = await response.json() as { keys?: Array<any> };
          const keyCount = data.keys?.length || 0;
          this.addResult('Auth0 JWKS Endpoint', true, `JWKS endpoint is accessible (${keyCount} keys found)`, {
            keys: keyCount,
            url: jwksUrl
          });
        } else {
          this.addResult('Auth0 JWKS Endpoint', false, `JWKS endpoint returned status ${response.status}`, {
            status: response.status,
            url: jwksUrl
          });
        }
      } catch (error: any) {
        this.addResult('Auth0 JWKS Endpoint', false, `Failed to access JWKS endpoint: ${error.message}`, {
          error: error.message,
          url: jwksUrl
        });
      }
    });
  }

  async testTokenValidationFunction(): Promise<void> {
    if (!this.auth0Domain) {
      this.addResult('Token Validation Function', false, 'Cannot test without AUTH0_DOMAIN', { skip: true });
      return;
    }

    await this.timeTest('Token Validation Function', async () => {
      // Test with obviously invalid token
      try {
        await verifyAuth0Token('invalid.token.here');
        this.addResult('Token Validation Function', false, 'Should have rejected invalid token');
      } catch (error: any) {
        if (error.message.includes('Invalid token') || error.message.includes('Token') || error.message.includes('format')) {
          this.addResult('Token Validation Function', true, 'Correctly rejects invalid tokens', {
            error: error.message
          });
        } else {
          this.addResult('Token Validation Function', false, `Unexpected error: ${error.message}`, {
            error: error.message
          });
        }
      }
    });
  }

  /**
   * Phase 3: Response Structure Validation
   */

  async testLoginResponseStructure(): Promise<void> {
    if (!this.entitlementToken) {
      this.addResult('Login Response Structure', false, 'No entitlement token available (skipping)', {
        skip: true,
        hint: 'Run login test first'
      });
      return;
    }

    await this.timeTest('Login Response Structure', async () => {
      const requiredFields = ['sub', 'product', 'plan', 'features'];
      const missingFields = requiredFields.filter(field => !(field in this.entitlementToken));

      if (missingFields.length === 0) {
        this.addResult('Login Response Structure', true, 'All required fields present in entitlement token', {
          fields: requiredFields,
          plan: this.entitlementToken.plan,
          features: this.entitlementToken.features,
        });
      } else {
        this.addResult('Login Response Structure', false, `Missing required fields: ${missingFields.join(', ')}`, {
          missing: missingFields,
          present: requiredFields.filter(f => !missingFields.includes(f))
        });
      }
    });
  }

  /**
   * Phase 4: Performance Tests
   */

  async testHealthEndpointPerformance(): Promise<void> {
    const times: number[] = [];
    const iterations = 10;

    for (let i = 0; i < iterations; i++) {
      const start = Date.now();
      await fetch(`${this.licenseServerUrl}/api/health`);
      times.push(Date.now() - start);
    }

    const avgTime = times.reduce((a, b) => a + b, 0) / times.length;
    const maxTime = Math.max(...times);
    const minTime = Math.min(...times);

    if (avgTime < 1000) {
      this.addResult('Health Endpoint Performance', true, `Average response time: ${avgTime.toFixed(2)}ms`, {
        average: avgTime,
        min: minTime,
        max: maxTime,
        iterations
      });
    } else {
      this.addResult('Health Endpoint Performance', false, `Average response time too slow: ${avgTime.toFixed(2)}ms`, {
        average: avgTime,
        min: minTime,
        max: maxTime,
        iterations
      });
    }
  }

  /**
   * Run all tests
   */
  async runAll(): Promise<void> {
    console.log('🧪 Running Comprehensive E2E Test Suite for License Server\n');
    console.log(`License Server URL: ${this.licenseServerUrl}`);
    console.log(`Auth0 Domain: ${this.auth0Domain || 'Not configured'}`);
    console.log(`Auth0 Audience: ${this.auth0Audience || 'Not configured'}\n`);
    console.log('─'.repeat(60) + '\n');

    // Phase 1: License Server API Tests
    console.log('📡 Phase 1: License Server API Tests\n');
    await this.testHealthEndpoint();
    await this.testHealthEndpointCors();
    await this.testLoginEndpointMissingToken();
    await this.testLoginEndpointInvalidToken();
    await this.testLoginEndpointValidToken();
    await this.testLoginEndpointCors();
    await this.testRefreshEndpointMissingToken();
    await this.testRefreshEndpointInvalidToken();
    await this.testRefreshEndpointValidToken();

    // Phase 2: Auth0 Configuration Tests
    console.log('\n🔐 Phase 2: Auth0 Configuration Tests\n');
    await this.testAuth0Configuration();
    await this.testTokenValidationFunction();

    // Phase 3: Response Structure Validation
    console.log('\n📋 Phase 3: Response Structure Validation\n');
    await this.testLoginResponseStructure();

    // Phase 4: Performance Tests
    console.log('\n⚡ Phase 4: Performance Tests\n');
    await this.testHealthEndpointPerformance();

    // Print summary
    console.log('\n' + '─'.repeat(60));
    console.log('📊 Test Summary\n');

    const passed = this.results.filter(r => r.passed).length;
    const failed = this.results.filter(r => !r.passed && !r.details?.skip).length;
    const skipped = this.results.filter(r => r.details?.skip).length;

    console.log(`✅ Passed: ${passed}`);
    console.log(`❌ Failed: ${failed}`);
    if (skipped > 0) {
      console.log(`⏭️  Skipped: ${skipped}`);
    }
    console.log(`📝 Total: ${this.results.length}\n`);

    // Calculate average duration
    const durations = this.results.filter(r => r.duration).map(r => r.duration!);
    if (durations.length > 0) {
      const avgDuration = durations.reduce((a, b) => a + b, 0) / durations.length;
      console.log(`⏱️  Average test duration: ${avgDuration.toFixed(2)}ms\n`);
    }

    if (failed === 0) {
      console.log('🎉 All tests passed!\n');
    } else {
      console.log('⚠️  Some tests failed. Please review the results above.\n');
    }

    // Print next steps
    console.log('📝 Next Steps:');
    console.log('   1. If Auth0 is not configured, set AUTH0_DOMAIN environment variable');
    console.log('   2. To test with a real token, set TEST_AUTH0_TOKEN environment variable');
    console.log('   3. Verify callback URLs are configured in Auth0 Dashboard');
    console.log('   4. Test the full OAuth flow in the Upload Bridge application\n');

    return {
      passed,
      failed,
      skipped,
      total: this.results.length,
      results: this.results
    } as any;
  }
}

// Run tests
const suite = new E2ETestSuite();
suite.runAll().catch((error) => {
  console.error('Test suite failed:', error);
  process.exit(1);
});

