<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class RevokedToken extends Model
{
    use HasFactory;

    public $timestamps = false;

    protected $fillable = [
        'token_hash',
        'user_id',
        'reason',
        'revoked_at',
    ];

    protected function casts(): array
    {
        return [
            'revoked_at' => 'datetime',
        ];
    }

    public function user()
    {
        return $this->belongsTo(User::class);
    }
}
