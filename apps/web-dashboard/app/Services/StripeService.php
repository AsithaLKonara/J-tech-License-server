<?php

namespace App\Services;

use Stripe\Stripe;
use Stripe\Checkout\Session;
use Stripe\Customer;
use Stripe\Subscription as StripeSubscription;
use Stripe\Webhook;
use App\Models\User;
use App\Models\Subscription;
use Illuminate\Support\Facades\Log;

class StripeService
{
    public function __construct()
    {
        Stripe::setApiKey(config('stripe.secret'));
    }

    public function createCheckoutSession(User $user, string $planType): Session
    {
        $prices = [
            'monthly' => env('STRIPE_PRICE_MONTHLY'),
            'annual' => env('STRIPE_PRICE_ANNUAL'),
            'lifetime' => env('STRIPE_PRICE_LIFETIME'),
        ];

        $priceId = $prices[$planType] ?? null;
        if (!$priceId) {
            throw new \Exception("Price ID not configured for plan: {$planType}");
        }

        $session = Session::create([
            'customer_email' => $user->email,
            'payment_method_types' => ['card'],
            'line_items' => [[
                'price' => $priceId,
                'quantity' => 1,
            ]],
            'mode' => $planType === 'lifetime' ? 'payment' : 'subscription',
            'success_url' => route('subscription.success') . '?session_id={CHECKOUT_SESSION_ID}',
            'cancel_url' => route('subscription'),
            'metadata' => [
                'user_id' => $user->id,
                'plan_type' => $planType,
            ],
        ]);

        return $session;
    }

    public function handleWebhook(string $payload, string $signature): void
    {
        try {
            $event = Webhook::constructEvent(
                $payload,
                $signature,
                config('stripe.webhook_secret')
            );
        } catch (\Exception $e) {
            Log::error('Stripe webhook error: ' . $e->getMessage());
            throw $e;
        }

        switch ($event->type) {
            case 'checkout.session.completed':
                $this->handleCheckoutCompleted($event->data->object);
                break;
            case 'customer.subscription.updated':
            case 'customer.subscription.deleted':
                $this->handleSubscriptionUpdate($event->data->object);
                break;
            case 'invoice.payment_succeeded':
                $this->handlePaymentSucceeded($event->data->object);
                break;
        }
    }

    protected function handleCheckoutCompleted($session): void
    {
        $userId = $session->metadata->user_id ?? null;
        $planType = $session->metadata->plan_type ?? null;

        if (!$userId || !$planType) {
            Log::error('Missing metadata in checkout session', ['session_id' => $session->id]);
            return;
        }

        $user = User::find($userId);
        if (!$user) {
            Log::error('User not found for checkout session', ['user_id' => $userId]);
            return;
        }

        $subscription = $this->createSubscription($user, $planType, $session);
        $this->createLicense($user, $subscription);
    }

    protected function createSubscription(User $user, string $planType, $session): Subscription
    {
        $expiresAt = null;
        if ($planType === 'monthly') {
            $expiresAt = now()->addMonth();
        } elseif ($planType === 'annual') {
            $expiresAt = now()->addYear();
        }

        return Subscription::create([
            'user_id' => $user->id,
            'plan_type' => $planType,
            'stripe_subscription_id' => $session->subscription ?? null,
            'stripe_customer_id' => $session->customer ?? null,
            'status' => 'active',
            'expires_at' => $expiresAt,
        ]);
    }

    protected function createLicense(User $user, Subscription $subscription): void
    {
        $features = $subscription->getFeatures();

        \App\Models\License::create([
            'user_id' => $user->id,
            'subscription_id' => $subscription->id,
            'plan' => $subscription->plan_type,
            'features' => $features,
            'status' => 'active',
            'expires_at' => $subscription->expires_at,
        ]);
    }

    protected function handleSubscriptionUpdate($stripeSubscription): void
    {
        $subscription = Subscription::where('stripe_subscription_id', $stripeSubscription->id)->first();
        if (!$subscription) {
            return;
        }

        if ($stripeSubscription->status === 'canceled' || $stripeSubscription->status === 'unpaid') {
            $subscription->update(['status' => 'canceled']);
            $subscription->licenses()->update(['status' => 'expired']);
        }
    }

    protected function handlePaymentSucceeded($invoice): void
    {
        // Handle successful payment
        \App\Models\Payment::create([
            'user_id' => $invoice->customer,
            'stripe_payment_intent_id' => $invoice->payment_intent,
            'amount' => $invoice->amount_paid / 100,
            'currency' => strtoupper($invoice->currency),
            'status' => 'completed',
        ]);
    }
}

