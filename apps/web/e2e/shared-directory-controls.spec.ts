import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

for (const width of [1440, 390, 320]) {
  for (const directory of ["artists", "museums"] as const) {
    test(`${directory} search and pickers preserve filters and keyboard focus at ${width}px`, async ({ page }, info) => {
      await page.setViewportSize({ width, height: 1000 });
      await page.goto(`/${directory}`);
      const main = page.getByRole("main");
      const results = page.getByRole("region", { name: directory === "artists" ? "Artist results" : "Museum results", exact: true });
      await expect(results).toHaveAttribute("aria-busy", "false");
      const searchName = directory === "artists" ? "Search artists" : "Search collections";
      const search = main.getByRole("searchbox", { name: searchName, exact: true });
      if (width < 761) await main.getByRole("button", { name: "Filters", exact: true }).click();
      const countries = main.locator(".multi-filter").filter({ has: page.locator('summary[aria-label^="Countries:"]') });
      await countries.locator("summary").click();
      await countries.getByRole("searchbox", { name: "Search countries", exact: true }).fill("Nether");
      await countries.getByRole(directory === "artists" ? "radio" : "checkbox", { name: "Netherlands", exact: true }).check();
      await page.keyboard.press("Escape");
      await expect(countries.locator("summary")).toBeFocused();
      await expect(countries).not.toHaveAttribute("open");
      await expect(results).toHaveAttribute("aria-busy", "false");
      await page.keyboard.press("/");
      await expect(search).toBeFocused();
      await search.pressSequentially(directory === "artists" ? "Rembrandt" : "Rijks", { delay: 25 });
      await expect(results).toHaveAttribute("aria-busy", "false");
      await expect(results.getByRole("link").first()).toBeVisible();
      const params = new URL(page.url()).searchParams;
      expect(params.get("country")?.toUpperCase()).toBe("NL");
      expect(params.get("q")).toBe(directory === "artists" ? "Rembrandt" : "Rijks");
      await main.getByRole("button", { name: `Clear ${searchName.toLowerCase()}`, exact: true }).click();
      await expect(search).toHaveValue("");
      await expect(search).toBeFocused();
      expect(new URL(page.url()).searchParams.get("country")?.toUpperCase()).toBe("NL");
      await main.getByRole("button", { name: "Reset view", exact: true }).click();
      await expect(results).toHaveAttribute("aria-busy", "false");
      expect(new URL(page.url()).searchParams.has("country")).toBe(false);
      expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
      if (width < 761) await main.getByRole("button", { name: "Filters", exact: true }).click();
      await countries.locator("summary").click();
      const panel = countries.locator(".multi-filter-panel");
      await expect(panel).toBeInViewport();
      const bounds = await panel.boundingBox();
      expect(bounds!.x).toBeGreaterThanOrEqual(0);
      expect(bounds!.x + bounds!.width).toBeLessThanOrEqual(width);
      await page.screenshot({ path: info.outputPath(`${directory}-picker-${width}.png`) });
      if (width === 390) expect((await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze()).violations).toEqual([]);
    });
  }
}

test("filtered artist results and pagination remain server rendered", async ({ browser, baseURL }) => {
  const context = await browser.newContext({ javaScriptEnabled: false, baseURL });
  try {
    const page = await context.newPage();
    await page.goto("/artists?q=Rembrandt&country=NL");
    await expect(page.getByRole("region", { name: "Artist results" }).getByRole("heading", { name: "Rembrandt van Rijn", exact: true })).toBeVisible();
    await expect(page.getByRole("searchbox", { name: "Search artists", exact: true })).toHaveValue("Rembrandt");
    await page.goto("/artists");
    await expect(page.locator("main li h3")).toHaveCount(24);
    await expect(page.getByRole("link", { name: "Next artists", exact: true })).toHaveAttribute("href", /cursor=/);
  } finally { await context.close(); }
});
