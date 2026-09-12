"use client";
import Link from "next/link";
import { useState } from "react";
import { queryValues, updateQuery, useQueryString } from "@/lib/url-state";
import { countryName } from "@/lib/api";
import type { MuseumPage } from "@/lib/types";
import { ArtworkImage } from "./ArtworkViewer";
import { MultiSelectFilter } from "./MultiSelectFilter";
import { usePainterChoices } from "./use-painter-choices";
import { useEditorToken } from "./EditorAccess";
import { useMuseumRequest } from "./museum-state";
import { MuseumChips, MuseumError, setMuseumFilters } from "./MuseumFilters";
import { CursorPager } from "./CursorPager";
import { formatCount, useCursorPaging } from "./use-cursor-paging";
import styles from "./Museums.module.css";

export function MuseumsIndex({ preview }: { preview: boolean }) {
  const params = new URLSearchParams(useQueryString());
  const [token] = useEditorToken();
  const painters = queryValues(params, "artist"), movements = queryValues(params, "movement");
  const painterChoices = usePainterChoices(painters, false, "", token);
  const [retry, setRetry] = useState(0);
  const request = new URLSearchParams();
  for (const key of ["q", "region", "country", "artist", "movement", "selection", "display"]) params.getAll(key).forEach(value => request.append(key, value));
  const paging = useCursorPaging(`${request}|${token}`, params.get("cursor") ?? "", cursor => {
    updateQuery({cursor}, true);
    document.getElementById("museum-results-title")?.focus();
  });
  if (params.get("cursor")) request.set("cursor", params.get("cursor")!);
  const collectionQuery = new URLSearchParams();
  for (const key of ["artist", "movement", "selection", "display"]) params.getAll(key).forEach(value => collectionQuery.append(key, value));
  const { data, previousData, error, loading } = useMuseumRequest<MuseumPage>(`museums?${request}`, token, retry);
  const facets = data?.facets ?? previousData?.facets;
  const regions = queryValues(params, "region"), countries = queryValues(params, "country").map(value => value.toUpperCase());
  const selection = params.get("selection") ?? "", display = params.get("display") ?? "", query = params.get("q") ?? "";
  const europe = ["northern-europe", "western-europe", "southern-europe", "eastern-europe"];
  const europeanScope = regions.length === europe.length && europe.every(region => regions.includes(region));
  const clear = () => setMuseumFilters({ q: null, region: null, country: null, artist: null, movement: null, selection: null, display: null });
  const filters = [
    ...regions.map(value => ({ key: `region-${value}`, label: facets?.regions.find(item => item.slug === value)?.name ?? value.replaceAll("-", " "), remove: () => setMuseumFilters({ region: regions.filter(item => item !== value) }) })),
    ...countries.map(value => ({ key: `country-${value}`, label: countryName(value), remove: () => setMuseumFilters({ country: countries.filter(item => item !== value) }) })),
    ...[{ key: "q", value: query, label: `Search: ${query}` }, { key: "selection", value: selection, label: selection === "owner" ? "My must-see works" : "Museum highlights" }, { key: "display", value: display, label: "Confirmed on view" }].filter(item => item.value).map(item => ({ ...item, remove: () => setMuseumFilters({ [item.key]: null }) })),
  ];
  for (const group of [{ key: "artist", values: painters, options: painterChoices.options }, { key: "movement", values: movements, options: facets?.movements ?? [] }]) {
    for (const value of group.values) filters.push({ key: `${group.key}-${value}`, label: group.options.find(item => item.slug === value)?.name ?? value.replaceAll("-", " "), remove: () => setMuseumFilters({ [group.key]: group.values.filter(item => item !== value) }) });
  }
  return <main id="main-content" className={styles.page}>
    <header className={styles.intro}><div><h1>Museums and collections</h1><p>Follow the paintings to the places that hold them.</p></div><p className={styles.preview}>{preview || token ? "Research preview · records are still in review" : "Published catalogue"}</p></header>
    <div className={styles.locationShortcuts} role="group" aria-label="Museum location shortcuts">
      <button aria-pressed={europeanScope} onClick={() => setMuseumFilters({region:europe, country:null})}>European museums</button>
      <button aria-pressed={!regions.length && !countries.length} onClick={() => setMuseumFilters({region:null, country:null})}>All locations</button>
      <span>Or combine individual regions and countries below.</span>
    </div>
    <div className={styles.filters}>
      <label className={styles.search}><span>Search collections</span><input type="search" placeholder="Museum, city or country" value={query} onChange={event => setMuseumFilters({ q: event.target.value })} /></label>
      <MultiSelectFilter label="Painters" allLabel="All painters" {...painterChoices} values={painters} onChange={values => setMuseumFilters({ artist: values })} helpText="Find collections with works by any selected painter. A collection does not need to hold all the selected painters." />
      <MultiSelectFilter label="Movements" allLabel="All movements" options={facets?.movements ?? []} values={movements} onChange={values => setMuseumFilters({ movement: values })} />
      <MultiSelectFilter label="Regions" allLabel="All regions" options={facets?.regions ?? []} values={regions} onChange={values => setMuseumFilters({ region: values })} helpText="Choose any number. These are museum venue locations, not painters’ origins." />
      <MultiSelectFilter label="Countries" allLabel="All countries" options={facets?.countries ?? []} values={countries} onChange={values => setMuseumFilters({ country: values })} helpText="Match a venue in any selected country. Collections without a verified venue only appear with all locations." />
      <label><span>Selection</span><select value={selection} onChange={event => setMuseumFilters({ selection: event.target.value })}><option value="">All catalogued works</option><option value="owner">My must-see works</option><option value="museum">Museum highlights</option></select></label>
      <label><span>Display</span><select value={display} onChange={event => setMuseumFilters({ display: event.target.value })}><option value="">Any display status</option><option value="on_view">Confirmed on view</option></select></label>
    </div>
    <MuseumChips filters={filters} clear={clear} />
    <div className={styles.resultsHeading}><h2 id="museum-results-title" tabIndex={-1}>Explore the collections</h2><p role="status">{loading ? "Finding collections…" : error ? "Connection interrupted" : `${data?.total ?? 0} ${data?.total === 1 ? "collection" : "collections"} in this view`}</p></div>
    <p className={styles.note}>Filters match any selected value within a group, and combine across groups. Card counts describe the collection’s total Artline records, not just filtered matches. Confirmed display requires a report checked within 30 days.</p>
    <section aria-label="Museum results" aria-busy={loading}>
      {error ? <MuseumError message={error} retry={() => setRetry(value => value + 1)} /> : loading ? <p className={styles.loading}>Opening the collections…</p> : data?.items.length ? <ul className={styles.museumGrid}>{data.items.map(museum => <li key={museum.id}>
        <Link className={styles.museumCard} href={`/museums/${museum.slug}${collectionQuery.size ? `?${collectionQuery}` : ""}`}>
          <div className={styles.collectionImage}>{museum.cover ? <ArtworkImage work={museum.cover} /> : <span>No reproduction available</span>}</div>
          <div className={styles.collectionCopy}><p className={styles.place}>{museum.venues.length ? [...new Set(museum.venues.map(venue => `${venue.city}, ${countryName(venue.country)}`))].join(" / ") : "Collection · no verified visiting venue"}</p><h3>{museum.name}</h3><p>{museum.description}</p>
          <div className={styles.cardCounts}><span>{formatCount(museum.work_count)} {museum.work_count === 1 ? "work" : "works"} in Artline</span>{museum.highlight_count > 0 && <span>{formatCount(museum.highlight_count)} museum highlights</span>}{museum.must_see_count > 0 && <span>{formatCount(museum.must_see_count)} must-see picks</span>}</div>
          <p className={styles.displayNote}>{museum.on_view_count ? `${museum.on_view_count} recently confirmed on view` : "No confirmed display information"}</p><span className={styles.exploreLink}>Explore collection <span aria-hidden="true">↗</span></span></div>
        </Link>
      </li>)}</ul> : <div className={styles.empty}><h2>{filters.length ? "No collections match these filters" : "The museum catalogue is taking shape"}</h2><p>{selection === "owner" ? "Your must-see selection is empty for this view. Open a collection and use editor access to add your own picks." : display ? "No matching works have current, verified display information. This does not mean they are not on view." : "Research records appear in local preview. Public records appear after editorial review."}</p>{filters.length > 0 && <button onClick={clear}>Remove filters</button>}</div>}
    </section>
    {data && <CursorPager paging={paging} next={data.next_cursor} busy={loading} total={data.total} shown={data.items.length} label="Museum pages" noun="collections" />}
  </main>;
}
