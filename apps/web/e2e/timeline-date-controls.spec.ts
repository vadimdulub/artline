import { expect, test } from "@playwright/test";
import { mockMobileExplorers } from "./mobile-explorer-fixture";

test.beforeEach(async ({ page }) => { await mockMobileExplorers(page); });

for (const [name, route, minimum] of [
  ["painters", "/?start=1300&end=1650", 1100],
  ["paintings", "/?view=paintings&start=1300&end=1650", 1100],
  ["books", "/books?start=1300&end=1650", -5000],
  ["events", "/events?start=1300&end=1650", -12000],
  ["all", "/all?selection=true&type=artwork&type=book&type=event&start=1300&end=1650", -12000],
] as const) {
  test(`${name}: desktop date handles and Reset view replace the extra date controls`, async ({ page }, info) => {
    await page.setViewportSize({ width: 1440, height: 1000 });
    await page.goto(route);
    await expect(page.locator(".timeline-stage")).toHaveAttribute("aria-busy", "false");
    const start = page.getByRole("slider", { name: "Timeline start handle" });
    const end = page.getByRole("slider", { name: "Timeline end handle" });
    await expect(start).toBeInViewport();
    await expect(end).toBeInViewport();
    await expect(page.getByRole("spinbutton")).toHaveCount(0);
    await expect(page.getByRole("button", { name: /zoom out to all years|move range .*earlier|move range .*later|edit dates|done editing dates/i })).toHaveCount(0);
    if (name === "painters") {
      const heading = page.locator(".timeline-compact-heading"), key = heading.locator(".timeline-heading-key");
      await expect(key.getByText("Movement colour key", { exact: true })).toBeVisible();
      const headerBox = (await heading.boundingBox())!, keyBox = (await key.boundingBox())!;
      expect(Math.abs(headerBox.x + headerBox.width - keyBox.x - keyBox.width)).toBeLessThan(2);
      await page.screenshot({ path: info.outputPath("desktop-date-controls.png") });
    }
    await start.press("ArrowRight");
    await expect(page).toHaveURL(/start=1301/);
    await end.press("ArrowLeft");
    await expect(page).toHaveURL(/end=1649/);
    await page.reload();
    await expect(start).toHaveAttribute("aria-valuenow", "1301");
    await expect(end).toHaveAttribute("aria-valuenow", "1649");
    const reset = page.getByRole("button", { name: name === "all" ? "Show starting points" : "Reset view", exact: true });
    if (!await reset.isVisible()) await page.getByRole("button", { name: "Filters", exact: true }).click();
    await reset.click();
    if (name === "all") await expect(page.getByRole("heading", { name: "Explore a moment in history" })).toBeVisible();
    else {
      await expect(start).toHaveAttribute("aria-valuenow", String(minimum));
      await expect(end).toHaveAttribute("aria-valuenow", "2000");
    }
  });
}

for (const route of ["/?view=paintings&canvas=map&start=1300&end=1650", "/all?preset=renaissance&canvas=map"]) {
  test(`desktop map preserves dates for the timeline controls: ${route}`, async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 1000 });
    await page.goto(route);
    await expect(page.locator(".map-workspace-v2")).toBeVisible();
    await expect(page.locator(".range-track")).toHaveCount(0);
    await page.getByRole("button", { name: "Timeline", exact: true }).click();
    await expect(page.locator(".range-track")).toBeInViewport();
    await expect(page.getByRole("spinbutton")).toHaveCount(0);
    await page.getByRole("slider", { name: "Timeline start handle" }).press("ArrowRight");
    await expect(page).toHaveURL(/start=1301/);
  });
}
