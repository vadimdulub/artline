import Link from "next/link";
import { StructuredData } from "@/components/StructuredData";
import { breadcrumbs, pageMetadata } from "@/lib/seo";
import styles from "./guides.module.css";
import { GuideDirectory } from "./GuideDirectory";
import { guideFilters, type GuideSearchPage } from "@/lib/guide-search";

type Props = { searchParams: Promise<Record<string, string | string[] | undefined>> };

export async function generateMetadata({ searchParams }: Props) {
  const query = guideFilters(await searchParams);
  return pageMetadata("Art guides: artists, museums & interactive patterns", "Illustrated artist and museum guides, interactive geometric patterns, close-looking notes, books and historical context in ten languages.", "/guides", { index: !query.size });
}

export default async function GuidesPage({ searchParams }: Props) {
  const query = guideFilters(await searchParams);
  const url = new URL("/api/v1/guides", process.env.API_INTERNAL_URL ?? "http://localhost:8080");
  url.search = query.toString();
  let page: GuideSearchPage | undefined;
  try {
    const response = await fetch(url, { cache: "no-store", signal: AbortSignal.timeout(8000) });
    if (response.ok) page = await response.json();
  } catch { /* The directory offers a retry if the public API is unavailable. */ }
  return <main id="main-content" className={styles.page}>
    <StructuredData data={breadcrumbs([{ name: "Artline", path: "/" }, { name: "Guides", path: "/guides" }])} />
    <header className={styles.heading}>
      <div><h1>Guides</h1><p>Look closely. Follow a connection. Explore art, literature and history.</p></div>
      <Link href="/">Explore the timeline</Link>
    </header>
    <GuideDirectory initialPage={page} initialQuery={query.toString()} />
  </main>;
}
