import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { MapShare } from "./MapShare";
import { updateQuery } from "@/lib/url-state";
const write = vi.fn();
beforeEach(() => {
  write.mockReset(); Object.defineProperty(navigator, "clipboard", { configurable: true, value: { writeText: write } });
  window.history.replaceState(null, "", "/?canvas=map&map_record=artist:one&map_stop=chapter&map_hide=artist:two&artist=drawer#record");
});
afterEach(cleanup);
describe("map sharing", () => {
  it("copies the map selection and visibility without copying the native record drawer", async () => {
    write.mockResolvedValue(undefined); render(<MapShare compact />);
    fireEvent.click(screen.getByRole("button", { name: "Copy map link" }));
    expect(await screen.findByRole("button", { name: "Link copied" })).toBeInTheDocument();
    const url = new URL(write.mock.calls[0][0]); expect(url.searchParams.get("map_record")).toBe("artist:one");
    expect(url.searchParams.get("map_hide")).toBe("artist:two"); expect(url.searchParams.has("artist")).toBe(false); expect(url.hash).toBe("");
  });
  it("offers a selected link and returns focus when clipboard access fails", async () => {
    write.mockRejectedValue(new Error("Unavailable")); render(<MapShare compact />);
    fireEvent.click(screen.getByRole("button", { name: "Copy map link" }));
    const input = await screen.findByRole("textbox", { name: "Copy this map link" }); expect(input).toHaveFocus();
    fireEvent.keyDown(input, { key: "Escape" }); expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Copy map link" })).toHaveFocus();
  });
  it("clears copied feedback when the shared selection changes", async () => {
    write.mockResolvedValue(undefined); render(<MapShare compact />); fireEvent.click(screen.getByRole("button", { name: "Copy map link" }));
    await screen.findByRole("button", { name: "Link copied" }); act(() => updateQuery({ map_stop: "next-chapter" }));
    expect(screen.getByRole("button", { name: "Copy map link" })).toBeInTheDocument();
  });
});
