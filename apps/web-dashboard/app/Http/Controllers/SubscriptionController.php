<?php

namespace App\Http\Controllers;

use App\Services\StripeService;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Log;

class SubscriptionController extends Controller
{
    public function __construct(
        private StripeService $stripeService
    ) {}

    public function index()
    {
        $user = auth()->user();
        $subscription = $user->activeSubscription();
        $license = $user->activeLicense();

        return view('dashboard.subscription', [
            'subscription' => $subscription,
            'license' => $license,
        ]);
    }

    public function checkout(Request $request)
    {
        $request->validate([
            'plan_type' => 'required|in:monthly,annual,lifetime',
            'payment_method' => 'required|in:card,cash',
        ]);

        $user = auth()->user();
        $planType = $request->plan_type;
        $paymentMethod = $request->payment_method;

        // Handle cash payment
        if ($paymentMethod === 'cash') {
            return $this->handleCashPayment($user, $planType);
        }

        // Handle card payment (existing Stripe flow)
        try {
            $session = $this->stripeService->createCheckoutSession($user, $planType);
            return redirect($session->url);
        } catch (\Exception $e) {
            Log::error('Checkout error: ' . $e->getMessage());
            return back()->with('error', 'Failed to create checkout session.');
        }
    }

    private function handleCashPayment($user, $planType)
    {
        // Calculate expiration date
        $expiresAt = null;
        if ($planType === 'monthly') {
            $expiresAt = now()->addMonth();
        } elseif ($planType === 'annual') {
            $expiresAt = now()->addYear();
        }

        // Create subscription with pending status
        $subscription = \App\Models\Subscription::create([
            'user_id' => $user->id,
            'plan_type' => $planType,
            'payment_method' => 'cash',
            'status' => 'pending',
            'expires_at' => $expiresAt,
        ]);

        // Calculate amount based on plan type
        $amounts = [
            'monthly' => 9.99,
            'annual' => 99.99,
            'lifetime' => 299.99,
        ];

        // Create payment record with pending_approval status
        \App\Models\Payment::create([
            'user_id' => $user->id,
            'subscription_id' => $subscription->id,
            'amount' => $amounts[$planType],
            'currency' => 'USD',
            'payment_method' => 'cash',
            'status' => 'pending_approval',
        ]);

        return back()->with('success', 'Cash payment request submitted. Waiting for admin approval.');
    }

    public function cancel(Request $request)
    {
        $subscription = auth()->user()->activeSubscription();
        
        if (!$subscription) {
            return back()->with('error', 'No active subscription found.');
        }

        $subscription->update(['status' => 'canceled']);
        $subscription->licenses()->update(['status' => 'expired']);

        return back()->with('success', 'Subscription canceled successfully.');
    }

    public function success(Request $request)
    {
        return view('dashboard.subscription-success');
    }
}

