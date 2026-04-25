import { test, expect } from '@playwright/test';

test('verify v4.0 phase black visuals', async ({ page }) => {
  // Go to the dashboard
  await page.goto('http://localhost:4173/dashboard/index.html');

  // Verify the header title
  await expect(page.locator('h1')).toContainText('SACITY_OS v4.0-ATLATL');

  // Trigger Phase Black demo
  await page.click('button:has-text("Execute_Phase_Black")');

  // Verify the overlay is visible
  const overlay = page.locator('#black-overlay');
  await expect(overlay).toBeVisible();

  // Verify the status changed
  await expect(page.locator('#anomaly-status')).toContainText('PHASE_BLACK_V4.0');

  // Take a screenshot
  await page.screenshot({ path: '/home/jules/verification/phase_black_v4.png' });
});
