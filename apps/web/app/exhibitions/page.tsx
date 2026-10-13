import Image from "next/image";
import Link from "@/components/MemberLink";
import { AtlasPageHeader } from "@/components/AtlasPageHeader";
import { ExhibitionFilters } from "@/components/ExhibitionFilters";
import { getExhibitions } from "@/lib/exhibitions-server";
import { exhibitionDates, exhibitionQuery, exhibitionSources, exhibitionState } from "@/lib/exhibitions";
import { pageMetadata } from "@/lib/seo";
import styles from "./exhibitions.module.css";

type Props = { searchParams: Promise<Record<string, string | string[] | undefined>> };
export async function generateMetadata({ searchParams }: Props) {
  return pageMetadata("Exhibitions", "Explore historical exhibitions from 1600 to 1989, their paintings, drawings, prints and icons.", "/exhibitions", { index: !exhibitionQuery(await searchParams).size });
}
export default async function ExhibitionsPage({ searchParams }: Props) {
  const query = exhibitionQuery(await searchParams);
  const page = await getExhibitions(query);
  if (!page) return <main id="main-content" className={styles.page}><h1>Check the exhibition filters</h1><p>Use valid years and a current page link.</p><Link href="/exhibitions">Return to exhibitions</Link></main>;
  const expandedCount = page.expandedStudyCount ?? page.localStudyCount;
  const isExpanded = query.get("collection") === "expanded";
  const next = new URLSearchParams(query); next.set("after", page.nextCursor);
  const first = new URLSearchParams(query); first.delete("after");
  const feature = !query.size ? page.featured?.[0] : null;
  return <main id="main-content" className={styles.page}>
    <AtlasPageHeader title="Exhibitions" description="Paintings, drawings, prints and icons in historical exhibitions, 1600–1989." />
    {feature && <section className={styles.feature} aria-labelledby="featured-exhibition">
      <div className={styles.featureText}><p className={styles.meta}>From the museum archive</p><h2 id="featured-exhibition"><Link href={`/exhibitions/${feature.id}`} prefetch={false}>{feature.title}</Link></h2><p>{feature.research?.overview}</p><p className={styles.meta}>{exhibitionDates(feature)}</p><Link className={styles.action} href={`/exhibitions/${feature.id}`} prefetch={false}>Explore this exhibition</Link></div>
      <div className={styles.featureGallery}>{feature.previewWorks?.slice(0, 2).map(work => <figure key={work.id}><Link href={`/exhibitions/${feature.id}#work-${work.id}`} prefetch={false}><Image src={work.image!} width={520} height={460} alt={work.title ?? "Documented artwork"} unoptimized /></Link><figcaption>{work.title}{work.date ? `, ${work.date}` : ""}<small>{work.creator}</small><details className={styles.caption}><summary>Image credit</summary><p>{work.imageCredit}{work.imageLicense ? ` · ${work.imageLicense}` : ""}</p></details></figcaption></figure>)}</div>
    </section>}
    {expandedCount !== undefined && expandedCount > 0 && <div className={styles.collectionBar}><nav aria-label="Exhibition collections"><Link href="/exhibitions" aria-current={!isExpanded ? "page" : undefined}>Entire archive</Link><Link href="/exhibitions?collection=expanded" aria-current={isExpanded ? "page" : undefined}>Expanded studies <span>{expandedCount.toLocaleString("en-US")}</span></Link></nav><span>Exhibition histories</span></div>}
    <ExhibitionFilters key={query.toString()} initialQuery={query.toString()} />
    <div className={styles.summary}><h2>{page.total.toLocaleString("en-US")} exhibition{page.total === 1 ? "" : "s"}</h2><p>{expandedCount && isExpanded ? "Artwork lists, artists and source-led reading topics." : `${page.heldTotal.toLocaleString("en-US")} recorded as held.`}</p></div>
    <ul className={styles.rows}>{page.items.map(item => <li key={item.id}>
      {Boolean(item.previewWorks?.length) && <Link href={`/exhibitions/${item.id}`} className={styles.exhibitionPictures} aria-label={`View artworks in ${item.title}`} prefetch={false}>{item.previewWorks!.slice(0, 3).map(work => work.image && <Image key={work.id} src={work.image} width={work.imageWidth || 420} height={work.imageHeight || 420} alt={`${work.title || "Exhibition artwork"}${work.creator ? `, ${work.creator}` : ""}`} unoptimized />)}</Link>}
      <div className={styles.year}>{item.startYear ?? "?"}<span>{item.format === "online" ? "Online" : "Exhibition"}</span></div><div className={styles.rowBody}>
      <p className={styles.meta}>{exhibitionDates(item)}</p>
      <h3><Link href={`/exhibitions/${item.id}`} prefetch={false}>{item.title}</Link></h3>
      {item.venues.map((venue, index) => <p className={styles.meta} key={index}>{venue.museum_slug ? <Link href={`/museums/${venue.museum_slug}`} prefetch={false}>{venue.name}</Link> : venue.name}{venue.city ? `, ${venue.city}` : ""}</p>)}
      {!item.venues.length && item.research?.presenter && <p className={styles.meta}>{item.research.presenter}</p>}
      {item.research?.concepts.length ? <p className={styles.rowTopics}>{item.research.concepts.slice(0, 3).join(" / ")}</p> : null}
      <p className={styles.meta}>{item.entryCount.toLocaleString("en-US")} artwork{item.entryCount === 1 ? "" : "s"}{item.illustratedArtworkCount ? ` · ${item.illustratedArtworkCount} illustrated` : ""}{item.state !== "held" ? ` · ${exhibitionState(item.state)}` : ""}</p>
      </div>
    </li>)}</ul>
    {!page.items.length && <div className={styles.empty}><h3>No exhibitions match these filters</h3><p>Try a broader date range or clear the filters.</p><Link href="/exhibitions">Clear filters</Link></div>}
    <nav className={`${styles.paging} catalogue-pagination`} aria-label="Exhibition pages"><span>Newest exhibition years first.</span>{query.has("after") && <Link href={`/exhibitions?${first}`} prefetch={false}>First page</Link>}{page.hasMore && <Link href={`/exhibitions?${next}`} prefetch={false}>Next exhibitions →</Link>}</nav>
    <details className={styles.evidence}><summary>About these records</summary><p>Exhibition participation, museum ownership and current display are separate. A full online artwork list is not necessarily a final exhibition checklist. Each exhibition includes notes on its coverage and evidence.</p><nav className={styles.sources} aria-label="Exhibition sources">{exhibitionSources.filter(s => s.value).map(source => <Link key={source.value} href={`/exhibitions?collection=archive&source=${source.value}`} prefetch={false}>{source.label}</Link>)}</nav></details>
  </main>;
}
