<?php

namespace App\Http\Controllers\Admin;

use App\Http\Controllers\Controller;
use App\Models\User;
use Illuminate\Http\Request;

class UserController extends Controller
{
    public function index()
    {
        $users = User::with(['subscriptions', 'licenses'])->latest()->paginate(20);
        return view('admin.users', compact('users'));
    }

    public function show(User $user)
    {
        $user->load(['subscriptions', 'licenses', 'payments', 'devices']);
        return view('admin.user-detail', compact('user'));
    }
}

