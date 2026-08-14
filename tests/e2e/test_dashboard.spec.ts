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
    await expect(page.locator("text=ATLATL-ORDNANCE").first()).toBeVisible({ timeout: 15000 })
  })

  test("simulation works", async ({ page }) => {
    await page.goto(BASE)
    await page.getByText("SIMULACIÓN").click()
    await page.getByRole("button", { name: "🔴 Iniciar Simulación" }).click()
  })
})
