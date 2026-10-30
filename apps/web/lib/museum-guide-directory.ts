import index from "@/content/articles/museum-guides/index.json";
import institutions from "@/content/articles/museum-guides/institution-links.json";
import { guidePath } from "./museum-guide-types";

// This is the small published editorial index, not the artwork catalogue.
// Use the same explicit institution links as the server-rendered guide pages.
const links: Record<string, string[]> = institutions;
export function museumDirectoryGuides(slug: string) {
  return index.filter(guide => links[guide.slug]?.includes(slug)).map(guide => ({
    href: guidePath(guide.slug), title: guide.title,
    count: guide.count, languages: guide.locales.length,
  }));
}
