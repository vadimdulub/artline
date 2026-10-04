// Keep close controls apart without changing their actual year values.
// Coordinates are in track pixels; both grips stay inside its endpoints.
export function rangeHandlePositions(start: number, end: number, width: number) {
  const gap = Math.min(32, Math.max(0, width));
  if (end - start >= gap) return { start, end };
  const center = Math.max(gap / 2, Math.min(width - gap / 2, (start + end) / 2));
  return { start: center - gap / 2, end: center + gap / 2 };
}
