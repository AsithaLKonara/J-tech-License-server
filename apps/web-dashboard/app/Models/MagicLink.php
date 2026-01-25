<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Support\Str;

class MagicLink extends Model
{
    use HasFactory;

    protected $fillable = [
        'email',
        'token',
        'expires_at',
        'used',
    ];

    protected function casts(): array
    {
        return [
            'expires_at' => 'datetime',
            'used' => 'boolean',
        ];
    }

    public static function createForEmail(string $email): self
    {
        return self::create([
            'email' => $email,
            'token' => Str::random(64),
            'expires_at' => now()->addHours(1),
            'used' => false,
        ]);
    }

    public function isValid(): bool
    {
        return !$this->used && $this->expires_at->isFuture();
    }
}

