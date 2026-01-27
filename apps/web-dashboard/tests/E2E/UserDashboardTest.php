<?php

namespace Tests\E2E;

use Tests\Browser\BrowserTestCase;
use Tests\Helpers\TestHelpers;
use Laravel\Dusk\Browser;

class UserDashboardTest extends BrowserTestCase
{
    /**
     * Test dashboard loads for authenticated user.
     */
    public function test_dashboard_loads_for_authenticated_user(): void
    {
        $user = TestHelpers::createUser(['email' => 'dashboard@test.com']);

        $this->browse(function (Browser $browser) use ($user) {
            TestHelpers::loginAs($browser, $user);
            
            $browser->visit('/dashboard')
                ->assertPathIs('/dashboard')
                ->assertSee('Dashboard');
        });
    }

    /**
     * Test dashboard shows subscription status.
     */
    public function test_dashboard_shows_subscription_status(): void
    {
        $user = TestHelpers::createUser(['email' => 'subscription@test.com']);
        $subscription = TestHelpers::createSubscription($user, [
            'plan_type' => 'monthly',
            'status' => 'active',
        ]);

        $this->browse(function (Browser $browser) use ($user) {
            TestHelpers::loginAs($browser, $user);
            
            $browser->visit('/dashboard')
                ->assertPathIs('/dashboard')
                ->assertSee('Subscription')
                ->assertSee('monthly');
        });
    }

    /**
     * Test dashboard shows active license info.
     */
    public function test_dashboard_shows_active_license_info(): void
    {
        $user = TestHelpers::createUser(['email' => 'license@test.com']);
        $subscription = TestHelpers::createSubscription($user);
        $license = TestHelpers::createLicense($user, $subscription);

        $this->browse(function (Browser $browser) use ($user) {
            TestHelpers::loginAs($browser, $user);
            
            $browser->visit('/dashboard')
                ->assertPathIs('/dashboard')
                ->assertSee('License');
        });
    }

    /**
     * Test dashboard shows device count.
     */
    public function test_dashboard_shows_device_count(): void
    {
        $user = TestHelpers::createUser(['email' => 'devices@test.com']);
        $subscription = TestHelpers::createSubscription($user);
        $license = TestHelpers::createLicense($user, $subscription);
        TestHelpers::createDevice($license);
        TestHelpers::createDevice($license);

        $this->browse(function (Browser $browser) use ($user) {
            TestHelpers::loginAs($browser, $user);
            
            $browser->visit('/dashboard')
                ->assertPathIs('/dashboard')
                ->assertSee('Devices');
        });
    }

    /**
     * Test dashboard shows total spent.
     */
    public function test_dashboard_shows_total_spent(): void
    {
        $user = TestHelpers::createUser(['email' => 'spent@test.com']);
        $subscription = TestHelpers::createSubscription($user);
        TestHelpers::createPayment($user, $subscription, ['amount' => 29.99]);
        TestHelpers::createPayment($user, $subscription, ['amount' => 19.99]);

        $this->browse(function (Browser $browser) use ($user) {
            TestHelpers::loginAs($browser, $user);
            
            $browser->visit('/dashboard')
                ->assertPathIs('/dashboard')
                ->assertSee('Total Spent');
        });
    }

    /**
     * Test dashboard redirects to login if not authenticated.
     */
    public function test_dashboard_redirects_to_login_if_not_authenticated(): void
    {
        $this->browse(function (Browser $browser) {
            $browser->visit('/dashboard')
                ->assertPathIs('/login');
        });
    }

    /**
     * Test navigation links work correctly.
     */
    public function test_navigation_links_work_correctly(): void
    {
        $user = TestHelpers::createUser(['email' => 'nav@test.com']);

        $this->browse(function (Browser $browser) use ($user) {
            TestHelpers::loginAs($browser, $user);
            
            $browser->visit('/dashboard')
                ->clickLink('Subscription')
                ->assertPathIs('/subscription')
                ->clickLink('Licenses')
                ->assertPathIs('/licenses')
                ->clickLink('Devices')
                ->assertPathIs('/devices')
                ->clickLink('Billing')
                ->assertPathIs('/billing')
                ->clickLink('Account')
                ->assertPathIs('/account');
        });
    }
}
