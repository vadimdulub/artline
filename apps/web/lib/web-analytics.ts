// Read at request time so Cloud Run can configure analytics without rebuilding.
// This is the public site token from the JS snippet, never a Cloudflare API key.
export function cloudflareWebAnalyticsToken(): string | undefined {
  if (process.env.NODE_ENV !== "production") return undefined;
  return process.env.ARTLINE_CLOUDFLARE_WEB_ANALYTICS_TOKEN?.trim() || undefined;
}
