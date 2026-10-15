import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { useState } from "react";
import { TimelineRangeControls } from "./TimelineRangeControls";

beforeEach(() => {
  vi.stubGlobal("ResizeObserver", class { observe() {} disconnect() {} });
  window.matchMedia = vi.fn().mockReturnValue({ matches: true, addEventListener: vi.fn(), removeEventListener: vi.fn() });
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); });
function Dates({ onChange = vi.fn() }: { onChange?: (start: number, end: number) => void }) {
  const [range, setRange] = useState({ start: -500, end: 100 });
  return <TimelineRangeControls {...range} minimum={-12000} maximum={2000} omitYearZero endpoints={["12000 BCE", "2000"]}
    formatYear={year => year < 0 ? `${-year} BCE` : String(year)}
    onChange={(start, end) => { onChange(start, end); setRange({ start, end }); }} />;
}
it("starts with a labelled, collapsed mobile date editor", () => {
  const { container } = render(<Dates />);
  const toggle = screen.getByRole("button", { name: "Edit dates: 500 BCE to 100" });
  expect(toggle).toHaveAttribute("aria-expanded", "false");
  expect(container.querySelector(".range-editor")).toHaveAttribute("id", toggle.getAttribute("aria-controls"));
  fireEvent.click(toggle);
  expect(toggle).toHaveAttribute("aria-expanded", "true");
  expect(toggle).toHaveAccessibleName("Done editing dates");
});
it("commits a complete year pair and updates the collapsed range", () => {
  const change = vi.fn(); render(<Dates onChange={change} />);
  const toggle = screen.getByRole("button", { name: /Edit dates/ }); fireEvent.click(toggle);
  fireEvent.input(screen.getByLabelText("Start year"), { target: { value: "1500" } });
  fireEvent.input(screen.getByLabelText("End year"), { target: { value: "1600" } });
  fireEvent.keyDown(screen.getByLabelText("End year"), { key: "Enter" });
  expect(change).toHaveBeenCalledExactlyOnceWith(1500, 1600);
  fireEvent.click(toggle);
  expect(toggle).toHaveAccessibleName("Edit dates: 1500 to 1600");
});
it("Escape discards an invalid draft, closes dates, and restores focus", () => {
  const change = vi.fn(); render(<Dates onChange={change} />);
  const toggle = screen.getByRole("button", { name: /Edit dates/ }); fireEvent.click(toggle);
  const from = screen.getByLabelText("Start year");
  fireEvent.input(from, { target: { value: "0" } }); fireEvent.keyDown(from, { key: "Enter" });
  expect(screen.getByRole("alert")).toHaveTextContent("no year zero");
  fireEvent.keyDown(from, { key: "Escape" });
  expect(toggle).toHaveAttribute("aria-expanded", "false"); expect(toggle).toHaveFocus();
  expect(from).toHaveValue(-500); expect(change).not.toHaveBeenCalled();
});
it("Escape inside the date editor does not dismiss the containing full view", () => {
  const parent = vi.fn(); render(<div onKeyDown={parent}><Dates /></div>);
  fireEvent.click(screen.getByRole("button", { name: /Edit dates/ }));
  fireEvent.keyDown(screen.getByLabelText("End year"), { key: "Escape" });
  expect(parent).not.toHaveBeenCalled();
});
it("Done commits a draft once without relying on a field blur", () => {
  const change = vi.fn(); render(<Dates onChange={change} />);
  const toggle = screen.getByRole("button", { name: /Edit dates/ }); fireEvent.click(toggle);
  fireEvent.input(screen.getByLabelText("Start year"), { target: { value: "1500" } });
  fireEvent.input(screen.getByLabelText("End year"), { target: { value: "1600" } });
  fireEvent.click(toggle);
  expect(change).toHaveBeenCalledExactlyOnceWith(1500, 1600);
  expect(toggle).toHaveAttribute("aria-expanded", "false"); expect(toggle).toHaveFocus();
});
it("Done keeps invalid dates open for correction", () => {
  const change = vi.fn(); render(<Dates onChange={change} />);
  const toggle = screen.getByRole("button", { name: /Edit dates/ }); fireEvent.click(toggle);
  fireEvent.input(screen.getByLabelText("Start year"), { target: { value: "0" } });
  fireEvent.click(toggle);
  expect(toggle).toHaveAttribute("aria-expanded", "true");
  expect(screen.getByRole("alert")).toHaveTextContent("no year zero");
  expect(change).not.toHaveBeenCalled();
});
