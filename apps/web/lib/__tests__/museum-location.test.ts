import { expect, it } from "vitest";
import { museumLocations } from "../museum-location";
import type { MuseumVenue } from "../types";

const venue = (city: string, country: string): MuseumVenue => ({ id: city, slug: city, name: city, city, country, region: "", visit_url: "" });

it("shows an institution location without requiring a venue", () => {
  expect(museumLocations({ city: "Yerevan", country: "AM", venues: [] })).toEqual(["Yerevan, Armenia"]);
});
it("uses a venue's country when the institution has no location", () => {
  expect(museumLocations({ venues: [venue("Paris", "FR")] })).toEqual(["Paris, France"]);
});
it("keeps cities and countries paired and removes repeated locations", () => {
  expect(museumLocations({ city: "Paris", country: "FR", venues: [venue("Paris", "FR"), venue("London", "GB")] })).toEqual(["Paris, France", "London, United Kingdom"]);
  expect(museumLocations({ city: "Paris", venues: [venue("London", "GB")] })).toEqual(["London, United Kingdom"]);
});
it("omits missing values without stray commas or inventing a city", () => {
  expect(museumLocations({ venues: [] })).toEqual([]);
  expect(museumLocations({ country: "AM", venues: [] })).toEqual(["Armenia"]);
  expect(museumLocations({ city: " Yerevan ", country: " ", venues: [] })).toEqual(["Yerevan"]);
});
