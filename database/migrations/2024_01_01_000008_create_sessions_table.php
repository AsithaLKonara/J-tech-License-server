<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('api_sessions', function (Blueprint $table) {
            $table->id();
            $table->string('user_id');
            $table->foreign('user_id')->references('id')->on('users')->onDelete('cascade');
            $table->string('token_hash')->unique();
            $table->timestamp('expires_at');
            $table->timestamps();

            // Indexes for performance
            $table->index('token_hash');
            $table->index('expires_at');
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('api_sessions');
    }
};
