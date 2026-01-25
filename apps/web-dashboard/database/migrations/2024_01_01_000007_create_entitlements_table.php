<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('entitlements', function (Blueprint $table) {
            $table->string('id')->primary();
            $table->string('user_id');
            $table->foreign('user_id')->references('id')->on('users')->onDelete('cascade');
            $table->string('product_id')->default('upload-bridge');
            $table->enum('plan', ['trial', 'monthly', 'yearly', 'perpetual'])->default('trial');
            $table->enum('status', ['active', 'inactive', 'cancelled', 'expired'])->default('active');
            $table->json('features')->default('[]');
            $table->integer('max_devices')->default(1);
            $table->string('stripe_customer_id')->nullable();
            $table->string('stripe_subscription_id')->nullable();
            $table->string('stripe_price_id')->nullable();
            $table->timestamp('expires_at')->nullable();
            $table->timestamps();

            // Indexes for performance
            $table->index('user_id');
            $table->index('status');
            $table->index('expires_at');
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('entitlements');
    }
};
