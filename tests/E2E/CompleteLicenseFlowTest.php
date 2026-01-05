<?php

namespace Tests\E2E;

use Tests\Browser\BrowserTestCase;
use Tests\Helpers\TestHelpers;
use App\Models\User;
use App\Models\License;
use App\Models\Subscription;
use Laravel\Dusk\Browser;

class CompleteLicenseFlowTest extends BrowserTestCase
{
    /**
     * Test admin creates license and it appears in user account.
     */
    public function test_admin_creates_license_for_user(): void
    {
        $this->browse(function (Browser $browser) {
            $admin = TestHelpers::createAdmin(['email' => 'admin' . uniqid() . '@test.com']);
            $user = TestHelpers::createUser(['email' => 'licenseuser' . uniqid() . '@test.com']);
            $subscription = TestHelpers::createSubscription($user, ['plan_type' => 'yearly']);

            TestHelpers::loginAs($browser, $admin);

            // Admin creates license for user
            $browser->visit('/admin/users/' . $user->id)
                ->assertSee($user->email);

            // Create license via admin (if admin interface supports it)
            // For now, we verify license can be created
            $license = TestHelpers::createLicense($user, $subscription, [
                'plan' => 'yearly',
                'status' => 'active',
            ]);

            // User should see license
            TestHelpers::loginAs($browser, $user);
            $browser->visit('/licenses')
                ->assertSee('Licenses')
                ->assertSee($license->plan);
        });
    }

    /**
     * Test user views licenses page with all licenses displayed.
     */
    public function test_user_views_all_licenses(): void
    {
        $this->browse(function (Browser $browser) {
            $user = TestHelpers::createUser(['email' => 'viewlicenses' . uniqid() . '@test.com']);
            $subscription = TestHelpers::createSubscription($user);
            $license1 = TestHelpers::createLicense($user, $subscription, ['plan' => 'monthly']);
            $license2 = TestHelpers::createLicense($user, $subscription, ['plan' => 'yearly']);

            TestHelpers::loginAs($browser, $user);

            $browser->visit('/licenses')
                ->assertSee('Licenses')
                ->assertSee($license1->plan)
                ->assertSee($license2->plan)
                ->assertSee($license1->status)
                ->assertSee($license2->status);
        });
    }

    /**
     * Test license status updates (active → expired → cancelled).
     */
    public function test_license_status_updates(): void
    {
        $this->browse(function (Browser $browser) {
            $user = TestHelpers::createUser(['email' => 'statusupdate' . uniqid() . '@test.com']);
            $subscription = TestHelpers::createSubscription($user);
            $license = TestHelpers::createLicense($user, $subscription, [
                'status' => 'active',
                'expires_at' => now()->addMonth(),
            ]);

            TestHelpers::loginAs($browser, $user);

            // License should show as active
            $browser->visit('/licenses')
                ->assertSee('active')
                ->assertSee($license->plan);

            // Update license to expired
            $license->update(['status' => 'expired', 'expires_at' => now()->subDay()]);

            $browser->refresh()
                ->assertSee('expired');

            // Update license to cancelled
            $license->update(['status' => 'cancelled']);

            $browser->refresh()
                ->assertSee('cancelled');
        });
    }

    /**
     * Test license features validation.
     */
    public function test_license_features_validation(): void
    {
        $this->browse(function (Browser $browser) {
            $user = TestHelpers::createUser(['email' => 'features' . uniqid() . '@test.com']);
            $subscription = TestHelpers::createSubscription($user);
            $license = TestHelpers::createLicense($user, $subscription, [
                'features' => ['pattern_upload', 'wifi_upload', 'advanced_controls'],
            ]);

            TestHelpers::loginAs($browser, $user);

            $browser->visit('/licenses')
                ->assertSee('pattern_upload')
                ->assertSee('wifi_upload')
                ->assertSee('advanced_controls');
        });
    }

    /**
     * Test license expiration handling.
     */
    public function test_license_expiration_handling(): void
    {
        $this->browse(function (Browser $browser) {
            $user = TestHelpers::createUser(['email' => 'expiration' . uniqid() . '@test.com']);
            $subscription = TestHelpers::createSubscription($user, [
                'expires_at' => now()->subDay(), // Expired
            ]);
            $license = TestHelpers::createLicense($user, $subscription, [
                'status' => 'expired',
                'expires_at' => now()->subDay(),
            ]);

            TestHelpers::loginAs($browser, $user);

            $browser->visit('/licenses')
                ->assertSee('expired')
                ->assertSee('Expired');

            // User should be prompted to renew
            $browser->visit('/dashboard')
                ->assertSee('expired');
        });
    }

    /**
     * Test empty licenses state.
     */
    public function test_empty_licenses_state(): void
    {
        $this->browse(function (Browser $browser) {
            $user = TestHelpers::createUser(['email' => 'emptylicenses' . uniqid() . '@test.com']);

            TestHelpers::loginAs($browser, $user);

            $browser->visit('/licenses')
                ->assertSee('Licenses')
                ->assertSee('No licenses');
        });
    }

    /**
     * Test license subscription association.
     */
    public function test_license_subscription_association(): void
    {
        $this->browse(function (Browser $browser) {
            $user = TestHelpers::createUser(['email' => 'association' . uniqid() . '@test.com']);
            $subscription = TestHelpers::createSubscription($user, [
                'plan_type' => 'yearly',
                'status' => 'active',
            ]);
            $license = TestHelpers::createLicense($user, $subscription);

            TestHelpers::loginAs($browser, $user);

            $browser->visit('/licenses')
                ->assertSee($license->plan)
                ->assertSee($subscription->plan_type);
        });
    }
}
