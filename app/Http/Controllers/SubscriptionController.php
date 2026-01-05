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
        ]);

        try {
            $session = $this->stripeService->createCheckoutSession(
                auth()->user(),
                $request->plan_type
            );

            return redirect($session->url);
        } catch (\Exception $e) {
            Log::error('Checkout error: ' . $e->getMessage());
            return back()->with('error', 'Failed to create checkout session.');
        }
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

