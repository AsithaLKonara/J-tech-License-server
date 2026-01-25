<?php

use Illuminate\Support\Facades\Route;
use App\Http\Controllers\Auth\LoginController;
use App\Http\Controllers\Auth\RegisterController;
use App\Http\Controllers\Auth\MagicLinkController;
use App\Http\Controllers\DashboardController;
use App\Http\Controllers\SubscriptionController;
use App\Http\Controllers\LicenseController;
use App\Http\Controllers\DeviceController;
use App\Http\Controllers\BillingController;
use App\Http\Controllers\AccountController;
use App\Http\Controllers\Admin\UserController as AdminUserController;
use App\Http\Controllers\Admin\SubscriptionController as AdminSubscriptionController;
use App\Http\Controllers\StripeWebhookController;

// Public routes
Route::get('/', function () {
    return view('welcome');
})->name('home');

Route::get('/login', [LoginController::class, 'showLoginForm'])->name('login');
Route::post('/login', [LoginController::class, 'login']);
Route::post('/logout', [LoginController::class, 'logout'])->name('logout');

Route::get('/register', [RegisterController::class, 'showRegistrationForm'])->name('register');
Route::post('/register', [RegisterController::class, 'register']);

Route::get('/magic-link', [MagicLinkController::class, 'showRequestForm'])->name('magic-link.request');
Route::post('/magic-link', [MagicLinkController::class, 'sendMagicLink']);
Route::get('/magic-link/verify/{token}', [MagicLinkController::class, 'verify'])->name('magic-link.verify');

// Stripe webhook
Route::post('/webhook/stripe', [StripeWebhookController::class, 'handleWebhook']);

// Authenticated routes
Route::middleware(['auth'])->group(function () {
    Route::get('/dashboard', [DashboardController::class, 'index'])->name('dashboard');
    Route::get('/subscription', [SubscriptionController::class, 'index'])->name('subscription');
    Route::post('/subscription/checkout', [SubscriptionController::class, 'checkout'])->name('subscription.checkout');
    Route::post('/subscription/cancel', [SubscriptionController::class, 'cancel'])->name('subscription.cancel');
    Route::get('/licenses', [LicenseController::class, 'index'])->name('licenses');
    Route::get('/devices', [DeviceController::class, 'index'])->name('devices');
    Route::delete('/devices/{id}', [DeviceController::class, 'destroy'])->name('devices.destroy');
    Route::get('/billing', [BillingController::class, 'index'])->name('billing');
    Route::get('/account', [AccountController::class, 'index'])->name('account');
    Route::put('/account', [AccountController::class, 'update'])->name('account.update');
    Route::put('/account/password', [AccountController::class, 'updatePassword'])->name('account.password');
});

// Admin routes
Route::middleware(['auth', \App\Http\Middleware\AdminMiddleware::class])->prefix('admin')->name('admin.')->group(function () {
    Route::get('/', function () {
        return view('admin.dashboard');
    })->name('dashboard');
    Route::resource('users', AdminUserController::class);
    Route::resource('subscriptions', AdminSubscriptionController::class);
    Route::post('/subscriptions/{id}/manual', [AdminSubscriptionController::class, 'createManual'])->name('subscriptions.manual');
    Route::get('/payments/pending', [AdminSubscriptionController::class, 'pendingPayments'])->name('payments.pending');
    Route::post('/payments/{id}/approve', [AdminSubscriptionController::class, 'approvePayment'])->name('payments.approve');
    Route::post('/payments/{id}/reject', [AdminSubscriptionController::class, 'rejectPayment'])->name('payments.reject');
});

