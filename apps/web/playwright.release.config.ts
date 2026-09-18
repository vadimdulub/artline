import { defineConfig } from "@playwright/test";
import base from "./playwright.config";

const baseURL = process.env.ARTLINE_RELEASE_URL;
if (!baseURL || !baseURL.startsWith("https://")) {
  throw new Error("Set ARTLINE_RELEASE_URL to the explicit HTTPS release candidate.");
}

export default defineConfig({
  ...base,
  testMatch: ["release-readonly.spec.ts"],
  outputDir: "/tmp/artline-release-browser-results",
  timeout: 60000,
  expect: { timeout: 20000 },
  use: { ...base.use, baseURL },
});
