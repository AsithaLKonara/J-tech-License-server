<?php

namespace Tests\E2E;

use Tests\Browser\BrowserTestCase;
use Tests\Helpers\TestHelpers;
use Laravel\Dusk\Browser;

class LicenseTest extends BrowserTestCase
{
    /**
     * Test view licenses page.
     */
    public function test_can_view_licenses_page(): void
    {
        $user = TestHelpers::createUser(['email' => 'licenses@test.com']);

        $this->browse(function (Browser $browser) use ($user) {
            TestHelpers::loginAs($browser, $user);
            
            $browser->visit('/licenses')
                ->assertPathIs('/licenses')
                ->assertSee('Licenses');
        });
    }

    /**
     * Test display all user licenses.
     */
    public function test_displays_all_user_licenses(): void
    {
        $user = TestHelpers::createUser(['email' => 'alllicenses@test.com']);
        $subscription1 = TestHelpers::createSubscription($user, ['plan_type' => 'monthly']);
        $subscription2 = TestHelpers::createSubscription($user, ['plan_type' => 'annual']);
        $license1 = TestHelpers::createLicense($user, $subscription1);
        $license2 = TestHelpers::createLicense($user, $subscription2);

        $this->browse(function (Browser $browser) use ($user) {
            TestHelpers::loginAs($browser, $user);
            
            $browser->visit('/licenses')
                ->assertPathIs('/licenses')
                ->assertSee('monthly')
                ->assertSee('annual');
        });
    }

    /**
     * Test show license status.
     */
    public function test_shows_license_status(): void
    {
        $user = TestHelpers::createUser(['email' => 'status@test.com']);
        $subscription = TestHelpers::createSubscription($user);
        $activeLicense = TestHelpers::createLicense($user, $subscription, ['status' => 'active']);
        $expiredLicense = TestHelpers::createLicense($user, $subscription, ['status' => 'expired']);

        $this->browse(function (Browser $browser) use ($user) {
            TestHelpers::loginAs($browser, $user);
            
            $browser->visit('/licenses')
                ->assertPathIs('/licenses')
                ->assertSee('active')
                ->assertSee('expired');
        });
    }

    /**
     * Test show associated subscription info.
     */
    public function test_shows_associated_subscription_info(): void
    {
        $user = TestHelpers::createUser(['email' => 'subinfo@test.com']);
        $subscription = TestHelpers::createSubscription($user, [
            'plan_type' => 'lifetime',
            'status' => 'active',
        ]);
        $license = TestHelpers::createLicense($user, $subscription);

        $this->browse(function (Browser $browser) use ($user) {
            TestHelpers::loginAs($browser, $user);
            
            $browser->visit('/licenses')
                ->assertPathIs('/licenses')
                ->assertSee('lifetime');
        });
    }

    /**
     * Test empty state when no licenses.
     */
    public function test_shows_empty_state_when_no_licenses(): void
    {
        $user = TestHelpers::createUser(['email' => 'empty@test.com']);

        $this->browse(function (Browser $browser) use ($user) {
            TestHelpers::loginAs($browser, $user);
            
            $browser->visit('/licenses')
                ->assertPathIs('/licenses');
        });
    }
}
