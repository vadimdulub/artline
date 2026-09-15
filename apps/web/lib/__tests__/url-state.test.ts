import { afterEach, expect, it } from "vitest";
import { popularPaintersOnly, womenArtistsOnly, queryValues, updateQuery } from "../url-state";

afterEach(() => window.history.replaceState(null, "", "/"));

it("keeps women and popularity filters independent while preserving the view", () => {
  expect(womenArtistsOnly(new URLSearchParams())).toBe(false);
  window.history.replaceState(null, "", "/?start=1800&end=1900&popular=false");
  updateQuery({ women: "true" }, true);
  let params = new URLSearchParams(window.location.search);
  expect(womenArtistsOnly(params)).toBe(true);
  expect(popularPaintersOnly(params)).toBe(false);
  expect(params.get("start")).toBe("1800");
  updateQuery({ popular: null });
  params = new URLSearchParams(window.location.search);
  expect(womenArtistsOnly(params)).toBe(true);
  expect(popularPaintersOnly(params)).toBe(true);
  updateQuery({ women: null });
  expect(womenArtistsOnly(new URLSearchParams(window.location.search))).toBe(false);
});

it("defaults to popular painters and preserves an explicit opt-out", () => {
  expect(popularPaintersOnly(new URLSearchParams())).toBe(true);
  expect(popularPaintersOnly(new URLSearchParams("popular=true"))).toBe(true);
  expect(popularPaintersOnly(new URLSearchParams("popular=false"))).toBe(false);
  window.history.replaceState(null, "", "/?popular=false&artist=giotto&start=1200");
  updateQuery({ region: ["southern-europe"] });
  expect(popularPaintersOnly(new URLSearchParams(window.location.search))).toBe(false);
  updateQuery({ popular: null });
  expect(popularPaintersOnly(new URLSearchParams(window.location.search))).toBe(true);
  expect(new URLSearchParams(window.location.search).get("artist")).toBe("giotto");
});

it("reads legacy, repeated and comma-separated region bookmarks", () => {
  expect(queryValues(new URLSearchParams("region=northern-europe"), "region")).toEqual(["northern-europe"]);
  expect(queryValues(new URLSearchParams("region=Northern-Europe,eastern-asia&region=eastern-asia&region="), "region")).toEqual(["eastern-asia", "northern-europe"]);
});
it("updates multi-select values without losing range or selected artwork", () => {
  window.history.replaceState(null, "", "/?start=1800&end=1900&artist=giotto&work=example&region=old");
  updateQuery({ region: ["northern-europe", "eastern-asia", "northern-europe"] });
  const params = new URLSearchParams(window.location.search);
  expect(params.getAll("region")).toEqual(["eastern-asia", "northern-europe"]);
  expect(params.get("start")).toBe("1800");
  expect(params.get("work")).toBe("example");
  updateQuery({ region: [] });
  expect(new URLSearchParams(window.location.search).has("region")).toBe(false);
});
