<?php

namespace Tests\E2E;

use Tests\Browser\BrowserTestCase;
use Tests\Helpers\TestHelpers;
use App\Models\User;
use Laravel\Dusk\Browser;

class AccountTest extends BrowserTestCase
{
    /**
     * Test view account page.
     */
    public function test_can_view_account_page(): void
    {
        $user = TestHelpers::createUser(['email' => 'account@test.com']);

        $this->browse(function (Browser $browser) use ($user) {
            TestHelpers::loginAs($browser, $user);
            
            $browser->visit('/account')
                ->assertPathIs('/account')
                ->assertSee('Account');
        });
    }

    /**
     * Test update name.
     */
    public function test_can_update_name(): void
    {
        $user = TestHelpers::createUser(['email' => 'updatename@test.com']);

        $this->browse(function (Browser $browser) use ($user) {
            TestHelpers::loginAs($browser, $user);
            
            $browser->visit('/account')
                ->assertPathIs('/account')
                ->type('name', 'Updated Name')
                ->press('Update Profile')
                ->waitForText('Profile updated successfully')
                ->assertSee('Profile updated successfully');
        });

        $user->refresh();
        $this->assertEquals('Updated Name', $user->name);
    }

    /**
     * Test update email.
     */
    public function test_can_update_email(): void
    {
        $user = TestHelpers::createUser(['email' => 'updateemail@test.com']);
        $newEmail = 'newemail' . uniqid() . '@test.com';

        $this->browse(function (Browser $browser) use ($user, $newEmail) {
            TestHelpers::loginAs($browser, $user);
            
            $browser->visit('/account')
                ->assertPathIs('/account')
                ->type('email', $newEmail)
                ->press('Update Profile')
                ->waitForText('Profile updated successfully')
                ->assertSee('Profile updated successfully');
        });

        $user->refresh();
        $this->assertEquals($newEmail, $user->email);
    }

    /**
     * Test email uniqueness validation.
     */
    public function test_email_uniqueness_validation(): void
    {
        $user1 = TestHelpers::createUser(['email' => 'unique1@test.com']);
        $user2 = TestHelpers::createUser(['email' => 'unique2@test.com']);

        $this->browse(function (Browser $browser) use ($user1, $user2) {
            TestHelpers::loginAs($browser, $user1);
            
            $browser->visit('/account')
                ->assertPathIs('/account')
                ->type('email', $user2->email)
                ->press('Update Profile')
                ->assertSee('The email has already been taken');
        });
    }

    /**
     * Test update password with correct current password.
     */
    public function test_can_update_password_with_correct_current_password(): void
    {
        $user = TestHelpers::createUser(['email' => 'passupdate@test.com']);

        $this->browse(function (Browser $browser) use ($user) {
            TestHelpers::loginAs($browser, $user);
            
            $browser->visit('/account')
                ->assertPathIs('/account')
                ->type('current_password', 'password123')
                ->type('password', 'newpassword123')
                ->type('password_confirmation', 'newpassword123')
                ->press('Update Password')
                ->waitForText('Password updated successfully')
                ->assertSee('Password updated successfully');
        });
    }

    /**
     * Test reject password update with incorrect current password.
     */
    public function test_rejects_password_update_with_incorrect_current_password(): void
    {
        $user = TestHelpers::createUser(['email' => 'wrongpass@test.com']);

        $this->browse(function (Browser $browser) use ($user) {
            TestHelpers::loginAs($browser, $user);
            
            $browser->visit('/account')
                ->assertPathIs('/account')
                ->type('current_password', 'wrongpassword')
                ->type('password', 'newpassword123')
                ->type('password_confirmation', 'newpassword123')
                ->press('Update Password')
                ->assertSee('Current password is incorrect');
        });
    }

    /**
     * Test password confirmation required.
     */
    public function test_password_confirmation_required(): void
    {
        $user = TestHelpers::createUser(['email' => 'passconf@test.com']);

        $this->browse(function (Browser $browser) use ($user) {
            TestHelpers::loginAs($browser, $user);
            
            $browser->visit('/account')
                ->assertPathIs('/account')
                ->type('current_password', 'password123')
                ->type('password', 'newpassword123')
                ->type('password_confirmation', 'differentpassword')
                ->press('Update Password')
                ->assertSee('The password confirmation does not match');
        });
    }

    /**
     * Test success messages display.
     */
    public function test_success_messages_display(): void
    {
        $user = TestHelpers::createUser(['email' => 'success@test.com']);

        $this->browse(function (Browser $browser) use ($user) {
            TestHelpers::loginAs($browser, $user);
            
            $browser->visit('/account')
                ->assertPathIs('/account')
                ->type('name', 'New Name')
                ->press('Update Profile')
                ->waitForText('Profile updated successfully')
                ->assertSee('Profile updated successfully');
        });
    }
}
