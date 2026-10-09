import { act, cleanup, render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { apiRequest } from "@/lib/api";
import type { BookDetails, BookSummary } from "@/lib/books";
import { BookDrawer } from "./BookDrawer";
vi.mock("@/lib/api", async original => ({ ...await original<typeof import("@/lib/api")>(), apiRequest: vi.fn() }));
vi.mock("./RecordDrawer", () => ({ RecordDrawer: ({ children }: { children: React.ReactNode }) => <div>{children}</div> }));
vi.mock("./BookCover", () => ({ BookCover: () => <div>Cover</div> }));
afterEach(() => { cleanup(); vi.mocked(apiRequest).mockReset(); });
const summary: BookSummary = { summary: true, id: "book", title: "Book title", author: "Writer", years: "1900", startYear: 1900, endYear: 1900, approximate: false };
const detail: BookDetails = { ...summary, summary: undefined, description: "Detailed source-backed description", era: "Modern", theme: "History", coverTone: "", coverInk: "", coverMark: "", creators: [], sourceUrl: "", dateBasis: "", selectionBasis: "", status: "review" };
it("fetches full details for a timeline summary", async () => {
  vi.mocked(apiRequest).mockResolvedValue(detail);
  render(<BookDrawer id="book" items={[summary]} close={() => {}} select={() => {}} />);
  expect(await screen.findByText(detail.description)).toBeVisible();
  expect(apiRequest).toHaveBeenCalledWith("books/book", expect.objectContaining({ signal: expect.any(AbortSignal) }));
});
it("keeps complete legacy list records without a second request", async () => {
  render(<BookDrawer id="book" items={[detail]} close={() => {}} select={() => {}} />);
  expect(screen.getByText(detail.description)).toBeVisible();
  expect(apiRequest).not.toHaveBeenCalled();
});
it("does not show a previous book while new summary details are loading", async () => {
  vi.mocked(apiRequest).mockResolvedValueOnce(detail).mockImplementationOnce(() => new Promise(() => {}));
  const { rerender } = render(<BookDrawer id="book" items={[summary]} close={() => {}} select={() => {}} />);
  await screen.findByText(detail.description);
  await act(async () => rerender(<BookDrawer id="next" items={[{ ...summary, id: "next" }]} close={() => {}} select={() => {}} />));
  await waitFor(() => expect(screen.queryByText(detail.description)).not.toBeInTheDocument());
});
