import { test, expect } from "@playwright/test"

const BASE = "http://localhost:3000/" // Adjusted to local dev port

test.describe("Kalpixk Dashboard — E2E", () => {
  test("loads without blank page", async ({ page }) => {
    await page.goto(BASE)
    await expect(page.locator("#root")).not.toBeEmpty()
    // Using first() to handle multiple occurrences in the SAC_OS reskin
    await expect(page.locator("text=ATLATL-ORDNANCE").first()).toBeVisible({ timeout: 10000 })
  })

  test("WASM engine loads", async ({ page }) => {
    await page.goto(BASE)
    // Check if status changes from Loading
    await expect(page.locator("text=WASM v").first()).toBeVisible({ timeout: 15000 })
  })
})
