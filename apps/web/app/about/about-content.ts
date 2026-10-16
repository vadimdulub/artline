import "server-only";
import { getGuideIndex, getMuseumGuide } from "@/lib/museum-guides";
import type { GuideWork } from "@/lib/museum-guide-types";

type Selection = readonly [guide: string, id: string];
export type PreviewWork = { guide: string; work: GuideWork };
export const previewYears = { start: 1450, end: 1970 };

// Keep About's preview bounded as the full guide directory grows.
const guideSelections = [
  "louvre", "prado", "muma-le-havre", "leventis-gallery",
  "national-gallery-armenia", "munich-museums",
];

// Editorial selections pin object identities; all names, dates and images come
// from the existing guides. No catalogue-sized request or browser-side query.
const artworkSelections: Selection[] = [
  ["louvre", "4a399ca8-712b-40db-8493-6d89b653773e"],
  ["muma-le-havre", "af9c2c5c-6b32-4252-aa6c-ed175a6fc03e"],
  ["munich-museums", "d4265b60-3ab3-560e-ac33-24ef9c73cf03"],
  ["artemisia-gentileschi", "059a9b15-4857-5b67-a329-b6241c6e95da"],
  ["prado", "d666f4ae-1213-46db-a2fb-686ec272b449"],
  ["mary-cassatt", "e000e90d-89b1-4442-bb2f-7524e903bc00"],
  ["louvre", "ca7a7a26-0666-4a3e-b4b8-2e0a6911379d"],
  ["leventis-gallery", "af1662bf-dfe8-5cf6-bb89-fb7d0828a53a"],
  ["munich-museums", "df0700ac-e36b-53ed-a324-86d90e33c962"],
];

const timelineSelections: Selection[] = [
  ["munich-museums", "6c74c0ca-8dc6-43a3-a282-8f2add014354"],
  ["louvre", "fa6cb836-f59c-41a7-8d8f-8e468428e6b2"],
  ["prado", "d666f4ae-1213-46db-a2fb-686ec272b449"],
  ["louvre", "4bbc087f-8ee7-4fa5-9ebc-6a3fddbbb038"],
  ["muma-le-havre", "af9c2c5c-6b32-4252-aa6c-ed175a6fc03e"],
  ["munich-museums", "d4265b60-3ab3-560e-ac33-24ef9c73cf03"],
];
const artistSelections: Selection[] = [
  ["munich-museums", "acff2810-093d-4ce1-89f1-dc9f71411377"],
  ["muma-le-havre", "af9c2c5c-6b32-4252-aa6c-ed175a6fc03e"],
  ["munich-museums", "d4265b60-3ab3-560e-ac33-24ef9c73cf03"],
  ["leventis-gallery", "af1662bf-dfe8-5cf6-bb89-fb7d0828a53a"],
  ["louvre", "f0344de8-d834-440b-a2c7-069650dd4a34"],
  ["louvre", "ca7a7a26-0666-4a3e-b4b8-2e0a6911379d"],
  ["national-gallery-armenia", "0049c2da-bd83-51c9-a441-ac034b997d2b"],
  ["munich-museums", "df0700ac-e36b-53ed-a324-86d90e33c962"],
];

function select([guide, id]: Selection): PreviewWork[] {
  const work = getMuseumGuide(guide)?.works.find(item => item.id === id);
  return work?.image ? [{ guide, work }] : [];
}

export function getAboutPreviews() {
  const timeline = timelineSelections.flatMap(select).filter(({ work }) =>
    work.start !== null && work.end !== null && work.start >= previewYears.start && work.end <= previewYears.end);
  const artists = artistSelections.flatMap(select).flatMap(item => {
    const artist = item.work.artists.find(artist => artist.role === "primary");
    return artist ? [{ ...item, artist }] : [];
  });
  const guideIndex = getGuideIndex();
  const guides = guideSelections.flatMap(slug => {
    const guide = guideIndex.find(guide => guide.slug === slug && guide.kind !== "artist");
    if (!guide) return [];
    const work = getMuseumGuide(guide.slug)?.works.find(work => work.image === guide.image);
    return work ? [{ ...guide, work }] : [];
  });
  return { artworks: artworkSelections.flatMap(select), timeline, artists, guides };
}

// Short display credits; complete evidence remains attached to each guide work.
// Rights labels and the institutional CC BY-SA credits are preserved verbatim.
const shortCredits: Record<string, string> = {
  "4a399ca8-712b-40db-8493-6d89b653773e": "C2RMF, via Wikimedia Commons. Adjusted, resized and compressed.",
  "ca7a7a26-0666-4a3e-b4b8-2e0a6911379d": "Musée du Louvre, via Wikimedia Commons. Resized and compressed.",
  "af1662bf-dfe8-5cf6-bb89-fb7d0828a53a": "Loukia Nicolaides-Vassiliou; A. G. Leventis Gallery. Full frame preserved; resized and compressed.",
  "ceb20e49-d7af-5f95-a525-a8e64e36a969": "Vardges Sureniants; Wikimedia Commons. Full frame preserved; resized and compressed.",
};
export function imageCredit(work: GuideWork) { return shortCredits[work.id] ?? work.credit; }
