<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class License extends Model
{
    use HasFactory;

    protected $fillable = [
        'user_id',
        'subscription_id',
        'plan',
        'features',
        'status',
        'expires_at',
    ];

    protected function casts(): array
    {
        return [
            'features' => 'array',
            'expires_at' => 'datetime',
        ];
    }

    public function user()
    {
        return $this->belongsTo(User::class);
    }

    public function subscription()
    {
        return $this->belongsTo(Subscription::class);
    }

    public function devices()
    {
        return $this->hasMany(Device::class);
    }

    public function isActive(): bool
    {
        if ($this->status !== 'active') {
            return false;
        }

        if (!$this->expires_at) {
            return true;
        }

        return $this->expires_at->isFuture();
    }
}

