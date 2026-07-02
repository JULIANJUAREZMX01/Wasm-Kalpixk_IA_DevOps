import { test, expect } from '@playwright/test';

test('dashboard has v9 xochimilco branding', async ({ page }) => {
  // Use a local path if possible or assume a dev server will be running
  await page.goto('http://localhost:5173');
  // Check for the version string in the dashboard
  await expect(page.locator('text=v9.0.0-XOCHIMILCO').first()).toBeVisible();
  await expect(page.locator('text=GUERRA ESPECTRAL').first()).toBeVisible();
  await expect(page.locator('text=XOCHI-9').first()).toBeVisible();
  await page.screenshot({ path: 'v9_dashboard.png' });
});
