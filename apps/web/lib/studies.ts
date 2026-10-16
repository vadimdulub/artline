export type StudyKind = "artwork" | "book" | "event";
export type StudyInterval = { start: number; end: number };
export type StudyRecord = {
  kind: StudyKind; id: string; title: string; creator: string; date: string;
  intervals: StudyInterval[]; date_note: string; medium: string; dimensions: string;
  holding: string; href: string; sources: { name: string; url: string }[];
  image?: { artwork?: { id: string; title: string; href: string }; imageUrl: string; label: string; sourceUrl: string; credit: string; license: string; licenseUrl: string };
  personal: boolean; note: string; captured_at: string;
};
export type StudySummary = { public?: boolean; id: string; title: string; role: string; updated_at: string; count: number };
export type StudyListPage = { items: StudySummary[]; total: number; matched: number; next_cursor: string };
export type StudyView = StudySummary & {
  share_token?: string; items: StudyRecord[]; matched: number; counts: Record<StudyKind, number>; range: StudyInterval | null;
  next_cursor: string; artworks: StudyRecord[]; keys: string[];
};
export type StudySearchPage = { items: StudyRecord[]; next_cursor: string };
export const studyKinds: StudyKind[] = ["artwork", "book", "event"];
export const kindLabels: Record<StudyKind, string> = { artwork: "Artworks", book: "Books", event: "Events" };
export const recordKey = (record: Pick<StudyRecord, "kind" | "id">) => `${record.kind}:${record.id}`;
export const yearLabel = (year: number) => year < 0 ? `${Math.abs(year)} BCE` : String(year);
export function safeStudyLink(value: string) {
  if (/^\/(?!\/)[^\\]*$/.test(value)) return value;
  try { const url = new URL(value); return ["http:", "https:"].includes(url.protocol) && !url.username && !url.password ? url.href : undefined; } catch { return undefined; }
}
export function studyYearError(from: string, to: string) {
  for (const value of [from, to]) if (value && (!/^-?\d+$/.test(value) || Number(value) < -12000 || Number(value) > 2000 || Number(value) === 0)) return "Use whole years from −12000 to 2000, without year zero.";
  return from && to && Number(from) > Number(to) ? "From must be earlier than or equal to To." : "";
}
export async function studyRequest<T>(path = "", options: RequestInit = {}): Promise<T> {
  const response = await fetch(`/api/studies${path}`, { ...options, cache: "no-store", headers: { "content-type": "application/json", ...options.headers } });
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    if (response.status === 401) window.dispatchEvent(new Event("artline:session-expired"));
    throw new Error(body?.error?.message ?? "Studies are temporarily unavailable. Please try again.");
  }
  return body as T;
}

// Public reads never forward account credentials or dispatch sign-in prompts.
export async function readStudy(id: string, query: string, signal: AbortSignal, shared = false): Promise<StudyView> {
  if (!shared) return studyRequest<StudyView>(`/${id}?${query}`, { signal });
  const response = await fetch(`/api/shared-studies/${id}?${query}`, { cache: "no-store", credentials: "omit", signal });
  const body = await response.json().catch(() => null);
  if (!response.ok) throw new Error(response.status === 404 ? "This link is unavailable. The owner may have made the study private or removed it." : body?.error?.message ?? "This study could not be loaded. Please try again.");
  return body as StudyView;
}
