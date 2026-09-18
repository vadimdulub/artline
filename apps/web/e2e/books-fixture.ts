import type { Page } from "@playwright/test";
import seed from "../../server/internal/books/selection.json";
import type { Book, BooksResponse } from "../lib/books";

// Browser-only interaction fixtures; never inserted into a database. The live
// 10k catalogue is checked separately by books-catalogue.spec.ts.
export const booksFixture: Book[] = seed.map(book => ({ ...book, years: book.years.replaceAll(" CE", ""), status: "review", sourceUrl: "", selectionBasis: "UI fixture", dateBasis: "UI fixture", creators: [{ id: book.author, name: book.author, description: "Creator biography for the UI fixture.", birth: book.author === "Jean-Paul Sartre" ? "1905" : null, death: book.author === "Jean-Paul Sartre" ? "1980" : null, sourceUrl: "https://www.wikidata.org/" }] })).sort((a, b) => a.startYear! - b.startYear! || a.id.localeCompare(b.id));

export async function mockBooks(page: Page) {
  await page.route("**/api/backend/v1/books**", route => {
    const url = new URL(route.request().url()), params = url.searchParams;
    const path = url.pathname.split("/books")[1];
    if (path === "/facets") return route.fulfill({ json: { languages: [], countries: [], regions: [] } });
    if (path === "/authors") return route.fulfill({ json: { items: [...new Set(booksFixture.map(b => b.author))].filter(name => name.toLowerCase().includes((params.get("q") ?? "").toLowerCase())), hasMore: false } });
    if (path) {
      const book = booksFixture.find(b => b.id === path.slice(1));
      return route.fulfill(book ? { json: book } : { status: 404, json: { error: { message: "This book is not in the current selection." } } });
    }
    const start = Number(params.get("start") ?? -5000), end = Number(params.get("end") ?? 2000);
    if (!start || !end) return route.fulfill({ status: 400, json: { error: { message: "There is no year zero." } } });
    const items = booksFixture.filter(b => b.startYear! <= end && b.endYear! >= start && `${b.title} ${b.author} ${b.theme}`.toLowerCase().includes((params.get("q") ?? "").toLowerCase()) && (!params.has("author") || params.getAll("author").includes(b.author)));
    const result: BooksResponse = { items, total: items.length, selectionTotal: 17, hasMore: false, nextCursor: "", range: { start, end }, bounds: { start: -5000, end: 2000 }, periods: [{ start: -5000, end: 2000, label: "Full range" }, { start: -5000, end: -1, label: "BCE" }, { start: 1, end: 2000, label: "1–2000" }], ticks: [{ year: -2500, label: "BCE" }, ...Array.from({ length: 21 }, (_, i) => ({ year: i * 100 || 1, label: String(i * 100 || 1) }))], undatedTotal: 0, mode: "individual", density: [] };
    return route.fulfill({ json: result });
  });
}
