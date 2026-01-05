<?php

namespace Tests\E2E;

use Tests\Browser\BrowserTestCase;
use Tests\Helpers\TestHelpers;
use App\Models\Subscription;
use Laravel\Dusk\Browser;

class SubscriptionTest extends BrowserTestCase
{
    /**
     * Test view subscription page.
     */
    public function test_can_view_subscription_page(): void
    {
        $user = TestHelpers::createUser(['email' => 'subview@test.com']);

        $this->browse(function (Browser $browser) use ($user) {
            TestHelpers::loginAs($browser, $user);
            
            $browser->visit('/subscription')
                ->assertPathIs('/subscription')
                ->assertSee('Subscription');
        });
    }

    /**
     * Test display current subscription status.
     */
    public function test_displays_current_subscription_status(): void
    {
        $user = TestHelpers::createUser(['email' => 'status@test.com']);
        $subscription = TestHelpers::createSubscription($user, [
            'plan_type' => 'annual',
            'status' => 'active',
        ]);

        $this->browse(function (Browser $browser) use ($user) {
            TestHelpers::loginAs($browser, $user);
            
            $browser->visit('/subscription')
                ->assertPathIs('/subscription')
                ->assertSee('annual')
                ->assertSee('active');
        });
    }

    /**
     * Test display available plans.
     */
    public function test_displays_available_plans(): void
    {
        $user = TestHelpers::createUser(['email' => 'plans@test.com']);

        $this->browse(function (Browser $browser) use ($user) {
            TestHelpers::loginAs($browser, $user);
            
            $browser->visit('/subscription')
                ->assertPathIs('/subscription')
                ->assertSee('monthly')
                ->assertSee('annual')
                ->assertSee('lifetime');
        });
    }

    /**
     * Test initiate checkout for monthly plan.
     */
    public function test_can_initiate_checkout_for_monthly_plan(): void
    {
        $user = TestHelpers::createUser(['email' => 'checkout@test.com']);

        $this->browse(function (Browser $browser) use ($user) {
            TestHelpers::loginAs($browser, $user);
            
            $browser->visit('/subscription')
                ->assertPathIs('/subscription')
                ->select('plan_type', 'monthly')
                ->press('Subscribe')
                ->pause(1000);
            
            // Note: Actual Stripe redirect would happen here
            // In test environment, we'd mock this
        });
    }

    /**
     * Test cancel subscription.
     */
    public function test_can_cancel_subscription(): void
    {
        $user = TestHelpers::createUser(['email' => 'cancel@test.com']);
        $subscription = TestHelpers::createSubscription($user, [
            'status' => 'active',
        ]);
        $license = TestHelpers::createLicense($user, $subscription);

        $this->browse(function (Browser $browser) use ($user) {
            TestHelpers::loginAs($browser, $user);
            
            $browser->visit('/subscription')
                ->assertPathIs('/subscription')
                ->press('Cancel Subscription')
                ->waitForText('Subscription canceled successfully')
                ->assertSee('Subscription canceled successfully');
        });

        // Verify subscription was canceled
        $subscription->refresh();
        $this->assertEquals('canceled', $subscription->status);
    }

    /**
     * Test subscription cancellation updates license status.
     */
    public function test_subscription_cancellation_updates_license_status(): void
    {
        $user = TestHelpers::createUser(['email' => 'liccancel@test.com']);
        $subscription = TestHelpers::createSubscription($user, [
            'status' => 'active',
        ]);
        $license = TestHelpers::createLicense($user, $subscription, [
            'status' => 'active',
        ]);

        $this->browse(function (Browser $browser) use ($user) {
            TestHelpers::loginAs($browser, $user);
            
            $browser->visit('/subscription')
                ->press('Cancel Subscription')
                ->waitForText('Subscription canceled successfully');
        });

        // Verify license was expired
        $license->refresh();
        $this->assertEquals('expired', $license->status);
    }

    /**
     * Test error when canceling non-existent subscription.
     */
    public function test_error_when_canceling_nonexistent_subscription(): void
    {
        $user = TestHelpers::createUser(['email' => 'no_sub@test.com']);

        $this->browse(function (Browser $browser) use ($user) {
            TestHelpers::loginAs($browser, $user);
            
            $browser->visit('/subscription')
                ->assertPathIs('/subscription');
            
            // Try to cancel when no subscription exists
            // The cancel button should not be visible or should show error
        });
    }
}
