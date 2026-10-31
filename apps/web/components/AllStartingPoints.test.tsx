import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import type { AtlasMetadata } from "@/lib/atlas";
import presets from "../../server/internal/atlas/presets.json";
import { AllStartingPoints } from "./AllStartingPoints";

const metadata: AtlasMetadata = { presets, types: [], regions: [], continents: [], bounds: { start: -12000, end: 2000 }, defaultPreset: "" };
afterEach(cleanup);

it("makes every moment reachable exactly once before search", () => {
  const select = vi.fn();
  const { container } = render(<AllStartingPoints metadata={metadata} select={select} />);
  for (const preset of presets) expect(screen.getAllByRole("button", { name: preset.name })).toHaveLength(1);
  const cards = container.querySelectorAll(".all-story-grid .all-start-card");
  expect(cards).toHaveLength(presets.length);
  expect(cards[0]).toHaveAccessibleName("Women’s rights");
  expect(cards[2]).toHaveAccessibleName("The Second World War");
  expect(cards[3]).toHaveAccessibleName("World War II: Asia and Africa");
  fireEvent.click(cards[0]);
  expect(select).toHaveBeenCalledWith("womens-rights");
  fireEvent.click(screen.getByRole("button", { name: "The First World War" }));
  expect(select).toHaveBeenCalledWith("first-world-war");
});

it("combines topic search and era selection and recovers from no results", () => {
  render(<AllStartingPoints metadata={metadata} select={vi.fn()} />);
  fireEvent.change(screen.getByRole("searchbox", { name: "Find a moment" }), { target: { value: "world war" } });
  expect(screen.getByRole("button", { name: "The First World War" })).toBeVisible();
  expect(screen.queryByRole("button", { name: "The Renaissance" })).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: presets.find(p => p.id === "writing")!.group }));
  expect(screen.getByText("No moments match this search.")).toBeVisible();
  fireEvent.click(screen.getByRole("button", { name: "Show all moments" }));
  expect(screen.getByRole("searchbox")).toHaveValue("");
  expect(screen.getByRole("button", { name: "The Renaissance" })).toBeVisible();
});
