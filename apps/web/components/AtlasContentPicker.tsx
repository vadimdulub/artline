"use client";
import { useEffect, useState } from "react";
import { apiRequest, errorMessage } from "@/lib/api";
import type { AtlasItem, AtlasMetadata, AtlasResponse, AtlasType } from "@/lib/atlas";
import type { BookRange } from "@/lib/books";
import { EntityPickerFilters } from "./EntityPickerFilters";
import { readEntityFilters } from "@/lib/atlas-filters";
import { RecordDrawer } from "./RecordDrawer";

export function AtlasContentPicker({ metadata, range, layers, initialType="artwork", browse=false, filterQuery, close, addLayer, open }: {
 metadata:AtlasMetadata; range:BookRange; layers:string[]; initialType?:AtlasType; browse?:boolean; filterQuery:string;
 close:()=>void; addLayer:(type:AtlasType, filters:URLSearchParams, range:BookRange)=>void; open:(item:AtlasItem)=>void;
}) {
 const [type,setType]=useState(initialType),[query,setQuery]=useState(""),[cursor,setCursor]=useState(""),[retry,setRetry]=useState(0);
 const [drafts,setDrafts]=useState(()=>Object.fromEntries(metadata.types.map(kind=>[kind.key,readEntityFilters(kind.key,new URLSearchParams(filterQuery)).toString()])));
 const filters=new URLSearchParams(drafts[type]);
 function changeFilters(values:Record<string,string|string[]|null>){const next=new URLSearchParams(drafts[type]);for(const [key,value] of Object.entries(values)){next.delete(key);if(value!==null)for(const v of Array.isArray(value)?value:[value])next.append(key,v)}setDrafts(previous=>({...previous,[type]:next.toString()}));setCursor("")}
 function resetFilters(defaults:boolean){setDrafts(previous=>({...previous,[type]:new URLSearchParams({[type==="artwork"?"popular":"top100"]:String(defaults)}).toString()}));setCursor("")}
 const [result,setResult]=useState<{key:string;data?:AtlasResponse;error?:string}>();
 const search=new URLSearchParams(browse?filterQuery:undefined);
 if(!browse){search.set("selection","false");search.set("start",String(range.start));search.set("end",String(range.end));search.set("highlights","false")}
 if(!browse){const current=new URLSearchParams(filterQuery);for(const name of ["country","continent"])for(const value of current.getAll(name))search.append(name,value)}
 // Add needs the matching total; only Browse renders a page of records.
 search.delete("type");search.append("type",type);
 search.set("limit",browse?"30":"1");if(query)search.set("q",query);if(cursor)search.set(`after_${type}`,cursor);
 if(!browse)for(const [field,value] of filters)search.append(`${type}_${field}`,value);
 const key=search.toString(),busy=result?.key!==key,data=result?.key===key?result.data:undefined,error=result?.key===key?result.error:undefined;
 const lane=data?.lanes.find(lane=>lane.key===type),definition=metadata.types.find(item=>item.key===type)!;
 useEffect(()=>{const c=new AbortController();const timer=setTimeout(()=>apiRequest<AtlasResponse>(`atlas?${key}`,{signal:c.signal}).then(data=>setResult({key,data})).catch(e=>{if(!c.signal.aborted)setResult({key,error:errorMessage(e)})}),140);return()=>{clearTimeout(timer);c.abort()}},[key,retry]);
 return <RecordDrawer label={browse?`Browse ${definition.name.toLowerCase()}`:"Add a layer"} closeLabel="Close content picker" title={browse?definition.name:"Add a layer"} recordKey={type} close={close} fallbackFocusId="all-timeline-title">
  <div className={`atlas-picker${browse?"":" atlas-layer-picker"}`}>
   <h2>{browse?definition.name:"Add a layer"}</h2>
   {!browse&&<><div className="atlas-picker-types" role="group" aria-label="Content type">{metadata.types.map(kind=><button key={kind.key} aria-pressed={type===kind.key} onClick={()=>{setType(kind.key);setCursor("")}}>{kind.name}</button>)}</div>
</>}
   {!browse&&<EntityPickerFilters type={type} params={filters} change={changeFilters} reset={resetFilters}/>}
   {browse&&<label><span>Search {definition.name.toLowerCase()}</span><input type="search" maxLength={200} value={query} onChange={e=>{setQuery(e.target.value);setCursor("")}} placeholder="Title or creator"/></label>}
   {error&&<div role="alert"><p>{error}</p><button onClick={()=>setRetry(v=>v+1)}>Retry entries</button></div>}
   {!busy&&!error&&lane?.total===0&&<p>No matching entries. Try another search or adjust the filters.</p>}
   {browse?<>
    <div role="status">{busy?"Finding entries…":`${lane?.total.toLocaleString("en-GB")??0} matching entries`}</div>
    {!error&&<ul className="atlas-picker-list" aria-label={`${definition.name} entries`}>{lane?.items.map(item=><li key={item.id}><div><strong>{item.title}</strong><span>{item.context}</span><time>{item.years}</time></div><button aria-label={`Read ${item.title}`} onClick={()=>open(item)}>Read</button></li>)}</ul>}
    <div className="atlas-picker-pages">{cursor&&<button disabled={busy} onClick={()=>setCursor("")}>First page</button>}{lane?.nextCursor&&<button disabled={busy} onClick={()=>setCursor(lane.nextCursor)}>Next page</button>}</div>
   </>:<div className="atlas-layer-action">
    <div role="status">{busy?"Finding entries…":error?"Count unavailable":`${lane?.total.toLocaleString("en-GB")??0} matching entries`}</div>
    <button className="atlas-add-layer" disabled={busy||Boolean(error)||!lane?.total} onClick={()=>addLayer(type,filters,range)}>{layers.includes(type)?`Update ${definition.name.toLowerCase()} layer`:`Add ${definition.name.toLowerCase()} layer`}</button>
   </div>}
  </div>
 </RecordDrawer>;
}
