<?php

namespace Tests\E2E;

use Tests\Browser\BrowserTestCase;
use Tests\Helpers\TestHelpers;
use App\Models\User;
use App\Models\Subscription;
use Laravel\Dusk\Browser;

class CompleteAdminFlowTest extends BrowserTestCase
{
    /**
     * Test admin middleware blocks non-admin users.
     */
    public function test_admin_middleware_blocks_non_admin(): void
    {
        $this->browse(function (Browser $browser) {
            $user = TestHelpers::createUser(['email' => 'nonadmin' . uniqid() . '@test.com']);

            TestHelpers::loginAs($browser, $user);

            // Non-admin should be redirected from admin routes
            $browser->visit('/admin')
                ->assertPathIs('/dashboard')
                ->assertDontSee('Admin');

            $browser->visit('/admin/users')
                ->assertPathIs('/dashboard');
        });
    }

    /**
     * Test admin can access admin dashboard.
     */
    public function test_admin_can_access_admin_dashboard(): void
    {
        $this->browse(function (Browser $browser) {
            $admin = TestHelpers::createAdmin(['email' => 'admindash' . uniqid() . '@test.com']);

            TestHelpers::loginAs($browser, $admin);

            $browser->visit('/admin')
                ->assertPathIs('/admin')
                ->assertSee('Admin Dashboard');
        });
    }

    /**
     * Test admin can view all users.
     */
    public function test_admin_can_view_all_users(): void
    {
        $this->browse(function (Browser $browser) {
            $admin = TestHelpers::createAdmin(['email' => 'adminusers' . uniqid() . '@test.com']);
            $user1 = TestHelpers::createUser(['email' => 'user1' . uniqid() . '@test.com']);
            $user2 = TestHelpers::createUser(['email' => 'user2' . uniqid() . '@test.com']);

            TestHelpers::loginAs($browser, $admin);

            $browser->visit('/admin/users')
                ->assertSee('Users')
                ->assertSee($user1->email)
                ->assertSee($user2->email);
        });
    }

    /**
     * Test admin can view user details.
     */
    public function test_admin_can_view_user_details(): void
    {
        $this->browse(function (Browser $browser) {
            $admin = TestHelpers::createAdmin(['email' => 'admindetails' . uniqid() . '@test.com']);
            $user = TestHelpers::createUser(['email' => 'detailuser' . uniqid() . '@test.com']);

            TestHelpers::loginAs($browser, $admin);

            $browser->visit('/admin/users/' . $user->id)
                ->assertSee($user->email)
                ->assertSee($user->name);
        });
    }

    /**
     * Test admin can view subscriptions list.
     */
    public function test_admin_can_view_subscriptions(): void
    {
        $this->browse(function (Browser $browser) {
            $admin = TestHelpers::createAdmin(['email' => 'adminsubs' . uniqid() . '@test.com']);
            $user = TestHelpers::createUser(['email' => 'subuser' . uniqid() . '@test.com']);
            $subscription = TestHelpers::createSubscription($user, [
                'plan_type' => 'monthly',
                'status' => 'active',
            ]);

            TestHelpers::loginAs($browser, $admin);

            $browser->visit('/admin/subscriptions')
                ->assertSee('Subscriptions')
                ->assertSee($user->email)
                ->assertSee('monthly');
        });
    }

    /**
     * Test admin can create manual subscription.
     */
    public function test_admin_can_create_manual_subscription(): void
    {
        $this->browse(function (Browser $browser) {
            $admin = TestHelpers::createAdmin(['email' => 'adminmanual' . uniqid() . '@test.com']);
            $user = TestHelpers::createUser(['email' => 'manualuser' . uniqid() . '@test.com']);

            TestHelpers::loginAs($browser, $admin);

            $browser->visit('/admin/subscriptions')
                ->press('Create Manual Subscription')
                ->type('user_id', $user->id)
                ->type('plan_type', 'yearly')
                ->press('Create')
                ->waitForText('created')
                ->assertSee('yearly');
        });
    }

    /**
     * Test admin can manage licenses.
     */
    public function test_admin_can_manage_licenses(): void
    {
        $this->browse(function (Browser $browser) {
            $admin = TestHelpers::createAdmin(['email' => 'adminlicense' . uniqid() . '@test.com']);
            $user = TestHelpers::createUser(['email' => 'licenseuser' . uniqid() . '@test.com']);
            $subscription = TestHelpers::createSubscription($user);
            $license = TestHelpers::createLicense($user, $subscription);

            TestHelpers::loginAs($browser, $admin);

            $browser->visit('/admin/users/' . $user->id)
                ->assertSee('Licenses')
                ->assertSee($license->plan);
        });
    }

    /**
     * Test admin access control on all admin routes.
     */
    public function test_admin_access_control_on_all_routes(): void
    {
        $this->browse(function (Browser $browser) {
            $user = TestHelpers::createUser(['email' => 'accesscontrol' . uniqid() . '@test.com']);

            TestHelpers::loginAs($browser, $user);

            // All admin routes should redirect
            $adminRoutes = ['/admin', '/admin/users', '/admin/subscriptions'];

            foreach ($adminRoutes as $route) {
                $browser->visit($route)
                    ->assertPathIsNot($route)
                    ->assertDontSee('Admin');
            }
        });
    }
}
