<?php

namespace Tests\E2E;

use Tests\Browser\BrowserTestCase;
use Tests\Helpers\TestHelpers;
use App\Models\Device;
use Laravel\Dusk\Browser;

class DeviceTest extends BrowserTestCase
{
    /**
     * Test view devices page.
     */
    public function test_can_view_devices_page(): void
    {
        $user = TestHelpers::createUser(['email' => 'devices@test.com']);

        $this->browse(function (Browser $browser) use ($user) {
            TestHelpers::loginAs($browser, $user);
            
            $browser->visit('/devices')
                ->assertPathIs('/devices')
                ->assertSee('Devices');
        });
    }

    /**
     * Test display devices associated with active license.
     */
    public function test_displays_devices_associated_with_active_license(): void
    {
        $user = TestHelpers::createUser(['email' => 'devlist@test.com']);
        $subscription = TestHelpers::createSubscription($user);
        $license = TestHelpers::createLicense($user, $subscription);
        $device1 = TestHelpers::createDevice($license, ['device_name' => 'Device 1']);
        $device2 = TestHelpers::createDevice($license, ['device_name' => 'Device 2']);

        $this->browse(function (Browser $browser) use ($user) {
            TestHelpers::loginAs($browser, $user);
            
            $browser->visit('/devices')
                ->assertPathIs('/devices')
                ->assertSee('Device 1')
                ->assertSee('Device 2');
        });
    }

    /**
     * Test delete device.
     */
    public function test_can_delete_device(): void
    {
        $user = TestHelpers::createUser(['email' => 'delete@test.com']);
        $subscription = TestHelpers::createSubscription($user);
        $license = TestHelpers::createLicense($user, $subscription);
        $device = TestHelpers::createDevice($license, ['device_name' => 'To Delete']);

        $this->browse(function (Browser $browser) use ($user, $device) {
            TestHelpers::loginAs($browser, $user);
            
            $browser->visit('/devices')
                ->assertPathIs('/devices')
                ->assertSee('To Delete')
                ->press('Delete')
                ->waitForText('Device removed successfully')
                ->assertSee('Device removed successfully');
        });

        // Verify device was deleted
        $this->assertDatabaseMissing('devices', ['id' => $device->id]);
    }

    /**
     * Test verify device ownership before deletion.
     */
    public function test_verifies_device_ownership_before_deletion(): void
    {
        $user1 = TestHelpers::createUser(['email' => 'owner1@test.com']);
        $user2 = TestHelpers::createUser(['email' => 'owner2@test.com']);
        $subscription1 = TestHelpers::createSubscription($user1);
        $license1 = TestHelpers::createLicense($user1, $subscription1);
        $device = TestHelpers::createDevice($license1);

        // Try to delete as user2 - device should not appear in their list
        $this->browse(function (Browser $browser) use ($user2, $device) {
            TestHelpers::loginAs($browser, $user2);
            
            // Device should not appear in user2's device list
            $browser->visit('/devices')
                ->assertPathIs('/devices')
                ->assertDontSee($device->device_name);
        });
    }

    /**
     * Test cannot delete other users' devices.
     */
    public function test_cannot_delete_other_users_devices(): void
    {
        $user1 = TestHelpers::createUser(['email' => 'user1@test.com']);
        $user2 = TestHelpers::createUser(['email' => 'user2@test.com']);
        $subscription1 = TestHelpers::createSubscription($user1);
        $license1 = TestHelpers::createLicense($user1, $subscription1);
        $device = TestHelpers::createDevice($license1);

        $this->browse(function (Browser $browser) use ($user2, $device) {
            TestHelpers::loginAs($browser, $user2);
            
            // Device should not appear in user2's device list
            $browser->visit('/devices')
                ->assertPathIs('/devices')
                ->assertDontSee($device->device_name);
        });
    }

    /**
     * Test empty state when no devices.
     */
    public function test_shows_empty_state_when_no_devices(): void
    {
        $user = TestHelpers::createUser(['email' => 'nodevices@test.com']);

        $this->browse(function (Browser $browser) use ($user) {
            TestHelpers::loginAs($browser, $user);
            
            $browser->visit('/devices')
                ->assertPathIs('/devices');
        });
    }
}
