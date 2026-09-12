import "server-only";
import fs from "node:fs";
import path from "node:path";
import matter from "gray-matter";

export type PainterEssay = {
  title: string;
  artistSlug: string;
  status: "draft" | "review" | "published";
  sources: string[];
  content: string;
};

const contentDirectory = path.join(process.cwd(), "content", "artists");

export function getPainterEssay(slug: string, preview = false): PainterEssay | null {
  if (!/^[a-z0-9]+(-[a-z0-9]+)*$/.test(slug)) return null;
  const safeSlug = slug;
  const filename = path.join(contentDirectory, `${safeSlug}.md`);
  if (!fs.existsSync(filename)) return null;

  const file = fs.readFileSync(filename, "utf8");
  const parsed = matter(file);
  const status = parsed.data.status;
  if (status !== "draft" && status !== "review" && status !== "published") {
    throw new Error(`Invalid essay status in ${safeSlug}.md`);
  }
  if (!preview && status !== "published") return null;
  if (parsed.data.artist_slug && parsed.data.artist_slug !== slug) throw new Error("Essay artist_slug does not match its filename.");
  return {
    title: String(parsed.data.title ?? safeSlug),
    artistSlug: String(parsed.data.artist_slug ?? safeSlug),
    status,
    sources: Array.isArray(parsed.data.sources) ? parsed.data.sources.map(String) : [],
    content: parsed.content,
  };
}
