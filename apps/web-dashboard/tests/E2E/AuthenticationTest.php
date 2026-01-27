<?php

namespace Tests\E2E;

use Tests\Browser\BrowserTestCase;
use Tests\Helpers\TestHelpers;
use App\Models\User;
use Laravel\Dusk\Browser;

class AuthenticationTest extends BrowserTestCase
{
    /**
     * Test user registration with valid data.
     */
    public function test_user_can_register_with_valid_data(): void
    {
        $this->browse(function (Browser $browser) {
            $email = 'newuser' . uniqid() . '@test.com';
            
            $browser->visit('/register')
                ->type('name', 'New User')
                ->type('email', $email)
                ->type('password', 'password123')
                ->type('password_confirmation', 'password123')
                ->press('Register')
                ->waitForLocation('/dashboard')
                ->assertPathIs('/dashboard')
                ->assertSee('Dashboard');
        });
    }

    /**
     * Test registration with invalid email format.
     */
    public function test_registration_rejects_invalid_email(): void
    {
        $this->browse(function (Browser $browser) {
            $browser->visit('/register')
                ->type('name', 'Test User')
                ->type('email', 'invalid-email')
                ->type('password', 'password123')
                ->type('password_confirmation', 'password123')
                ->press('Register')
                ->assertPathIs('/register')
                ->assertSee('The email must be a valid email address');
        });
    }

    /**
     * Test registration with duplicate email.
     */
    public function test_registration_rejects_duplicate_email(): void
    {
        $user = TestHelpers::createUser(['email' => 'duplicate@test.com']);

        $this->browse(function (Browser $browser) use ($user) {
            $browser->visit('/register')
                ->type('name', 'Another User')
                ->type('email', $user->email)
                ->type('password', 'password123')
                ->type('password_confirmation', 'password123')
                ->press('Register')
                ->assertPathIs('/register')
                ->assertSee('The email has already been taken');
        });
    }

    /**
     * Test registration password validation.
     */
    public function test_registration_enforces_password_validation(): void
    {
        $this->browse(function (Browser $browser) {
            $browser->visit('/register')
                ->type('name', 'Test User')
                ->type('email', 'test@test.com')
                ->type('password', 'short')
                ->type('password_confirmation', 'short')
                ->press('Register')
                ->assertPathIs('/register');
        });
    }

    /**
     * Test user can login with valid credentials.
     */
    public function test_user_can_login_with_valid_credentials(): void
    {
        $user = TestHelpers::createUser(['email' => 'login@test.com']);

        $this->browse(function (Browser $browser) use ($user) {
            $browser->visit('/login')
                ->type('email', $user->email)
                ->type('password', 'password123')
                ->press('Login')
                ->waitForLocation('/dashboard')
                ->assertPathIs('/dashboard')
                ->assertSee('Dashboard');
        });
    }

    /**
     * Test login with invalid credentials shows error.
     */
    public function test_login_shows_error_for_invalid_credentials(): void
    {
        $this->browse(function (Browser $browser) {
            $browser->visit('/login')
                ->type('email', 'nonexistent@test.com')
                ->type('password', 'wrongpassword')
                ->press('Login')
                ->assertPathIs('/login')
                ->assertSee('The provided credentials do not match our records');
        });
    }

    /**
     * Test remember me functionality.
     */
    public function test_remember_me_functionality(): void
    {
        $user = TestHelpers::createUser(['email' => 'remember@test.com']);

        $this->browse(function (Browser $browser) use ($user) {
            $browser->visit('/login')
                ->type('email', $user->email)
                ->type('password', 'password123')
                ->check('remember')
                ->press('Login')
                ->waitForLocation('/dashboard')
                ->assertPathIs('/dashboard');
        });
    }

    /**
     * Test redirect to intended page after login.
     */
    public function test_redirect_to_intended_page_after_login(): void
    {
        $user = TestHelpers::createUser(['email' => 'redirect@test.com']);

        $this->browse(function (Browser $browser) use ($user) {
            $browser->visit('/dashboard')
                ->assertPathIs('/login')
                ->type('email', $user->email)
                ->type('password', 'password123')
                ->press('Login')
                ->waitForLocation('/dashboard')
                ->assertPathIs('/dashboard');
        });
    }

    /**
     * Test session persists across requests.
     */
    public function test_session_persists_across_requests(): void
    {
        $user = TestHelpers::createUser(['email' => 'session@test.com']);

        $this->browse(function (Browser $browser) use ($user) {
            TestHelpers::loginAs($browser, $user);
            
            $browser->visit('/dashboard')
                ->assertPathIs('/dashboard')
                ->visit('/licenses')
                ->assertPathIs('/licenses')
                ->visit('/devices')
                ->assertPathIs('/devices');
        });
    }

    /**
     * Test logout clears session.
     */
    public function test_logout_clears_session(): void
    {
        $user = TestHelpers::createUser(['email' => 'logout@test.com']);

        $this->browse(function (Browser $browser) use ($user) {
            TestHelpers::loginAs($browser, $user);
            
            $browser->visit('/dashboard')
                ->assertPathIs('/dashboard')
                ->press('Logout')
                ->waitForLocation('/')
                ->assertPathIs('/')
                ->visit('/dashboard')
                ->assertPathIs('/login');
        });
    }

    /**
     * Test cannot access protected routes after logout.
     */
    public function test_cannot_access_protected_routes_after_logout(): void
    {
        $user = TestHelpers::createUser(['email' => 'protected@test.com']);

        $this->browse(function (Browser $browser) use ($user) {
            TestHelpers::loginAs($browser, $user);
            
            $browser->visit('/dashboard')
                ->assertPathIs('/dashboard')
                ->press('Logout')
                ->waitForLocation('/')
                ->visit('/subscription')
                ->assertPathIs('/login')
                ->visit('/licenses')
                ->assertPathIs('/login')
                ->visit('/devices')
                ->assertPathIs('/login');
        });
    }
    
    /**
     * Test login form validation - empty email.
     */
    public function test_login_form_validation_empty_email(): void
    {
        $this->browse(function (Browser $browser) {
            $browser->visit('/login')
                ->type('password', 'password123')
                ->press('Login')
                ->assertPathIs('/login')
                ->assertSee('required');
        });
    }
    
    /**
     * Test login form validation - empty password.
     */
    public function test_login_form_validation_empty_password(): void
    {
        $this->browse(function (Browser $browser) {
            $browser->visit('/login')
                ->type('email', 'test@test.com')
                ->press('Login')
                ->assertPathIs('/login')
                ->assertSee('required');
        });
    }
    
    /**
     * Test login form validation - invalid email format.
     */
    public function test_login_form_validation_invalid_email_format(): void
    {
        $this->browse(function (Browser $browser) {
            $browser->visit('/login')
                ->type('email', 'not-an-email')
                ->type('password', 'password123')
                ->press('Login')
                ->assertPathIs('/login')
                ->assertSee('valid email');
        });
    }
    
    /**
     * Test loading state during login.
     */
    public function test_login_loading_state(): void
    {
        $user = TestHelpers::createUser(['email' => 'loading@test.com']);
        
        $this->browse(function (Browser $browser) use ($user) {
            $browser->visit('/login')
                ->type('email', $user->email)
                ->type('password', 'password123')
                ->press('Login')
                ->waitForLocation('/dashboard', 5)
                ->assertPathIs('/dashboard');
        });
    }
}
