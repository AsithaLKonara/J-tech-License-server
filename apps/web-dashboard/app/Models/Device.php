<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class Device extends Model
{
    use HasFactory;

    protected $fillable = [
        'license_id',
        'entitlement_id',
        'user_id',
        'device_id',
        'device_name',
        'last_seen_at',
    ];

    protected $casts = [
        'last_seen_at' => 'datetime',
    ];

    public function license()
    {
        return $this->belongsTo(License::class);
    }

    public function entitlement()
    {
        return $this->belongsTo(Entitlement::class, 'entitlement_id');
    }

    public function user()
    {
        return $this->belongsTo(User::class);
    }
}

