export type ExhibitionVenue = { id?: string; name: string | null; city: string | null; country?: string | null; museum_slug: string | null; start_date?: string | null; end_date?: string | null };
export type Exhibition = {
  id: string; title: string; alternateTitles: string[]; startDate: string | null; endDate: string | null;
  startYear: number | null; endYear: number | null; dates: string; datePrecision: string;
  state: string; stateBasis: string; format: string; checklistState: string; entryCount: number;
  linkedArtworkCount?: number; localArtworkCount?: number; illustratedArtworkCount?: number; participationCounts?: Record<string, number>; venues: ExhibitionVenue[]; research?: ExhibitionResearch;
  participants?: ExhibitionPerson[]; previewWorks?: ExhibitionEntry[];
};
export type ExhibitionResearch = { overview: string; excerpt: string; excerptSource: string; concepts: string[]; conceptBasis: string; publicListComplete: boolean; publicListTotal: number; scope: string; presenter: string | null; reviewedAt: string };
export type ExhibitionPerson = { id: string; name: string; role: string; artist_id: string | null; artist_slug: string | null; sourceURL?: string; birthday?: string | null; deathday?: string | null; nationality?: string | null; portrait?: string | null; imageCredit?: string | null; imageLicense?: string | null; imageSource?: string | null };
export type ExhibitionPage = { items: Exhibition[]; total: number; heldTotal: number; hasMore: boolean; nextCursor: string; expandedStudyCount?: number; localStudyCount?: number; featured?: Exhibition[] };
export type ExhibitionDetail = Exhibition & {
  participantCount: number; venueCount: number;
  participants: ExhibitionPerson[];
  expandedStudy?: boolean; localStudy?: boolean; related?: { id: string; title: string; startYear: number }[];
  sources: { provider: string; source_record_id: string; url: string; retrieved_at: string; interpretation: { research_issues?: string[] | null } }[];
  publications: { kind: string; title: string | null; author: string | null; url: string | null; source_identifier: string | null }[];
};
export type ParticipationEvidence = { kind: string; note: string; url: string; retrievedAt?: string | null };
export type ExhibitionEntry = { id: string; artworkId: string | null; localArtworkId?: string; title: string | null; creator: string | null; date: string | null; medium?: string | null; catalogueNumber: string | null; participation: string; participationEvidence?: ParticipationEvidence; sourcePage: string | null; sourceURL: string; provider: string; sourceCaption: string | null; imageCredit: string | null; imageLicense: string | null; imageSource: string | null; image: string | null; imageWidth?: number; imageHeight?: number };
export function exhibitionArtworkPath(entry: Pick<ExhibitionEntry, "artworkId" | "localArtworkId">) {
  return entry.localArtworkId ? `/exhibitions/artworks/${entry.localArtworkId}` : entry.artworkId ? `/all?selection=true&type=artwork&highlights=false&artwork_id=${entry.artworkId}&item=${entry.artworkId}&itemType=artwork` : null;
}
export type ExhibitionEntries = { items: ExhibitionEntry[]; total: number; hasMore: boolean; nextCursor: string };
export type ExhibitionArtwork = Pick<ExhibitionEntry, "id" | "artworkId" | "title" | "creator" | "date" | "medium" | "provider" | "sourceURL" | "sourceCaption" | "image" | "imageCredit" | "imageLicense" | "imageSource"> & {
  artists: ExhibitionPerson[]; dimensions: string | null; attribution: string | null;
  sourceArtworkID: string; hasSourceExhibitionHistory: boolean; identityBasis: string;
  appearanceCount: number; localStudy: boolean;
};
export type ArtworkAppearance = { id: string; exhibitionId: string; title: string; startDate: string | null; endDate: string | null; dates: string; startYear: number; format: string; venues: Pick<ExhibitionVenue, "name" | "start_date" | "end_date">[]; participation: string; evidence: ParticipationEvidence };
export type ArtworkAppearances = { items: ArtworkAppearance[]; total: number; hasMore: boolean; nextCursor: string };
export function participationLabel(value: string) { return ({ exhibited: "Recorded as exhibited", catalogued: "Listed in exhibition", illustrated_only: "Illustrated in catalogue", discussed_only: "Discussed in catalogue" } as Record<string, string>)[value] ?? value.replaceAll("_", " "); }
export const exhibitionSources = [{ value: "", label: "All sources" }, { value: "royal-academy", label: "Royal Academy catalogues" }, { value: "orsay-historical-index", label: "Musée d’Orsay historical index" }, { value: "moma", label: "MoMA" }, { value: "cleveland", label: "Cleveland Museum of Art" }, { value: "apj_full", label: "Art Platform Japan" }, { value: "artsy", label: "Artsy" }];
export function exhibitionSource(key: string) { return exhibitionSources.find(s => s.value === key)?.label ?? key; }
export function exhibitionDates(record: { startDate: string | null; endDate: string | null; dates: string }) {
  const format = (s: string) => new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "short", year: "numeric", timeZone: "UTC" }).format(new Date(`${s}T12:00:00Z`));
  if (record.startDate && record.endDate) return record.startDate === record.endDate ? format(record.startDate) : `${format(record.startDate)} – ${format(record.endDate)}`;
  return record.dates && !/^\?\s*\/\s*\?$/.test(record.dates) ? record.dates : "Dates not recorded";
}
export function exhibitionState(state: string) { return ({ held: "Held", uncertain: "Details uncertain", announced: "Announced", cancelled: "Cancelled or postponed" } as Record<string, string>)[state] ?? state; }
export function sourceLink(url: string | null | undefined): string | null {
  if (!url) return null;
  try { const parsed = new URL(url); return ["https:", "http:"].includes(parsed.protocol) && !parsed.username && !parsed.password ? parsed.href : null; } catch { return null; }
}
export const exhibitionFilterKeys = ["q", "start", "end", "source", "format", "state", "institution", "artist", "artwork", "after", "collection", "theme", "person"];
export function exhibitionQuery(raw: Record<string, string | string[] | undefined>) {
  const out = new URLSearchParams();
  for (const key of exhibitionFilterKeys) if (typeof raw[key] === "string" && raw[key]) out.set(key, raw[key]);
  return out;
}
