import { describe, expect, it } from "vitest";
import { fitImage, imageZoomLevels } from "../image-view";

describe("artwork image fitting", () => {
  it("preserves tall and wide compositions inside the viewport", () => {
    expect(fitImage(1000, 2000, 800, 600)).toEqual({ width: 300, height: 600 });
    expect(fitImage(2000, 1000, 800, 600)).toEqual({ width: 800, height: 400 });
  });
  it("uses the available view for small originals without cropping", () => {
    const landscape = fitImage(300, 200, 800, 600);
    expect(landscape.width).toBe(800);
    expect(landscape.height).toBeCloseTo(1600 / 3);
    expect(fitImage(200, 300, 800, 600)).toEqual({ width: 400, height: 600 });
  });
  it("waits for real image and viewport dimensions", () => {
    expect(fitImage(0, 0, 800, 600)).toEqual({ width: 0, height: 0 });
    expect(fitImage(800, 600, 0, 0)).toEqual({ width: 0, height: 0 });
    expect(imageZoomLevels).toEqual([1, 1.5, 2, 3, 4]);
  });
});
