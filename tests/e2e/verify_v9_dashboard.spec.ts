import { test, expect } from '@playwright/test';

test('dashboard has v9 xochimilco branding', async ({ page }) => {
  await page.goto('http://localhost:5173');
  await expect(page.locator('text=v9.0.0-XOCHIMILCO').first()).toBeVisible();
  await expect(page.locator('text=ATLATL_V9_XOCHIMILCO_ACTIVE')).toBeVisible();
  await expect(page.locator('text=XOCHI-9')).toBeVisible();
  await expect(page.locator('text=XOCHI-10')).toBeVisible();
  await page.screenshot({ path: 'v9_dashboard.png' });
});
