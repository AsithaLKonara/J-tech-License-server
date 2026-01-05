<?php

namespace App\Http\Controllers\Auth;

use App\Http\Controllers\Controller;
use App\Models\MagicLink;
use App\Models\User;
use App\Services\EmailService;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\Hash;
use Illuminate\Support\Str;

class MagicLinkController extends Controller
{
    public function __construct(
        private EmailService $emailService
    ) {}

    public function showRequestForm()
    {
        return view('auth.magic-link');
    }

    public function sendMagicLink(Request $request)
    {
        $request->validate([
            'email' => 'required|email',
        ]);

        $magicLink = MagicLink::createForEmail($request->email);
        $this->emailService->sendMagicLink($request->email, $magicLink->token);

        return back()->with('success', 'Magic link sent to your email!');
    }

    public function verify(string $token)
    {
        $magicLink = MagicLink::where('token', $token)->first();

        if (!$magicLink || !$magicLink->isValid()) {
            return redirect()->route('login')->with('error', 'Invalid or expired magic link.');
        }

        $user = User::where('email', $magicLink->email)->first();
        
        if (!$user) {
            // Create user if doesn't exist
            $user = User::create([
                'id' => Str::uuid()->toString(),
                'email' => $magicLink->email,
                'password' => Hash::make(Str::random(32)),
            ]);
        }

        $magicLink->update(['used' => true]);
        Auth::login($user);

        return redirect()->route('dashboard');
    }
}

