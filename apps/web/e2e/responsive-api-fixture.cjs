// In-memory, GET-only responses for responsive UI tests, including server renders.
// This service has no database, credentials, external requests, or write routes.

const facets = {
  countries: [{ slug: "FR", name: "France", count: 2 }, { slug: "NL", name: "Netherlands", count: 1 }],
  movements: [{ slug: "impressionism", name: "Impressionism", color: "#c4aa81", count: 2 }],
  regions: [{ slug: "europe", name: "Europe", count: 3 }],
  languages: [{ slug: "french", name: "French", count: 2 }],
  topics: [{ slug: "Politics", name: "Politics", count: 1 }],
  kinds: [{ slug: "Event", name: "Event", count: 1 }],
};
const painters = [
  { slug: "claude-monet", name: "Claude Monet" },
  { slug: "camille-pissarro", name: "Camille Pissarro" },
];
const artist = { id: "monet", ...painters[0], start_year: 1840, end_year: 1926, date_display: "1840–1926", movement: facets.movements[0], countries: ["FR"], artwork_count: 2, status: "published" };
const museum = { id: "museum", slug: "national-gallery", name: "National Gallery", city: "London", country: "GB", kind: "museum", description: "Paintings in the collection.", website_url: null, status: "published", venues: [{ id: "venue", slug: "main-gallery", name: "Main gallery", city: "London", country: "GB", region: "europe", visit_url: "" }], work_count: 2, holding_count: 2, on_view_count: 0, highlight_count: 1, cover: null };

function directoryResponse(url) {
  const path = url.pathname.replace(/^\/api\/(?:backend\/)?v1\//, "");
  if (path === "health") return { ok: true };
  if (path === "auth/session") return { enabled: true, user: { id: "responsive-ui", name: "UI test", email: "ui@example.invalid" } };
  if (path === "member/bookmarks") return { items: [], total: 0, next_cursor: "" };
  if (path === "artists") return { items: url.searchParams.get("q") === "no-matches" ? [] : [artist], total: 1, next_cursor: "", facets };
  if (path === "museums") return { items: [museum], total: 1, next_cursor: "", facets };
  if (path === "museums/national-gallery") return museum;
  if (path === "museums/national-gallery/works") return { items: [], total: 0, image_count: 0, next_cursor: "", facets };
  if (path === "artworks") return { items: [], total: 0, next_cursor: "" };
  if (path === "exhibitions") return { items: [], total: 0, heldTotal: 0, hasMore: false, nextCursor: "" };
  return undefined;
}

module.exports = { facets, painters, museum, directoryResponse };
