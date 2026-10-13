export type PaletteColor = { hex: string; share: number };
type Color = { rgb: number[]; weight: number };
type Box = { colors: Color[]; weight: number; axis: number; score: number };

function box(colors: Color[]): Box {
  const weight = colors.reduce((sum, color) => sum + color.weight, 0);
  const means = [0, 1, 2].map(axis => colors.reduce((sum, color) => sum + color.rgb[axis] * color.weight, 0) / weight);
  const variances = means.map((mean, axis) => colors.reduce((sum, color) => sum + (color.rgb[axis] - mean) ** 2 * color.weight, 0));
  const axis = variances.indexOf(Math.max(...variances));
  return { colors, weight, axis, score: colors.length > 1 ? variances[axis] : 0 };
}

/** Weighted median-cut palette. Work is bounded to a 160 × 160 pixel sample.
 * Keep light/dark pixels: paper, black ink and pale paint are meaningful colors.
 * Shares describe approximate sampled image area, not pigment composition.
 */
export function extractPalette(pixels: Uint8ClampedArray, requested = 6): PaletteColor[] {
  const count = Number.isFinite(requested) ? Math.max(5, Math.min(8, Math.round(requested))) : 6;
  const histogram = new Map<number, { sums: number[]; weight: number }>();
  const stride = Math.max(1, Math.ceil(pixels.length / 4 / 25600)) * 4;
  for (let i = 0; i + 3 < pixels.length; i += stride) {
    if (pixels[i + 3] < 128) continue;
    const [r, g, b] = [pixels[i], pixels[i + 1], pixels[i + 2]];
    const key = ((r >> 3) << 10) | ((g >> 3) << 5) | (b >> 3);
    const entry = histogram.get(key) ?? { sums: [0, 0, 0], weight: 0 };
    entry.sums[0] += r; entry.sums[1] += g; entry.sums[2] += b; entry.weight++;
    histogram.set(key, entry);
  }
  if (!histogram.size) return [];
  const colors = [...histogram.entries()].sort(([a], [b]) => a - b).map(([, entry]) => ({ rgb: entry.sums.map(sum => sum / entry.weight), weight: entry.weight }));
  const boxes = [box(colors)];
  const total = boxes[0].weight;
  while (boxes.length < count) {
    boxes.sort((a, b) => b.score - a.score);
    const current = boxes[0];
    if (!current.score) break;
    current.colors.sort((a, b) => a.rgb[current.axis] - b.rgb[current.axis]);
    let sum = 0, cut = 0;
    while (cut < current.colors.length - 1 && sum < current.weight / 2) sum += current.colors[cut++].weight;
    boxes.splice(0, 1, box(current.colors.slice(0, cut)), box(current.colors.slice(cut)));
  }
  const merged = new Map<string, number>();
  for (const group of boxes) {
    const hex = "#" + [0, 1, 2].map(axis => Math.round(group.colors.reduce((sum, color) => sum + color.rgb[axis] * color.weight, 0) / group.weight).toString(16).padStart(2, "0")).join("").toUpperCase();
    merged.set(hex, (merged.get(hex) ?? 0) + group.weight / total);
  }
  return [...merged].map(([hex, share]) => ({ hex, share })).sort((a, b) => b.share - a.share || a.hex.localeCompare(b.hex));
}

const samples = new Map<string, Uint8ClampedArray>();

/** Only read Artline's same-origin image route; no upload or catalogue mutation. */
export async function sampleArtworkImage(path: string, signal: AbortSignal): Promise<Uint8ClampedArray> {
  if (!/^\/assets\/[a-zA-Z0-9/_-]+\.(jpg|jpeg|png|webp|avif)$/.test(path) || path.includes("..")) throw new Error("Unsupported image");
  signal.throwIfAborted();
  const cached = samples.get(path);
  if (cached) {
    samples.delete(path); samples.set(path, cached);
    return cached;
  }
  return new Promise((resolve, reject) => {
    const image = new Image();
    const finish = (error?: Error, pixels?: Uint8ClampedArray) => {
      clearTimeout(timeout);
      signal.removeEventListener("abort", abort);
      image.onload = null; image.onerror = null;
      image.src = "";
      if (error) reject(error);
      else resolve(pixels!);
    };
    const abort = () => finish(new DOMException("Aborted", "AbortError"));
    const timeout = setTimeout(() => finish(new Error("Image timed out")), 20000);
    signal.addEventListener("abort", abort, { once: true });
    image.onload = () => {
      try {
        const scale = Math.min(1, 160 / Math.max(image.naturalWidth, image.naturalHeight));
        const canvas = document.createElement("canvas");
        canvas.width = Math.max(1, Math.round(image.naturalWidth * scale));
        canvas.height = Math.max(1, Math.round(image.naturalHeight * scale));
        const context = canvas.getContext("2d", { willReadFrequently: true });
        if (!context) throw new Error("Canvas unavailable");
        context.drawImage(image, 0, 0, canvas.width, canvas.height);
        const pixels = context.getImageData(0, 0, canvas.width, canvas.height).data;
        samples.set(path, pixels);
        if (samples.size > 12) samples.delete(samples.keys().next().value!);
        finish(undefined, pixels);
      } catch { finish(new Error("Image colors unavailable")); }
    };
    image.onerror = () => finish(new Error("Image could not load"));
    image.src = path;
  });
}
