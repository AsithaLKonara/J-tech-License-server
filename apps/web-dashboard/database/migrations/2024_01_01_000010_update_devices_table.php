<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        // SQLite doesn't support dropping foreign keys, so we'll just add the new columns
        Schema::table('devices', function (Blueprint $table) {
            // Add entitlement_id column if it doesn't exist
            if (!Schema::hasColumn('devices', 'entitlement_id')) {
                $table->string('entitlement_id')->nullable();
            }
            
            // Add user_id column if it doesn't exist
            if (!Schema::hasColumn('devices', 'user_id')) {
                $table->string('user_id')->nullable();
            }
        });
        
        // Add indexes and constraints
        Schema::table('devices', function (Blueprint $table) {
            // Add indexes if they don't exist
            if (Schema::hasColumn('devices', 'entitlement_id')) {
                try {
                    $table->index('entitlement_id');
                } catch (\Exception $e) {
                    // Index might already exist
                }
            }
            
            if (Schema::hasColumn('devices', 'user_id')) {
                try {
                    $table->index('user_id');
                } catch (\Exception $e) {
                    // Index might already exist
                }
                
                // Add unique constraint for user_id + device_id
                try {
                    $table->unique(['user_id', 'device_id'], 'devices_user_device_unique');
                } catch (\Exception $e) {
                    // Unique constraint might already exist
                }
            }
        });
    }

    public function down(): void
    {
        Schema::table('devices', function (Blueprint $table) {
            $table->dropUnique('devices_user_device_unique');
            $table->dropIndex(['entitlement_id']);
            $table->dropIndex(['user_id']);
            $table->dropColumn(['entitlement_id', 'user_id']);
            $table->foreign('license_id')->references('id')->on('licenses')->onDelete('cascade');
        });
    }
};
