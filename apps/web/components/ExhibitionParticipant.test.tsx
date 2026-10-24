import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { ExhibitionParticipant } from "./ExhibitionParticipant";
import type { ExhibitionPerson } from "@/lib/exhibitions";

vi.mock("./MemberLink", () => ({ default: ({ children, href }: React.ComponentProps<"a">) => <a href={href}>{children}</a> }));
afterEach(cleanup);

const artist: ExhibitionPerson = { id: "participant", name: "Elisabeth Jerichau-Baumann", role: "represented_artist", artist_id: "artist", artist_slug: "elisabeth-jerichau-baumann" };

it("shows the saved key artwork with its title and correct credit", () => {
  render(<ul><ExhibitionParticipant person={{ ...artist, image: "/assets/artworks/key.jpg", imageKind: "artwork", imageTitle: "Young Mother and her Child", imageWidth: 700, imageHeight: 500, imageCredit: "Nationalmuseum", imageLicense: "Public domain" }} /></ul>);
  const image = screen.getByRole("img", { name: "Young Mother and her Child — Elisabeth Jerichau-Baumann" });
  expect(image).toHaveAttribute("src", expect.stringContaining("/assets/artworks/key.jpg"));
  expect(image).toHaveAttribute("width", "700");
  expect(screen.getByRole("link", { name: artist.name })).toHaveAttribute("href", `/artists/${artist.artist_slug}`);
  expect(screen.getByText("represented artist")).toBeVisible();
  fireEvent.click(screen.getByText("Artwork & image credit"));
  expect(screen.getByText("Key artwork: Young Mother and her Child")).toBeVisible();
  expect(screen.getByText("Nationalmuseum · Public domain")).toBeVisible();
  expect(screen.queryByText("Portrait credit")).not.toBeInTheDocument();
});

it.each([
  { image: "/assets/artists/portrait.jpg", imageKind: "portrait" as const },
  { portrait: "/assets/artists/portrait.jpg" },
])("retains canonical and existing study portraits", picture => {
  render(<ul><ExhibitionParticipant person={{ ...artist, ...picture, imageCredit: "Portrait photographer" }} showHistory /></ul>);
  expect(screen.getByRole("img", { name: `Portrait of ${artist.name}` })).toHaveAttribute("src", expect.stringContaining("/assets/artists/portrait.jpg"));
  expect(screen.getByText("Portrait credit")).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Exhibition history" })).toHaveAttribute("href", "/exhibitions?artist=artist");
});

it("keeps missing images and failed image loads explicit", () => {
  const { rerender } = render(<ul><ExhibitionParticipant person={artist} /></ul>);
  expect(screen.getByText("Image not available")).toBeVisible();
  expect(screen.queryByText(/credit/)).not.toBeInTheDocument();
  rerender(<ul><ExhibitionParticipant person={{ ...artist, image: "/assets/artworks/missing.jpg", imageKind: "artwork" }} /></ul>);
  fireEvent.error(screen.getByRole("img"));
  expect(screen.getByText("Image not available")).toBeVisible();
});
