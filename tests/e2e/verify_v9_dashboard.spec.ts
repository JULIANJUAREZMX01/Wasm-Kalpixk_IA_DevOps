import { test, expect } from "@playwright/test";

const PORT = 5173;
const BASE = `http://localhost:${PORT}`;

test.describe("Kalpixk Dashboard v9 — XOCHIMILCO", () => {
  test("loads and shows XOCHIMILCO branding", async ({ page }) => {
    await page.goto(BASE);
    // Check for v9 branding
    await expect(page.locator("text=XOCHIMILCO-ORDNANCE").first()).toBeVisible({ timeout: 15000 });
    await expect(page.locator("text=v9.0.0-XOCHIMILCO").first()).toBeVisible();
  });

  test("displays Node-9 and Node-10 indicators", async ({ page }) => {
    await page.goto(BASE);
    await expect(page.locator("text=NODE-9").first()).toBeVisible({ timeout: 15000 });
    await expect(page.locator("text=NODE-10").first()).toBeVisible();
    await expect(page.locator("text=MESH_AUTH").first()).toBeVisible();
    await expect(page.locator("text=INTEGRITY_GUARD").first()).toBeVisible();
  });

  test("terminal reflects XOCHIMILCO mode", async ({ page }) => {
    await page.goto(BASE);
    await expect(page.locator("text=XOCHIMILCO MODE v9").first()).toBeVisible({ timeout: 15000 });
  });
});
