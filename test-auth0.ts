/**
 * Test Script for Auth0 Configuration
 * 
 * This script helps verify that Auth0 is correctly configured.
 * Run this locally to test your Auth0 setup before deploying.
 * 
 * Usage:
 *   npx ts-node test-auth0.ts
 * 
 * Or compile and run:
 *   tsc test-auth0.ts
 *   node test-auth0.js
 */

import { verifyAuth0Token, extractUserInfo } from './lib/jwt-validator';

async function testAuth0Config() {
  console.log('🔍 Testing Auth0 Configuration...\n');

  // Check environment variables
  const domain = process.env.AUTH0_DOMAIN;
  const audience = process.env.AUTH0_AUDIENCE;
  const jwksUri = process.env.AUTH0_JWKS_URI;

  console.log('Environment Variables:');
  console.log(`  AUTH0_DOMAIN: ${domain || '❌ NOT SET'}`);
  console.log(`  AUTH0_AUDIENCE: ${audience || '⚠️  Not set (optional)'}`);
  console.log(`  AUTH0_JWKS_URI: ${jwksUri || '⚠️  Not set (will auto-derive)'}`);
  console.log('');

  if (!domain) {
    console.error('❌ AUTH0_DOMAIN is required!');
    console.error('   Set it in your .env file or environment variables.');
    process.exit(1);
  }

  console.log('✅ AUTH0_DOMAIN is set');
  console.log('');

  // Test JWKS endpoint accessibility
  const jwksUrl = jwksUri || `https://${domain}/.well-known/jwks.json`;
  console.log(`Testing JWKS endpoint: ${jwksUrl}`);

  try {
    const response = await fetch(jwksUrl);
    if (response.ok) {
      const data = await response.json();
      console.log(`✅ JWKS endpoint is accessible (${data.keys?.length || 0} keys found)`);
    } else {
      console.error(`❌ JWKS endpoint returned status ${response.status}`);
    }
  } catch (error: any) {
    console.error(`❌ Failed to access JWKS endpoint: ${error.message}`);
  }

  console.log('');

  // Test token validation (if token provided)
  const testToken = process.env.TEST_AUTH0_TOKEN;
  if (testToken) {
    console.log('Testing token validation...');
    try {
      const decoded = await verifyAuth0Token(testToken);
      console.log('✅ Token is valid');
      console.log(`   Subject (sub): ${decoded.sub}`);
      console.log(`   Email: ${decoded.email || 'Not in token'}`);
      console.log(`   Issuer: ${decoded.iss}`);
      console.log(`   Expires: ${new Date(decoded.exp * 1000).toISOString()}`);

      try {
        const userInfo = extractUserInfo(decoded);
        console.log('✅ User info extracted successfully');
        console.log(`   Sub: ${userInfo.sub}`);
        console.log(`   Email: ${userInfo.email}`);
      } catch (error: any) {
        console.error(`❌ Failed to extract user info: ${error.message}`);
      }
    } catch (error: any) {
      console.error(`❌ Token validation failed: ${error.message}`);
    }
  } else {
    console.log('⚠️  No TEST_AUTH0_TOKEN provided');
    console.log('   Set TEST_AUTH0_TOKEN environment variable to test token validation');
  }

  console.log('');
  console.log('📝 Next Steps:');
  console.log('   1. Deploy to Vercel with these environment variables');
  console.log('   2. Test the /api/v2/auth/login endpoint with a real Auth0 token');
  console.log('   3. See VERIFY_AUTH0_SETUP.md for verification steps');
}

// Run the test
testAuth0Config().catch((error) => {
  console.error('Test failed:', error);
  process.exit(1);
});

