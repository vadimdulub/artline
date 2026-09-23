import { expect, test } from "@playwright/test";

type Frame = { title: string; imageWidth: number; imageHeight: number; fitWidth: number; fitHeight: number; stageWidth: number; stageHeight: number; nextX: number; nextY: number; overflow: boolean };
type CaptureWindow = Window & { imageNavigationCapture?: { frames: Frame[]; stopped: boolean } };

for (const width of [1440, 390]) {
  test(`rapid artwork navigation keeps every painted image inside its frame at ${width}px`, async ({ page }, info) => {
    await page.setViewportSize({ width, height: 1000 });
    await page.goto("/artists/claude-monet?art_images=true");
    await page.locator(".work-card").first().click();
    const viewer = page.getByRole("dialog", { name: /Enlarged image:/ });
    await expect(viewer.getByRole("button", { name: "Zoom in", exact: true })).toBeEnabled();
    const next = viewer.getByRole("button", { name: "Next artwork", exact: true });
    const before = (await next.boundingBox())!;

    // Slow layout/effect processing enough to expose frames that settled-state checks miss.
    const session = await page.context().newCDPSession(page);
    await session.send("Emulation.setCPUThrottlingRate", { rate: 4 });
    await page.evaluate(() => {
      const capture = { frames: [] as Frame[], stopped: false };
      (window as CaptureWindow).imageNavigationCapture = capture;
      const sample = () => {
        if (capture.stopped) return;
        const dialog = document.querySelector<HTMLDialogElement>(".image-dialog[open]");
        const image = dialog?.querySelector<HTMLImageElement>(".image-scroll-canvas img");
        const stage = dialog?.querySelector(".image-dialog-stage");
        const arrow = dialog?.querySelector('[aria-label="Next artwork"]');
        if (dialog && image?.complete && image.naturalWidth && stage && arrow) {
          const imageBox = image.getBoundingClientRect(), stageBox = stage.getBoundingClientRect(), arrowBox = arrow.getBoundingClientRect();
          const scale = Math.min(1, stageBox.width / image.naturalWidth, stageBox.height / image.naturalHeight);
          capture.frames.push({ title: image.alt, imageWidth: imageBox.width, imageHeight: imageBox.height, fitWidth: image.naturalWidth * scale, fitHeight: image.naturalHeight * scale, stageWidth: stageBox.width, stageHeight: stageBox.height, nextX: arrowBox.x, nextY: arrowBox.y, overflow: dialog.scrollHeight > dialog.clientHeight + 1 });
        }
        requestAnimationFrame(sample);
      };
      requestAnimationFrame(sample);
    });
    for (let index = 0; index < 8; index++) await next.click();
    for (let index = 0; index < 4; index++) await viewer.getByRole("button", { name: "Previous artwork", exact: true }).click();
    await expect(viewer.getByRole("button", { name: "Zoom in", exact: true })).toBeEnabled();
    const frames = await page.evaluate(() => {
      const capture = (window as CaptureWindow).imageNavigationCapture!;
      capture.stopped = true;
      return capture.frames;
    });
    await session.send("Emulation.setCPUThrottlingRate", { rate: 1 });
    await info.attach("navigation-frames", { body: JSON.stringify(frames, null, 2), contentType: "application/json" });
    expect(new Set(frames.map(frame => frame.title)).size).toBeGreaterThan(4);
    expect(frames.filter(frame => frame.imageWidth > frame.stageWidth + 1 || frame.imageHeight > frame.stageHeight + 1 || frame.overflow)).toEqual([]);
    expect(frames.filter(frame => Math.abs(frame.imageWidth - frame.fitWidth) > 1 || Math.abs(frame.imageHeight - frame.fitHeight) > 1)).toEqual([]);
    expect(frames.filter(frame => Math.abs(frame.nextX - before.x) > 1 || Math.abs(frame.nextY - before.y) > 1)).toEqual([]);
    await page.screenshot({ path: info.outputPath(`rapid-image-navigation-${width}.png`) });
  });
}
