/**
 * Load Test Scenarios
 * Different load patterns for testing application performance
 */

const ApiClient = require('../helpers/api-client');

const BASE_URL = process.env.LICENSE_SERVER_URL || process.env.API_URL || 'http://localhost:8000';

/**
 * Scenario 1: Steady Load
 * Constant number of concurrent users
 */
async function steadyLoad(users = 10, duration = 60) {
    console.log(`\n=== Steady Load: ${users} users for ${duration}s ===`);
    
    const startTime = Date.now();
    const endTime = startTime + (duration * 1000);
    const requests = [];
    let success = 0;
    let failed = 0;
    const responseTimes = [];
    
    while (Date.now() < endTime) {
        // Maintain constant number of concurrent requests
        while (requests.length < users && Date.now() < endTime) {
            const client = new ApiClient(BASE_URL, { logging: false });
            const request = client.health()
                .then(response => {
                    if (response.status === 200) {
                        success++;
                    } else {
                        failed++;
                    }
                    return response;
                })
                .catch(error => {
                    failed++;
                    return null;
                });
            
            requests.push(request);
        }
        
        // Remove completed requests
        const completed = await Promise.allSettled(requests);
        requests.length = 0;
        
        // Small delay to prevent overwhelming
        await new Promise(resolve => setTimeout(resolve, 100));
    }
    
    // Wait for remaining requests
    await Promise.allSettled(requests);
    
    console.log(`Results: ${success} success, ${failed} failed`);
    return { success, failed, duration };
}

/**
 * Scenario 2: Ramp Up
 * Gradually increase load
 */
async function rampUp(maxUsers = 50, rampDuration = 300, stepDuration = 10) {
    console.log(`\n=== Ramp Up: 0 to ${maxUsers} users over ${rampDuration}s ===`);
    
    const steps = Math.floor(rampDuration / stepDuration);
    const usersPerStep = maxUsers / steps;
    let currentUsers = 0;
    let totalSuccess = 0;
    let totalFailed = 0;
    
    for (let step = 0; step < steps; step++) {
        currentUsers = Math.floor(usersPerStep * (step + 1));
        console.log(`Step ${step + 1}/${steps}: ${currentUsers} users`);
        
        const result = await steadyLoad(currentUsers, stepDuration);
        totalSuccess += result.success;
        totalFailed += result.failed;
    }
    
    console.log(`Total Results: ${totalSuccess} success, ${totalFailed} failed`);
    return { success: totalSuccess, failed: totalFailed };
}

/**
 * Scenario 3: Spike Test
 * Sudden increase in load
 */
async function spikeTest(baseUsers = 5, spikeUsers = 100, spikeDuration = 30) {
    console.log(`\n=== Spike Test: ${baseUsers} → ${spikeUsers} users for ${spikeDuration}s ===`);
    
    // Baseline
    console.log('Baseline load...');
    await steadyLoad(baseUsers, 30);
    
    // Spike
    console.log(`Spike to ${spikeUsers} users...`);
    const spikeResult = await steadyLoad(spikeUsers, spikeDuration);
    
    // Recovery
    console.log('Recovery...');
    await steadyLoad(baseUsers, 30);
    
    return spikeResult;
}

/**
 * Scenario 4: Stress Test
 * Gradually increase until failure
 */
async function stressTest(startUsers = 10, maxUsers = 500, increment = 10) {
    console.log(`\n=== Stress Test: Find breaking point ===`);
    
    let currentUsers = startUsers;
    let lastSuccess = 0;
    
    while (currentUsers <= maxUsers) {
        console.log(`Testing with ${currentUsers} users...`);
        
        const result = await steadyLoad(currentUsers, 30);
        const successRate = result.success / (result.success + result.failed);
        
        console.log(`Success rate: ${(successRate * 100).toFixed(1)}%`);
        
        if (successRate < 0.5) {
            console.log(`\nBreaking point reached at ${currentUsers} users`);
            console.log(`Recommended max: ${lastSuccess} users`);
            break;
        }
        
        lastSuccess = currentUsers;
        currentUsers += increment;
    }
    
    return { maxUsers: lastSuccess };
}

/**
 * Scenario 5: Endurance Test
 * Sustained load over long period
 */
async function enduranceTest(users = 20, duration = 600) {
    console.log(`\n=== Endurance Test: ${users} users for ${duration}s ===`);
    
    const result = await steadyLoad(users, duration);
    
    console.log(`Endurance test complete`);
    console.log(`Results: ${result.success} success, ${result.failed} failed`);
    
    return result;
}

/**
 * Scenario 6: Mixed Workload
 * Different types of requests
 */
async function mixedWorkload(users = 10, duration = 60) {
    console.log(`\n=== Mixed Workload: ${users} users for ${duration}s ===`);
    
    const startTime = Date.now();
    const endTime = startTime + (duration * 1000);
    const requests = [];
    const stats = {
        health: { success: 0, failed: 0 },
        login: { success: 0, failed: 0 },
        license: { success: 0, failed: 0 },
    };
    
    while (Date.now() < endTime) {
        while (requests.length < users && Date.now() < endTime) {
            const client = new ApiClient(BASE_URL, { logging: false });
            const rand = Math.random();
            
            let request;
            if (rand < 0.4) {
                // 40% health checks
                request = client.health().then(r => {
                    if (r.status === 200) stats.health.success++;
                    else stats.health.failed++;
                });
            } else if (rand < 0.7) {
                // 30% login attempts
                request = client.login('test@example.com', 'testpassword123', 'LOAD_TEST', 'Load Test Device')
                    .then(r => {
                        if (r.status === 200) stats.login.success++;
                        else stats.login.failed++;
                    });
            } else {
                // 30% license info (requires auth)
                request = client.login('test@example.com', 'testpassword123', 'LOAD_TEST', 'Load Test Device')
                    .then(async loginR => {
                        if (loginR.status === 200) {
                            const licenseR = await client.getLicenseInfo();
                            if (licenseR.status === 200) stats.license.success++;
                            else stats.license.failed++;
                        } else {
                            stats.license.failed++;
                        }
                    });
            }
            
            requests.push(request.catch(() => {}));
        }
        
        const completed = await Promise.allSettled(requests);
        requests.length = 0;
        await new Promise(resolve => setTimeout(resolve, 100));
    }
    
    await Promise.allSettled(requests);
    
    console.log('Mixed Workload Results:');
    console.log(`  Health: ${stats.health.success} success, ${stats.health.failed} failed`);
    console.log(`  Login: ${stats.login.success} success, ${stats.login.failed} failed`);
    console.log(`  License: ${stats.license.success} success, ${stats.license.failed} failed`);
    
    return stats;
}

// Export scenarios
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        steadyLoad,
        rampUp,
        spikeTest,
        stressTest,
        enduranceTest,
        mixedWorkload,
    };
}

// Run scenario if called directly
if (require.main === module) {
    const scenario = process.argv[2] || 'steady';
    const users = parseInt(process.argv[3]) || 10;
    const duration = parseInt(process.argv[4]) || 60;
    
    (async () => {
        switch (scenario) {
            case 'steady':
                await steadyLoad(users, duration);
                break;
            case 'ramp':
                await rampUp(users, duration);
                break;
            case 'spike':
                await spikeTest(5, users, duration);
                break;
            case 'stress':
                await stressTest(10, users);
                break;
            case 'endurance':
                await enduranceTest(users, duration);
                break;
            case 'mixed':
                await mixedWorkload(users, duration);
                break;
            default:
                console.log('Available scenarios: steady, ramp, spike, stress, endurance, mixed');
        }
    })();
}
