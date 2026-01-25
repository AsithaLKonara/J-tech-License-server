<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;

class LicenseController extends Controller
{
    public function index()
    {
        $user = auth()->user();
        $licenses = $user->licenses()->with('subscription')->latest()->get();

        return view('dashboard.licenses', [
            'licenses' => $licenses,
        ]);
    }
}

