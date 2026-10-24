import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { Artwork } from "@/lib/types";
import Image from "next/image";
import { ArtworkDialog, ArtworkImage, ArtworkViewer } from "./ArtworkViewer";

vi.mock("./Bookmarks", () => ({ BookmarkButton: () => null }));
vi.mock("./ArtworkPalette", () => ({ ArtworkPalette: () => null }));
vi.mock("next/image", () => ({ default: vi.fn((props: Record<string, unknown>) => {
  const image = { ...props }; delete image.unoptimized;
  // eslint-disable-next-line @next/next/no-img-element
  return <img {...image} alt={String(image.alt)} />;
}) }));
const work = { id: "one", title: "Unillustrated study", media_url: null, alt_text: null, rights_status: null } as Artwork;
beforeEach(() => {
  HTMLDialogElement.prototype.showModal = function () { this.setAttribute("open", ""); };
  HTMLDialogElement.prototype.close = function () { this.removeAttribute("open"); };
});
afterEach(cleanup);

it("uses the same cached image file for thumbnails and visible covers", () => {
  const image = { ...work, media_url: "/assets/one.jpg" };
  const { rerender } = render(<ArtworkImage work={image} />);
  expect(vi.mocked(Image).mock.lastCall?.[0]).toMatchObject({ src: image.media_url, unoptimized: true, loading: "lazy", decoding: "async" });
  rerender(<ArtworkImage work={image} eager />);
  expect(screen.getByRole("img")).toHaveAttribute("loading", "eager");
  expect(vi.mocked(Image).mock.lastCall?.[0]).toMatchObject({ src: image.media_url, unoptimized: true });
});

it("shows a readable missing-image message at thumbnail and large sizes", () => {
  const { rerender } = render(<ArtworkImage work={work} number={2} />);
  expect(screen.getByText("Image not available")).toBeVisible();
  expect(screen.queryByText("02")).toBeNull();
  rerender(<ArtworkImage work={work} large />);
  expect(screen.getByText("Image not available")).toBeVisible();
  expect(screen.queryByRole("img")).toBeNull();
});
it("recovers from a broken thumbnail when navigation supplies a different image", () => {
  const { rerender } = render(<ArtworkImage work={{ ...work, media_url: "/assets/one.jpg" }} />);
  fireEvent.error(screen.getByRole("img"));
  expect(screen.getByText("Image not available")).toBeVisible();
  rerender(<ArtworkImage work={{ ...work, id: "two", media_url: "/assets/two.jpg" } as Artwork} />);
  expect(screen.getByRole("img")).toHaveAttribute("src", "/assets/two.jpg");
  expect(screen.queryByText("Image not available")).toBeNull();
});
it("keeps the artwork frame after failure and removes the enlarge action", () => {
  render(<ArtworkViewer work={{ ...work, media_url: "/assets/missing.jpg" }} />);
  fireEvent.error(screen.getByRole("img"));
  expect(screen.getByText("Image not available").closest("figure")).not.toBeNull();
  expect(screen.queryByRole("button", { name: /View larger/ })).toBeNull();
});
it("keeps details and close available for an unillustrated full-screen artwork", () => {
  const close = vi.fn();
  const { container } = render(<ArtworkDialog work={work} creator="James Ensor" close={close} details={<p>Catalogue evidence</p>} />);
  expect(screen.getByRole("status")).toHaveTextContent("Image not available");
  const summary = screen.getByText("Details");
  fireEvent.click(summary);
  expect(container.querySelector("details")).toHaveAttribute("open");
  expect(screen.getByText("Catalogue evidence")).toBeVisible();
  expect(screen.queryByRole("group", { name: "Image zoom" })).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: "Close enlarged image" }));
  expect(close).toHaveBeenCalledOnce();
});
