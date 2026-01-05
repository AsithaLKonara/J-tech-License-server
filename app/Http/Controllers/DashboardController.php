<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;

class DashboardController extends Controller
{
    public function index()
    {
        $user = auth()->user();
        $subscription = $user->activeSubscription();
        $license = $user->activeLicense();
        $devices = $license ? $license->devices()->count() : 0;
        $payments = $user->payments()->where('status', 'completed')->sum('amount');

        return view('dashboard.index', [
            'subscription' => $subscription,
            'license' => $license,
            'devices' => $devices,
            'totalSpent' => $payments,
        ]);
    }
}

