<?php

namespace App\Mail;

use Illuminate\Bus\Queueable;
use Illuminate\Mail\Mailable;
use Illuminate\Queue\SerializesModels;

class MagicLinkMail extends Mailable
{
    use Queueable, SerializesModels;

    public function __construct(
        public string $url
    ) {}

    public function build()
    {
        return $this->subject('Login to Upload Bridge')
            ->view('emails.magic-link')
            ->with(['url' => $this->url]);
    }
}

