import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { ExhibitionFilters } from "./ExhibitionFilters";

const push = vi.hoisted(() => vi.fn());
vi.mock("next/navigation", () => ({ useRouter: () => ({ push }) }));
beforeEach(() => { window.matchMedia = vi.fn().mockReturnValue({ matches: false, addEventListener() {}, removeEventListener() {} }); });
afterEach(() => { cleanup(); push.mockClear(); });

function destination() { return new URL(push.mock.calls.at(-1)![0], "http://localhost").searchParams; }

it("applies country and city with existing filters and restarts pagination", () => {
  render(<ExhibitionFilters initialQuery="q=Prints&start=1800&after=old-page" />);
  fireEvent.change(screen.getByRole("textbox", { name: "Country" }), { target: { value: "France" } });
  fireEvent.change(screen.getByRole("textbox", { name: "City" }), { target: { value: "Paris" } });
  fireEvent.submit(screen.getByRole("form", { name: "Filter exhibitions" }));
  const query = destination();
  expect(query.get("country")).toBe("France");
  expect(query.get("city")).toBe("Paris");
  expect(query.get("q")).toBe("Prints");
  expect(query.get("start")).toBe("1800");
  expect(query.has("after")).toBe(false);
});

it("restores locations and removes one location without losing the other", () => {
  render(<ExhibitionFilters initialQuery="country=France&city=Paris&q=Prints&after=old-page" />);
  expect(screen.getByRole("textbox", { name: "Country" })).toHaveValue("France");
  expect(screen.getByRole("textbox", { name: "City" })).toHaveValue("Paris");
  fireEvent.click(screen.getByRole("button", { name: "Remove Country: France filter" }));
  const query = destination();
  expect(query.has("country")).toBe(false);
  expect(query.get("city")).toBe("Paris");
  expect(query.get("q")).toBe("Prints");
  expect(query.has("after")).toBe(false);
});

it("clears both location filters", () => {
  render(<ExhibitionFilters initialQuery="country=France&city=Paris" />);
  fireEvent.click(screen.getByRole("button", { name: "Clear filters" }));
  expect(destination().size).toBe(0);
});
