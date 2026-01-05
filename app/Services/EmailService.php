<?php

namespace App\Services;

use Illuminate\Support\Facades\Mail;
use App\Mail\MagicLinkMail;

class EmailService
{
    public function sendMagicLink(string $email, string $token): void
    {
        $url = route('magic-link.verify', ['token' => $token]);
        
        Mail::to($email)->send(new MagicLinkMail($url));
    }
}

