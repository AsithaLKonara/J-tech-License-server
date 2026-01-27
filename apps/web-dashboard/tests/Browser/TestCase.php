<?php

namespace Tests\Browser;

use Illuminate\Foundation\Testing\DatabaseMigrations;
use Laravel\Dusk\TestCase as BaseTestCase;
use Illuminate\Support\Facades\Artisan;
use Illuminate\Support\Facades\Hash;
use App\Models\User;

abstract class BrowserTestCase extends BaseTestCase
{
    use DatabaseMigrations;

    /**
     * Prepare for Dusk test execution.
     *
     * @beforeClass
     */
    public static function prepare(): void
    {
        if (!static::runningInSail()) {
            static::startChromeDriver();
        }
    }

    /**
     * Create the RemoteWebDriver instance.
     *
     * @return \Facebook\WebDriver\Remote\RemoteWebDriver
     */
    protected function driver()
    {
        $options = (new \Facebook\WebDriver\Chrome\ChromeOptions)
            ->addArguments([
                '--disable-gpu',
                '--headless',
                '--window-size=1920,1080',
                '--no-sandbox',
                '--disable-dev-shm-usage',
            ]);

        return \Facebook\WebDriver\Remote\RemoteWebDriver::create(
            'http://localhost:9515',
            \Facebook\WebDriver\Remote\DesiredCapabilities::chrome()->setCapability(
                \Facebook\WebDriver\Chrome\ChromeOptions::CAPABILITY,
                $options
            )
        );
    }

    /**
     * Setup the test environment.
     */
    protected function setUp(): void
    {
        parent::setUp();

        // Run migrations
        Artisan::call('migrate:fresh');
        
        // Seed test data
        $this->seedTestData();
    }

    /**
     * Seed test data for all tests.
     */
    protected function seedTestData(): void
    {
        // Create test admin user
        User::create([
            'name' => 'Test Admin',
            'email' => 'admin@test.com',
            'password' => Hash::make('password123'),
            'is_admin' => true,
        ]);

        // Create test regular user
        User::create([
            'name' => 'Test User',
            'email' => 'user@test.com',
            'password' => Hash::make('password123'),
            'is_admin' => false,
        ]);
    }

    /**
     * Get base URL for the application.
     */
    protected function baseUrl(): string
    {
        return config('app.url') ?? 'http://localhost:8000';
    }
}
