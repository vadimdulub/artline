import { expect, test } from "@playwright/test";

test("Renaissance fitting reuses the first bounded response", async ({ page }) => {
  await page.goto("/all");
  const renaissance = page.locator(".all-start-card").filter({ hasText: "Renaissance" }).first();
  await expect(renaissance).toBeVisible();
  const requests: string[] = [];
  page.on("request", request => {
    const url = new URL(request.url());
    if (url.pathname === "/api/backend/v1/atlas") requests.push(url.search);
  });
  await renaissance.click();
  await expect.poll(() => new URL(page.url()).searchParams.get("start")).toBe("1300");
  await expect.poll(() => new URL(page.url()).searchParams.get("fit")).toBeNull();
  await expect(page.locator(".timeline-stage")).toHaveAttribute("aria-busy", "false");
  await page.waitForLoadState("networkidle");
  expect(requests).toHaveLength(1);
  expect(new URLSearchParams(requests[0]).has("fit")).toBe(false);
  await expect(page.locator(".all-lane")).toHaveCount(3);
  // Manual date changes still request freshly grouped, cursor-safe server data.
  await page.getByLabel("All start year", { exact: true }).fill("1400");
  await page.getByLabel("All start year", { exact: true }).press("Enter");
  await expect.poll(() => requests.length).toBe(2);
  await expect(page.locator(".timeline-stage")).toHaveAttribute("aria-busy", "false");
  await expect(page.getByLabel("All start year", { exact: true })).toHaveValue("1400");
});

test("discovery responses stay private while repeated reads use the backend cache", async ({ request }) => {
  const path = "/api/backend/v1/timeline?start=1100&end=2000&popular=true&women=false";
  const first = await request.get(path);
  expect(first.ok()).toBe(true);
  const expected = await first.json();
  // Production can route sequential reads to different instances. Each cache
  // warms independently; a database commit also correctly invalidates a hit.
  const statuses: string[] = [];
  for (let attempt = 0; attempt < 5; attempt++) {
    const response = await request.get(path);
    expect(response.headers()["cache-control"]).toBe("private, no-store");
    expect(await response.json()).toEqual(expected);
    statuses.push(response.headers()["x-artline-cache"]);
    if (statuses.at(-1) === "HIT") break;
  }
  expect(statuses).toContain("HIT");
});
