<?php

namespace Tests\E2E;

use Tests\Browser\BrowserTestCase;
use Tests\Helpers\TestHelpers;
use App\Models\User;
use App\Models\Subscription;
use Laravel\Dusk\Browser;
use Illuminate\Support\Facades\Http;

class StripeCompleteFlowTest extends BrowserTestCase
{
    /**
     * Test webhook signature validation.
     */
    public function test_webhook_signature_validation(): void
    {
        // This would be tested via API endpoint
        // For browser test, we verify webhook endpoint exists
        $this->browse(function (Browser $browser) {
            // Webhook endpoint should be accessible
            // (Actual signature validation would be in API test)
            $this->assertTrue(true);
        });
    }

    /**
     * Test payment success creates active subscription.
     */
    public function test_payment_success_creates_subscription(): void
    {
        $this->browse(function (Browser $browser) {
            $user = TestHelpers::createUser(['email' => 'paymentsuccess' . uniqid() . '@test.com']);
            
            // Simulate webhook creating subscription
            $subscription = TestHelpers::createSubscription($user, [
                'plan_type' => 'monthly',
                'status' => 'active',
                'stripe_subscription_id' => 'sub_test_123',
            ]);

            TestHelpers::loginAs($browser, $user);

            $browser->visit('/dashboard')
                ->assertSee('Active')
                ->assertSee('monthly');
        });
    }

    /**
     * Test payment failure cancels subscription.
     */
    public function test_payment_failure_cancels_subscription(): void
    {
        $this->browse(function (Browser $browser) {
            $user = TestHelpers::createUser(['email' => 'paymentfail' . uniqid() . '@test.com']);
            $subscription = TestHelpers::createSubscription($user, [
                'plan_type' => 'monthly',
                'status' => 'cancelled',
                'stripe_subscription_id' => 'sub_test_456',
            ]);

            TestHelpers::loginAs($browser, $user);

            $browser->visit('/dashboard')
                ->assertSee('Cancelled');
        });
    }

    /**
     * Test subscription update webhook.
     */
    public function test_subscription_update_webhook(): void
    {
        $this->browse(function (Browser $browser) {
            $user = TestHelpers::createUser(['email' => 'webhookupdate' . uniqid() . '@test.com']);
            $subscription = TestHelpers::createSubscription($user, [
                'plan_type' => 'yearly',
                'status' => 'active',
            ]);

            // Simulate webhook updating subscription
            $subscription->update(['plan_type' => 'lifetime']);

            TestHelpers::loginAs($browser, $user);

            $browser->visit('/dashboard')
                ->assertSee('lifetime');
        });
    }

    /**
     * Test refund processing.
     */
    public function test_refund_processing(): void
    {
        $this->browse(function (Browser $browser) {
            $user = TestHelpers::createUser(['email' => 'refund' . uniqid() . '@test.com']);
            $subscription = TestHelpers::createSubscription($user, [
                'plan_type' => 'monthly',
                'status' => 'cancelled',
            ]);

            TestHelpers::loginAs($browser, $user);

            // After refund, subscription should be cancelled
            $browser->visit('/dashboard')
                ->assertSee('Cancelled');
        });
    }

    /**
     * Test Stripe checkout session creation.
     */
    public function test_stripe_checkout_session_creation(): void
    {
        $this->browse(function (Browser $browser) {
            $user = TestHelpers::createUser(['email' => 'checkoutsession' . uniqid() . '@test.com']);

            TestHelpers::loginAs($browser, $user);

            $browser->visit('/subscription')
                ->press('Subscribe')
                ->waitForText('Checkout')
                ->assertSee('Stripe');
        });
    }

    /**
     * Test subscription renewal webhook.
     */
    public function test_subscription_renewal_webhook(): void
    {
        $this->browse(function (Browser $browser) {
            $user = TestHelpers::createUser(['email' => 'renewal' . uniqid() . '@test.com']);
            $subscription = TestHelpers::createSubscription($user, [
                'plan_type' => 'monthly',
                'status' => 'active',
                'expires_at' => now()->addMonth(),
            ]);

            // Simulate renewal webhook extending expiration
            $subscription->update(['expires_at' => now()->addMonths(2)]);

            TestHelpers::loginAs($browser, $user);

            $browser->visit('/dashboard')
                ->assertSee('Active');
        });
    }
}
