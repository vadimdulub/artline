import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { ArtworkPalette } from "./ArtworkPalette";
import { sampleArtworkImage } from "@/lib/artwork-palette";

vi.mock("@/lib/artwork-palette", async importOriginal => ({ ...await importOriginal<typeof import("@/lib/artwork-palette")>(), sampleArtworkImage: vi.fn() }));
const sample = vi.mocked(sampleArtworkImage);
const red = new Uint8ClampedArray([255, 0, 0, 255]);
const blue = new Uint8ClampedArray([0, 0, 255, 255]);
beforeEach(() => { sample.mockReset(); sample.mockResolvedValue(red); });
afterEach(cleanup);

it("automatically shows eight colors without a toggle or count selector", async () => {
  sample.mockResolvedValueOnce(new Uint8ClampedArray([[255, 0, 0], [0, 255, 0], [0, 0, 255], [255, 255, 255], [0, 0, 0], [255, 0, 255], [255, 128, 0], [128, 128, 128]].flatMap(rgb => [...rgb, 255])));
  render(<ArtworkPalette src="/assets/artworks/a.jpg" />);
  await screen.findByRole("button", { name: /Copy #FF0000/ });
  expect(screen.getAllByRole("button", { name: /^Copy #/ })).toHaveLength(8);
  expect(screen.queryByRole("combobox")).not.toBeInTheDocument();
  expect(screen.queryByRole("button", { name: "Colors" })).not.toBeInTheDocument();
  expect(screen.queryByText(/Approximate image colors/)).not.toBeInTheDocument();
  expect(sample).toHaveBeenCalledTimes(1);
});

it("discards a slow response when navigating to another image", async () => {
  let resolve!: (value: Uint8ClampedArray) => void;
  sample.mockImplementationOnce(() => new Promise(done => { resolve = done; })).mockResolvedValueOnce(blue);
  const view = render(<ArtworkPalette src="/assets/artworks/a.jpg" />);
  const oldSignal = sample.mock.calls[0][1];
  view.rerender(<ArtworkPalette src="/assets/artworks/b.jpg" />);
  expect(oldSignal.aborted).toBe(true);
  await screen.findByRole("button", { name: /Copy #0000FF/ });
  await act(async () => resolve(red));
  expect(screen.queryByRole("button", { name: /Copy #FF0000/ })).not.toBeInTheDocument();
});

it("offers a working retry after image failure", async () => {
  sample.mockRejectedValueOnce(new Error("Unavailable"));
  render(<ArtworkPalette src="/assets/artworks/a.jpg" />);
  fireEvent.click(await screen.findByRole("button", { name: "Try again" }));
  await screen.findByRole("button", { name: /Copy #FF0000/ });
  expect(sample).toHaveBeenCalledTimes(2);
});

it("copies the chosen HEX and provides selectable text if clipboard permission is denied", async () => {
  const writeText = vi.fn().mockResolvedValueOnce(undefined).mockRejectedValueOnce(new Error("Denied"));
  Object.defineProperty(navigator, "clipboard", { value: { writeText }, configurable: true });
  render(<ArtworkPalette src="/assets/artworks/a.jpg" />);
  const swatch = await screen.findByRole("button", { name: /Copy #FF0000/ });
  fireEvent.click(swatch);
  await screen.findByText("#FF0000 copied");
  expect(writeText).toHaveBeenCalledWith("#FF0000");
  fireEvent.click(swatch);
  const input = await screen.findByRole("textbox", { name: "Copy HEX value" });
  await waitFor(() => expect(input).toHaveFocus());
  expect(input).toHaveValue("#FF0000");
  expect((input as HTMLInputElement).selectionEnd).toBe(7);
  fireEvent.keyDown(input, { key: "Escape" });
  expect(screen.queryByRole("textbox", { name: "Copy HEX value" })).not.toBeInTheDocument();
  expect(swatch).toHaveFocus();
});
