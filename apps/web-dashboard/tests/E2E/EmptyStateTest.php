<?php

namespace Tests\E2E;

use Tests\Browser\BrowserTestCase;
use Tests\Helpers\TestHelpers;
use Laravel\Dusk\Browser;

class EmptyStateTest extends BrowserTestCase
{
    /**
     * Test empty devices list displays correctly.
     */
    public function test_empty_devices_list(): void
    {
        $user = TestHelpers::createUser(['email' => 'emptydevices@test.com']);
        
        $this->browse(function (Browser $browser) use ($user) {
            TestHelpers::loginAs($browser, $user);
            
            $browser->visit('/devices')
                ->assertPathIs('/devices')
                ->assertSee('No devices')
                ->assertSee('Register');
        });
    }
    
    /**
     * Test empty licenses list displays correctly.
     */
    public function test_empty_licenses_list(): void
    {
        $user = TestHelpers::createUser(['email' => 'emptylicenses@test.com']);
        
        $this->browse(function (Browser $browser) use ($user) {
            TestHelpers::loginAs($browser, $user);
            
            $browser->visit('/licenses')
                ->assertPathIs('/licenses')
                ->assertSee('No licenses')
                ->assertSee('Subscribe');
        });
    }
    
    /**
     * Test empty payment history displays correctly.
     */
    public function test_empty_payment_history(): void
    {
        $user = TestHelpers::createUser(['email' => 'emptypayments@test.com']);
        
        $this->browse(function (Browser $browser) use ($user) {
            TestHelpers::loginAs($browser, $user);
            
            $browser->visit('/billing')
                ->assertPathIs('/billing')
                ->assertSee('No payments')
                ->assertSee('history');
        });
    }
    
    /**
     * Test empty subscription state.
     */
    public function test_empty_subscription_state(): void
    {
        $user = TestHelpers::createUser(['email' => 'emptysub@test.com']);
        
        $this->browse(function (Browser $browser) use ($user) {
            TestHelpers::loginAs($browser, $user);
            
            $browser->visit('/subscription')
                ->assertPathIs('/subscription')
                ->assertSee('No subscription')
                ->assertSee('Subscribe');
        });
    }
    
    /**
     * Test dashboard empty state for new user.
     */
    public function test_dashboard_empty_state_new_user(): void
    {
        $user = TestHelpers::createUser(['email' => 'newuser@test.com']);
        
        $this->browse(function (Browser $browser) use ($user) {
            TestHelpers::loginAs($browser, $user);
            
            $browser->visit('/dashboard')
                ->assertPathIs('/dashboard')
                ->assertSee('Dashboard');
            // Should show empty state or welcome message
        });
    }
}
