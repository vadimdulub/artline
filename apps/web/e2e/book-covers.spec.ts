import { expect, test } from "@playwright/test";
import { booksFixture, mockBooks } from "./books-fixture";

test("edition image loads only in the drawer, credits its license, and recovers from failure", async ({ page }) => {
  await mockBooks(page);
  const cover = {
    imageUrl: "https://upload.wikimedia.org/wikipedia/commons/test-cover.png",
    sourceUrl: "https://commons.wikimedia.org/wiki/File:Test_cover.png",
    label: "Title page · 1859", credit: "Source creator", license: "Public domain",
    licenseUrl: "https://creativecommons.org/publicdomain/mark/1.0/", checkedAt: "2026-09-17",
  };
  await page.route("**/api/backend/v1/books?**", async route => {
    const response = await route.fetch();
    const data = await response.json();
    // Browser-only fixture, independent of production cover selection.
    await route.fulfill({ json: { ...data, items: [{ ...booksFixture[0], cover }], total: 1, mode: "individual" } });
  });
  let requests = 0;
  await page.route(cover.imageUrl, route => { requests++; return route.abort(); });
  await page.goto("/books");
  await expect(page.locator('ul[aria-label="Book index"] > li')).toHaveCount(1);
  expect(requests).toBe(0);
  await expect(page.locator('[class*="coverImage"]')).toHaveCount(0);
  await page.locator(".book-mark").click();
  await expect.poll(() => requests).toBe(1);
  const drawer = page.getByRole("dialog", { name: "Book details" });
  await expect(drawer).toContainText("Original Artline text cover");
  await expect(drawer.getByRole("link", { name: "Public domain" })).toHaveCount(0);
  await page.keyboard.press("Escape");
  await page.unroute(cover.imageUrl);
  await page.route(cover.imageUrl, route => route.fulfill({ contentType: "image/png", body: Buffer.from("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aAmkAAAAASUVORK5CYII=", "base64") }));
  await page.locator(".book-mark").click();
  await expect(drawer.getByRole("img")).toBeVisible();
  await expect(drawer.getByRole("link", { name: "Image source", exact: true })).toHaveAttribute("href", cover.sourceUrl);
  await expect(drawer.getByRole("link", { name: "Public domain", exact: true })).toHaveAttribute("href", cover.licenseUrl);
  await expect(drawer).toContainText("Source creator");
});

test("real selected edition images open with source credits on desktop and phones", async ({ page }, testInfo) => {
  for (const [width, id] of [[1440, "odyssey"], [390, "wd-q20124"]] as const) {
    await page.setViewportSize({ width, height: 900 });
    await page.goto(`/books?book=${id}`);
    const drawer = page.getByRole("dialog", { name: "Book details" });
    const image = drawer.getByRole("img");
    await expect(image).toBeVisible();
    await expect.poll(() => image.evaluate(node => {
      const element = node as HTMLImageElement;
      return element.complete && element.naturalWidth > 100;
    }), { timeout: 25000 }).toBe(true);
    await image.evaluate(node => (node as HTMLImageElement).decode());
    await expect(drawer.getByRole("link", { name: "Public domain", exact: true })).toHaveAttribute("href", "https://creativecommons.org/publicdomain/mark/1.0/");
    await expect(drawer.getByRole("link", { name: "Image source", exact: true })).toHaveAttribute("href", /^https:\/\/commons.wikimedia.org\/wiki\/File:/);
    const rect = (await drawer.boundingBox())!;
    expect(await drawer.evaluate(node => node.scrollWidth)).toBeLessThanOrEqual(rect.width + 1);
    await page.screenshot({ path: testInfo.outputPath(`edition-cover-${width}.png`) });
    await page.keyboard.press("Escape");
    await expect(page.locator('[class*="coverImage"]')).toHaveCount(0);
  }
});
