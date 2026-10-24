import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { Museum } from "@/lib/types";
import { MuseumDetail } from "./MuseumDetail";
import { useMuseumRequest } from "./museum-state";

vi.mock("./museum-state", () => ({ useMuseumRequest: vi.fn((_path: string, _revision: number, initial: unknown) => ({ data: initial, loading: !initial })) }));
vi.mock("./use-painter-choices", () => ({ usePainterChoices: () => ({ options: [] }), workTypeOptions: [] }));
const museum: Museum = { id: "museum", slug: "museum", name: "Collection", kind: "museum", description: "", website_url: null, status: "review", venues: [], work_count: 400000, holding_count: 400000, on_view_count: 0, highlight_count: 24, highlight_source: "artlines", cover: null };
beforeEach(() => { window.matchMedia = vi.fn().mockReturnValue({ matches: false, addEventListener() {}, removeEventListener() {} }); });
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
