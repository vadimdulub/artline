import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { useState } from "react";
import { TimelineRangeControls } from "./TimelineRangeControls";

beforeEach(() => {
  vi.stubGlobal("ResizeObserver", class { observe() {} disconnect() {} });
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); });
function Dates({ onChange = vi.fn(), initial = { start: -500, end: 100 }, disabled = false }: {
  onChange?: (start: number, end: number) => void; initial?: { start: number; end: number }; disabled?: boolean;
}) {
  const [range, setRange] = useState(initial);
  return <TimelineRangeControls {...range} minimum={-12000} maximum={2000} omitYearZero disabled={disabled}
    endpoints={["12000 BCE", "2000"]} formatYear={year => year < 0 ? `${-year} BCE` : String(year)}
    onChange={(start, end) => { onChange(start, end); setRange({ start, end }); }} />;
}
it("offers date handles without year fields or date-editing buttons", () => {
  render(<Dates />);
  expect(screen.getAllByRole("slider")).toHaveLength(2);
  expect(screen.getByLabelText("Timeline start handle")).toHaveAttribute("aria-valuetext", "500 BCE");
  expect(screen.queryByRole("spinbutton")).not.toBeInTheDocument();
  expect(screen.queryByRole("button", { name: /earlier|later|edit dates|done/i })).not.toBeInTheDocument();
});
it("changes each endpoint independently with the keyboard", () => {
  const change = vi.fn(); render(<Dates onChange={change} />);
  fireEvent.keyDown(screen.getByLabelText("Timeline start handle"), { key: "ArrowRight" });
  expect(change).toHaveBeenLastCalledWith(-499, 100);
  fireEvent.keyDown(screen.getByLabelText("Timeline end handle"), { key: "ArrowLeft" });
  expect(change).toHaveBeenLastCalledWith(-499, 99);
});
it("moves from 1 BCE to 1 CE without selecting year zero", () => {
  const change = vi.fn(); render(<Dates initial={{ start: -1, end: 100 }} onChange={change} />);
  fireEvent.keyDown(screen.getByLabelText("Timeline start handle"), { key: "ArrowRight" });
  expect(change).toHaveBeenLastCalledWith(1, 100);
  expect(screen.getByLabelText("Timeline start handle")).toHaveAttribute("aria-valuenow", "1");
});
it("keeps the handles ordered and within the available dates", () => {
  const change = vi.fn(); render(<Dates onChange={change} />);
  fireEvent.keyDown(screen.getByLabelText("Timeline start handle"), { key: "End" });
  expect(change).toHaveBeenLastCalledWith(99, 100);
  fireEvent.keyDown(screen.getByLabelText("Timeline end handle"), { key: "Home" });
  expect(change).toHaveBeenLastCalledWith(99, 100);
  fireEvent.keyDown(screen.getByLabelText("Timeline start handle"), { key: "Home" });
  expect(change).toHaveBeenLastCalledWith(-12000, 100);
  fireEvent.keyDown(screen.getByLabelText("Timeline end handle"), { key: "End" });
  expect(change).toHaveBeenLastCalledWith(-12000, 2000);
});
it("supports moving the selected band with a keyboard", () => {
  const change = vi.fn(); render(<Dates onChange={change} />);
  fireEvent.keyDown(screen.getByRole("button", { name: "Move selected time range" }), { key: "ArrowLeft" });
  expect(change).toHaveBeenLastCalledWith(-501, 99);
});
it("disables the handles while interaction is unavailable", () => {
  render(<Dates disabled />);
  for (const handle of screen.getAllByRole("slider")) expect(handle).toBeDisabled();
  expect(screen.getByRole("button", { name: "Move selected time range" })).toBeDisabled();
});
