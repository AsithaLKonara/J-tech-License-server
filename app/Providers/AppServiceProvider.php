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
        
        // Force absolute database path for SQLite to override .env relative path
        $dbPath = config('database.connections.sqlite.database');
        if ($dbPath && !preg_match('/^[A-Z]:\\\\/', $dbPath)) {
            // Convert relative path to absolute
            $absolutePath = base_path($dbPath);
            $absolutePath = realpath($absolutePath) ?: $absolutePath;
            if (PHP_OS_FAMILY === 'Windows') {
                $absolutePath = str_replace('/', '\\', $absolutePath);
            }
            config(['database.connections.sqlite.database' => $absolutePath]);
        }
    }
}

