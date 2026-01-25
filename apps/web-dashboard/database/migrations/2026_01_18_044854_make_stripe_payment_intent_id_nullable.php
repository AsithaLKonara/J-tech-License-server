<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;
use Illuminate\Support\Facades\DB;

return new class extends Migration
{
    public function up(): void
    {
        // For SQLite, we need to recreate the table to modify the column
        // For other databases, we could use ->change()
        
        // First, check if we're using SQLite
        $driver = Schema::getConnection()->getDriverName();
        
        if ($driver === 'sqlite') {
            // SQLite approach: We'll update the constraint by allowing NULL values
            DB::statement('PRAGMA foreign_keys=OFF');
            
            // Create new table with nullable stripe_payment_intent_id
            Schema::create('payments_new', function (Blueprint $table) {
                $table->id();
                $table->foreignId('user_id')->constrained()->onDelete('cascade');
                $table->foreignId('subscription_id')->nullable()->constrained()->onDelete('set null');
                $table->string('stripe_payment_intent_id')->nullable();
                $table->decimal('amount', 10, 2);
                $table->string('currency', 3)->default('USD');
                $table->enum('payment_method', ['card', 'cash'])->default('card');
                $table->text('admin_notes')->nullable();
                $table->enum('status', ['pending', 'pending_approval', 'approved', 'completed', 'rejected', 'failed'])->default('pending');
                $table->timestamps();
            });
            
            // Copy data from old table to new table
            DB::statement('INSERT INTO payments_new (id, user_id, subscription_id, stripe_payment_intent_id, amount, currency, payment_method, admin_notes, status, created_at, updated_at)
                          SELECT id, user_id, subscription_id, stripe_payment_intent_id, amount, currency, payment_method, admin_notes, status, created_at, updated_at
                          FROM payments');
            
            // Drop old table
            Schema::drop('payments');
            
            // Rename new table
            Schema::rename('payments_new', 'payments');
            
            DB::statement('PRAGMA foreign_keys=ON');
        } else {
            // For MySQL/PostgreSQL, use change()
            Schema::table('payments', function (Blueprint $table) {
                $table->string('stripe_payment_intent_id')->nullable()->change();
            });
        }
    }

    public function down(): void
    {
        $driver = Schema::getConnection()->getDriverName();
        
        if ($driver === 'sqlite') {
            // Reverse the change for SQLite
            DB::statement('PRAGMA foreign_keys=OFF');
            
            Schema::create('payments_new', function (Blueprint $table) {
                $table->id();
                $table->foreignId('user_id')->constrained()->onDelete('cascade');
                $table->foreignId('subscription_id')->nullable()->constrained()->onDelete('set null');
                $table->string('stripe_payment_intent_id'); // NOT NULL
                $table->decimal('amount', 10, 2);
                $table->string('currency', 3)->default('USD');
                $table->enum('status', ['pending', 'completed', 'failed'])->default('pending');
                $table->timestamps();
            });
            
            DB::statement('INSERT INTO payments_new (id, user_id, subscription_id, stripe_payment_intent_id, amount, currency, status, created_at, updated_at)
                          SELECT id, user_id, subscription_id, stripe_payment_intent_id, amount, currency, status, created_at, updated_at
                          FROM payments WHERE stripe_payment_intent_id IS NOT NULL');
            
            Schema::drop('payments');
            Schema::rename('payments_new', 'payments');
            
            DB::statement('PRAGMA foreign_keys=ON');
        } else {
            Schema::table('payments', function (Blueprint $table) {
                $table->string('stripe_payment_intent_id')->nullable(false)->change();
            });
        }
    }
};
