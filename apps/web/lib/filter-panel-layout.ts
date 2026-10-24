/** Keep an anchored filter panel inside the viewport, including after resizing. */
export function fitFilterPanel(panel: HTMLElement | null) {
  if (!panel) return;
  panel.style.removeProperty("--filter-panel-shift");
  // Phone, full-view and map panels already have their own containing layout.
  if (getComputedStyle(panel).position !== "absolute" || panel.closest(".map-selection-picker")) return;
  const box = panel.getBoundingClientRect(), gutter = 12;
  const shift = Math.max(gutter - box.left, Math.min(0, document.documentElement.clientWidth - gutter - box.right));
  panel.style.setProperty("--filter-panel-shift", `${shift}px`);
}
