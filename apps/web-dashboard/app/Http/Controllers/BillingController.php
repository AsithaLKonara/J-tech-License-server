<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;

class BillingController extends Controller
{
    public function index()
    {
        $user = auth()->user();
        $payments = $user->payments()->where('status', 'completed')->latest()->get();

        return view('dashboard.billing', [
            'payments' => $payments,
        ]);
    }
}

