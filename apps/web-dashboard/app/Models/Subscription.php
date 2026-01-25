<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class Subscription extends Model
{
    use HasFactory;

    protected $fillable = [
        'user_id',
        'plan_type',
        'payment_method',
        'stripe_subscription_id',
        'stripe_customer_id',
        'status',
        'expires_at',
    ];

    protected function casts(): array
    {
        return [
            'expires_at' => 'datetime',
        ];
    }

    public function user()
    {
        return $this->belongsTo(User::class);
    }

    public function licenses()
    {
        return $this->hasMany(License::class);
    }

    public function payments()
    {
        return $this->hasMany(Payment::class);
    }

    public function isActive(): bool
    {
        if ($this->status !== 'active') {
            return false;
        }

        if ($this->plan_type === 'lifetime') {
            return true;
        }

        return $this->expires_at && $this->expires_at->isFuture();
    }

    public function getFeatures(): array
    {
        $features = [
            'monthly' => ['pattern_upload', 'wifi_upload'],
            'annual' => ['pattern_upload', 'wifi_upload', 'advanced_controls'],
            'lifetime' => ['pattern_upload', 'wifi_upload', 'advanced_controls', 'ai_features'],
        ];

        return $features[$this->plan_type] ?? [];
    }
}

