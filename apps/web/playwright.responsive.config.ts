import { defineConfig, devices } from "@playwright/test";
import { tmpdir } from "node:os";
import { join } from "node:path";

export default defineConfig({
  testDir: "./e2e",
  testMatch: ["responsive-filters.spec.ts", "responsive-member-filters.spec.ts", "mobile-explorer-layout.spec.ts", "timeline-date-controls.spec.ts", "timeline-introduction.spec.ts"],
  fullyParallel: true,
  workers: 2,
  timeout: 45000,
  expect: { timeout: 10000 },
  outputDir: join(tmpdir(), "artline-responsive-results"),
  reporter: [["list"], ["html", { outputFolder: join(tmpdir(), "artline-responsive-report"), open: "never" }], ["json", { outputFile: join(tmpdir(), "artline-responsive-report", "results.json") }]],
  use: { baseURL: "http://127.0.0.1:3097", actionTimeout: 10000, trace: "retain-on-failure", screenshot: "only-on-failure" },
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"], hasTouch: true } },
    // The existing swipe helper uses Chromium's CDP; the new filter pack is portable.
    { name: "webkit", testIgnore: "mobile-explorer-layout.spec.ts", use: { ...devices["Desktop Safari"], hasTouch: true } },
  ],
  webServer: [
    { command: "node e2e/responsive-api-fixture.mjs", url: "http://127.0.0.1:3098/api/v1/health", reuseExistingServer: false, gracefulShutdown: { signal: "SIGTERM", timeout: 5000 } },
    {
      command: "node e2e/start-responsive-web.mjs",
      stdout: "pipe",
      url: "http://127.0.0.1:3097", reuseExistingServer: false, timeout: 240000,
      gracefulShutdown: { signal: "SIGTERM", timeout: 5000 },
      env: { API_INTERNAL_URL: "http://127.0.0.1:3098", EXHIBITIONS_REVIEW_API_URL: "", ARTLINE_GOOGLE_ANALYTICS_ID: "", ARTLINE_CLOUDFLARE_WEB_ANALYTICS_TOKEN: "" },
    },
  ],
});
