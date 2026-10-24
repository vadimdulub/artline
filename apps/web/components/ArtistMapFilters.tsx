"use client";
import { MapMenu } from "./MapMenu";
import { artistPlaceFilters } from "@/lib/map";

export function ArtistMapFilters({ selected, toggle }: { selected: string[]; toggle: (value: string) => void }) {
  function option(filter: typeof artistPlaceFilters[number]) {
    return <label key={filter.value}><input type="checkbox" checked={selected.includes(filter.value)} onChange={() => toggle(filter.value)} />{filter.label}</label>;
  }
  const more = artistPlaceFilters.slice(3);
  return <fieldset className="map-relation-filters"><legend className="sr-only">Show places connected with</legend>
    <div className="map-primary-relations">{artistPlaceFilters.slice(0, 3).map(option)}</div>
    <MapMenu className="map-more-relations" label={<>More places<span>{more.filter(f => selected.includes(f.value)).length}</span></>}><div>{more.map(option)}</div></MapMenu>
  </fieldset>;
}
