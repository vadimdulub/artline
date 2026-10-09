import { expect, it } from "vitest";
import { painterRecordPath, painterReturnTo, painterSignInPath } from "../painter-return";

it.each([
  "/artists/claude-monet",
  "/artists/artist_import?catalogue=all&art_q=Water+lilies&art_year=1900#works-painter",
  "/artists/giotto/works/11111111-1111-4111-8111-111111111111?art_images=false",
])("retains the selected painter destination %s", path => {
  expect(painterReturnTo(path)).toBe(path);
  expect(new URL(painterSignInPath(path), "https://artlines.org").searchParams.get("return_to")).toBe(path);
});

it.each([
  null, ["/artists/monet"], "https://evil.example", "//evil.example/artists/monet",
  "/artists/../account", "/artists/%2e%2e/account", "/artists/monet/extra",
  "/artists/monet\\evil", "/artists/monet\n", "/artists/monet?x=\r\nLocation:evil",
  "/api/auth/logout", "/account?return_to=/artists/monet", "/artists/" + "x".repeat(101),
  "/artists/monet?q=" + "x".repeat(768),
])("rejects unsafe or unsupported destinations %s", path => {
  expect(painterReturnTo(path)).toBeNull();
});

it("preserves supported artwork filters and discards unrelated query parameters", () => {
  expect(painterRecordPath("monet", { art_q: "Water lilies", art_images: "false", catalogue: "all", tracking: "ignored" }))
    .toBe("/artists/monet?art_images=false&art_q=Water+lilies");
  expect(painterRecordPath("monet", { art_q: "x".repeat(1000) })).toBe("/artists/monet");
  expect(painterSignInPath("//evil.example")).toBe("/account");
});

it("restarts legacy pagination while retaining the artwork selection", () => {
  expect(painterRecordPath("monet", { catalogue: "all", art_cursor: "old-scope", art_museum: "the-met", art_type: "painting" }))
    .toBe("/artists/monet?art_museum=the-met&art_type=painting");
  expect(painterRecordPath("monet", { art_cursor: "current-scope" })).toBe("/artists/monet?art_cursor=current-scope");
});
