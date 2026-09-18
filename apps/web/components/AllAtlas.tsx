"use client";
import { useEffect, useRef, useState } from "react";
import { apiRequest, errorMessage, safeSourceURL } from "@/lib/api";
import { updateQuery, useQueryString } from "@/lib/url-state";
import { bookTickPosition, bookYearAtPosition, bookYearLabel, positionBooks, bookAxisTicks, type BookRange } from "@/lib/books";
import { allEntityKeys, entityUpdates } from "@/lib/atlas-filters";
import type { AtlasItem, AtlasLane, AtlasMetadata, AtlasResponse, AtlasType } from "@/lib/atlas";
import { MultiSelectFilter } from "./MultiSelectFilter";
import { AtlasFilters, ActiveFilters, AtlasSelect, AtlasCheckbox } from "./AtlasFilters";
import { TimelineGrid, TimelineLanes, TimelineMark } from "./TimelineGrid";
import { TimelineOverview } from "./TimelineOverview";
import { TimelineRangeControls } from "./TimelineRangeControls";
import { BookDrawer } from "./BookDrawer";
import { EventDrawer } from "./EventDrawer";
import { AllArtworkDrawer } from "./AllArtworkDrawer";
import { AtlasContentPicker } from "./AtlasContentPicker";
import { RecordDrawer } from "./RecordDrawer";
import "./AllAtlas.css";

const allKinds:AtlasType[]=["artwork","book","event"];
const suggestions=["first-world-war","renaissance","french-revolution","byzantium","reformation","second-world-war"];
function Lane({lane,range,bounds,width,busy,selected,select,narrow,browse,remove}:{lane:AtlasLane;range:BookRange;bounds:BookRange;width:number;busy:boolean;selected:string;select:(item:AtlasItem)=>void;narrow:(start:number,end:number,kind:AtlasType)=>void;browse:()=>void;remove:()=>void}){
 const marks=positionBooks(lane.items,bounds,width),height=Math.max(1,...marks.map(item=>item.lane+1))*72+8;
 return <section className="all-lane" aria-labelledby={`all-lane-${lane.key}`}>
  <header><h2 id={`all-lane-${lane.key}`}><span style={{background:lane.color}} aria-hidden="true"/>{lane.name}</h2><span>{lane.total.toLocaleString("en-GB")}</span><button onClick={browse} disabled={busy} aria-label={`Browse ${lane.name.toLowerCase()}`}>Browse</button><button onClick={remove} aria-label={`Remove ${lane.name.toLowerCase()} from timeline`}>×</button></header>
  {lane.mode==="density"?<TimelineOverview color={lane.color} currentAction="Browse entries for" periods={lane.density} start={range.start} end={range.end} disabled={busy} noun={lane.key==="artwork"?"artworks":lane.key==="book"?"books":"events"} guidanceId="all-timeline-help" formatPeriod={(a,b)=>a===b?bookYearLabel(a):`${bookYearLabel(a)}–${bookYearLabel(b)}`} position={year=>bookTickPosition(year,bounds)} footnote="" onSelect={(a,b)=>narrow(a,b,lane.key)}/>:marks.length?<TimelineLanes label={`${lane.name} in the combined timeline`} descriptionId="all-timeline-help" height={height} loading={busy}>{marks.map(item=><TimelineMark key={item.id} name={item.title} context={item.context} date={item.years} label={`${item.title}, ${item.context}, ${item.years}. Open ${lane.singular.toLowerCase()} details`} color={lane.color} left={item.left} top={item.lane*72+6} width={item.width} labelOffset={item.labelOffset} labelWidth={item.labelWidth} approximate={item.approximate} selected={selected===item.id} disabled={busy} hasPopup="dialog" onSelect={()=>select(item)}/>)}</TimelineLanes>:<p className="all-lane-empty">{range.start>lane.cutoff?`${lane.name} end at ${lane.cutoff}.`:`No dated ${lane.name.toLowerCase()} match these filters.`}</p>}
 </section>;
}

export function AllAtlas(){
 const queryString=useQueryString(),params=new URLSearchParams(queryString);
 const shell=useRef<HTMLElement>(null),stage=useRef<HTMLDivElement>(null),search=useRef<HTMLInputElement>(null);
 const [metadata,setMetadata]=useState<AtlasMetadata>(),[metaError,setMetaError]=useState(""),[retry,setRetry]=useState(0),[width,setWidth]=useState(1000),[periodOpen,setPeriodOpen]=useState(false);
 const [geography,setGeography]=useState<{countries:{slug:string;name:string}[];error?:string}>({countries:[]});
 const [result,setResult]=useState<{key:string;data?:AtlasResponse;error?:string}>();
 const presetID=params.get("preset")??"",windowKind=params.get("window")??"context",preset=metadata?.presets.find(p=>p.id===presetID);
 const layers=params.getAll("type").length?params.getAll("type"):presetID&&!params.has("selection")?allKinds:[];
 const populated=layers.length>0;
 const bounds=metadata?.bounds??{start:-12000,end:2000},fallback=preset?.[windowKind==="period"?"period":"context"]??bounds;
 const targetRange={start:params.has("start")?Number(params.get("start")):fallback.start,end:params.has("end")?Number(params.get("end")):fallback.end};
 const query=params.get("q")??"",region=params.get("region")??"",highlights=params.get("highlights")!=="false";
 const countries=params.getAll("country"),continents=params.getAll("continent");
 const request=new URLSearchParams({selection:"true",highlights:String(highlights)});
 for(const key of ["preset","window","start","end","q","region","country","continent",...allEntityKeys])params.getAll(key).forEach(value=>request.append(key,value));
 for(const kind of layers)request.append("type",kind);
 const requestKey=request.toString(),busy=populated&&result?.key!==requestKey;
 const data=populated?result?.data:undefined,error=populated&&result?.key===requestKey?result.error:undefined,range=data?.range??targetRange;
 const selected=params.get("item")??"",selectedType=params.get("itemType"),panel=params.get("panel"),browseKind=params.get("browse") as AtlasType|null;
 useEffect(()=>{const c=new AbortController();apiRequest<AtlasMetadata>("atlas/presets",{signal:c.signal}).then(value=>{setMetadata(value);setMetaError("")}).catch(e=>{if(!c.signal.aborted)setMetaError(errorMessage(e))});return()=>c.abort()},[retry]);
 useEffect(()=>{const c=new AbortController();apiRequest<{countries:{slug:string;name:string}[]}>("atlas/geography",{signal:c.signal}).then(setGeography).catch(e=>{if(!c.signal.aborted)setGeography(previous=>({...previous,error:errorMessage(e)}))});return()=>c.abort()},[retry]);
 useEffect(()=>{if(!populated)return;const c=new AbortController();const timer=setTimeout(()=>apiRequest<AtlasResponse>(`atlas?${requestKey}`,{signal:c.signal}).then(data=>setResult({key:requestKey,data})).catch(e=>{if(!c.signal.aborted)setResult({key:requestKey,error:errorMessage(e)})}),140);return()=>{clearTimeout(timer);c.abort()}},[requestKey,populated,retry]);
 useEffect(()=>{const header=document.querySelector('.site-header');if(!header)return;const observer=new ResizeObserver(()=>shell.current?.style.setProperty('--all-header-height',`${header.getBoundingClientRect().height}px`));observer.observe(header);return()=>observer.disconnect()},[]);
 useEffect(()=>{if(!stage.current)return;const observer=new ResizeObserver(entries=>setWidth(entries[0].contentRect.width));observer.observe(stage.current);return()=>observer.disconnect()},[populated]);
 function change(values:Record<string,string|string[]|null>,push=true){updateQuery({selection:"true",book_collection:null,pick_artwork:null,pick_book:null,pick_event:null,after_artwork:null,after_book:null,after_event:null,item:null,itemType:null,...values},push)}
 function reset(){change({...Object.fromEntries(allEntityKeys.map(key=>[key,null])),preset:null,window:null,start:null,end:null,q:null,type:null,country:null,continent:null,region:null,highlights:null,panel:null,browse:null,add:null});setPeriodOpen(false)}
 function selectPreset(id:string){if(!id)return;change({...Object.fromEntries(allEntityKeys.map(key=>[key,null])),preset:id,window:"context",start:null,end:null,type:allKinds,q:null,country:null,continent:null,region:null,highlights:null,panel:null,browse:null})}
 function setRange(start:number,end:number){change({preset:null,window:null,start:String(start),end:String(end)})}
 function browse(kind:AtlasType){updateQuery({panel:null,browse:kind,item:null,itemType:null},true)}
 function narrow(start:number,end:number,kind:AtlasType){if(start===end){if(end<range.end)end+=end===-1?2:1;else start-=start===1?2:1}if(start===range.start&&end===range.end){browse(kind);return}setRange(start,end)}
 function open(item:AtlasItem){updateQuery({item:item.id,itemType:item.type,panel:null,browse:null},true)}
 function close(){updateQuery({item:null,itemType:null},true)}
 function remove(kind:AtlasType){change({...entityUpdates(kind),type:layers.filter(t=>t!==kind)})}
 function addLayer(kind:AtlasType,filters:URLSearchParams,years:BookRange){change({...entityUpdates(kind,filters),type:[...new Set([...layers,kind])],q:null,region:null,start:String(years.start),end:String(years.end),panel:null,browse:null})}
 function clearFilters(){change({q:null,country:null,continent:null,region:null,highlights:"false"})}
 const activeFilters=[
  ...(query?[{key:"q",label:`Search: ${query}`,remove:()=>change({q:null})}]:[]),
  ...(highlights?[{key:"highlights",label:"Highlights",remove:()=>change({highlights:"false"})}]:[]),
  ...(region?[{key:"region",label:metadata?.regions.find(option=>option.slug===region)?.name??region,remove:()=>change({region:null})}]:[]),
  ...[{key:"country",values:countries,options:geography.countries},{key:"continent",values:continents,options:metadata?.continents??[]}].flatMap(group=>group.values.map(value=>({key:`${group.key}-${value}`,label:group.options.find(option=>option.slug===value)?.name??value,remove:()=>change({[group.key]:group.values.filter(item=>item!==value)})}))),
 ];
 const ticks=bookAxisTicks(bounds,width);
 const band=preset&&windowKind==="context"&&!params.has("start")?{left:bookTickPosition(preset.period.start,bounds),right:bookTickPosition(preset.period.end,bounds)}:null;
 return <section ref={shell} className="explorer all-explorer" aria-labelledby="all-timeline-title">
  {geography.error&&<p className="save-message" role="status">Some filter choices could not be loaded. <button onClick={()=>setRetry(v=>v+1)}>Retry filters</button></p>}
  <AtlasFilters searchRef={search} query={query} onQuery={value=>change({q:value||null},false)} onReset={reset} searchLabel="Search the timeline" placeholder="Title, creator or event" columns={4} activeCount={activeFilters.filter(filter=>filter.key!=="q").length}
   actions={<button className="reset-button all-add-button" onClick={()=>updateQuery({panel:"add",browse:null,item:null,itemType:null},true)} disabled={!metadata}>+ Add</button>}>
   <div className="all-period-filter">
    <label className="atlas-select"><span>Historical period</span><select aria-label="Historical period" value={presetID} onChange={e=>selectPreset(e.target.value)}><option value="">{populated?"Choose a period…":"Start with a period…"}</option>{[...new Set(metadata?.presets.map(p=>p.group)??[])].map(group=><optgroup key={group} label={group}>{metadata!.presets.filter(p=>p.group===group).map(p=><option key={p.id} value={p.id}>{p.name}</option>)}</optgroup>)}</select></label>
    {preset&&<button type="button" className="all-period-info selection-info" aria-label="About this period" title="About this period" aria-haspopup="dialog" onClick={()=>setPeriodOpen(true)}>ⓘ</button>}
   </div>
   <MultiSelectFilter label="Continents" allLabel="All continents" values={continents} options={metadata?.continents??[]} onChange={values=>change({continent:values})}/>
   <MultiSelectFilter label="Countries" allLabel="All countries" values={countries} options={geography.countries} unavailable={Boolean(geography.error)} retry={()=>setRetry(v=>v+1)} onChange={values=>change({country:values})} helpText="Recorded country associations. Historical states remain separate; a country filter applies across all layers."/>
   <AtlasSelect label="Region" value={region} onChange={value=>change({region:value||null})} options={[{value:"",label:"All regions"},...(metadata?.regions??[]).map(r=>({value:r.slug,label:r.name}))]}/>
   <AtlasCheckbox label="Highlights" checked={highlights} onChange={checked=>change({highlights:checked?null:"false"})}/>
  </AtlasFilters>
  <ActiveFilters filters={activeFilters} onClear={clearFilters} searchRef={search}/>
  <div className={`timeline-dark${populated?"":" all-empty-canvas"}`}>
   {metaError&&<p role="alert">Periods could not be loaded. <button onClick={()=>setRetry(v=>v+1)}>Retry periods</button></p>}
   {populated?<>
    <div className="all-canvas-heading"><h1 className="time-title" data-bce={range.start<0||range.end<0} id="all-timeline-title" tabIndex={-1}>{bookYearLabel(range.start)}<span aria-hidden="true">—</span><span className="sr-only"> to </span>{bookYearLabel(range.end)}</h1><span role="status">{busy?"Loading…":error?"Couldn’t load":`${data?.total.toLocaleString("en-GB")??0} entries`}</span><button onClick={reset}>Clear</button></div>
    <TimelineGrid stageRef={stage} busy={busy} selection={{left:bookTickPosition(range.start,bounds),right:bookTickPosition(range.end,bounds)}} ticks={ticks.map(t=>({key:t.year,label:t.label,position:bookTickPosition(t.year,bounds)}))}>
     {band&&band.right>band.left&&<div className="all-period-band" aria-hidden="true" style={{left:`${band.left}%`,width:`${band.right-band.left}%`}}/>}
     {error?<div className="state-panel" role="alert"><h2>We couldn’t load this view</h2><p>{error}</p><button onClick={()=>setRetry(v=>v+1)}>Retry</button> <button onClick={reset}>Reset view</button></div>:data?.lanes.map(lane=><Lane key={lane.key} lane={lane} range={range} bounds={bounds} width={width} busy={busy} selected={selected} select={open} narrow={narrow} browse={()=>browse(lane.key)} remove={()=>remove(lane.key)}/>)}
    </TimelineGrid>
    <p className="sr-only" id="all-timeline-help">Select an entry for details. Select a busy period to narrow every lane, or Browse to see its entries.</p>
    <TimelineRangeControls start={range.start} end={range.end} minimum={bounds.start} maximum={bounds.end} onChange={setRange} omitYearZero inputPrefix="All " formatYear={bookYearLabel} endpoints={[bookYearLabel(bounds.start),bookYearLabel(bounds.end)]} scale={{position:year=>bookTickPosition(year,bounds),yearAt:position=>bookYearAtPosition(position,bounds),markers:[1700,1900].map(year=>({year,label:String(year)}))}} disabled={Boolean(error)}/>
   </>:<div className="all-start"><h1 id="all-timeline-title" tabIndex={-1}>Choose a starting point</h1><div className="all-suggestions">{suggestions.map(id=>metadata?.presets.find(p=>p.id===id)).filter(p=>p!==undefined).map(p=><button key={p.id} onClick={()=>selectPreset(p.id)}>{p.name}</button>)}</div><p>Or use Add to choose artwork, book and event layers.</p></div>}
  </div>
  {periodOpen&&preset&&<RecordDrawer label="Historical period details" closeLabel="Close period details" recordKey={preset.id} title="Historical period" close={()=>setPeriodOpen(false)} fallbackFocusId="all-timeline-title"><div className="atlas-picker">
   <h2>{preset.name}</h2><p>{preset.description}</p>
   <AtlasSelect label="Time window" value={windowKind} onChange={value=>change({window:value,start:null,end:null})} options={[{value:"context",label:"Before and after"},{value:"period",label:"Main period"}]}/>
   <div className="all-preset-details"><p>Main period: {bookYearLabel(preset.period.start)}–{bookYearLabel(preset.period.end)}. Entries share these years; this does not establish influence.</p>{preset.sources.map(source=><a key={source.url} href={safeSourceURL(source.url)} target="_blank" rel="noreferrer">{source.name}</a>)}</div>
  </div></RecordDrawer>}
  {!periodOpen&&metadata&&(panel==="add"||allKinds.includes(browseKind!))&&<AtlasContentPicker key={browseKind??"add"} metadata={metadata} range={range} layers={layers} initialType={browseKind??"artwork"} browse={Boolean(browseKind)} filterQuery={requestKey} close={()=>updateQuery({panel:null,browse:null},true)} addLayer={addLayer} open={open}/>}
  {!periodOpen&&!panel&&!browseKind&&selected&&selectedType==="book"&&<BookDrawer id={selected} items={[]} close={close} select={id=>updateQuery({item:id},true)} fallbackFocusId="all-timeline-title"/>}
  {!periodOpen&&!panel&&!browseKind&&selected&&selectedType==="event"&&<EventDrawer id={selected} close={close} fallbackFocusId="all-timeline-title"/>}
  {!periodOpen&&!panel&&!browseKind&&selected&&selectedType==="artwork"&&<AllArtworkDrawer id={selected} close={close}/>}
 </section>;
}
