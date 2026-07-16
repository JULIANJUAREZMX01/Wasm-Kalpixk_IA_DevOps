import { test, expect } from "@playwright/test"

const BASE = "http://localhost:3000/" // Adjusted to local dev port

test.describe("Kalpixk Dashboard — E2E", () => {
  test("loads without blank page", async ({ page }) => {
    await page.goto(BASE)
    await expect(page.locator("#root")).not.toBeEmpty()
    await expect(page.locator("text=KALPIXK").first()).toBeVisible({ timeout: 10000 })
  })

  test("WASM engine loads", async ({ page }) => {
    await page.goto(BASE)
    // Check if status changes from Loading
    await expect(page.locator("text=Motor listo").first()).toBeVisible({ timeout: 15000 })
  })

  test("simulation works", async ({ page }) => {
    await page.goto(BASE)
    await page.getByRole("button", { name: "▶ SIMULAR ATAQUE" }).click()
    await expect(page.locator("text=EVENTOS EN TIEMPO REAL").first()).toBeVisible()
    // Check if table rows appear
    await expect(page.locator(".new-row").first()).toBeVisible({ timeout: 10000 })
  })
})
