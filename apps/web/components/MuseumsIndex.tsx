"use client";
import { museumDescription } from "@/lib/display-metadata";
import Link from "@/components/MemberLink";
import { useRef, useState } from "react";
import { queryValues, updateQuery, useQueryString } from "@/lib/url-state";
import { countryName } from "@/lib/api";
import type { MuseumPage } from "@/lib/types";
import { ArtworkImage, permittedImagePath } from "./ArtworkViewer";
import { MultiSelectFilter } from "./MultiSelectFilter";
import { usePainterChoices } from "./use-painter-choices";
import { useMuseumRequest } from "./museum-state";
import { MuseumError, setMuseumFilters } from "./MuseumFilters";
import { AtlasFilters, AtlasSelect, ActiveFilters } from "./AtlasFilters";
import { AtlasPageHeader } from "./AtlasPageHeader";
import { CursorPager } from "./CursorPager";
import { formatCount, useCursorPaging } from "./use-cursor-paging";
import styles from "./Museums.module.css";

export function MuseumsIndex() {
  const search = useRef<HTMLInputElement>(null);
  const params = new URLSearchParams(useQueryString());
  if (params.has("selection") && params.get("selection") !== "museum") { params.delete("selection"); params.delete("cursor"); }
  const painters = queryValues(params, "artist"), movements = queryValues(params, "movement");
  const painterChoices = usePainterChoices(painters);
  const [retry, setRetry] = useState(0);
  const request = new URLSearchParams();
  for (const key of ["q", "region", "country", "artist", "movement", "selection", "display"]) params.getAll(key).forEach(value => request.append(key, value));
  const paging = useCursorPaging(request.toString(), params.get("cursor") ?? "", cursor => {
    updateQuery({cursor}, true);
    document.getElementById("museum-results-title")?.focus();
  });
  if (params.get("cursor")) request.set("cursor", params.get("cursor")!);
  const collectionQuery = new URLSearchParams();
  for (const key of ["artist", "movement", "selection", "display"]) params.getAll(key).forEach(value => collectionQuery.append(key, value));
  const { data, previousData, error, loading } = useMuseumRequest<MuseumPage>(`museums?${request}`, retry);
  const facets = data?.facets ?? previousData?.facets;
  const regions = queryValues(params, "region"), countries = queryValues(params, "country").map(value => value.toUpperCase());
  const selection = params.get("selection") ?? "", display = params.get("display") ?? "", query = params.get("q") ?? "";
  const clear = () => setMuseumFilters({ q: null, region: null, country: null, artist: null, movement: null, selection: null, display: null });
  const filters = [
    ...regions.map(value => ({ key: `region-${value}`, label: facets?.regions.find(item => item.slug === value)?.name ?? value.replaceAll("-", " "), remove: () => setMuseumFilters({ region: regions.filter(item => item !== value) }) })),
    ...countries.map(value => ({ key: `country-${value}`, label: countryName(value), remove: () => setMuseumFilters({ country: countries.filter(item => item !== value) }) })),
    ...[{ key: "q", value: query, label: `Search: ${query}` }, { key: "selection", value: selection, label: "Museum highlights" }, { key: "display", value: display, label: "Confirmed on view" }].filter(item => item.value).map(item => ({ ...item, remove: () => setMuseumFilters({ [item.key]: null }) })),
  ];
  for (const group of [{ key: "artist", values: painters, options: painterChoices.options }, { key: "movement", values: movements, options: facets?.movements ?? [] }]) {
    for (const value of group.values) filters.push({ key: `${group.key}-${value}`, label: group.options.find(item => item.slug === value)?.name ?? value.replaceAll("-", " "), remove: () => setMuseumFilters({ [group.key]: group.values.filter(item => item !== value) }) });
  }
  return <main id="main-content" className={styles.page}>
    <AtlasPageHeader title="Museums and collections" />
    <AtlasFilters searchRef={search} query={query} onQuery={value => setMuseumFilters({ q: value })} onReset={clear} placeholder="Museum, city or country" searchLabel="Search collections" columns={6} activeCount={filters.filter(f => f.key !== "q").length}>
      <MultiSelectFilter label="Painters" allLabel="All painters" {...painterChoices} values={painters} onChange={values => setMuseumFilters({ artist: values })} helpText="Find collections with works by any selected painter. A collection does not need to hold all the selected painters." />
      <MultiSelectFilter label="Movements" allLabel="All movements" options={facets?.movements ?? []} values={movements} onChange={values => setMuseumFilters({ movement: values })} />
      <MultiSelectFilter label="Regions" allLabel="All regions" options={facets?.regions ?? []} values={regions} onChange={values => setMuseumFilters({ region: values })} helpText="Choose any number. These are recorded museum or venue locations." />
      <MultiSelectFilter label="Countries" allLabel="All countries" options={facets?.countries ?? []} values={countries} onChange={values => setMuseumFilters({ country: values })} helpText="Match a recorded museum or venue location in any selected country." />
      <AtlasSelect label="Selection" value={selection} onChange={value => setMuseumFilters({ selection: value })} options={[{ value: "", label: "All catalogued works" }, { value: "museum", label: "Museum highlights" }]} />
      <AtlasSelect label="Display" value={display} onChange={value => setMuseumFilters({ display: value })} options={[{ value: "", label: "Any display status" }, { value: "on_view", label: "Confirmed on view" }]} />
    </AtlasFilters>
    <ActiveFilters filters={filters} onClear={clear} searchRef={search} />
    <div className={styles.resultsHeading}><h2 id="museum-results-title" tabIndex={-1}>Explore the collections</h2><p role="status">{loading ? "Finding collections…" : error ? "Connection interrupted" : `${data?.total ?? 0} ${data?.total === 1 ? "collection" : "collections"} in this view`}</p></div>
    <p className={styles.note}>Collection totals include all Artline records. Confirmed on-view reports were checked within 30 days.</p>
    <section aria-label="Museum results" aria-busy={loading}>
      {error ? <MuseumError message={error} retry={() => setRetry(value => value + 1)} /> : loading ? <p className={styles.loading}>Opening the collections…</p> : data?.items.length ? <ul className={styles.museumGrid}>{data.items.map(museum => <li key={museum.id}>
        <Link className={styles.museumCard} href={`/museums/${museum.slug}${collectionQuery.size ? `?${collectionQuery}` : ""}`}>
          {museum.cover && permittedImagePath(museum.cover.media_url) && <div className={styles.collectionImage}><ArtworkImage work={museum.cover} /></div>}
          <div className={styles.collectionCopy}>{(museum.venues.length > 0 || museum.country) && <p className={styles.place}>{ museum.venues.length ? [...new Set(museum.venues.map(venue => `${venue.city}, ${countryName(venue.country)}`))].join(" / ") : [museum.city, countryName(museum.country!)].filter(Boolean).join(", ") }</p>}<h3>{museum.name}</h3>{museumDescription(museum.description) && <p>{museumDescription(museum.description)}</p>}
          <div className={styles.cardCounts}><span>{formatCount(museum.work_count)} {museum.work_count === 1 ? "work" : "works"} in Artline</span>{museum.highlight_count > 0 && <span>{formatCount(museum.highlight_count)} museum highlights</span>}</div>
          {museum.on_view_count > 0 && <p className={styles.displayNote}>{museum.on_view_count} recently confirmed on view</p>}<span className={styles.exploreLink}>Explore collection <span aria-hidden="true">↗</span></span></div>
        </Link>
      </li>)}</ul> : <div className={styles.empty}><h2>{filters.length ? "No collections match these filters" : "The museum catalogue is taking shape"}</h2><p>{display ? "No matching works have current, verified display information. This does not mean they are not on view." : "No collections are available in this view yet."}</p>{filters.length > 0 && <button onClick={clear}>Remove filters</button>}</div>}
    </section>
    {data && <CursorPager paging={paging} next={data.next_cursor} busy={loading} total={data.total} shown={data.items.length} label="Museum pages" noun="collections" />}
  </main>;
}
