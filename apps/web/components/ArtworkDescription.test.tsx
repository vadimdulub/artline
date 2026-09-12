import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { ArtworkDescription } from "./ArtworkDescription";
import type { Artwork } from "@/lib/types";

const request = vi.hoisted(() => vi.fn(() => ({ data: undefined, error: undefined, loading: false })));
vi.mock("./museum-state", () => ({ useMuseumRequest: request }));
afterEach(() => { cleanup(); request.mockClear(); });
function open(container: HTMLElement) {
  const details = container.querySelector("details")!;
  act(() => { details.open = true; fireEvent(details, new Event("toggle")); });
}
it("loads one description only after the disclosure is opened", () => {
  const work = { id: "one" } as Artwork;
  const { container } = render(<ArtworkDescription work={work} detailPath="artists/painter/works/one" />);
  expect(request).toHaveBeenLastCalledWith(null, "", 0);
  open(container);
  expect(request).toHaveBeenLastCalledWith("artists/painter/works/one", "", 0);
});
it("renders factual markdown without HTML or remote image embeds", () => {
  const work = { id: "one", description_md: "Museum **description**. [Source](https://www.nga.gov/)\n\n<img src='https://example.invalid/track'>\n\n![tracking](https://example.invalid/track)\n\n[Unsafe](javascript:alert(1))" } as Artwork;
  const { container } = render(<ArtworkDescription work={work} detailPath="unused" />);
  open(container);
  expect(screen.getByText("description")).toBeVisible();
  expect(screen.getByRole("link", { name: "Source" })).toHaveAttribute("href", "https://www.nga.gov/");
  expect(container.querySelector("img")).toBeNull();
  expect(container.querySelector('a[href^="javascript:"]')).toBeNull();
  expect(request).toHaveBeenLastCalledWith(null, "", 0);
});
