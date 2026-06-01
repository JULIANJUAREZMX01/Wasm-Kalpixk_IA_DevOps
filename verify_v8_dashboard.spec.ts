import { test, expect } from '@playwright/test';

test('dashboard has v8 guerrilla branding', async ({ page }) => {
  // Use a local path if possible or assume a dev server will be running
  // For the purpose of this task, I will check the file content as well.
  await page.goto('http://localhost:5173');
  await expect(page.locator('text=v8.0.0-GUERRILLA')).toBeVisible();
  await expect(page.locator('text=ATLATL_V8_GUERRILLA_ACTIVE')).toBeVisible();
  await page.screenshot({ path: 'v8_dashboard.png' });
});
