import Link from "next/link";
import { getArtistDirectory } from "@/lib/server-api";
import { pageMetadata } from "@/lib/seo";
import styles from "./directory.module.css";
import { ArtistsIndex } from "@/components/ArtistsIndex";

type Props = { searchParams: Promise<Record<string, string | string[] | undefined>> };
const keys = ["q", "country", "movement", "sort", "popular", "women", "cursor"];
function filters(raw: Record<string, string | string[] | undefined>) {
  const result = new URLSearchParams();
  for (const key of keys) {
    const value = raw[key];
    if (typeof value === "string" && value) result.set(key, value);
    else if (Array.isArray(value)) value.forEach(item => result.append(key, item));
  }
  return result;
}
export async function generateMetadata({ searchParams }: Props) {
  const query = filters(await searchParams);
  return pageMetadata("Artists", "Find artists by name, country or movement. Study their biographies, browse recorded artworks and explore museum holdings.", "/artists", { index: !query.size });
}
export default async function ArtistsPage({ searchParams }: Props) {
  const query = filters(await searchParams);
  const page = await getArtistDirectory(query);
  if (!page) return <main id="main-content" className={styles.page}><h1>Check the artist filters</h1><p>This page link is no longer valid for these filters.</p><Link href="/artists">Return to the artist directory</Link></main>;
  return <ArtistsIndex initialPage={page} initialQuery={query.toString()} />;
}
