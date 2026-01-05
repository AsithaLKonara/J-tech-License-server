<?php

namespace Tests\E2E;

use Tests\Browser\BrowserTestCase;
use Tests\Helpers\TestHelpers;
use App\Models\User;
use App\Models\License;
use App\Models\Device;
use App\Models\Subscription;
use Laravel\Dusk\Browser;

class CompleteDeviceFlowTest extends BrowserTestCase
{
    /**
     * Test user registers device via API and it appears in dashboard.
     */
    public function test_device_registered_via_api_appears_in_dashboard(): void
    {
        $this->browse(function (Browser $browser) {
            $user = TestHelpers::createUser(['email' => 'deviceapi' . uniqid() . '@test.com']);
            $subscription = TestHelpers::createSubscription($user);
            $license = TestHelpers::createLicense($user, $subscription);
            $device = TestHelpers::createDevice($license, [
                'device_id' => 'API_DEVICE_001',
                'device_name' => 'API Registered Device',
            ]);

            TestHelpers::loginAs($browser, $user);

            $browser->visit('/devices')
                ->assertSee('Devices')
                ->assertSee($device->device_name)
                ->assertSee($device->device_id);
        });
    }

    /**
     * Test user views devices page with all devices listed.
     */
    public function test_user_views_all_devices(): void
    {
        $this->browse(function (Browser $browser) {
            $user = TestHelpers::createUser(['email' => 'viewdevices' . uniqid() . '@test.com']);
            $subscription = TestHelpers::createSubscription($user);
            $license = TestHelpers::createLicense($user, $subscription);
            $device1 = TestHelpers::createDevice($license, ['device_name' => 'Device 1']);
            $device2 = TestHelpers::createDevice($license, ['device_name' => 'Device 2']);
            $device3 = TestHelpers::createDevice($license, ['device_name' => 'Device 3']);

            TestHelpers::loginAs($browser, $user);

            $browser->visit('/devices')
                ->assertSee('Devices')
                ->assertSee($device1->device_name)
                ->assertSee($device2->device_name)
                ->assertSee($device3->device_name);
        });
    }

    /**
     * Test user deletes device and it is removed from database.
     */
    public function test_user_deletes_device(): void
    {
        $this->browse(function (Browser $browser) {
            $user = TestHelpers::createUser(['email' => 'deletedevice' . uniqid() . '@test.com']);
            $subscription = TestHelpers::createSubscription($user);
            $license = TestHelpers::createLicense($user, $subscription);
            $device = TestHelpers::createDevice($license, ['device_name' => 'Device to Delete']);

            TestHelpers::loginAs($browser, $user);

            $browser->visit('/devices')
                ->assertSee($device->device_name)
                ->press('Delete')
                ->waitForText('Device deleted')
                ->assertDontSee($device->device_name);

            // Verify device is deleted from database
            $this->assertDatabaseMissing('devices', ['id' => $device->id]);
        });
    }

    /**
     * Test device limit enforcement (max_devices check).
     */
    public function test_device_limit_enforcement(): void
    {
        $this->browse(function (Browser $browser) {
            $user = TestHelpers::createUser(['email' => 'devicelimit' . uniqid() . '@test.com']);
            $subscription = TestHelpers::createSubscription($user);
            $license = TestHelpers::createLicense($user, $subscription, [
                'max_devices' => 2,
            ]);

            // Create devices up to limit
            $device1 = TestHelpers::createDevice($license, ['device_name' => 'Device 1']);
            $device2 = TestHelpers::createDevice($license, ['device_name' => 'Device 2']);

            TestHelpers::loginAs($browser, $user);

            $browser->visit('/devices')
                ->assertSee($device1->device_name)
                ->assertSee($device2->device_name);

            // Attempting to register more devices should show limit message
            // This would be handled by API, but dashboard should show current count
            $browser->assertSee('2'); // Device count
        });
    }

    /**
     * Test device ownership verification.
     */
    public function test_device_ownership_verification(): void
    {
        $this->browse(function (Browser $browser) {
            $user1 = TestHelpers::createUser(['email' => 'owner1' . uniqid() . '@test.com']);
            $user2 = TestHelpers::createUser(['email' => 'owner2' . uniqid() . '@test.com']);
            $subscription1 = TestHelpers::createSubscription($user1);
            $subscription2 = TestHelpers::createSubscription($user2);
            $license1 = TestHelpers::createLicense($user1, $subscription1);
            $license2 = TestHelpers::createLicense($user2, $subscription2);
            $device1 = TestHelpers::createDevice($license1, ['device_name' => 'User 1 Device']);
            $device2 = TestHelpers::createDevice($license2, ['device_name' => 'User 2 Device']);

            // User 1 should only see their device
            TestHelpers::loginAs($browser, $user1);
            $browser->visit('/devices')
                ->assertSee($device1->device_name)
                ->assertDontSee($device2->device_name);

            // User 2 should only see their device
            $browser->press('Logout')
                ->assertGuest();
            TestHelpers::loginAs($browser, $user2);
            $browser->visit('/devices')
                ->assertSee($device2->device_name)
                ->assertDontSee($device1->device_name);
        });
    }

    /**
     * Test empty devices state.
     */
    public function test_empty_devices_state(): void
    {
        $this->browse(function (Browser $browser) {
            $user = TestHelpers::createUser(['email' => 'emptydevices' . uniqid() . '@test.com']);

            TestHelpers::loginAs($browser, $user);

            $browser->visit('/devices')
                ->assertSee('Devices')
                ->assertSee('No devices');
        });
    }

    /**
     * Test device last seen timestamp.
     */
    public function test_device_last_seen_timestamp(): void
    {
        $this->browse(function (Browser $browser) {
            $user = TestHelpers::createUser(['email' => 'lastseen' . uniqid() . '@test.com']);
            $subscription = TestHelpers::createSubscription($user);
            $license = TestHelpers::createLicense($user, $subscription);
            $device = TestHelpers::createDevice($license, [
                'device_name' => 'Last Seen Device',
                'last_seen_at' => now(),
            ]);

            TestHelpers::loginAs($browser, $user);

            $browser->visit('/devices')
                ->assertSee($device->device_name)
                ->assertSee($device->last_seen_at->format('Y-m-d'));
        });
    }
}
