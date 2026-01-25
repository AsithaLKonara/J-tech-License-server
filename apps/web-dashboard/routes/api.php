<?php

use Illuminate\Support\Facades\Route;
use App\Http\Controllers\Api\ApiHealthController;
use App\Http\Controllers\Api\ApiAuthController;
use App\Http\Controllers\Api\ApiLicenseController;
use App\Http\Controllers\Api\ApiDeviceController;

Route::prefix('api/v2')->group(function () {
    // Health check
    Route::get('/health', [ApiHealthController::class, 'check']);
    
    // Authentication
    Route::post('/auth/login', [ApiAuthController::class, 'login']);
    Route::post('/auth/refresh', [ApiAuthController::class, 'refresh']);
    Route::post('/auth/logout', [ApiAuthController::class, 'logout']);
    Route::post('/auth/magic-link/request', [ApiAuthController::class, 'requestMagicLink']);
    Route::post('/auth/magic-link/verify', [ApiAuthController::class, 'verifyMagicLink']);
    
    // License
    Route::middleware(['api.auth'])->group(function () {
        Route::get('/license/validate', [ApiLicenseController::class, 'validateLicense']);
        Route::post('/license/verify', [ApiLicenseController::class, 'verify']);
        Route::get('/license/info', [ApiLicenseController::class, 'info']);
    });
    
    // Devices
    Route::middleware(['api.auth'])->group(function () {
        Route::post('/devices/register', [ApiDeviceController::class, 'register']);
        Route::get('/devices', [ApiDeviceController::class, 'index']);
        Route::delete('/devices/{id}', [ApiDeviceController::class, 'destroy']);
    });
});
