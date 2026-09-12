// Public preview grants read access in the Go API; it never supplies editor credentials.
export function researchPreviewEnabled(): boolean {
  return process.env.ARTLINE_PUBLIC_RESEARCH_PREVIEW === "true" || Boolean(researchPreviewToken());
}

export function researchPreviewToken(): string {
  return process.env.NODE_ENV === "development" ? process.env.ARTLINE_RESEARCH_PREVIEW_TOKEN ?? "" : "";
}
