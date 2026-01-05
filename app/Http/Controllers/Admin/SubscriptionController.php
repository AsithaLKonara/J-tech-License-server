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
}

