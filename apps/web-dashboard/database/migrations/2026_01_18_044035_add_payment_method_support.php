<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        // Add payment_method to subscriptions table
        Schema::table('subscriptions', function (Blueprint $table) {
            if (!Schema::hasColumn('subscriptions', 'payment_method')) {
                $table->enum('payment_method', ['card', 'cash'])->default('card')->after('plan_type');
            }
        });

        // Modify payments table for cash payment support
        Schema::table('payments', function (Blueprint $table) {
            // Add payment_method column
            if (!Schema::hasColumn('payments', 'payment_method')) {
                $table->enum('payment_method', ['card', 'cash'])->default('card')->after('subscription_id');
            }
            
            // Add admin_notes for approval/rejection notes
            if (!Schema::hasColumn('payments', 'admin_notes')) {
                $table->text('admin_notes')->nullable()->after('currency');
            }
        });

        // Update status enums - drop and recreate
        if (Schema::hasColumn('payments', 'status')) {
            Schema::table('payments', function (Blueprint $table) {
                $table->dropColumn('status');
            });
        }

        Schema::table('payments', function (Blueprint $table) {
            $table->enum('status', ['pending', 'pending_approval', 'approved', 'completed', 'rejected', 'failed'])->default('pending')->after('admin_notes');
        });

        // Update subscription status to include 'pending'
        if (Schema::hasColumn('subscriptions', 'status')) {
            Schema::table('subscriptions', function (Blueprint $table) {
                $table->dropColumn('status');
            });
        }

        Schema::table('subscriptions', function (Blueprint $table) {
            $table->enum('status', ['pending', 'active', 'canceled', 'expired'])->default('active')->after('stripe_customer_id');
        });
    }

    public function down(): void
    {
        Schema::table('subscriptions', function (Blueprint $table) {
            $table->dropColumn('payment_method');
        });

        Schema::table('payments', function (Blueprint $table) {
            $table->dropColumn('payment_method');
            $table->dropColumn('admin_notes');
            $table->dropColumn('status');
        });

        Schema::table('payments', function (Blueprint $table) {
            $table->enum('status', ['pending', 'completed', 'failed'])->default('pending');
            $table->string('stripe_payment_intent_id')->nullable(false)->change();
        });
    }
};
