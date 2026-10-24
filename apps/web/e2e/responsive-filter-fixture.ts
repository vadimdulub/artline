import type { Page } from "@playwright/test";
import { mockMobileExplorers, mobileAtlasMetadata } from "./mobile-explorer-fixture";
// The same in-memory records serve SSR and browser requests.
// @ts-expect-error Plain JS fixture is shared with the standalone Node server.
import { directoryResponse, facets, painters } from "./responsive-api-fixture.cjs";

export async function mockResponsiveFilters(page: Page) {
  await page.route("**/*", route => ["127.0.0.1", "localhost"].includes(new URL(route.request().url()).hostname) ? route.continue() : route.abort());
  await mockMobileExplorers(page);
  await page.route("**/api/backend/v1/**", route => {
    const url = new URL(route.request().url());
    const path = url.pathname.split("/v1/")[1];
    if (route.request().method() !== "GET") return route.fulfill({ status: 405 });
    const directory = directoryResponse(url);
    if (directory) return route.fulfill({ json: directory });
    if (path === "events/facets") return route.fulfill({ json: { ...facets, regions: [{ slug: "Europe", name: "Europe", count: 1 }], countries: [{ slug: "France", name: "France", count: 1 }] } });
    if (path.endsWith("/facets")) return route.fulfill({ json: facets });
    if (path === "books/authors") return route.fulfill({ json: { items: ["Leo Tolstoy", "Virginia Woolf"], hasMore: false } });
    if (path === "painters/options" || path === "atlas/creators") {
      const choices = path === "atlas/creators" ? painters.map((p: { slug: string; name: string }) => ({ slug: `painter:${p.slug}`, name: `${p.name} · Painter` })) : painters;
      return route.fulfill({ json: { items: choices, selected: choices.filter((p: { slug: string }) => url.searchParams.getAll("selected").includes(p.slug)), has_more: false } });
    }
    if (path === "atlas/presets") return route.fulfill({ json: { ...mobileAtlasMetadata, regions: facets.regions, continents: [{ slug: "europe", name: "Europe" }] } });
    if (path === "atlas/geography") return route.fulfill({ json: { countries: facets.countries } });
    return route.fallback();
  });
}
