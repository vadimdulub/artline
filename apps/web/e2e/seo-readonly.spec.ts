import { test, expect } from "@playwright/test";

// Run against the real local catalogue with a read-only API connection.
// No database fixtures, publication changes or editor credentials are used.
test.use({ javaScriptEnabled: false });

test("crawler discovery, canonical domain and internal-route exclusions", async ({ request, page }) => {
  const origin = process.env.ARTLINE_SEO_EXPECTED_ORIGIN;
  test.skip(!origin, "Set ARTLINE_SEO_EXPECTED_ORIGIN to the configured canonical origin.");
  const robots = await request.get("/robots.txt");
  expect(robots.status()).toBe(200);
  expect(await robots.text()).toContain(`Sitemap: ${origin}/sitemap.xml`);
  const sitemap = await request.get("/sitemap.xml");
  expect(sitemap.status()).toBe(200);
  expect(await sitemap.text()).toContain(`${origin}/sitemap-pages.xml`);
  const pages = await request.get("/sitemap-pages.xml");
  expect(await pages.text()).not.toContain("/catalogue");
  await page.goto("/about");
  await expect(page.locator('head link[rel="canonical"]')).toHaveAttribute("href", `${origin}/about`);
  await expect(page.locator('head meta[name="robots"]')).toHaveAttribute("content", "index, follow");
  await page.goto("/catalogue");
  await expect(page.locator('head meta[name="robots"]')).toHaveAttribute("content", "noindex, follow");
  expect((await request.get("/api/backend/v1/seo/artists")).headers()["x-robots-tag"]).toBe("noindex");
});

test("artist links and complete artwork content work without JavaScript", async ({ page, request }) => {
  test.skip(!process.env.ARTLINE_SEO_EXPECTED_ORIGIN, "Requires the read-only SEO preview server.");
  const slug = "leonardo-da-vinci";
  const id = "1aae4f1a-3b50-4424-adfb-f59a734dfc36";
  const path = `/artists/${slug}/works/${id}`;
  await page.goto(`/artists/${slug}`);
  await expect(page.getByRole("navigation", { name: "Artwork pages" }).getByRole("link").first()).toHaveAttribute("href", /\/works\//);
  await page.goto(path);
  await expect(page).toHaveTitle(/Ginevra.*Leonardo.*Artline/);
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Ginevra de’ Benci (obverse)");
  await expect(page.locator('head meta[name="robots"]')).toHaveAttribute("content", "index, follow");
  const fallback = page.locator(".standalone-artwork");
  await expect(fallback).toBeVisible();
  await expect(page.locator(".image-dialog")).not.toBeVisible();
  await expect(fallback.locator(".artwork-description")).toHaveCount(1);
  await fallback.getByText("About this artwork", { exact: true }).click();
  await expect(fallback.locator(".artwork-description")).toBeVisible();
  const redirect = await request.get(`/artists/${slug}?work=${id}`, { maxRedirects: 0 });
  expect(redirect.status()).toBe(308);
  expect(redirect.headers().location).toContain(path);
  expect((await request.get(`/artists/${slug}/works/00000000-0000-0000-0000-000000000000`)).status()).toBe(404);
});

test("museum identity is rendered before client requests", async ({ page }) => {
  test.skip(!process.env.ARTLINE_SEO_EXPECTED_ORIGIN, "Requires the read-only SEO preview server.");
  await page.goto("/museums/national-gallery-london");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("National Gallery");
  await expect(page.locator('head meta[name="description"]')).toHaveAttribute("content", /National Gallery/);
  await expect(page.locator('head meta[name="robots"]')).toHaveAttribute("content", "index, follow");
});

test("browsing the full painter collection preserves page identity and canonical artwork links", async ({ browser }) => {
  const origin = process.env.ARTLINE_SEO_EXPECTED_ORIGIN;
  test.skip(!origin, "Requires the read-only SEO preview server.");
  const context = await browser.newContext({ javaScriptEnabled: true });
  const page = await context.newPage();
  await page.goto(`${test.info().project.use.baseURL}/artists/leonardo-da-vinci`);
  await page.locator('.work-card[aria-pressed="false"]').first().click();
  await expect(page).toHaveURL(/\/artists\/leonardo-da-vinci\?work=/);
  const heading = await page.locator(".artist-heading h1").innerText();
  await expect(page).toHaveTitle(new RegExp(heading.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")));
  await expect(page.locator('head link[rel="canonical"]')).toHaveAttribute("href", `${origin}${new URL(page.url()).pathname}`);
  await expect(page.locator('nav[aria-label="Artwork pages"] a').first()).toHaveAttribute("href", /\/artists\/leonardo-da-vinci\/works\//);
  await expect.poll(() => page.locator(".image-dialog img").evaluate((image: HTMLImageElement) => image.naturalWidth)).toBeGreaterThan(0);
  await page.screenshot({ path: "/tmp/artline-seo-artwork.png", fullPage: true });
  await context.close();
});
