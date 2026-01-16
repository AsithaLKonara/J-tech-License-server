/**
 * Test Data Generator
 * 
 * Generates realistic test data for performance and load testing
 */

const BASE_URL = process.env.API_URL || process.env.BASE_URL || 'http://localhost:8000';
const API_BASE = `${BASE_URL}/api/v2`;

// Simple data generator
function generateEmail(prefix = 'test') {
    const random = Math.random().toString(36).substring(2, 9);
    return `${prefix}_${random}@example.com`;
}

function generatePassword() {
    return 'TestPassword123!' + Math.random().toString(36).substring(2, 9);
}

function generateDeviceId() {
    return 'DEVICE_' + Math.random().toString(36).substring(2, 15).toUpperCase();
}

async function createTestUser(email, password) {
    // Note: This assumes a registration endpoint exists
    // If not, users need to be created via seeder or admin
    console.log(`Creating test user: ${email}`);
    
    try {
        const fetch = (await import('node-fetch')).default;
        const response = await fetch(`${API_BASE}/auth/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email,
                password,
                name: `Test User ${email}`,
            }),
        });
        
        if (response.ok) {
            return await response.json();
        } else {
            const error = await response.text();
            throw new Error(`Registration failed: ${error}`);
        }
    } catch (error) {
        // If registration endpoint doesn't exist, just log
        console.log(`  Note: Registration endpoint may not exist. User ${email} needs to be created via seeder.`);
        return null;
    }
}

async function login(email, password) {
    const fetch = (await import('node-fetch')).default;
    const response = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            email,
            password,
            device_id: generateDeviceId(),
            device_name: 'Test Device',
        }),
    });
    
    if (!response.ok) {
        throw new Error(`Login failed: ${response.status}`);
    }
    
    return await response.json();
}

async function generateTestData(count = 10) {
    console.log(`Generating ${count} test users...\n`);
    
    const users = [];
    
    for (let i = 0; i < count; i++) {
        const email = generateEmail('loadtest');
        const password = generatePassword();
        
        try {
            const userData = await createTestUser(email, password);
            if (userData) {
                users.push({ email, password, ...userData });
                console.log(`✓ Created user ${i + 1}/${count}: ${email}`);
            } else {
                users.push({ email, password });
                console.log(`  User ${i + 1}/${count}: ${email} (needs manual creation)`);
            }
        } catch (error) {
            console.error(`✗ Failed to create user ${i + 1}: ${error.message}`);
        }
        
        // Small delay to avoid overwhelming the server
        await new Promise(resolve => setTimeout(resolve, 100));
    }
    
    console.log(`\nGenerated ${users.length} test users.`);
    console.log('\nTest users (email, password):');
    console.log('----------------------------------------');
    users.forEach((user, index) => {
        console.log(`${index + 1}. ${user.email} / ${user.password}`);
    });
    
    // Save to file for use in tests
    const fs = await import('fs');
    const testDataFile = 'tests/fixtures/load-test-users.json';
    await fs.promises.writeFile(
        testDataFile,
        JSON.stringify(users, null, 2)
    );
    console.log(`\n✓ Test data saved to ${testDataFile}`);
    
    return users;
}

// Main execution
if (require.main === module) {
    const count = parseInt(process.argv[2] || '10');
    generateTestData(count).catch(error => {
        console.error('Error generating test data:', error);
        process.exit(1);
    });
}

module.exports = { generateTestData, generateEmail, generatePassword, generateDeviceId };
