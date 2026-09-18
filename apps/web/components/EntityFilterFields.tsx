"use client";
import type { ComponentProps } from "react";
import type { BooksFacets, BookFilterOption } from "@/lib/books";
import type { EventsFacets } from "@/lib/events";
import type { TimelineFacets } from "@/lib/types";
import { AtlasCheckbox } from "./AtlasFilters";
import { MultiSelectFilter } from "./MultiSelectFilter";
import { SelectionHint } from "./SelectionHint";
import { PopularPaintersHint } from "./PopularPaintersHint";
import { workTypeOptions } from "./use-painter-choices";
export type FilterChange = (values: Record<string, string | string[] | null>) => void;
type RemoteChoices = Pick<ComponentProps<typeof MultiSelectFilter>, "options" | "remote" | "retry" | "unavailable">;
type Fields = { params: URLSearchParams; change: FilterChange; unavailable?: boolean };
export const eventDimensions = [
  { key: "topic", field: "topics", label: "Topics", all: "All topics", help: "Explore war, religion, science, society, culture, and their connections." },
  { key: "kind", field: "kinds", label: "Types", all: "All types", help: "Events include wars and individual occurrences. Periods include empires; movements describe wider historical change." },
  { key: "region", field: "regions", label: "Regions", all: "All regions", help: "Regions of recorded locations. Some historical places have no region assigned." },
  { key: "country", field: "countries", label: "Countries", all: "All countries", help: "Recorded countries or historical states. Modern location and political control are different; source details remain in each record." },
] as const;

export function BookFilterFields({params, change, facets, authorChoices, unavailable=false}: Fields & {facets?:BooksFacets; authorChoices:RemoteChoices}) {
 const authors=params.getAll("author"),regions=params.getAll("region"),countries=params.getAll("country"),languages=params.getAll("language");
 const womenOnly=params.get("women")==="true",top100Only=params.get("top100")!=="false";
 const choices=(options:BookFilterOption[]|undefined,selected:string[])=>[...(options??[]),...selected.filter(slug=>!options?.some(o=>o.slug===slug)).map(slug=>({slug,name:slug.replaceAll("-"," ")}))];
 return <>
        <MultiSelectFilter label="Authors" allLabel="All authors" {...authorChoices} values={authors} onChange={values => change({ author: values })} />
        <MultiSelectFilter label="Regions" allLabel="All regions" options={choices(facets?.regions, regions)} values={regions} onChange={values => change({ region: values })} unavailable={unavailable} helpText="Regions of recorded book origins, using the same geographic groupings as Painters. Some historical origins have no region assigned." />
        <MultiSelectFilter label="Countries" allLabel="All countries" options={choices(facets?.countries, countries)} values={countries} onChange={values => change({ country: values })} unavailable={unavailable} helpText="Recorded countries of origin, including historical states. Different filters combine." />
        <MultiSelectFilter label="Languages" allLabel="All languages" options={choices(facets?.languages, languages)} values={languages} onChange={values => change({ language: values })} unavailable={unavailable} helpText="Languages and varieties recorded for the work. Select several to include them together. Translation availability may differ." />
        <AtlasCheckbox label="Women authors" checked={womenOnly} onChange={checked => change({ women: checked ? "true" : null })} />
        <AtlasCheckbox label="Top 100 books" checked={top100Only} onChange={checked => change({ top100: checked ? "true" : "false" })}><SelectionHint label="About the Top 100 book selection">100 editorial starting points across literature, philosophy, religion, science and society. An unranked selection of important books to explore, open to revision.</SelectionHint></AtlasCheckbox>
 </>;
}
export function ArtworkFilterFields({params,change,facets,painterChoices,unavailable=false}: Fields & {facets:TimelineFacets;painterChoices:RemoteChoices}) {
 const painters=params.getAll("painter"),selectedMovements=params.getAll("movement"),regions=params.getAll("region"),countries=params.getAll("country"),workTypes=params.getAll("work_type");
 const womenOnly=params.get("women")==="true",popularOnly=params.get("popular")!=="false";
 return <>
          <MultiSelectFilter label="Painters" allLabel="All painters" {...painterChoices} values={painters} onChange={values => change({ painter: values })} helpText="Select painters together, for example Monet and Pissarro. Search here adds names; it does not replace your selection." />
          <MultiSelectFilter label="Movements" allLabel="All movements" options={facets.movements} values={selectedMovements} onChange={values => change({ movement: values })} unavailable={unavailable} />
          <MultiSelectFilter label="Regions" allLabel="All regions" options={facets.regions ?? []} values={regions} onChange={values => change({ region: values })} unavailable={unavailable} />
          <MultiSelectFilter label="Countries" allLabel="All countries" options={facets.countries} values={countries} onChange={values => change({ country: values })} unavailable={unavailable} />
          <MultiSelectFilter label="Work types" allLabel="All types" options={workTypeOptions} values={workTypes} onChange={values => change({ work_type: values })} />
          <AtlasCheckbox label="Women artists" checked={womenOnly} onChange={checked => change({ women: checked ? "true" : null })} />
          <AtlasCheckbox label="Top 100 painters" checked={popularOnly} onChange={checked => change({ popular: checked ? "true" : "false" })}><PopularPaintersHint /></AtlasCheckbox>
 </>;
}
export function EventFilterFields({params,change,facets,unavailable=false}:Fields & {facets?:EventsFacets}) {
 const choices=eventDimensions.map(d=>({...d,values:params.getAll(d.key)}));
 const top100=params.get("top100")!=="false";
 return <>
        {choices.map(d => {
          const options = facets?.[d.field] ?? [];
          return <MultiSelectFilter key={d.key} label={d.label} allLabel={d.all} options={[...options, ...d.values.filter(value => !options.some(option => option.slug === value)).map(value => ({ slug: value, name: value }))]}
            values={d.values} onChange={values => change({ [d.key]: values })} unavailable={unavailable} helpText={d.help} />;
        })}
        <AtlasCheckbox label="Top 100 events" checked={top100} onChange={checked => change({ top100: checked ? "true" : "false" })}><SelectionHint label="About the Top 100 event selection">100 editorial starting points across world history, through 2000. Events, empires and movements connect politics, religion, science, books and art. An unranked selection, open to revision.</SelectionHint></AtlasCheckbox>
 </>;
}
