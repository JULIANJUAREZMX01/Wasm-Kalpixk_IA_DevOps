import { test, expect } from "@playwright/test"

const BASE = "http://localhost:3000/" // Adjusted to local dev port

test.describe("Kalpixk Dashboard — E2E", () => {
  test("loads without blank page", async ({ page }) => {
    await page.goto(BASE)
    await expect(page.locator("#root")).not.toBeEmpty()
    await expect(page.locator("text=ATLATL-ORDNANCE").first()).toBeVisible({ timeout: 10000 })
  })

  test("WASM engine loads", async ({ page }) => {
    await page.goto(BASE)
    // Check if status changes from Loading
    await expect(page.locator("text=WASM v").first()).toBeVisible({ timeout: 15000 })
  })

  test("simulation works", async ({ page }) => {
    await page.goto(BASE)
    await page.locator("text=🎯 Simulación").click()
    await page.locator("text=🔴 Iniciar Simulación").click()
    await page.locator("text=⚡ Real-Time").click()
    await expect(page.locator("text=LIVE THREAT FEED").first()).toBeVisible()
    // Check if table rows appear
    await expect(page.locator("text=SCORE").first()).toBeVisible({ timeout: 10000 })
    await expect(page.locator("text=CRIT").first()).toBeVisible({ timeout: 10000 })
  })
})
