import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

// Session responses are browser-only. No account or catalogue fixtures are written.
test.beforeEach(async ({ page }) => {
  await page.route("**/api/auth/session", route => route.fulfill({ json: { enabled: true, user: null } }));
});

test("About is a crawlable entrance to the guides and timelines without JavaScript", async ({ browser, baseURL }) => {
  const context = await browser.newContext({ javaScriptEnabled: false, baseURL });
  const page = await context.newPage();
  await page.goto("/about");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("See art.Discover its world.");
  await expect(page).toHaveTitle(/About Artline: art, timelines & museum guides/);
  await expect(page.locator('head link[rel="canonical"]')).toHaveAttribute("href", "https://artlines.org/about");
  await expect(page.locator('head meta[name="robots"]')).toHaveAttribute("content", "index, follow");
  await expect(page.locator('head meta[name="description"]')).toHaveAttribute("content", /interactive timelines.*museum guides/);
  const structured = await page.locator('script[type="application/ld+json"]').allTextContents();
  expect(structured.map(text => JSON.parse(text)["@type"])).toEqual(["BreadcrumbList", "AboutPage"]);
  for (const href of ["/all", "/", "/books", "/events", "/artists", "/artworks", "/museums", "/art-history-timeline", "/guides", "/guides/louvre", "/guides/prado", "/guides/muma-le-havre", "/guides/leventis-gallery", "/guides/national-gallery-armenia", "/guides/munich-museums"]) {
    expect(await page.locator(`main a[href="${href}"]`).count(), href).toBeGreaterThan(0);
  }
  await expect(page.locator("body")).not.toContainText(/\bsources?\b/i);
  await expect(page.locator("details[open]")).toHaveCount(0);
  await expect(page.locator("#museum-guides img")).toHaveCount(6);
  await expect(page.locator("#artwork-carousel a")).toHaveCount(9);
  await expect(page.locator("#artist-carousel a")).toHaveCount(8);
  await expect(page.locator("#timeline-preview a")).toHaveCount(6);
  await page.getByRole("link", { name: "Image credits", exact: true }).click();
  await expect(page.locator("#image-credits")).toBeInViewport();
  await expect(page.locator("#image-credits")).toContainText("Public domain");
  await page.getByRole("link", { name: "Browse all museum guides", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Guides", exact: true })).toBeVisible();
  await context.close();
});

test("timeline preview scrolls through real dates and opens the same selection", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/about");
  const preview = page.getByRole("region", { name: "Artwork timeline preview" });
  await expect(page.getByRole("button", { name: "Earlier artworks", exact: true })).toBeDisabled();
  await page.getByRole("button", { name: "Later artworks", exact: true }).click();
  await expect.poll(() => preview.evaluate(element => element.scrollLeft)).toBeGreaterThan(100);
  await preview.focus();
  await page.keyboard.press("End");
  await expect(page.getByRole("button", { name: "Later artworks", exact: true })).toBeDisabled();
  await expect(preview.getByRole("link", { name: /Colour Study.*1913/ })).toBeInViewport();
  await page.keyboard.press("Home");
  await expect.poll(() => preview.evaluate(element => element.scrollLeft)).toBe(0);

  const ids = await preview.locator("a").evaluateAll(links => links.map(link => link.getAttribute("href")!.split("#work-")[1]));
  await page.getByRole("link", { name: "Open interactive timeline", exact: true }).click();
  await expect(page).toHaveURL(/\/all\?/);
  const parameters = new URL(page.url()).searchParams;
  expect(parameters.getAll("artwork_id")).toEqual(ids);
  expect(parameters.get("start")).toBe("1450");
  expect(parameters.get("end")).toBe("1970");
  expect(parameters.getAll("type")).toEqual(["artwork", "book", "event"]);
  await expect(page.locator(".all-start")).toHaveCount(0);
});

test("artist carousel supports buttons, keyboard boundaries and public artist links", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/about");
  const carousel = page.getByRole("region", { name: "Artists to explore" });
  const previous = page.getByRole("button", { name: "Previous artists", exact: true });
  const next = page.getByRole("button", { name: "Next artists", exact: true });
  await expect(previous).toBeDisabled();
  await next.click();
  await expect.poll(() => carousel.evaluate(element => element.scrollLeft)).toBeGreaterThan(100);
  await previous.click();
  await expect.poll(() => carousel.evaluate(element => element.scrollLeft)).toBeLessThan(10);
  await page.setViewportSize({ width: 390, height: 844 });
  await carousel.focus();
  await page.keyboard.press("End");
  await expect(next).toBeDisabled();
  await expect(carousel.getByRole("link", { name: "Explore Marianne von Werefkin", exact: true })).toBeInViewport();
  await page.keyboard.press("Home");
  await expect(previous).toBeDisabled();
  await page.keyboard.press("ArrowRight");
  await expect.poll(() => carousel.evaluate(element => element.scrollLeft)).toBeGreaterThan(100);
  await carousel.getByRole("link", { name: "Explore Claude Monet", exact: true }).click();
  await expect(page).toHaveURL(/\/artists\/claude-monet$/);
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Claude Monet");
  await expect(page.getByRole("dialog", { name: "Sign in to Artline" })).toHaveCount(0);
});

test("featured guides stay in one bounded carousel with button and keyboard navigation", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/about");
  const carousel = page.getByRole("region", { name: "Museum guides to explore" });
  const previous = page.getByRole("button", { name: "Previous guides", exact: true });
  const next = page.getByRole("button", { name: "Next guides", exact: true });
  await expect(carousel.getByRole("link")).toHaveCount(6);
  for (const width of [1440, 390]) {
    await page.setViewportSize({ width, height: 900 });
    expect(await carousel.locator("li").evaluateAll(cards => new Set(cards.map(card => card.getBoundingClientRect().top)).size)).toBe(1);
    await expect(previous).toBeDisabled();
    await next.click();
    await expect.poll(() => carousel.evaluate(element => element.scrollLeft)).toBeGreaterThan(100);
    await previous.click();
    await expect(previous).toBeDisabled();
    await carousel.focus();
    await page.keyboard.press("End");
    await expect(next).toBeDisabled();
    await expect(carousel.locator('a[href="/guides/munich-museums"]')).toBeInViewport();
    await page.keyboard.press("Home");
    await expect(previous).toBeDisabled();
    await page.keyboard.press("ArrowRight");
    await expect.poll(() => carousel.evaluate(element => element.scrollLeft)).toBeGreaterThan(100);
    await page.keyboard.press("ArrowLeft");
    await expect(previous).toBeDisabled();
  }
  await carousel.locator('a[href="/guides/prado"]').click();
  await expect(page).toHaveURL(/\/guides\/prado$/);
  await expect(page.getByRole("dialog", { name: "Sign in to Artline" })).toHaveCount(0);
});

test("guide links open the selected work and museum sign-in retains its destination", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", error => errors.push(error.message));
  await page.goto("/about");
  const museums = page.getByRole("link", { name: "Explore museums", exact: true });
  await museums.click();
  const signIn = page.getByRole("dialog", { name: "Sign in to Artline" });
  await expect(signIn).toBeVisible();
  await expect(signIn.getByRole("button", { name: "Sign in with Google", exact: true })).toBeVisible();
  await expect(signIn.locator("form")).toHaveAttribute("action", /return_to=%2Fmuseums/);
  await page.keyboard.press("Escape");
  await expect(signIn).toHaveCount(0);
  await expect(museums).toBeFocused();
  await page.getByRole("link", { name: "Explore Winter Sun at Lavacourt by Claude Monet", exact: true }).click();
  await expect(page).toHaveURL(/\/guides\/muma-le-havre#work-af9c2c5c-6b32-4252-aa6c-ed175a6fc03e$/);
  await expect(page.locator("#work-af9c2c5c-6b32-4252-aa6c-ed175a6fc03e")).toBeInViewport();
  expect(errors).toEqual([]);
});

test("period starting points open all three timeline layers", async ({ page }) => {
  await page.goto("/about");
  await page.getByRole("link", { name: "The Renaissance", exact: true }).click();
  await expect(page).toHaveURL(/\/all\?preset=renaissance/);
  const parameters = new URL(page.url()).searchParams;
  expect(parameters.getAll("type")).toEqual(["artwork", "book", "event"]);
  await expect(page.locator(".all-start")).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Remove The Renaissance filter", exact: true })).toBeVisible();
  for (const name of ["Artworks", "Books", "Events"]) {
    await expect(page.getByRole("checkbox", { name, exact: true })).toBeChecked();
  }
});

test("About fits small screens with working anchors, images and accessible controls", async ({ page }, info) => {
  await page.goto("/about");
  for (const width of [1440, 1024, 768, 390, 320]) {
    await page.setViewportSize({ width, height: 900 });
    expect(await page.evaluate(() => document.documentElement.scrollWidth), `${width}px overflow`).toBeLessThanOrEqual(width);
    await page.getByRole("link", { name: "Find a museum guide", exact: true }).click();
    await expect(page.locator("#guides-title")).toBeInViewport();
    expect((await page.locator("#guides-title").boundingBox())!.y).toBeGreaterThan((await page.locator(".site-header").boundingBox())!.height);
    if (width === 1440 || width === 390) {
      const audit = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
      expect(audit.violations).toEqual([]);
      await page.evaluate(async () => {
        await Promise.all([...document.querySelectorAll<HTMLImageElement>("main img")].map(image => { image.loading = "eager"; return image.decode(); }));
        window.scrollTo(0, 0);
      });
      await page.screenshot({ path: info.outputPath(`about-${width}.png`), fullPage: true });
    }
  }
  await page.goto("/about#popular-painters");
  await expect(page.locator("#popular-painters")).toBeVisible();
  await expect(page.locator("#popular-painters")).toBeInViewport();
  await expect(page.locator("#popular-painters")).toContainText("Pantheon 2025");
});


test("opening artwork carousel preserves nine full images and supports navigation", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/about");
  const carousel = page.getByRole("region", { name: "Artworks to explore", exact: true });
  const previous = page.getByRole("button", { name: "Previous artworks", exact: true });
  const next = page.getByRole("button", { name: "Next artworks", exact: true });
  await expect(carousel.locator("li")).toHaveCount(9);
  const destinations = await carousel.locator("a").evaluateAll(links => links.map(link => link.getAttribute("href")));
  expect(new Set(destinations).size).toBe(9);
  for (const width of [1440, 1024, 768, 390, 320]) {
    await page.setViewportSize({ width, height: 900 });
    await carousel.focus(); await page.keyboard.press("Home");
    await expect(previous).toBeDisabled();
    await next.click();
    await expect.poll(() => carousel.evaluate(element => element.scrollLeft)).toBeGreaterThan(100);
    await carousel.focus(); await page.keyboard.press("End");
    await expect(next).toBeDisabled();
    await expect(carousel.locator("a").last()).toBeInViewport();
    await page.keyboard.press("Home");
    await expect(previous).toBeDisabled();
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
    const images = await page.locator("#artwork-carousel img, #artist-carousel img, #guide-carousel img").evaluateAll(async nodes => {
      return Promise.all(nodes.map(async node => {
        const image = node as HTMLImageElement;
        image.loading = "eager"; await image.decode();
        const rect = image.getBoundingClientRect(), frame = image.parentElement!.getBoundingClientRect();
        return { loaded: image.naturalWidth > 0, fit: getComputedStyle(image).objectFit,
          contained: rect.left >= frame.left && rect.top >= frame.top && rect.right <= frame.right + 1 && rect.bottom <= frame.bottom + 1 };
      }));
    });
    expect(images).toHaveLength(23);
    for (const image of images) expect(image).toEqual({ loaded: true, fit: "contain", contained: true });
  }
  await page.setViewportSize({ width: 1440, height: 1000 });
  await carousel.locator("a").first().click();
  await expect(page).toHaveURL(/\/guides\/louvre#work-4a399ca8-712b-40db-8493-6d89b653773e$/);
  await expect(page.locator("#work-4a399ca8-712b-40db-8493-6d89b653773e")).toBeInViewport();
});
