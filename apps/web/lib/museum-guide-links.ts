import "server-only";
import institutions from "@/content/articles/museum-guides/institution-links.json";
import { getGuideIndex } from "./museum-guides";
import type { GuideLocale, MuseumGuide } from "./museum-guide-types";

const institutionLinks: Record<string, string[]> = institutions;
const sharedGuideMuseumNames: Record<string, string> = {
  "alte-pinakothek": "Alte Pinakothek",
  "neue-pinakothek": "Neue Pinakothek",
  "lenbachhaus-munich": "Lenbachhaus",
};

export const museumCollectionLabels: Record<GuideLocale, string> = {
  en: "Museum collection", ru: "Коллекция музея", it: "Collezione del museo",
  de: "Museumssammlung", zh: "博物馆馆藏", fr: "Collection du musée",
  es: "Colección del museo", pt: "Coleção do museu", ja: "美術館のコレクション", ar: "مجموعة المتحف",
};

export function getGuideMuseumLinks(guide: Pick<MuseumGuide, "slug" | "museum" | "kind">) {
  if (guide.kind === "artist") return [];
  return (institutionLinks[guide.slug] ?? []).map(slug => ({
    slug, name: sharedGuideMuseumNames[slug] ?? guide.museum, href: `/museums/${slug}`,
  }));
}

export function getMuseumGuideLinks(museumSlug: string) {
  return getGuideIndex().filter(guide => guide.kind !== "artist" && institutionLinks[guide.slug]?.includes(museumSlug));
}
