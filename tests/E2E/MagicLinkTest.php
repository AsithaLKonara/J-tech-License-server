<?php

namespace Tests\E2E;

use Tests\Browser\BrowserTestCase;
use Tests\Helpers\TestHelpers;
use App\Models\MagicLink;
use App\Models\User;
use Laravel\Dusk\Browser;

class MagicLinkTest extends BrowserTestCase
{
    /**
     * Test requesting magic link with valid email.
     */
    public function test_can_request_magic_link_with_valid_email(): void
    {
        $user = TestHelpers::createUser(['email' => 'magic@test.com']);

        $this->browse(function (Browser $browser) use ($user) {
            $browser->visit('/magic-link')
                ->type('email', $user->email)
                ->press('Send Magic Link')
                ->waitForText('Magic link sent to your email!')
                ->assertSee('Magic link sent to your email!');
        });
    }

    /**
     * Test requesting magic link with non-existent email creates user.
     */
    public function test_magic_link_creates_user_if_not_exists(): void
    {
        $email = 'newuser' . uniqid() . '@test.com';

        $this->browse(function (Browser $browser) use ($email) {
            $browser->visit('/magic-link')
                ->type('email', $email)
                ->press('Send Magic Link')
                ->waitForText('Magic link sent to your email!')
                ->assertSee('Magic link sent to your email!');

            // Verify user was created
            $this->assertDatabaseHas('users', ['email' => $email]);
        });
    }

    /**
     * Test magic link token expires after timeout.
     */
    public function test_magic_link_token_expires_after_timeout(): void
    {
        $user = TestHelpers::createUser(['email' => 'expired@test.com']);
        $magicLink = TestHelpers::createMagicLink($user->email, [
            'expires_at' => now()->subHour(),
        ]);

        $this->browse(function (Browser $browser) use ($magicLink) {
            $browser->visit("/magic-link/verify/{$magicLink->token}")
                ->assertPathIs('/login')
                ->assertSee('Invalid or expired magic link');
        });
    }

    /**
     * Test magic link can only be used once.
     */
    public function test_magic_link_can_only_be_used_once(): void
    {
        $user = TestHelpers::createUser(['email' => 'once@test.com']);
        $magicLink = TestHelpers::createMagicLink($user->email);
        
        // Use the magic link once
        $magicLink->update(['used' => true]);

        $this->browse(function (Browser $browser) use ($magicLink) {
            $browser->visit("/magic-link/verify/{$magicLink->token}")
                ->assertPathIs('/login')
                ->assertSee('Invalid or expired magic link');
        });
    }

    /**
     * Test clicking magic link logs user in.
     */
    public function test_clicking_magic_link_logs_user_in(): void
    {
        $user = TestHelpers::createUser(['email' => 'click@test.com']);
        $magicLink = TestHelpers::createMagicLink($user->email);

        $this->browse(function (Browser $browser) use ($magicLink) {
            $browser->visit("/magic-link/verify/{$magicLink->token}")
                ->waitForLocation('/dashboard')
                ->assertPathIs('/dashboard')
                ->assertSee('Dashboard');
        });
    }

    /**
     * Test invalid token shows error.
     */
    public function test_invalid_token_shows_error(): void
    {
        $this->browse(function (Browser $browser) {
            $browser->visit('/magic-link/verify/invalid-token-12345')
                ->assertPathIs('/login')
                ->assertSee('Invalid or expired magic link');
        });
    }
}
