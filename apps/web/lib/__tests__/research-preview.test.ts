import { afterEach, describe, expect, it, vi } from "vitest";
import { researchPreviewEnabled, researchPreviewToken } from "../research-preview";

afterEach(() => vi.unstubAllEnvs());

describe("research preview configuration", () => {
  it("requires explicit production opt-in and never supplies editor credentials", () => {
    vi.stubEnv("NODE_ENV", "production");
    vi.stubEnv("ARTLINE_RESEARCH_PREVIEW_TOKEN", "local-editor-secret");
    vi.stubEnv("ARTLINE_PUBLIC_RESEARCH_PREVIEW", "false");
    expect(researchPreviewEnabled()).toBe(false);
    vi.stubEnv("ARTLINE_PUBLIC_RESEARCH_PREVIEW", "true");
    expect(researchPreviewEnabled()).toBe(true);
    expect(researchPreviewToken()).toBe("");
  });

  it("preserves the explicit local preview", () => {
    vi.stubEnv("NODE_ENV", "development");
    vi.stubEnv("ARTLINE_PUBLIC_RESEARCH_PREVIEW", "false");
    vi.stubEnv("ARTLINE_RESEARCH_PREVIEW_TOKEN", "local-editor-secret");
    expect(researchPreviewEnabled()).toBe(true);
    expect(researchPreviewToken()).toBe("local-editor-secret");
  });

  it("does not enable preview for a malformed configuration value", () => {
    vi.stubEnv("NODE_ENV", "production");
    vi.stubEnv("ARTLINE_PUBLIC_RESEARCH_PREVIEW", "yes");
    expect(researchPreviewEnabled()).toBe(false);
  });
});
