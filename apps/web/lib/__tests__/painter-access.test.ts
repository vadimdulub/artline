import { beforeEach, expect, it, vi } from "vitest";
vi.mock("@/lib/member-session", () => ({ getMemberSession: vi.fn(), requireMemberSession: vi.fn() }));
vi.mock("@/lib/server-api", () => ({ getArtist: vi.fn(), getArtistArtwork: vi.fn(), getArtistIdentity: vi.fn(), getMuseum: vi.fn(), getMuseumDirectory: vi.fn().mockResolvedValue(null) }));
vi.mock("@/lib/museum-publications", () => ({ getMuseumPublications: vi.fn().mockResolvedValue({ items: [], next_cursor: "" }), getPublishedMuseum: vi.fn() }));
vi.mock("@/lib/content", () => ({ getPainterEssay: vi.fn() }));
vi.mock("next/navigation", () => ({ redirect: (path: string) => { throw new Error(`redirect:${path}`); }, notFound: () => { throw new Error("not found"); }, permanentRedirect: vi.fn() }));
import ArtistPage, { generateMetadata as painterMetadata } from "../../app/artists/[slug]/page";
import ArtworkPage, { generateMetadata as artworkMetadata } from "../../app/artists/[slug]/works/[artworkId]/page";
import MuseumsPage from "../../app/museums/page";
import MuseumPage, { generateMetadata as museumMetadata } from "../../app/museums/[slug]/page";
import AccountPage from "../../app/account/page";
import { getMuseumPublications } from "../museum-publications";
import { getMemberSession, requireMemberSession } from "../member-session";
import { getArtist, getArtistArtwork, getArtistIdentity, getMuseum, getMuseumDirectory } from "../server-api";

const props = { params: Promise.resolve({ slug: "monet", artworkId: "11111111-1111-4111-8111-111111111111" }), searchParams: Promise.resolve({ art_year: "1900" }) };
beforeEach(() => {
  vi.resetAllMocks();
  vi.mocked(getMuseumDirectory).mockResolvedValue(null);
  vi.mocked(getMuseumPublications).mockResolvedValue({ items: [], next_cursor: "" });
  vi.mocked(getMuseum).mockResolvedValue({ id: "museum", slug: "monet", name: "Museum", description: "A collection", venues: [], work_count: 1, cover: null } as never);
  const artist = { slug: "monet", display_name: "Claude Monet", status: "review", aliases: [], timeline_display: "1840–1926" } as never;
  vi.mocked(getArtist).mockResolvedValue(artist);
  vi.mocked(getArtistIdentity).mockResolvedValue(artist);
  vi.mocked(getArtistArtwork).mockResolvedValue({ id: "11111111-1111-4111-8111-111111111111", title: "Water lilies", date_display: "1900", citations: [], attribution_role: "primary" } as never);
});
it.each([ArtistPage, ArtworkPage])("renders public artist and artwork records without requiring a session", async Page => {
  vi.mocked(requireMemberSession).mockRejectedValue(new Error("sign in"));
  await Page(props);
  expect(requireMemberSession).not.toHaveBeenCalled();
  expect(getMemberSession).not.toHaveBeenCalled();
});
it.each([painterMetadata, artworkMetadata])("keeps artist and artwork metadata public and indexable", async metadata => {
  expect(await metadata(props)).toMatchObject({ robots: { index: true } });
  expect(getMemberSession).not.toHaveBeenCalled();
});
it.each([MuseumsPage])("requires login before rendering the museum directory", async Page => {
  vi.mocked(requireMemberSession).mockRejectedValue(new Error("sign in"));
  await expect(Page(props)).rejects.toThrow("sign in");
  expect(requireMemberSession).toHaveBeenCalledWith(expect.stringMatching(/^\/museums/));
  expect(getMuseum).not.toHaveBeenCalled();
});
it("renders public museum pages and indexable metadata without session access", async () => {
  vi.mocked(requireMemberSession).mockRejectedValue(new Error("sign in"));
  await MuseumPage(props);
  expect(await museumMetadata(props)).toMatchObject({ robots: { index: true } });
  expect(requireMemberSession).not.toHaveBeenCalled();
  expect(getMemberSession).not.toHaveBeenCalled();
});
it("returns existing members to the selected museum and its filters", async () => {
  vi.mocked(getMemberSession).mockResolvedValue({ user: { id: "member", name: "Reader", email: "reader@example.org" } });
  await expect(AccountPage({ searchParams: Promise.resolve({ return_to: "/museums/the-met?artist=monet" }) })).rejects.toThrow("redirect:/museums/the-met?artist=monet");
});
it("rejects an external return destination", async () => {
  await AccountPage({ searchParams: Promise.resolve({ return_to: "https://evil.example" }) });
  expect(getMemberSession).not.toHaveBeenCalled();
});
