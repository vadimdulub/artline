import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { Museum } from "@/lib/types";
import { MuseumDetail } from "./MuseumDetail";
import { useMuseumRequest } from "./museum-state";

const exhibitionState = vi.hoisted(() => ({ total: 0, available: true }));
vi.mock("./museum-state", () => ({ useMuseumRequest: vi.fn((path: string | null, _revision: number, initial: unknown) => path?.startsWith("exhibitions?") ? { data: exhibitionState.available ? { total: exhibitionState.total } : undefined, loading: false } : { data: initial, loading: !initial }) }));
vi.mock("./use-painter-choices", () => ({ usePainterChoices: () => ({ options: [] }), workTypeOptions: [] }));
const museum: Museum = { id: "museum", slug: "museum", name: "Collection", kind: "museum", description: "", website_url: null, status: "review", venues: [], work_count: 400000, holding_count: 400000, on_view_count: 0, highlight_count: 24, highlight_source: "museum", cover: null };
beforeEach(() => { exhibitionState.total = 0; exhibitionState.available = true; window.matchMedia = vi.fn().mockReturnValue({ matches: false, addEventListener() {}, removeEventListener() {} }); });
afterEach(() => { cleanup(); vi.clearAllMocks(); window.history.replaceState(null, "", "/"); });

it.each(["artlines", "museum"] as const)("shows %s highlights distinctly and keeps gallery requests bounded", source => {
  render(<MuseumDetail slug="museum" initialMuseum={{ ...museum, highlight_source: source }} />);
  const label = source === "museum" ? "Museum highlights" : "Artlines highlights";
  expect(screen.getByRole("combobox", { name: "Sort artworks" })).toHaveValue("highlights");
  expect(screen.getByRole("combobox", { name: "Artworks per page" })).toHaveValue("24");
  fireEvent.click(screen.getByRole("button", { name: `${label}24` }));
  expect(new URLSearchParams(window.location.search).get("selection")).toBe(source);
  expect(useMuseumRequest).toHaveBeenCalledWith(`museums/museum/works?selection=${source}&sort=curated`, 0);
});

it.each(["artlines", "museum"] as const)("clears other filters when opening %s highlights while retaining layout and page size", source => {
  window.history.replaceState(null, "", "/museums/museum?q=portrait&artist=one&artist=two&movement=study&display=on_view&venue=room&work_type=print&start=1800&end=1900&unknown_date=1&image_only=1&cursor=old&view=list&limit=48");
  render(<MuseumDetail slug="museum" initialMuseum={{ ...museum, highlight_source: source }} />);
  fireEvent.click(screen.getByRole("button", { name: `${source === "museum" ? "Museum" : "Artlines"} highlights24` }));
  const params = new URLSearchParams(window.location.search);
  expect([...params.keys()].sort()).toEqual(["limit", "selection", "sort", "view"]);
  expect(params.get("selection")).toBe(source);
  expect(params.get("view")).toBe("list");
  expect(params.get("limit")).toBe("48");
  expect(useMuseumRequest).toHaveBeenCalledWith(`museums/museum/works?selection=${source}&sort=curated&limit=48`, 0);
});

it.each([false, true])("puts exhibition history after highlights when the museum has exhibitions (embedded=%s)", embedded => {
  exhibitionState.total = 1;
  render(<MuseumDetail slug="museum" initialMuseum={museum} embedded={embedded} />);
  const history = screen.getByRole("link", { name: "Exhibition history" });
  expect(history).toHaveAttribute("href", "/exhibitions?institution=museum");
  expect(history.previousElementSibling).toBe(screen.getByRole("button", { name: "Museum highlights24" }));
  expect(useMuseumRequest).toHaveBeenCalledWith("exhibitions?institution=museum&limit=1", 0);
});

it.each([true, false])("hides exhibition history without a confirmed exhibition (response available=%s)", available => {
  exhibitionState.available = available;
  render(<MuseumDetail slug="museum" initialMuseum={museum} />);
  expect(screen.queryByRole("link", { name: "Exhibition history" })).not.toBeInTheDocument();
});
