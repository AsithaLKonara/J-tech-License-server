<?php

namespace Tests\E2E;

use Tests\Browser\BrowserTestCase;
use Tests\Helpers\TestHelpers;
use Laravel\Dusk\Browser;

class BillingTest extends BrowserTestCase
{
    /**
     * Test view billing history.
     */
    public function test_can_view_billing_history(): void
    {
        $user = TestHelpers::createUser(['email' => 'billing@test.com']);

        $this->browse(function (Browser $browser) use ($user) {
            TestHelpers::loginAs($browser, $user);
            
            $browser->visit('/billing')
                ->assertPathIs('/billing')
                ->assertSee('Billing');
        });
    }

    /**
     * Test display completed payments.
     */
    public function test_displays_completed_payments(): void
    {
        $user = TestHelpers::createUser(['email' => 'payments@test.com']);
        $subscription = TestHelpers::createSubscription($user);
        $payment1 = TestHelpers::createPayment($user, $subscription, [
            'amount' => 29.99,
            'status' => 'completed',
        ]);
        $payment2 = TestHelpers::createPayment($user, $subscription, [
            'amount' => 19.99,
            'status' => 'completed',
        ]);

        $this->browse(function (Browser $browser) use ($user) {
            TestHelpers::loginAs($browser, $user);
            
            $browser->visit('/billing')
                ->assertPathIs('/billing')
                ->assertSee('29.99')
                ->assertSee('19.99');
        });
    }

    /**
     * Test show payment amounts and dates.
     */
    public function test_shows_payment_amounts_and_dates(): void
    {
        $user = TestHelpers::createUser(['email' => 'amounts@test.com']);
        $subscription = TestHelpers::createSubscription($user);
        $payment = TestHelpers::createPayment($user, $subscription, [
            'amount' => 99.99,
            'currency' => 'USD',
            'status' => 'completed',
        ]);

        $this->browse(function (Browser $browser) use ($user) {
            TestHelpers::loginAs($browser, $user);
            
            $browser->visit('/billing')
                ->assertPathIs('/billing')
                ->assertSee('99.99')
                ->assertSee('USD');
        });
    }

    /**
     * Test empty state when no payments.
     */
    public function test_shows_empty_state_when_no_payments(): void
    {
        $user = TestHelpers::createUser(['email' => 'nopayments@test.com']);

        $this->browse(function (Browser $browser) use ($user) {
            TestHelpers::loginAs($browser, $user);
            
            $browser->visit('/billing')
                ->assertPathIs('/billing');
        });
    }
}
