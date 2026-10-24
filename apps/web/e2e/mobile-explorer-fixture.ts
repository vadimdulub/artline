import type { Page } from "@playwright/test";
import { readFile } from "node:fs/promises";
import { join } from "node:path";
import type { AtlasDefinition, AtlasItem, AtlasMetadata, AtlasResponse } from "../lib/atlas";
import type { BooksResponse } from "../lib/books";
import covers from "../../server/internal/books/cover-selection.json";
import { booksFixture } from "./books-fixture";

// Bounded browser-only responses. No catalogue, account, or research-job writes.
// Snapshot of six existing Louvre guide objects. Keep this fixture self-contained:
// generated guide content is not tracked in Git and is unavailable in clean clones.
const artworks: AtlasItem[] = [
  { id: "4a399ca8-712b-40db-8493-6d89b653773e", title: "Mona Lisa", context: "Leonardo da Vinci", startYear: 1503, endYear: 1519, years: "1503–1519", media_url: "/assets/artworks/imported/wikipedia-painter-by-painter-20260914/4a399ca8-712b-40db-8493-6d89b653773e-221294be0cea91fb.jpg" },
  { id: "fa6cb836-f59c-41a7-8d8f-8e468428e6b2", title: "The Wedding at Cana", context: "Paolo Veronese", startYear: 1562, endYear: 1563, years: "1562–1563", media_url: "/assets/artworks/wikiart-louvre-20261006/57727609edc2cb3880d01b38-814a88239b1a19e2.jpg" },
  { id: "ea796eac-7c7f-4b84-b354-e35bc093f083", title: "The Cheat with the Ace of Diamonds", context: "Georges de La Tour", startYear: 1636, endYear: 1640, years: "c. 1636–1640", media_url: "/assets/artworks/wikiart-louvre-20261006/57727296edc2cb3880c581ce-58167b4aa45393f2.jpg" },
  { id: "0e901d0b-c217-4865-bbd9-3fad82491be7", title: "Baldassare Castiglione", context: "Raphael", startYear: 1514, endYear: 1515, years: "c. 1514–1515", media_url: "/assets/artworks/wikiart-louvre-20261006/577271f9edc2cb3880c37cd0-fa7b76a32e98af86.jpg" },
  { id: "0429297d-fccc-495f-9d13-ca353ecb168e", title: "The Virgin of Chancellor Rolin", context: "Jan van Eyck", startYear: 1430, endYear: 1435, years: "c. 1430–1435", media_url: "/assets/artworks/wikiart-louvre-20261006/57727019edc2cb3880bcf09a-4d296a5c829754b5.jpg" },
  { id: "71916124-81c9-4df0-814d-8eca990f7cbf", title: "La Belle Jardinière", context: "Raphael", startYear: 1507, endYear: 1507, years: "1507", media_url: "/assets/artworks/wikiart-louvre-20261006/577271fdedc2cb3880c383ea-216a27312d7bf442.jpg" },
].map(work => ({ ...work, type: "artwork", approximate: false, alt_text: work.title }));
const types: AtlasDefinition[] = [
  { key: "artwork", name: "Artworks", singular: "Artwork", dateLabel: "Created", cutoff: 1970, color: "#c4aa81" },
  { key: "book", name: "Books", singular: "Book", dateLabel: "Published", cutoff: 2000, color: "#76b8b5" },
  { key: "event", name: "Events", singular: "Event", dateLabel: "Occurred", cutoff: 2000, color: "#b4bb80" },
];
const metadata: AtlasMetadata = {
  bounds: { start: -12000, end: 2000 }, defaultPreset: "", types, regions: [], continents: [],
  presets: [{ id: "renaissance", name: "The Renaissance", group: "History", description: "Art, books and events from this period.", startingScope: "Europe", startingHighlights: false, period: { start: 1300, end: 1650 }, context: { start: 1300, end: 1650 }, sources: [] }],
};
export { metadata as mobileAtlasMetadata };

export async function mockMobileExplorers(page: Page) {
  // Optional exact-object copies for visual review; the default also exercises
  // the missing-image state without any external image or storage dependency.
  await page.route("**/_next/image?**", async route => {
    const imagePath = new URL(route.request().url()).searchParams.get("url");
    const work = artworks.find(item => item.media_url === imagePath);
    const imageDirectory = process.env.ARTLINE_MOBILE_IMAGE_DIR;
    if (!work || !imageDirectory) return route.fulfill({ status: 404 });
    return route.fulfill({ contentType: "image/jpeg", body: await readFile(join(imageDirectory, `${work.id}.jpg`)) });
  });
  await page.route("**/api/auth/session", route => route.fulfill({ json: { enabled: true, user: null } }));
  await page.route("**/api/backend/v1/**", route => {
    const url = new URL(route.request().url()), params = url.searchParams;
    const path = url.pathname.split("/v1/")[1];
    const range = { start: Number(params.get("start") ?? (path === "books" ? -5000 : path === "atlas" ? 1300 : -12000)), end: Number(params.get("end") ?? (path === "atlas" ? 1650 : 2000)) };
    if (route.request().method() !== "GET") return route.fulfill({ status: 405 });
    if (path === "atlas/presets") return route.fulfill({ json: metadata });
    if (path === "atlas/geography") return route.fulfill({ json: { countries: [] } });
    if (path === "atlas/creators" || path === "painters/options") return route.fulfill({ json: { items: [], selected: [], has_more: false } });
    if (path.endsWith("/facets")) return route.fulfill({ json: { countries: [], movements: [], languages: [], regions: [], kinds: [], topics: [] } });
    if (path === "books/authors") return route.fulfill({ json: { items: [], hasMore: false } });
    if (path === "atlas") {
      const selected = params.getAll("type");
      const lanes = types.filter(type => !selected.length || selected.includes(type.key)).map(type => ({
        ...type, mode: "individual" as const, total: type.key === "artwork" ? artworks.length : 1, density: [], nextCursor: "",
        items: type.key === "artwork" ? artworks : [{ id: type.key, type: type.key, title: type.key === "book" ? "Utopia" : "Council of Trent", context: type.key === "book" ? "Thomas More" : "", startYear: type.key === "book" ? 1516 : 1545, endYear: type.key === "book" ? 1516 : 1563, years: type.key === "book" ? "1516" : "1545–1563", approximate: false }],
      }));
      return route.fulfill({ json: { bounds: metadata.bounds, range, lanes, total: lanes.reduce((sum, lane) => sum + lane.total, 0), ticks: [] } satisfies AtlasResponse });
    }
    if (path === "books") {
      const items = booksFixture.slice(-6).map(book => ({ ...book, cover: covers.find(cover => cover.bookId === book.id) }));
      const authors = [{ id: "author", name: "Leo Tolstoy", description: "", birth: "1828", death: "1910", sourceUrl: "", startYear: 1828, endYear: 1910, lifespan: "1828–1910", approximate: false, bookCount: 2, credits: [] }];
      return route.fulfill({ json: { items, authors, total: params.get("view") === "authors" ? 1 : items.length, selectionTotal: items.length, undatedTotal: 0, hasMore: false, nextCursor: "", range, bounds: { start: -5000, end: 2000 }, periods: [], ticks: [], mode: "density", density: [] } satisfies BooksResponse });
    }
    if (path === "events") return route.fulfill({ json: { items: [{ id: "revolution", title: "French Revolution", years: "1789–1799", startYear: 1789, endYear: 1799, approximate: false, kind: "Event", topics: ["Politics"], countries: ["France"], regions: ["Europe"] }], total: 1, selectionTotal: 1, undatedTotal: 0, hasMore: false, nextCursor: "", range, bounds: metadata.bounds, ticks: [], mode: "individual", density: [], suggested_filters: [] } });
    if (path === "timeline") return route.fulfill({ json: { range, mode: "individual", items: [{ id: "leonardo", slug: "leonardo-da-vinci", name: "Leonardo da Vinci", start_year: 1452, end_year: 1519, date_display: "1452–1519", movement: { slug: "renaissance", name: "Renaissance", color: "#c4aa81" }, countries: ["IT"], artwork_count: 6, status: "published" }], bins: [], total: 1, popular_only: true, periods: [] } });
    return route.fulfill({ status: 404, json: { error: { message: "Not part of this browser fixture" } } });
  });
}
