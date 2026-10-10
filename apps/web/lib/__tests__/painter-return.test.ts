import { expect, it } from "vitest";
import { painterRecordPath } from "../painter-return";
import { memberReturnTo, memberSignInPath, museumRecordPath, requiresMember } from "../member-return";

it.each([
  "/artists/claude-monet",
  "/museums",
  "/bookmarks?kind=artwork",
  "/books?book=odyssey&start=-800&end=2000",
  "/events?event=event-q123#details",
  "/all?itemType=artwork&item=11111111-1111-4111-8111-111111111111",
  "/museums/the-met?artist=monet&artist=giotto#collection",
  "/artists/artist_import?catalogue=all&art_q=Water+lilies&art_year=1900#works-painter",
  "/artists/giotto/works/11111111-1111-4111-8111-111111111111?art_images=false",
])("retains the selected painter destination %s", path => {
  expect(memberReturnTo(path)).toBe(path);
  expect(new URL(memberSignInPath(path), "https://artlines.org").searchParams.get("return_to")).toBe(path);
});

it.each([
  null, ["/artists/monet"], "/museums/../account", "/museums/%2Fexample", "/museums/" + "x".repeat(101), "https://evil.example", "//evil.example/artists/monet",
  "/artists/../account", "/artists/%2e%2e/account", "/artists/monet/extra",
  "/artists/monet\\evil", "/artists/monet\n", "/artists/monet?x=\r\nLocation:evil",
  "/api/auth/logout", "/account?return_to=/artists/monet", "/artists/" + "x".repeat(101),
  "/artists/monet?q=" + "x".repeat(768),
])("rejects unsafe or unsupported destinations %s", path => {
  expect(memberReturnTo(path)).toBeNull();
});

it("preserves supported artwork filters and discards unrelated query parameters", () => {
  expect(painterRecordPath("monet", { art_q: "Water lilies", art_images: "false", catalogue: "all", tracking: "ignored" }))
    .toBe("/artists/monet?art_images=false&art_q=Water+lilies");
  expect(painterRecordPath("monet", { art_q: "x".repeat(1000) })).toBe("/artists/monet");
  expect(memberSignInPath("//evil.example")).toBe("/account");
});

it("restarts legacy pagination while retaining the artwork selection", () => {
  expect(painterRecordPath("monet", { catalogue: "all", art_cursor: "old-scope", art_museum: "the-met", art_type: "painting" }))
    .toBe("/artists/monet?art_museum=the-met&art_type=painting");
  expect(painterRecordPath("monet", { art_cursor: "current-scope" })).toBe("/artists/monet?art_cursor=current-scope");
});

it("retains repeated museum filters while normalizing obsolete visibility options", () => {
  expect(museumRecordPath("the-met", { artist: ["monet", "giotto"], catalogue: "all", image_only: "true" })).toBe("/museums/the-met?artist=monet&artist=giotto&image_only=true");
});
it("gates museums while preserving public painter, artwork and directory links", () => {
  for (const path of ["/museums", "/museums/the-met?artist=monet"]) expect(requiresMember(path)).toBe(true);
  for (const path of ["/artists", "/", "/artists/monet?art_year=1900", "/artists/monet/works/11111111-1111-4111-8111-111111111111"]) expect(requiresMember(path)).toBe(false);
});
