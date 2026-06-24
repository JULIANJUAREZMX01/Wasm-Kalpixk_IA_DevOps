import { test, expect } from '@playwright/test';

test('verify landing page', async ({ page }) => {
  await page.goto('http://localhost:3001/index.html');
  await page.screenshot({ path: 'landing_page.png', fullPage: true });
  await expect(page).toHaveTitle(/Kalpixk SIEM/);
  await expect(page.locator('h1')).toContainText('KALPIXK');
});

test('verify dashboard', async ({ page }) => {
  await page.goto('http://localhost:3001/dashboard/index.html');
  await page.waitForTimeout(3000); // Wait for simulation to start
  await page.screenshot({ path: 'dashboard.png', fullPage: true });
  await expect(page.locator('#stat-throughput')).toContainText('4.2');

  // Test manual analysis
  await page.fill('#log-input', 'Apr 09 14:22:15 cancun sshd[123]: Failed password for root from 185.220.101.35');
  await page.click('button:has-text("ANALYZE LOG")');
  await page.waitForTimeout(1000);
  const score = await page.textContent('#manual-score');
  console.log('Manual Score:', score);
  await page.screenshot({ path: 'dashboard_analyzed.png', fullPage: true });
});
