import { test, expect } from "@playwright/test"

const BASE = "http://localhost:3000/" // Adjusted to local dev port

test.describe("Kalpixk Dashboard — E2E", () => {
  test("loads without blank page", async ({ page }) => {
    await page.goto(BASE)
    await expect(page.locator("#app")).not.toBeEmpty()
    await expect(page.locator("text=KALPIXK")).toBeVisible({ timeout: 10000 })
  })

  test("WASM engine loads", async ({ page }) => {
    await page.goto(BASE)
    // Check if status changes from Loading
    await expect(page.locator("text=Motor listo")).toBeVisible({ timeout: 15000 })
  })

  test("simulation works", async ({ page }) => {
    await page.goto(BASE)
    await page.get_by_role("button", name="▶ SIMULAR ATAQUE").click()
    await expect(page.locator("text=EVENTOS EN TIEMPO REAL")).toBeVisible()
    // Check if table rows appear
    await expect(page.locator("table tbody tr")).toHaveCount(1, { timeout: 10000 })
  })
})
