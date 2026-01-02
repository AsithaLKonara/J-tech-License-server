// apps/license-server/test-e2e/frontend.spec.ts
import { test, expect } from '@playwright/test';

test.describe('License Frontend E2E Tests', () => {
  test('should allow user to log in and display pro plan features', async ({ page }) => {
    await page.goto('https://j-tech-license-server.vercel.app/');

    await page.fill('input[type="email"]', 'test@example.com');
    await page.fill('input[type="password"]', 'testpassword123');
    await page.click('button:has-text("Login")');

    // Assertions using specific element IDs
    await expect(page.locator('#userEmail')).toHaveText('test@example.com');
    await expect(page.locator('#userPlan')).toHaveText('pro');
    await expect(page.locator('#userFeatures')).toHaveText('pattern_uploadwifi_uploadadvanced_controls');

    await page.click('button:has-text("Logout")');
    await expect(page.locator('input[type="email"]')).toBeVisible();
  });

  test('should display basic plan features for demo user', async ({ page }) => {
    await page.goto('https://j-tech-license-server.vercel.app/');

    await page.fill('input[type="email"]', 'demo@example.com');
    await page.fill('input[type="password"]', 'demo123');
    await page.click('button:has-text("Login")');

    // Assertions using specific element IDs
    await expect(page.locator('#userEmail')).toHaveText('demo@example.com');
    await expect(page.locator('#userPlan')).toHaveText('basic');
    await expect(page.locator('#userFeatures')).toHaveText('pattern_upload'); // Basic user has only one feature

    await page.click('button:has-text("Logout")');
    await expect(page.locator('input[type="email"]')).toBeVisible();
  });

  test('should show error for invalid login', async ({ page }) => {
    await page.goto('https://j-tech-license-server.vercel.app/');

    await page.fill('input[type="email"]', 'invalid@example.com');
    await page.fill('input[type="password"]', 'wrongpassword');
    await page.click('button:has-text("Login")');

    await expect(page.locator('text=Invalid credentials')).toBeVisible();
  });
});