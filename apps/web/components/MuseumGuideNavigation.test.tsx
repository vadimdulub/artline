import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { Museum } from "@/lib/types";
import { MuseumDetail } from "./MuseumDetail";

vi.mock("./museum-state", () => ({ useMuseumRequest: (_path: string, _revision: number, initial: unknown) => ({ data: initial, loading: !initial }) }));
vi.mock("./use-painter-choices", () => ({ usePainterChoices: () => ({ options: [] }), workTypeOptions: [] }));
const museum: Museum = { id: "museum", slug: "musee-du-louvre", name: "Louvre", kind: "museum", description: "", website_url: null, status: "review", venues: [], work_count: 1, holding_count: 1, on_view_count: 0, highlight_count: 0, cover: null };
beforeEach(() => { window.matchMedia = vi.fn().mockReturnValue({ matches: false, addEventListener() {}, removeEventListener() {} }); });
afterEach(cleanup);

it("renders the existing guide as a direct, named link in a standalone collection", () => {
  render(<MuseumDetail slug={museum.slug} initialMuseum={museum} guides={[{ href: "/guides/louvre", title: "Louvre: Masterpieces" }]} />);
  expect(screen.getByRole("navigation", { name: "Museum guides" })).toBeVisible();
  expect(screen.getByRole("link", { name: "Read guide: Louvre: Masterpieces" })).toHaveAttribute("href", "/guides/louvre");
});

it("omits guide navigation when there is no matching guide", () => {
  render(<MuseumDetail slug={museum.slug} initialMuseum={museum} />);
  expect(screen.queryByRole("navigation", { name: "Museum guides" })).not.toBeInTheDocument();
});
