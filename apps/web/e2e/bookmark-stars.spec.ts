import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test("mobile stars save books and events into Account", async ({ page, request, baseURL }, info) => {
  expect((await (await request.get("/api/auth/session")).json()).local_debug).toBe(true);
  await page.setViewportSize({ width: 390, height: 844 });
  const refs = [{ kind: "book", id: "odyssey", title: "The Odyssey" }, { kind: "event", id: "event-q180548", title: "Neolithic Revolution" }];
  const query = new URLSearchParams(refs.map(ref => [ref.kind, ref.id]));
  const original = (await (await request.get(`/api/bookmarks/state?${query}`)).json()).saved as typeof refs;
  const headers = { origin: new URL(baseURL!).origin };
  try {
    for (const ref of refs) {
      await request.delete(`/api/bookmarks/${ref.kind}/${ref.id}`, { headers });
      await page.goto(`/${ref.kind}s?${ref.kind}=${ref.id}`);
      const dialog = page.getByRole("dialog", { name: `${ref.kind === "book" ? "Book" : "Event"} details`, exact: true });
      const star = dialog.getByRole("button", { name: `Save ${ref.title} to bookmarks`, exact: true });
      await expect(star).toBeEnabled();
      await expect(star).toHaveText("");
      const box = (await star.boundingBox())!;
      expect(box.width).toBeGreaterThanOrEqual(44);
      expect(box.height).toBeGreaterThanOrEqual(44);
      await star.click();
      await expect(dialog.getByRole("button", { name: `Remove ${ref.title} from bookmarks`, exact: true })).toHaveAttribute("aria-pressed", "true");
      await expect(dialog).toBeVisible();
      expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
      await dialog.getByRole("button", { name: `Close ${ref.kind} details`, exact: true }).click();
    }
    const menu = page.getByRole("button", { name: "Menu", exact: true });
    await menu.click();
    const navigation = page.getByRole("dialog", { name: "Explore Artline" });
    await expect(navigation.getByRole("link", { name: "Bookmarks", exact: true })).toHaveCount(0);
    await navigation.getByRole("link", { name: "Your account", exact: true }).click();
    await page.getByRole("main").getByRole("link", { name: "Your bookmarks", exact: true }).click();
    await expect(page).toHaveURL(/\/bookmarks$/);
    for (const ref of refs) {
      await page.getByRole("navigation", { name: "Bookmark type" }).getByRole("button", { name: `${ref.kind === "book" ? "Books" : "Events"}`, exact: true }).click();
      const card = page.locator(".bookmark-card").filter({ has: page.getByRole("heading", { name: ref.title, exact: true }) });
      await expect(card).toBeVisible();
      await expect(card.getByRole("button")).toHaveAttribute("aria-pressed", "true");
      await card.getByRole("link", { name: new RegExp(ref.title) }).click();
      await expect(page.getByRole("dialog", { name: `${ref.kind === "book" ? "Book" : "Event"} details`, exact: true })).toBeVisible();
      await page.goBack();
      await card.getByRole("button").click();
      await expect(card).toHaveCount(0);
    }
    expect((await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze()).violations).toEqual([]);
    await page.screenshot({ path: info.outputPath("bookmarks-mobile.png") });
    await page.goto("/");
    await expect(page.locator(".site-header a[href='/bookmarks']")).toHaveCount(0);
  } finally {
    for (const ref of refs) {
      const saved = original.some(item => item.kind === ref.kind && item.id === ref.id);
      await request.fetch(`/api/bookmarks/${ref.kind}/${ref.id}`, { method: saved ? "PUT" : "DELETE", headers });
    }
  }
});

test("a signed-out book star preserves the selected record through sign-in", async ({ page }) => {
  await page.route("**/api/auth/session", route => route.fulfill({ json: { enabled: true, user: null } }));
  await page.goto("/books?book=odyssey");
  const star = page.getByRole("dialog", { name: "Book details", exact: true }).getByRole("button", { name: "Save The Odyssey to bookmarks", exact: true });
  await star.click();
  const login = page.getByRole("dialog", { name: "Sign in to Artline", exact: true });
  await expect(login).toBeVisible();
  const action = await login.locator("form").getAttribute("action");
  expect(new URL(action!, "http://localhost").searchParams.get("return_to")).toBe("/books?book=odyssey");
  expect(await page.evaluate(() => JSON.parse(sessionStorage.getItem("artline:pending-bookmark")!).ref)).toEqual({ kind: "book", id: "odyssey" });
  await login.getByRole("button", { name: "Close sign-in window" }).click();
  await expect(star).toBeFocused();
  expect(await page.evaluate(() => sessionStorage.getItem("artline:pending-bookmark"))).toBeNull();
});
