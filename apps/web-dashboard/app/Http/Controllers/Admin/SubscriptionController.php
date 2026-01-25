<?php

namespace App\Http\Controllers\Admin;

use App\Http\Controllers\Controller;
use App\Models\Subscription;
use App\Models\User;
use App\Services\LicenseService;
use Illuminate\Http\Request;

class SubscriptionController extends Controller
{
    public function __construct(
        private LicenseService $licenseService
    ) {}

    public function index()
    {
        $subscriptions = Subscription::with('user')->latest()->paginate(20);
        return view('admin.subscriptions', compact('subscriptions'));
    }

    public function createManual(Request $request, $userId)
    {
        $request->validate([
            'plan_type' => 'required|in:monthly,annual,lifetime',
        ]);

        $user = User::findOrFail($userId);

        $expiresAt = null;
        if ($request->plan_type === 'monthly') {
            $expiresAt = now()->addMonth();
        } elseif ($request->plan_type === 'annual') {
            $expiresAt = now()->addYear();
        }

        $subscription = Subscription::create([
            'user_id' => $user->id,
            'plan_type' => $request->plan_type,
            'status' => 'active',
            'expires_at' => $expiresAt,
        ]);

        $this->licenseService->generateLicenseFromSubscription($user, $subscription);

        return back()->with('success', 'Manual subscription created successfully.');
    }

    public function pendingPayments()
    {
        $payments = \App\Models\Payment::with(['user', 'subscription'])
            ->where('payment_method', 'cash')
            ->where('status', 'pending_approval')
            ->latest()
            ->paginate(20);

        return view('admin.pending-payments', compact('payments'));
    }

    public function approvePayment(Request $request, $paymentId)
    {
        $payment = \App\Models\Payment::findOrFail($paymentId);

        if ($payment->status !== 'pending_approval') {
            return back()->with('error', 'Payment is not pending approval.');
        }

        // Update payment status
        $payment->update([
            'status' => 'approved',
            'admin_notes' => $request->input('admin_notes'),
        ]);

        // Activate the subscription
        if ($payment->subscription) {
            $payment->subscription->update(['status' => 'active']);

            // Generate license for the user
            $this->licenseService->generateLicenseFromSubscription(
                $payment->user,
                $payment->subscription
            );
        }

        return back()->with('success', 'Payment approved and subscription activated.');
    }

    public function rejectPayment(Request $request, $paymentId)
    {
        $request->validate([
            'admin_notes' => 'required|string|max:500',
        ]);

        $payment = \App\Models\Payment::findOrFail($paymentId);

        if ($payment->status !== 'pending_approval') {
            return back()->with('error', 'Payment is not pending approval.');
        }

        // Update payment status
        $payment->update([
            'status' => 'rejected',
            'admin_notes' => $request->admin_notes,
        ]);

        // Cancel or delete the subscription
        if ($payment->subscription) {
            $payment->subscription->update(['status' => 'canceled']);
        }

        return back()->with('success', 'Payment rejected.');
    }
}

