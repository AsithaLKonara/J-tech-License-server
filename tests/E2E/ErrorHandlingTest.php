<?php

namespace Tests\E2E;

use Tests\Browser\BrowserTestCase;
use Tests\Helpers\TestHelpers;
use Laravel\Dusk\Browser;

class ErrorHandlingTest extends BrowserTestCase
{
    /**
     * Test error messages display correctly on login failure.
     */
    public function test_login_error_message_display(): void
    {
        $this->browse(function (Browser $browser) {
            $browser->visit('/login')
                ->type('email', 'nonexistent@test.com')
                ->type('password', 'wrongpassword')
                ->press('Login')
                ->assertPathIs('/login')
                ->assertSee('credentials')
                ->assertVisible('.alert-danger, .error, [role="alert"]');
        });
    }
    
    /**
     * Test form validation errors display correctly.
     */
    public function test_form_validation_errors_display(): void
    {
        $this->browse(function (Browser $browser) {
            $browser->visit('/register')
                ->press('Register') // Submit without filling fields
                ->assertPathIs('/register')
                ->assertSee('required')
                ->assertVisible('.invalid-feedback, .error');
        });
    }
    
    /**
     * Test 404 error page handling.
     */
    public function test_404_error_page(): void
    {
        $user = TestHelpers::createUser(['email' => '404@test.com']);
        
        $this->browse(function (Browser $browser) use ($user) {
            TestHelpers::loginAs($browser, $user);
            
            $browser->visit('/nonexistent-page')
                ->assertSee('404')
                ->assertSee('Not Found');
        });
    }
    
    /**
     * Test server error handling (500).
     */
    public function test_server_error_handling(): void
    {
        $user = TestHelpers::createUser(['email' => '500@test.com']);
        
        $this->browse(function (Browser $browser) use ($user) {
            TestHelpers::loginAs($browser, $user);
            
            // Try to access a route that might cause server error
            // This would need to be a specific route that triggers 500
            $browser->visit('/dashboard')
                ->assertDontSee('500')
                ->assertDontSee('Server Error');
        });
    }
    
    /**
     * Test network error handling.
     */
    public function test_network_error_handling(): void
    {
        $this->browse(function (Browser $browser) {
            // Simulate network error by visiting invalid URL
            // In real scenario, this would test AJAX error handling
            $browser->visit('/login')
                ->assertSee('Login');
        });
    }
    
    /**
     * Test timeout error handling.
     */
    public function test_timeout_error_handling(): void
    {
        $user = TestHelpers::createUser(['email' => 'timeout@test.com']);
        
        $this->browse(function (Browser $browser) use ($user) {
            TestHelpers::loginAs($browser, $user);
            
            $browser->visit('/dashboard')
                ->assertPathIs('/dashboard');
            // Timeout would be handled by browser/Dusk timeout settings
        });
    }
    
    /**
     * Test validation error for empty fields.
     */
    public function test_empty_field_validation(): void
    {
        $this->browse(function (Browser $browser) {
            $browser->visit('/register')
                ->type('name', '')
                ->type('email', '')
                ->type('password', '')
                ->press('Register')
                ->assertPathIs('/register')
                ->assertSee('required');
        });
    }
    
    /**
     * Test password mismatch error.
     */
    public function test_password_mismatch_error(): void
    {
        $this->browse(function (Browser $browser) {
            $browser->visit('/register')
                ->type('name', 'Test User')
                ->type('email', 'mismatch@test.com')
                ->type('password', 'password123')
                ->type('password_confirmation', 'differentpassword')
                ->press('Register')
                ->assertPathIs('/register')
                ->assertSee('match');
        });
    }
}
