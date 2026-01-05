<?php

namespace Tests\E2E;

use Tests\Browser\BrowserTestCase;
use Tests\Helpers\TestHelpers;
use Laravel\Dusk\Browser;

class AdminTest extends BrowserTestCase
{
    /**
     * Test admin can access admin dashboard.
     */
    public function test_admin_can_access_admin_dashboard(): void
    {
        $admin = TestHelpers::createAdmin(['email' => 'admin@test.com']);

        $this->browse(function (Browser $browser) use ($admin) {
            TestHelpers::loginAs($browser, $admin);
            
            $browser->visit('/admin')
                ->assertPathIs('/admin')
                ->assertSee('Admin');
        });
    }

    /**
     * Test non-admin cannot access admin routes.
     */
    public function test_non_admin_cannot_access_admin_routes(): void
    {
        $user = TestHelpers::createUser(['email' => 'user@test.com']);

        $this->browse(function (Browser $browser) use ($user) {
            TestHelpers::loginAs($browser, $user);
            
            $browser->visit('/admin')
                ->assertSee('403'); // Should get 403 Forbidden
        });
    }

    /**
     * Test view users list with pagination.
     */
    public function test_can_view_users_list_with_pagination(): void
    {
        $admin = TestHelpers::createAdmin(['email' => 'adminlist@test.com']);
        
        // Create multiple users
        for ($i = 0; $i < 5; $i++) {
            TestHelpers::createUser(['email' => "user{$i}@test.com"]);
        }

        $this->browse(function (Browser $browser) use ($admin) {
            TestHelpers::loginAs($browser, $admin);
            
            $browser->visit('/admin/users')
                ->assertPathIs('/admin/users')
                ->assertSee('Users');
        });
    }

    /**
     * Test view user details.
     */
    public function test_can_view_user_details(): void
    {
        $admin = TestHelpers::createAdmin(['email' => 'admindetail@test.com']);
        $user = TestHelpers::createUser(['email' => 'detailuser@test.com']);
        $subscription = TestHelpers::createSubscription($user);
        $license = TestHelpers::createLicense($user, $subscription);

        $this->browse(function (Browser $browser) use ($admin, $user) {
            TestHelpers::loginAs($browser, $admin);
            
            $browser->visit("/admin/users/{$user->id}")
                ->assertPathIs("/admin/users/{$user->id}")
                ->assertSee($user->email)
                ->assertSee($user->name);
        });
    }

    /**
     * Test view subscriptions list.
     */
    public function test_can_view_subscriptions_list(): void
    {
        $admin = TestHelpers::createAdmin(['email' => 'adminsub@test.com']);
        $user = TestHelpers::createUser(['email' => 'subuser@test.com']);
        $subscription = TestHelpers::createSubscription($user);

        $this->browse(function (Browser $browser) use ($admin) {
            TestHelpers::loginAs($browser, $admin);
            
            $browser->visit('/admin/subscriptions')
                ->assertPathIs('/admin/subscriptions')
                ->assertSee('Subscriptions');
        });
    }

    /**
     * Test create manual subscription.
     */
    public function test_can_create_manual_subscription(): void
    {
        $admin = TestHelpers::createAdmin(['email' => 'adminmanual@test.com']);
        $user = TestHelpers::createUser(['email' => 'manualuser@test.com']);

        $this->browse(function (Browser $browser) use ($admin, $user) {
            TestHelpers::loginAs($browser, $admin);
            
            $browser->visit("/admin/users/{$user->id}")
                ->assertPathIs("/admin/users/{$user->id}")
                ->select('plan_type', 'lifetime')
                ->press('Create Manual Subscription')
                ->waitForText('Manual subscription created successfully')
                ->assertSee('Manual subscription created successfully');
        });
    }

    /**
     * Test admin middleware blocks non-admins.
     */
    public function test_admin_middleware_blocks_non_admins(): void
    {
        $user = TestHelpers::createUser(['email' => 'blocked@test.com']);

        $this->browse(function (Browser $browser) use ($user) {
            TestHelpers::loginAs($browser, $user);
            
            $browser->visit('/admin/users')
                ->assertSee('403');
            
            $browser->visit('/admin/subscriptions')
                ->assertSee('403');
        });
    }
}
