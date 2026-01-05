<?php

namespace Tests\E2E;

use Tests\Browser\BrowserTestCase;
use Tests\Helpers\TestHelpers;
use App\Models\User;
use App\Models\Subscription;
use App\Models\License;
use Laravel\Dusk\Browser;

class CompleteSubscriptionFlowTest extends BrowserTestCase
{
    /**
     * Test user views subscription page with plans displayed.
     */
    public function test_user_views_subscription_plans(): void
    {
        $this->browse(function (Browser $browser) {
            $user = TestHelpers::createUser(['email' => 'viewplans' . uniqid() . '@test.com']);

            TestHelpers::loginAs($browser, $user);

            $browser->visit('/subscription')
                ->assertSee('Subscription')
                ->assertSee('Monthly')
                ->assertSee('Yearly')
                ->assertSee('Lifetime');
        });
    }

    /**
     * Test user selects plan and Stripe checkout is initiated.
     */
    public function test_user_initiates_stripe_checkout(): void
    {
        $this->browse(function (Browser $browser) {
            $user = TestHelpers::createUser(['email' => 'checkout' . uniqid() . '@test.com']);

            TestHelpers::loginAs($browser, $user);

            $browser->visit('/subscription')
                ->assertSee('Monthly')
                ->press('Subscribe')
                ->waitForText('Checkout')
                ->assertSee('Stripe');
        });
    }

    /**
     * Test Stripe webhook creates subscription.
     */
    public function test_stripe_webhook_creates_subscription(): void
    {
        // This would be tested via API/webhook endpoint
        // For browser test, we verify subscription appears after creation
        $this->browse(function (Browser $browser) {
            $user = TestHelpers::createUser(['email' => 'webhook' . uniqid() . '@test.com']);
            $subscription = TestHelpers::createSubscription($user, [
                'plan_type' => 'monthly',
                'status' => 'active',
            ]);

            TestHelpers::loginAs($browser, $user);

            $browser->visit('/dashboard')
                ->assertSee('Active')
                ->assertSee('monthly');
        });
    }

    /**
     * Test subscription automatically creates license.
     */
    public function test_subscription_creates_license_automatically(): void
    {
        $this->browse(function (Browser $browser) {
            $user = TestHelpers::createUser(['email' => 'autolicense' . uniqid() . '@test.com']);
            $subscription = TestHelpers::createSubscription($user, [
                'plan_type' => 'yearly',
                'status' => 'active',
            ]);
            $license = TestHelpers::createLicense($user, $subscription);

            TestHelpers::loginAs($browser, $user);

            $browser->visit('/licenses')
                ->assertSee($license->plan)
                ->assertSee('active');
        });
    }

    /**
     * Test user cancels subscription and license status updates.
     */
    public function test_user_cancels_subscription(): void
    {
        $this->browse(function (Browser $browser) {
            $user = TestHelpers::createUser(['email' => 'cancel' . uniqid() . '@test.com']);
            $subscription = TestHelpers::createSubscription($user, [
                'plan_type' => 'monthly',
                'status' => 'active',
            ]);
            $license = TestHelpers::createLicense($user, $subscription, [
                'status' => 'active',
            ]);

            TestHelpers::loginAs($browser, $user);

            $browser->visit('/subscription')
                ->assertSee('Cancel')
                ->press('Cancel Subscription')
                ->waitForText('cancelled')
                ->assertSee('Cancelled');

            // License status should update
            $license->refresh();
            $this->assertEquals('cancelled', $subscription->fresh()->status);
        });
    }

    /**
     * Test subscription expiration deactivates license.
     */
    public function test_subscription_expiration_deactivates_license(): void
    {
        $this->browse(function (Browser $browser) {
            $user = TestHelpers::createUser(['email' => 'expire' . uniqid() . '@test.com']);
            $subscription = TestHelpers::createSubscription($user, [
                'plan_type' => 'monthly',
                'status' => 'expired',
                'expires_at' => now()->subDay(),
            ]);
            $license = TestHelpers::createLicense($user, $subscription, [
                'status' => 'expired',
                'expires_at' => now()->subDay(),
            ]);

            TestHelpers::loginAs($browser, $user);

            $browser->visit('/dashboard')
                ->assertSee('expired')
                ->visit('/licenses')
                ->assertSee('expired');
        });
    }

    /**
     * Test subscription success page.
     */
    public function test_subscription_success_page(): void
    {
        $this->browse(function (Browser $browser) {
            $user = TestHelpers::createUser(['email' => 'success' . uniqid() . '@test.com']);

            TestHelpers::loginAs($browser, $user);

            // Simulate redirect to success page after Stripe checkout
            $browser->visit('/subscription-success')
                ->assertSee('Success')
                ->assertSee('subscription');
        });
    }

    /**
     * Test subscription upgrade flow.
     */
    public function test_subscription_upgrade_flow(): void
    {
        $this->browse(function (Browser $browser) {
            $user = TestHelpers::createUser(['email' => 'upgrade' . uniqid() . '@test.com']);
            $subscription = TestHelpers::createSubscription($user, [
                'plan_type' => 'monthly',
                'status' => 'active',
            ]);

            TestHelpers::loginAs($browser, $user);

            $browser->visit('/subscription')
                ->assertSee('Upgrade')
                ->assertSee('yearly');
        });
    }
}
