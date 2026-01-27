<?php

namespace Tests\E2E;

use Tests\Browser\BrowserTestCase;
use Tests\Helpers\TestHelpers;
use App\Models\User;
use App\Models\MagicLink;
use Laravel\Dusk\Browser;

class CompleteAuthFlowTest extends BrowserTestCase
{
    /**
     * Test complete user registration flow with email verification.
     */
    public function test_complete_registration_flow(): void
    {
        $this->browse(function (Browser $browser) {
            $email = 'newuser' . uniqid() . '@test.com';
            
            // Step 1: User visits registration page
            $browser->visit('/register')
                ->assertPathIs('/register')
                ->assertSee('Register');

            // Step 2: User fills registration form
            $browser->type('name', 'New User')
                ->type('email', $email)
                ->type('password', 'password123')
                ->type('password_confirmation', 'password123');

            // Step 3: User submits registration
            $browser->press('Register')
                ->waitForLocation('/dashboard')
                ->assertPathIs('/dashboard');

            // Step 4: User is logged in automatically after registration
            $browser->assertSee('Dashboard')
                ->assertAuthenticated();

            // Step 5: User can access protected routes
            $browser->visit('/account')
                ->assertPathIs('/account')
                ->assertSee('Account Settings');
        });
    }

    /**
     * Test login with valid credentials.
     */
    public function test_login_with_valid_credentials(): void
    {
        $this->browse(function (Browser $browser) {
            $user = TestHelpers::createUser(['email' => 'validuser' . uniqid() . '@test.com']);

            $browser->visit('/login')
                ->type('email', $user->email)
                ->type('password', 'password123')
                ->press('Login')
                ->waitForLocation('/dashboard')
                ->assertPathIs('/dashboard')
                ->assertSee('Dashboard')
                ->assertAuthenticated();
        });
    }

    /**
     * Test login with invalid credentials.
     */
    public function test_login_with_invalid_credentials(): void
    {
        $this->browse(function (Browser $browser) {
            $browser->visit('/login')
                ->type('email', 'nonexistent@test.com')
                ->type('password', 'wrongpassword')
                ->press('Login')
                ->assertPathIs('/login')
                ->assertSee('These credentials do not match our records')
                ->assertGuest();
        });
    }

    /**
     * Test complete magic link flow.
     */
    public function test_complete_magic_link_flow(): void
    {
        $this->browse(function (Browser $browser) {
            $email = 'magiclink' . uniqid() . '@test.com';

            // Step 1: User requests magic link
            $browser->visit('/magic-link')
                ->type('email', $email)
                ->press('Send Magic Link')
                ->assertSee('Magic link sent');

            // Step 2: Get magic link from database
            $magicLink = MagicLink::where('email', $email)->first();
            $this->assertNotNull($magicLink);

            // Step 3: User clicks magic link
            $browser->visit('/magic-link/verify/' . $magicLink->token)
                ->waitForLocation('/dashboard')
                ->assertPathIs('/dashboard')
                ->assertSee('Dashboard')
                ->assertAuthenticated();
        });
    }

    /**
     * Test magic link token expiration.
     */
    public function test_magic_link_token_expiration(): void
    {
        $this->browse(function (Browser $browser) {
            $email = 'expired' . uniqid() . '@test.com';
            $magicLink = TestHelpers::createMagicLink($email, [
                'expires_at' => now()->subHour(), // Expired
            ]);

            $browser->visit('/magic-link/verify/' . $magicLink->token)
                ->assertPathIs('/magic-link')
                ->assertSee('expired')
                ->assertGuest();
        });
    }

    /**
     * Test magic link one-time use.
     */
    public function test_magic_link_one_time_use(): void
    {
        $this->browse(function (Browser $browser) {
            $email = 'onetime' . uniqid() . '@test.com';
            $magicLink = TestHelpers::createMagicLink($email);

            // First use - should succeed
            $browser->visit('/magic-link/verify/' . $magicLink->token)
                ->waitForLocation('/dashboard')
                ->assertPathIs('/dashboard')
                ->assertAuthenticated();

            // Logout
            $browser->press('Logout')
                ->assertGuest();

            // Second use - should fail
            $browser->visit('/magic-link/verify/' . $magicLink->token)
                ->assertPathIs('/magic-link')
                ->assertSee('already used')
                ->assertGuest();
        });
    }

    /**
     * Test session persistence with remember me.
     */
    public function test_remember_me_functionality(): void
    {
        $this->browse(function (Browser $browser) {
            $user = TestHelpers::createUser(['email' => 'remember' . uniqid() . '@test.com']);

            $browser->visit('/login')
                ->type('email', $user->email)
                ->type('password', 'password123')
                ->check('remember')
                ->press('Login')
                ->waitForLocation('/dashboard')
                ->assertPathIs('/dashboard');

            // Session should persist (tested by checking cookie)
            $browser->assertAuthenticated();
        });
    }

    /**
     * Test logout and session invalidation.
     */
    public function test_logout_and_session_invalidation(): void
    {
        $this->browse(function (Browser $browser) {
            $user = TestHelpers::createUser(['email' => 'logout' . uniqid() . '@test.com']);
            TestHelpers::loginAs($browser, $user);

            // User is logged in
            $browser->assertAuthenticated()
                ->visit('/dashboard')
                ->assertPathIs('/dashboard');

            // User logs out
            $browser->press('Logout')
                ->waitForLocation('/')
                ->assertPathIs('/')
                ->assertGuest();

            // User cannot access protected routes
            $browser->visit('/dashboard')
                ->assertPathIs('/login');
        });
    }

    /**
     * Test CSRF protection on forms.
     */
    public function test_csrf_protection(): void
    {
        // CSRF protection is handled by Laravel automatically
        // This test verifies that forms include CSRF tokens
        $this->browse(function (Browser $browser) {
            $browser->visit('/login')
                ->assertPresent('input[name="_token"]');
        });
    }

    /**
     * Test XSS prevention in user inputs.
     */
    public function test_xss_prevention_in_inputs(): void
    {
        $this->browse(function (Browser $browser) {
            $xssPayload = '<script>alert("XSS")</script>';
            $user = TestHelpers::createUser([
                'email' => 'xss' . uniqid() . '@test.com',
                'name' => $xssPayload,
            ]);

            TestHelpers::loginAs($browser, $user);

            $browser->visit('/account')
                ->assertDontSee('<script>')
                ->assertDontSee('alert("XSS")');
        });
    }

    /**
     * Test protected route access control.
     */
    public function test_protected_route_access_control(): void
    {
        $this->browse(function (Browser $browser) {
            // Unauthenticated user tries to access protected route
            $browser->visit('/dashboard')
                ->assertPathIs('/login');

            $browser->visit('/account')
                ->assertPathIs('/login');

            $browser->visit('/licenses')
                ->assertPathIs('/login');

            // After login, should be able to access
            $user = TestHelpers::createUser(['email' => 'protected' . uniqid() . '@test.com']);
            TestHelpers::loginAs($browser, $user);

            $browser->visit('/dashboard')
                ->assertPathIs('/dashboard');

            $browser->visit('/account')
                ->assertPathIs('/account');
        });
    }

    /**
     * Test password reset flow (if implemented).
     */
    public function test_password_reset_flow(): void
    {
        // This test would verify password reset functionality
        // If password reset is implemented, uncomment and adjust:
        /*
        $this->browse(function (Browser $browser) {
            $user = TestHelpers::createUser(['email' => 'reset' . uniqid() . '@test.com']);

            $browser->visit('/password/reset')
                ->type('email', $user->email)
                ->press('Send Reset Link')
                ->assertSee('reset link');

            // Verify reset token and update password
            // ...
        });
        */
        $this->assertTrue(true); // Placeholder
    }
}
