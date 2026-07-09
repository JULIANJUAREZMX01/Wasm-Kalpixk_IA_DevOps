import { test, expect } from '@playwright/test';

test('dashboard has v9 xochimilco branding', async ({ page }) => {
  // Use a local path if possible or assume a dev server will be running
  // For the purpose of this task, I will check the file content as well.
  await page.goto('http://localhost:5173');
  await expect(page.locator('text=v9.0.0-XOCHIMILCO').first()).toBeVisible();
  await expect(page.locator('text=ATLATL_V9_XOCHIMILCO_ACTIVE')).toBeVisible();
  await page.screenshot({ path: 'v9_dashboard.png' });
});
