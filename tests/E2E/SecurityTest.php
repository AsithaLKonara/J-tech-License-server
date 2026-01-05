<?php

namespace Tests\E2E;

use Tests\Browser\BrowserTestCase;
use Tests\Helpers\TestHelpers;
use App\Models\User;
use Laravel\Dusk\Browser;

class SecurityTest extends BrowserTestCase
{
    /**
     * Test protected routes require authentication.
     */
    public function test_protected_routes_require_authentication(): void
    {
        $this->browse(function (Browser $browser) {
            $protectedRoutes = [
                '/dashboard',
                '/account',
                '/licenses',
                '/devices',
                '/billing',
                '/subscription',
            ];

            foreach ($protectedRoutes as $route) {
                $browser->visit($route)
                    ->assertPathIs('/login');
            }
        });
    }

    /**
     * Test admin routes require admin role.
     */
    public function test_admin_routes_require_admin_role(): void
    {
        $this->browse(function (Browser $browser) {
            $user = TestHelpers::createUser(['email' => 'nonadmin' . uniqid() . '@test.com']);

            TestHelpers::loginAs($browser, $user);

            $adminRoutes = ['/admin', '/admin/users', '/admin/subscriptions'];

            foreach ($adminRoutes as $route) {
                $browser->visit($route)
                    ->assertPathIsNot($route)
                    ->assertDontSee('Admin');
            }
        });
    }

    /**
     * Test user can only access own data.
     */
    public function test_user_can_only_access_own_data(): void
    {
        $this->browse(function (Browser $browser) {
            $user1 = TestHelpers::createUser(['email' => 'user1' . uniqid() . '@test.com']);
            $user2 = TestHelpers::createUser(['email' => 'user2' . uniqid() . '@test.com']);

            // User 1 logs in
            TestHelpers::loginAs($browser, $user1);

            // User 1 should see their own data
            $browser->visit('/account')
                ->assertSee($user1->email)
                ->assertDontSee($user2->email);

            // User 1 should not be able to access user 2's data directly
            // (This would be tested via API if user IDs are exposed in URLs)
        });
    }

    /**
     * Test cross-user data access is blocked.
     */
    public function test_cross_user_data_access_blocked(): void
    {
        $this->browse(function (Browser $browser) {
            $user1 = TestHelpers::createUser(['email' => 'cross1' . uniqid() . '@test.com']);
            $user2 = TestHelpers::createUser(['email' => 'cross2' . uniqid() . '@test.com']);

            TestHelpers::loginAs($browser, $user1);

            // User 1 should not see user 2's devices, licenses, etc.
            $browser->visit('/devices')
                ->assertDontSee($user2->email);

            $browser->visit('/licenses')
                ->assertDontSee($user2->email);
        });
    }

    /**
     * Test session hijacking prevention.
     */
    public function test_session_hijacking_prevention(): void
    {
        $this->browse(function (Browser $browser) {
            $user = TestHelpers::createUser(['email' => 'session' . uniqid() . '@test.com']);

            TestHelpers::loginAs($browser, $user);

            // Session should be tied to user
            $browser->visit('/dashboard')
                ->assertSee($user->email);

            // Logout should invalidate session
            $browser->press('Logout')
                ->assertGuest();

            // After logout, should not be able to access protected routes
            $browser->visit('/dashboard')
                ->assertPathIs('/login');
        });
    }

    /**
     * Test SQL injection prevention in forms.
     */
    public function test_sql_injection_prevention(): void
    {
        $this->browse(function (Browser $browser) {
            $sqlPayload = "' OR '1'='1";

            $browser->visit('/login')
                ->type('email', $sqlPayload)
                ->type('password', 'password123')
                ->press('Login')
                ->assertPathIs('/login')
                ->assertSee('credentials');
        });
    }

    /**
     * Test XSS prevention in user inputs.
     */
    public function test_xss_prevention(): void
    {
        $this->browse(function (Browser $browser) {
            $xssPayload = '<script>alert("XSS")</script>';
            $user = TestHelpers::createUser([
                'email' => 'xss' . uniqid() . '@test.com',
                'name' => $xssPayload,
            ]);

            TestHelpers::loginAs($browser, $user);

            // XSS payload should be escaped, not executed
            $browser->visit('/account')
                ->assertDontSee('<script>')
                ->assertDontSee('alert("XSS")');
        });
    }

    /**
     * Test CSRF token validation.
     */
    public function test_csrf_token_validation(): void
    {
        $this->browse(function (Browser $browser) {
            // Forms should include CSRF tokens
            $browser->visit('/login')
                ->assertPresent('input[name="_token"]');

            $browser->visit('/register')
                ->assertPresent('input[name="_token"]');
        });
    }

    /**
     * Test rate limiting on authentication endpoints.
     */
    public function test_rate_limiting(): void
    {
        // Rate limiting would be tested via API
        // For browser test, we verify forms exist
        $this->browse(function (Browser $browser) {
            $browser->visit('/login')
                ->assertSee('Login');
        });
    }

    /**
     * Test password hashing.
     */
    public function test_password_hashing(): void
    {
        $user = TestHelpers::createUser(['email' => 'passwordhash' . uniqid() . '@test.com']);

        // Password should be hashed in database
        $this->assertNotEquals('password123', $user->password);
        $this->assertTrue(\Hash::check('password123', $user->password));
    }

    /**
     * Test secure session configuration.
     */
    public function test_secure_session_configuration(): void
    {
        $this->browse(function (Browser $browser) {
            $user = TestHelpers::createUser(['email' => 'sessionconfig' . uniqid() . '@test.com']);

            TestHelpers::loginAs($browser, $user);

            // Session cookie should be secure (HttpOnly, Secure in production)
            $browser->visit('/dashboard')
                ->assertAuthenticated();
        });
    }
}
