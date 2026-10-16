import { expect, it } from "vitest";
import { extractPalette, sampleArtworkImage } from "./artwork-palette";

function pixels(colors: { rgb: number[]; count: number; alpha?: number }[]) {
  return new Uint8ClampedArray(colors.flatMap(({ rgb, count, alpha = 255 }) => Array.from({ length: count }, () => [...rgb, alpha]).flat()));
}

it("keeps a solid color exact without inventing extra swatches", () => {
  expect(extractPalette(pixels([{ rgb: [123, 45, 67], count: 400 }]), 8)).toEqual([{ hex: "#7B2D43", share: 1 }]);
});

it("ranks colors by sampled area and preserves black and white", () => {
  const result = extractPalette(pixels([{ rgb: [255, 0, 0], count: 60 }, { rgb: [0, 0, 0], count: 30 }, { rgb: [255, 255, 255], count: 10 }]));
  expect(result).toEqual([{ hex: "#FF0000", share: .6 }, { hex: "#000000", share: .3 }, { hex: "#FFFFFF", share: .1 }]);
});

it("excludes transparent pixels, including their hidden RGB values", () => {
  expect(extractPalette(pixels([{ rgb: [255, 0, 0], count: 10, alpha: 0 }, { rgb: [0, 0, 255], count: 1 }]))).toEqual([{ hex: "#0000FF", share: 1 }]);
  expect(extractPalette(new Uint8ClampedArray())).toEqual([]);
  expect(extractPalette(pixels([{ rgb: [200, 100, 50], count: 10, alpha: 0 }]))).toEqual([]);
});

it("quantizes a broad image into five to eight deterministic area-weighted colors", () => {
  const image = new Uint8ClampedArray(Array.from({ length: 4096 }, (_, i) => [i % 256, (i * 17) % 256, (i * 47) % 256, 255]).flat());
  for (const count of [5, 6, 7, 8]) {
    const result = extractPalette(image, count);
    expect(result).toHaveLength(count);
    expect(result).toEqual(extractPalette(image, count));
    expect(result.reduce((sum, color) => sum + color.share, 0)).toBeCloseTo(1, 12);
    expect(new Set(result.map(color => color.hex)).size).toBe(count);
    expect(result.every((color, index) => /^#[0-9A-F]{6}$/.test(color.hex) && (index === 0 || color.share <= result[index - 1].share))).toBe(true);
  }
  expect(extractPalette(image, Infinity)).toHaveLength(6);
  expect(extractPalette(image, 10000)).toHaveLength(8);
});

it("rejects arbitrary URLs and traversal before loading an image", async () => {
  for (const path of ["https://example.com/painting.jpg", "//example.com/image.png", "/assets/../private.png", "/api/image.png"])
    await expect(sampleArtworkImage(path, new AbortController().signal)).rejects.toThrow("Unsupported image");
});

it("honors cancellation before loading", async () => {
  const controller = new AbortController(); controller.abort();
  await expect(sampleArtworkImage("/assets/artworks/test.jpg", controller.signal)).rejects.toThrow();
});
