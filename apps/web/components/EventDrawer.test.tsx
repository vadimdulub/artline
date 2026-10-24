import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { apiRequest } from "@/lib/api";
import type { HistoricalEvent } from "@/lib/events";
import { EventDrawer } from "./EventDrawer";

vi.mock("@/lib/api", async original => ({ ...await original<typeof import("@/lib/api")>(), apiRequest: vi.fn() }));
vi.mock("./RecordDrawer", () => ({ RecordDrawer: ({ children }: { children: React.ReactNode }) => <div>{children}</div> }));
vi.mock("./Bookmarks", () => ({ BookmarkButton: () => null }));
afterEach(() => { cleanup(); vi.mocked(apiRequest).mockReset(); });

const event: HistoricalEvent = {
  id: "event-q689128", sourceId: "Q689128", sourceRevision: 1, sourceUrl: "https://www.wikidata.org/wiki/Q689128",
  title: "Haitian Revolution", description: "", significance: "", years: "1791–1804", startYear: 1791, endYear: 1804,
  approximate: false, dateBasis: "", kind: "Event", topics: [], countries: [], regions: [], geographyBasis: "",
  locations: [], people: [], sources: [], connections: [], top100: true, selectionBasis: "", status: "review",
  image: { imageUrl: "/assets/artworks/battle.jpg", sourceUrl: "https://commons.wikimedia.org/wiki/File:Battle.jpg",
    label: "Battle of San Domingo · later painting, 1845", credit: "January Suchodolski", license: "Public domain",
    licenseUrl: "https://creativecommons.org/publicdomain/mark/1.0/", checkedAt: "2026-10-12",
    artwork: { id: "work", title: "Battle of San Domingo", href: "/artists/january-suchodolski/works/work" } },
};

it("links both the reproduction and caption to the Artline artwork, preserving the later date and separate source", async () => {
  vi.mocked(apiRequest).mockResolvedValue(event);
  render(<EventDrawer id={event.id} close={() => {}} />);
  const imageLink = await screen.findByRole("link", { name: "View Battle of San Domingo in Artline" });
  expect(imageLink).toHaveAttribute("href", event.image!.artwork!.href);
  expect(imageLink).not.toHaveAttribute("target");
  expect(screen.getByRole("img")).toHaveAttribute("src", event.image!.imageUrl);
  expect(screen.getByRole("link", { name: event.image!.label })).toHaveAttribute("href", event.image!.artwork!.href);
  expect(screen.getByRole("link", { name: "Image source" })).toHaveAttribute("href", event.image!.sourceUrl);
  expect(screen.getByText("1791–1804", { selector: "header p" })).toBeVisible();
});

it("keeps the artwork caption usable if its reproduction cannot load", async () => {
  vi.mocked(apiRequest).mockResolvedValue(event);
  render(<EventDrawer id={event.id} close={() => {}} />);
  fireEvent.error(await screen.findByRole("img"));
  expect(screen.queryByRole("img")).not.toBeInTheDocument();
  expect(screen.getByRole("link", { name: event.image!.label })).toHaveAttribute("href", event.image!.artwork!.href);
});

it("retains an unmatched historical illustration without inventing an artwork link", async () => {
  vi.mocked(apiRequest).mockResolvedValue({ ...event, image: { ...event.image, artwork: undefined } });
  render(<EventDrawer id={event.id} close={() => {}} />);
  expect(await screen.findByRole("link", { name: event.image!.label })).toHaveAttribute("href", event.image!.sourceUrl);
  expect(screen.queryByRole("link", { name: /in Artline/ })).not.toBeInTheDocument();
});

it("hides photographic context in the paintings-only All view", async () => {
  vi.mocked(apiRequest).mockResolvedValue({ ...event, image: { ...event.image, artwork: undefined, label: "Historical photograph" } });
  render(<EventDrawer paintingsOnly id={event.id} close={() => {}} />);
  await screen.findByRole("heading", { name: event.title });
  expect(screen.queryByRole("img")).not.toBeInTheDocument();
  expect(screen.queryByText("Historical photograph")).not.toBeInTheDocument();
});

it("retains a canonical painting and its source in the All view", async () => {
  vi.mocked(apiRequest).mockResolvedValue(event);
  render(<EventDrawer paintingsOnly id={event.id} close={() => {}} />);
  expect(await screen.findByRole("img")).toHaveAttribute("src", event.image!.imageUrl);
  expect(screen.getByRole("link", { name: "Image source" })).toHaveAttribute("href", event.image!.sourceUrl);
});
