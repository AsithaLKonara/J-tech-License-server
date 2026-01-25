<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class Entitlement extends Model
{
    use HasFactory;

    protected $primaryKey = 'id';
    public $incrementing = false;
    protected $keyType = 'string';

    protected $fillable = [
        'id',
        'user_id',
        'product_id',
        'plan',
        'status',
        'features',
        'max_devices',
        'stripe_customer_id',
        'stripe_subscription_id',
        'stripe_price_id',
        'expires_at',
    ];

    protected $casts = [
        'features' => 'array',
        'expires_at' => 'datetime',
    ];

    public function user()
    {
        return $this->belongsTo(User::class);
    }

    public function devices()
    {
        return $this->hasMany(Device::class, 'entitlement_id');
    }

    public function isActive(): bool
    {
        if ($this->status !== 'active') {
            return false;
        }

        if (!$this->expires_at) {
            return true; // Perpetual license
        }

        // Ensure expires_at is a Carbon instance - handle both string and object
        $expiresAt = $this->expires_at;
        if (!($expiresAt instanceof \Carbon\Carbon) && !($expiresAt instanceof \DateTimeInterface)) {
            if (is_string($expiresAt)) {
                $expiresAt = \Carbon\Carbon::parse($expiresAt);
            } elseif (is_numeric($expiresAt)) {
                $expiresAt = \Carbon\Carbon::createFromTimestamp($expiresAt);
            } else {
                $expiresAt = \Carbon\Carbon::parse($expiresAt);
            }
        }

        return $expiresAt->isFuture();
    }

    /**
     * Accessor for features attribute to ensure it's always an array
     */
    public function getFeaturesAttribute($value)
    {
        // If it's already an array, return it
        if (is_array($value)) {
            return $value;
        }
        
        // If it's a string, try to decode it
        if (is_string($value)) {
            $decoded = json_decode($value, true);
            return is_array($decoded) ? $decoded : [];
        }
        
        // Default to empty array
        return [];
    }

    public function getFeatures(): array
    {
        return $this->features ?? [];
    }

    public function canAddDevice(): bool
    {
        if (!$this->isActive()) {
            return false;
        }

        $currentDeviceCount = $this->devices()->count();
        return $currentDeviceCount < $this->max_devices;
    }
}
