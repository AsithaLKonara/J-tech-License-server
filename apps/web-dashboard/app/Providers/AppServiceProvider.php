<?php

namespace App\Providers;

use Illuminate\Support\ServiceProvider;
use Illuminate\Support\Facades\Route;

class AppServiceProvider extends ServiceProvider
{
    public function register(): void
    {
        //
    }

    public function boot(): void
    {
        Route::aliasMiddleware('admin', \App\Http\Middleware\AdminMiddleware::class);
        Route::aliasMiddleware('api.auth', \App\Http\Middleware\ApiAuthMiddleware::class);
        
        // Path resolution is now handled in config/database.php

    }
}

