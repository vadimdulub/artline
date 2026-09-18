"use client";
import { useEffect, useRef, useState, type ReactNode } from "react";
import { apiRequest, errorMessage } from "@/lib/api";
import type { BooksFacets } from "@/lib/books";
import type { EventsFacets } from "@/lib/events";
import type { TimelineFacets } from "@/lib/types";
import type { AtlasType } from "@/lib/atlas";
import { AtlasFilters, ActiveFilters } from "./AtlasFilters";
import { BookFilterFields, ArtworkFilterFields, EventFilterFields, type FilterChange } from "./EntityFilterFields";
import { usePainterChoices, workTypeOptions } from "./use-painter-choices";

function useChoices<T>(path: string) {
  const [result, setResult] = useState<{path:string;data?:T;error?:string}>();
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    const timer = setTimeout(() => apiRequest<T>(path, { signal: controller.signal })
      .then(data => { if (!controller.signal.aborted) setResult({ path, data }); })
      .catch(e => { if (!controller.signal.aborted) setResult({ path, error: errorMessage(e) }); }), 140);
    return () => { clearTimeout(timer); controller.abort(); };
  }, [path, attempt]);
  return { data: result?.path === path ? result.data : undefined, error: result?.path === path ? result.error : undefined, loading: result?.path !== path, retry: () => setAttempt(v => v + 1) };
}
type Props = { params: URLSearchParams; change: FilterChange; reset: (defaults: boolean) => void };
type Option = { slug: string; name: string };
function Shell({ type, params, change, reset, options=[], error, retry, children }: Props & { type: AtlasType; options?: Option[]; error?: string; retry: () => void; children: ReactNode }) {
  const search = useRef<HTMLInputElement>(null);
  const topLabel = type === "book" ? "Top 100 books" : type === "artwork" ? "Top 100 painters" : "Top 100 events";
  const active = [...params].filter(([key,value]) => value && !["false"].includes(value) && (key !== "women" || value === "true")).map(([key,value]) => ({
    key: `${key}-${value}`, label: key === "q" ? `Search: ${value}` : key === "women" ? type === "book" ? "Women authors" : "Women artists" : ["popular","top100"].includes(key) ? topLabel : options.find(o=>o.slug===value)?.name ?? value.replaceAll("-"," "),
    remove: () => change({[key]: ["top100","popular"].includes(key) ? "false" : params.getAll(key).filter(v=>v!==value)}),
  }));
  const placeholder = type === "book" ? "Book, author, or idea" : type === "event" ? "Event, place, or idea" : "Painter, place, movement, or work";
  return <div className="atlas-picker-filters">
    {error && <p role="status">Some filter choices could not be loaded. <button onClick={retry}>Retry filters</button></p>}
    <AtlasFilters searchRef={search} query={params.get("q")??""} onQuery={q=>change({q:q||null})} onReset={()=>reset(true)} placeholder={placeholder} searchLabel={type==="book"?"Find a book or author":type==="event"?"Find an event":"Find an artwork or painter"} columns={type==="book"||type==="event"?4:5} activeCount={active.filter(f=>!f.key.startsWith("q-")).length}>{children}</AtlasFilters>
    <ActiveFilters filters={active} onClear={()=>reset(false)} searchRef={search}/>
  </div>;
}
function Books(props: Props) {
  const selection = `women=${props.params.get("women")==="true"}&top100=${props.params.get("top100")!=="false"}`;
  const facets = useChoices<BooksFacets>(`books/facets?${selection}`);
  const [search,setSearch] = useState("");
  const authors = useChoices<{items:string[];hasMore:boolean}>(`books/authors?${selection}&q=${encodeURIComponent(search)}`);
  return <Shell {...props} type="book" options={[...(facets.data?.regions??[]),...(facets.data?.countries??[]),...(facets.data?.languages??[])]} error={facets.error} retry={facets.retry}>
    <BookFilterFields {...props} facets={facets.data} unavailable={Boolean(facets.error)} authorChoices={{options:(authors.data?.items??[]).map(name=>({slug:name,name})),unavailable:Boolean(authors.error),retry:authors.retry,remote:{search,onSearch:setSearch,loading:authors.loading,hasMore:Boolean(authors.data?.hasMore)}}}/>
  </Shell>;
}
function Artworks(props: Props) {
  const popular=props.params.get("popular")!=="false",women=props.params.get("women")==="true";
  const facets=useChoices<TimelineFacets>(`timeline/facets?popular=${popular}&women=${women}`);
  const painters=usePainterChoices(props.params.getAll("painter"),popular,"","",women);
  return <Shell {...props} type="artwork" options={[...painters.options,...workTypeOptions,...(facets.data?.countries??[]),...(facets.data?.regions??[]),...(facets.data?.movements??[])]} error={facets.error} retry={facets.retry}>
    <ArtworkFilterFields {...props} facets={facets.data??{countries:[],movements:[],regions:[]}} painterChoices={painters} unavailable={Boolean(facets.error)}/>
  </Shell>;
}
function Events(props: Props) {
  const facets=useChoices<EventsFacets>(`events/facets?top100=${props.params.get("top100")!=="false"}`);
  return <Shell {...props} type="event" error={facets.error} retry={facets.retry}><EventFilterFields {...props} facets={facets.data} unavailable={Boolean(facets.error)}/></Shell>;
}
export function EntityPickerFilters({type,...props}:Props & {type:AtlasType}) {
  return type==="book"?<Books {...props}/>:type==="artwork"?<Artworks {...props}/>:<Events {...props}/>;
}
