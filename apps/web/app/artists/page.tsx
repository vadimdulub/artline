import Link from "next/link";
import { getArtistDirectory, researchPreviewEnabled } from "@/lib/server-api";
import { countryName } from "@/lib/api";
import { pageMetadata } from "@/lib/seo";
import styles from "./directory.module.css";

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
  return pageMetadata("Artists", "Find artists by name, country or movement. Study their biographies, browse recorded artworks and explore museum holdings.", "/artists", { index: !researchPreviewEnabled() && !query.size });
}
export default async function ArtistsPage({ searchParams }: Props) {
  const query = filters(await searchParams);
  const page = await getArtistDirectory(query);
  if (!page) return <main id="main-content" className={styles.page}><h1>Check the artist filters</h1><p>This page link is no longer valid for these filters.</p><Link href="/artists">Return to the artist directory</Link></main>;
  const next = new URLSearchParams(query); next.set("cursor", page.next_cursor);
  const first = new URLSearchParams(query); first.delete("cursor");
  const count = (value: number) => value.toLocaleString("en-GB");
  return <main id="main-content" className={styles.page}>
    <header className={styles.heading}><div><h1>Artists</h1><p>Explore a life, study a body of work, follow it into the world’s collections.</p></div><Link href="/">Explore the timeline</Link></header>
    <form key={query.toString()} action="/artists" className={styles.filters} role="search" aria-label="Find artists">
      <label className={styles.search}><span>Artist name</span><input type="search" name="q" defaultValue={query.get("q") ?? ""} maxLength={200} placeholder="Name or alternative spelling" /></label>
      <label><span>Country</span><select name="country" defaultValue={query.get("country") ?? ""}><option value="">All countries</option>{page.facets.countries.map(option => <option value={option.slug} key={option.slug}>{option.name}</option>)}</select></label>
      <label><span>Movement</span><select name="movement" defaultValue={query.get("movement") ?? ""}><option value="">All movements</option>{page.facets.movements.map(option => <option value={option.slug} key={option.slug}>{option.name}</option>)}</select></label>
      <label><span>Order</span><select name="sort" defaultValue={query.get("sort") ?? "popular"}><option value="popular">Popularity</option><option value="name">Name A–Z</option></select></label>
      <div className={styles.options}><label><input type="checkbox" name="popular" value="true" defaultChecked={query.get("popular") === "true"} /><span>Top 1,000 cohort</span></label><label><input type="checkbox" name="women" value="true" defaultChecked={query.get("women") === "true"} /><span>Women artists</span></label></div>
      <div className={styles.actions}><Link href="/artists">Clear filters</Link><button type="submit">Find artists</button></div>
    </form>
    <div className={styles.resultsHeading}><h2>{count(page.total)} {page.total === 1 ? "artist" : "artists"}</h2><p>{query.get("sort") === "name" ? "Alphabetical by catalogue name" : "Popularity uses the Pantheon cohort; it is not a ranking of artistic quality."}</p></div>
    {page.items.length ? <ul className={styles.artists}>{page.items.map(artist => <li key={artist.id}><Link href={`/artists/${artist.slug}${researchPreviewEnabled() ? "?catalogue=all" : ""}`} prefetch={false}>
      <h3>{artist.name}</h3><p className={styles.dates}>{artist.date_display}</p>
      <p className={styles.context}>{artist.movement.name !== "Unclassified" && <span>{artist.movement.name}</span>}{artist.countries.length > 0 && <span>{artist.countries.map(countryName).join(", ")}</span>}</p>
      <span className={styles.works}>{count(artist.artwork_count)} recorded {artist.artwork_count === 1 ? "work" : "works"}</span>
    </Link></li>)}</ul> : <div className={styles.empty}><h3>No artists match these filters</h3><p>Try another spelling, or broaden the country and movement filters.</p><Link href="/artists">Show all artists</Link></div>}
    <nav className={styles.pagination} aria-label="Artist directory pages"><span>{page.items.length} shown on this page</span><div>{query.has("cursor") && <Link href={`/artists?${first}`} prefetch={false}>First artists</Link>}{page.next_cursor && <Link href={`/artists?${next}`} prefetch={false}>Next artists</Link>}</div></nav>
  </main>;
}
