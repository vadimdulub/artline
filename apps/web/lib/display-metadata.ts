import type { Artwork } from "./types";

// Keep source values intact in the catalogue; omit empty editorial placeholders
// from public metadata. Real qualifications such as “c.” and “before” remain.
export function displayMetadata(value: string | null | undefined): string | undefined {
  const text = value?.trim();
  if (!text || /^(?:unknown|uncertain|undated|n\/?a|none|null|[-—?])$/i.test(text)) return undefined;
  if (/\b(?:in review|under review|needs? review|not (?:recorded|established|available|provided|supplied|known|documented|identified)|not yet|no .{0,45}(?:recorded|available|provided|supplied|added yet))\b/i.test(text)) return undefined;
  if (/^(?:unverified date|creation date unknown|date unknown|needs_review|unknown_)/i.test(text)) return undefined;
  return text;
}

export function artworkDate(work: Pick<Artwork, "date_display"> & Partial<Pick<Artwork, "date_precision">>) {
  return work.date_precision === "unknown" ? undefined : displayMetadata(work.date_display);
}

export function artworkMedium(work: Pick<Artwork, "medium_text" | "work_type">) {
  return displayMetadata(work.medium_text) ?? displayMetadata(work.work_type.replaceAll("_", " "));
}

export function museumDescription(value: string | null | undefined) {
  const text = displayMetadata(value);
  if (!text || /(?:authority candidate|source[- ]backed|object-level|source identity|source label|source capture|primary.source|reconciliation|no (?:current|opening|individual|physical|automatic)|not (?:assigned|duplicated|a current)|official .*directory|museum individually listed|historical institution identity|identity documented|collecting museum function|institution page confirms|current display|visitor access|not asserted|catalogue evidence|institution record|holding link)/i.test(text)) return undefined;
  return text;
}
