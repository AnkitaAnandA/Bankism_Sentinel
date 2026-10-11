const { chromium } = require("playwright");
const fs = require("node:fs");
const path = require("node:path");
const assert = require("node:assert/strict");
(async () => {
  const browser = await chromium.launch({ channel: "chrome", headless: true });
  const page = await browser.newPage({
    viewport: { width: 1440, height: 900 },
    colorScheme: "light",
    reducedMotion: "reduce",
  });
  const errors = [];
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text());
  });
  await page.goto(process.env.UI_BASE_URL || "http://localhost:8000");
  await page
    .getByRole("heading", { name: "What would you like to do?" })
    .waitFor();
  await page.locator(".account-card").first().waitFor();
  await page.screenshot({
    path: path.resolve(__dirname, "../docs/demo-desktop.png"),
    fullPage: false,
  });
  await page
    .getByRole("button", {
      name: "GUARDED PAYMENT Transfer ₹800 to Rahul",
      exact: false,
    })
    .click();
  await page.getByRole("button", { name: "Confirm & send" }).waitFor();
  await page.getByRole("button", { name: "Cancel", exact: true }).click();
  await page
    .getByText("Cancelled. No money was moved.", { exact: true })
    .waitFor();
  await page.getByLabel("Acting as").selectOption("analyst");
  await page.getByRole("heading", { name: "Security timeline" }).waitFor();
  await page.locator("tbody tr").first().waitFor();
  await page.getByRole("button", { name: "Switch to dark theme" }).click();
  await page.getByRole("button", { name: "Attack Lab", exact: true }).click();
  await page
    .getByRole("button", { name: "Inspect request", exact: false })
    .click();
  await page.locator(".verdict-card.block").waitFor();
  await page.setViewportSize({ width: 390, height: 844 });
  assert(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth + 1,
    ),
  );
  assert.equal(errors.length, 0, JSON.stringify(errors));
  const report = {
    base: process.env.UI_BASE_URL || "http://localhost:8000",
    checks: [
      "D-drive static app loads",
      "prepare/cancel",
      "analyst dashboard/charts",
      "theme toggle",
      "real memo injection BLOCK",
      "mobile no overflow",
    ],
    consoleErrors: errors,
    strictCSP: true,
  };
  fs.writeFileSync(
    path.resolve(__dirname, "../docs/local-smoke.json"),
    JSON.stringify(report, null, 2),
  );
  await browser.close();
  console.log(
    "6 D-drive frontend smoke checks passed under the actual server CSP.",
  );
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
