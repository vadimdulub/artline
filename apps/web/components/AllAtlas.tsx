"use client";
import { displayMetadata } from "@/lib/display-metadata";
import { ExplorerFrame } from "./ExplorerFrame";
import { useFitYears } from "./use-fit-years";
import { timelineRequestKey } from "@/lib/timeline-request";
import { discoveryChanges } from "@/lib/discovery";
import { useEffect, useRef, useState, type CSSProperties } from "react";
import { apiRequest, errorMessage } from "@/lib/api";
import { updateQuery, useQueryString } from "@/lib/url-state";
import { bookTickPosition, bookYearAtPosition, bookYearLabel, positionBooks, type BookRange } from "@/lib/books";
import { atlasTimelineScale } from "@/lib/atlas-timeline";
import { allAtlasKinds as allKinds, allEntityKeys, atlasLayers, entityFields, entityUpdates, layersAfterFilter } from "@/lib/atlas-filters";
import type { AtlasItem, AtlasLane, AtlasMetadata, AtlasResponse, AtlasType } from "@/lib/atlas";
import { MultiSelectFilter } from "./MultiSelectFilter";
import { AtlasFilters, ActiveFilters, AtlasSelect, AtlasCheckbox } from "./AtlasFilters";
import { TimelineGrid, TimelineLanes, TimelineMark } from "./TimelineGrid";
import { TimelineOverview } from "./TimelineOverview";
import { TimelineRangeControls } from "./TimelineRangeControls";
import { TimelineZoomOut } from "./TimelineZoomOut";
import { TimelineHeader } from "./TimelineHeader";
import { TimelinePopover } from "./TimelinePopover";
import { BookDrawer } from "./BookDrawer";
import { EventDrawer } from "./EventDrawer";
import { useRecordNavigation } from "./RecordNavigation";
import { AllArtworkDrawer } from "./AllArtworkDrawer";
import { AtlasContentPicker } from "./AtlasContentPicker";
import { LoadingIndicator } from "./LoadingIndicator";
import { AllStartingPoints } from "./AllStartingPoints";
import { AllArtworkGallery, GalleryScrollButtons } from "./AllArtworkGallery";
import { AllBookGallery } from "./AllBookGallery";
import { resolvedStartingFilters, startingFilters } from "@/lib/atlas-starting-points";
import { useAtlasCreators } from "./use-atlas-creators";
import "./AllAtlas.css";

const linearFrom=1400;
function Lane({lane,range,position,width,busy,loadingRange,selected,select,narrow,browse,isolated,onIsolate,galleryQuery}:{lane:AtlasLane;range:BookRange;position:(year:number)=>number;width:number;busy:boolean;loadingRange:boolean;selected:string;select:(item:AtlasItem)=>void;narrow:(start:number,end:number,kind:AtlasType)=>void;browse:()=>void;isolated:boolean;onIsolate:()=>void;galleryQuery:string}){
 const strip=useRef<HTMLUListElement>(null);
 const bookGallery=lane.key==="book"&&lane.mode==="density";
 const focusLabel=isolated?"Show all types":`Show only ${lane.name.toLowerCase()}`;
 // Narrower years reveal larger reproductions. Isolating Artworks also gives
 // its images more of the canvas without changing server pages or ordering.
 const dateZoom=Math.min(1,Math.max(0,Math.log2(600/Math.max(1,range.end-range.start))/6));
 const artworkZoom=isolated ? 0.65 + 0.35 * dateZoom : dateZoom;
 const marks=positionBooks(loadingRange||bookGallery?[]:lane.items,range,width,linearFrom,position),height=Math.max(1,...marks.map(item=>item.lane+1))*72+8;
 return <section className={`all-lane${lane.key==="artwork"?" all-artwork-lane":bookGallery?" all-book-gallery-lane":""}`} style={lane.key==="artwork"?{"--artwork-zoom":artworkZoom} as CSSProperties:undefined} aria-labelledby={`all-lane-${lane.key}`}>
  <header><h2 id={`all-lane-${lane.key}`}><button type="button" onClick={browse} disabled={busy} aria-haspopup="dialog"><span style={{background:lane.color}} aria-hidden="true"/>{lane.name}</button></h2><button type="button" className="all-lane-focus" data-isolated={isolated} aria-label={focusLabel} title={focusLabel} onClick={onIsolate}><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d={isolated?"M3 8h5V3m8 0v5h5m0 8h-5v5M8 21v-5H3":"M8 3H3v5m13-5h5v5m0 8v5h-5M8 21H3v-5"}/></svg></button><span>{lane.total.toLocaleString("en-GB")}</span>{(lane.key==="artwork"||bookGallery)&&lane.items.length>0&&<GalleryScrollButtons strip={strip} disabled={busy||loadingRange} noun={lane.key==="book"?"books":"artworks"}/>}</header>
  {loadingRange||busy?<p className="all-lane-empty"><LoadingIndicator label="Loading these years…"/></p>:lane.key==="artwork"&&lane.items.length?<AllArtworkGallery key={galleryQuery} lane={lane} query={galleryQuery} busy={busy} selected={selected} select={select} stripRef={strip} inlineControls={false} showDetails={false}/>:bookGallery&&lane.items.length?<AllBookGallery key={galleryQuery} lane={lane} query={galleryQuery} busy={busy} selected={selected} select={select} stripRef={strip}/>:lane.mode==="density"?<TimelineOverview color={lane.color} currentAction="Browse entries for" showCurrentAction={false} periods={lane.density} start={range.start} end={range.end} disabled={busy} noun={lane.key==="artwork"?"artworks":lane.key==="book"?"books":"events"} guidanceId="all-timeline-help" formatPeriod={(a,b)=>a===b?bookYearLabel(a):`${bookYearLabel(a)}–${bookYearLabel(b)}`} position={position} footnote="" onSelect={(a,b)=>narrow(a,b,lane.key)}/>:marks.length?<TimelineLanes label={`${lane.name} in the combined timeline`} descriptionId="all-timeline-help" height={height} loading={busy}>{marks.map(item=><TimelineMark key={item.id} name={item.title} context={displayMetadata(item.context) ? (item.relation==="context"?`Context · ${item.context}`:item.context) : undefined} date={displayMetadata(item.years) ?? ""} label={`${[item.title, displayMetadata(item.context), displayMetadata(item.years)].filter(Boolean).join(", ")}. Open ${lane.singular.toLowerCase()} details`} color={lane.color} left={item.left} top={item.lane*72+6} width={item.width} labelOffset={item.labelOffset} labelWidth={item.labelWidth} approximate={item.approximate} selected={selected===item.id} disabled={busy} hasPopup="dialog" onSelect={()=>select(item)}/>)}</TimelineLanes>:<p className="all-lane-empty">{range.start>lane.cutoff?`${lane.name} end at ${lane.cutoff}.`:`No dated ${lane.name.toLowerCase()} match these filters.`}</p>}
 </section>;
}

export function AllAtlas(){
 const queryString=useQueryString(),rawParams=new URLSearchParams(queryString);
 const shell=useRef<HTMLElement>(null),stage=useRef<HTMLDivElement>(null),search=useRef<HTMLInputElement>(null);
 const [metadata,setMetadata]=useState<AtlasMetadata>(),[metaError,setMetaError]=useState(""),[retry,setRetry]=useState(0),[width,setWidth]=useState(1000);
 const [geography,setGeography]=useState<{countries:{slug:string;name:string}[];error?:string}>({countries:[]});
 const [result,setResult]=useState<{key:string;attempt:number;data?:AtlasResponse;error?:string}>();
 const [rangePreview,setRangePreview]=useState<BookRange|null>(null);
 const presetID=rawParams.get("preset")??"",windowKind=rawParams.get("window")??"context",preset=metadata?.presets.find(p=>p.id===presetID);
 const params=resolvedStartingFilters(rawParams,preset);
 const layers=atlasLayers(params);
 const populated=layers.length>0;
 const bounds=metadata?.bounds??{start:-12000,end:2000},fallback=preset?.[windowKind==="period"?"period":"context"]??bounds;
 const targetRange={start:params.has("start")?Number(params.get("start")):fallback.start,end:params.has("end")?Number(params.get("end")):fallback.end};
 const query=params.get("q")??"",region=params.get("region")??"",highlights=params.get("highlights")!=="false";
 const countries=params.getAll("country"),continents=params.getAll("continent"),creators=params.getAll("creator");
 const creatorChoices=useAtlasCreators(creators);
 const artworkCountries=params.get("country_scope")==="artwork";
 const request=new URLSearchParams({selection:"true",highlights:String(highlights),preset_filters:"custom"});
 for(const key of ["fit","preset","window","start","end","q","region","country","country_scope","continent","creator","after_artwork",...allEntityKeys])params.getAll(key).forEach(value=>request.append(key,value));
 request.set("artwork_image_only","true");
 for(const kind of layers)request.append("type",kind);
 const requestKey=timelineRequestKey(request,fallback),busy=populated&&(result?.key!==requestKey||result?.attempt!==retry);
 const data=populated?result?.data:undefined,error=populated&&!busy?result?.error:undefined;
 // Selection is interaction state. A slow response must never move the handles back.
 // Invalid shared URLs still reach server validation, but cannot break the chart geometry.
 const validRange=Number.isInteger(targetRange.start)&&Number.isInteger(targetRange.end)&&targetRange.start!==0&&targetRange.end!==0&&targetRange.start>=bounds.start&&targetRange.end<=bounds.end&&targetRange.start<targetRange.end;
 const range=validRange?targetRange:fallback,displayRange=rangePreview??range;
 useFitYears(params.get("fit")==="true", !!data&&!busy&&!error, data?.matchedRange);
 const selected=params.get("item")??"",selectedType=params.get("itemType"),panel=params.get("panel"),browseKind=params.get("browse") as AtlasType|null;
 useEffect(()=>{const c=new AbortController();apiRequest<AtlasMetadata>("atlas/presets",{signal:c.signal}).then(value=>{setMetadata(value);setMetaError("")}).catch(e=>{if(!c.signal.aborted)setMetaError(errorMessage(e))});return()=>c.abort()},[retry]);
 useEffect(()=>{const c=new AbortController();apiRequest<{countries:{slug:string;name:string}[]}>("atlas/geography",{signal:c.signal}).then(setGeography).catch(e=>{if(!c.signal.aborted)setGeography(previous=>({...previous,error:errorMessage(e)}))});return()=>c.abort()},[retry]);
 useEffect(()=>{if(!populated||presetID&&!metadata)return;const c=new AbortController();const timer=setTimeout(()=>apiRequest<AtlasResponse>(`atlas?${requestKey}`,{signal:c.signal}).then(data=>{if(!c.signal.aborted)setResult({key:requestKey,attempt:retry,data})}).catch(e=>{if(!c.signal.aborted)setResult(previous=>({key:requestKey,attempt:retry,data:previous?.data,error:errorMessage(e)}))}),140);return()=>{clearTimeout(timer);c.abort()}},[requestKey,populated,retry,presetID,metadata]);
 useEffect(()=>{const header=document.querySelector('.site-header');if(!header)return;const observer=new ResizeObserver(()=>shell.current?.style.setProperty('--all-header-height',`${header.getBoundingClientRect().height}px`));observer.observe(header);return()=>observer.disconnect()},[]);
 useEffect(()=>{if(!stage.current)return;const observer=new ResizeObserver(entries=>setWidth(entries[0].contentRect.width));observer.observe(stage.current);return()=>observer.disconnect()},[populated]);
 function change(values:Record<string,string|string[]|null>,push=true){setRangePreview(null);values=discoveryChanges(values,"highlights");updateQuery({fit:null,selection:"true",type:layers,creator:creators,country:countries,country_scope:params.get("country_scope"),highlights:String(highlights),preset_filters:"custom",book_collection:null,pick_artwork:null,pick_book:null,pick_event:null,after_artwork:null,after_book:null,after_event:null,item:null,itemType:null,...(Object.hasOwn(values,"country")&&(!values.country||Array.isArray(values.country)&&values.country.length===0)?{country_scope:null}:{}),...values},push)}
 function changeFilter(values:Record<string,string|string[]|null>,push=true){change({type:layersAfterFilter(layers,values),...(Object.hasOwn(values,"highlights")?{book_top100:null,event_top100:null}:{}),...values},push)}
 function reset(){change({...Object.fromEntries(allEntityKeys.map(key=>[key,null])),preset:null,preset_filters:null,window:null,start:null,end:null,q:null,type:null,creator:null,country:null,country_scope:null,continent:null,region:null,highlights:null,panel:null,browse:null,add:null})}
 function selectPreset(id:string){const next=metadata?.presets.find(p=>p.id===id);change({...(id?{...Object.fromEntries(allEntityKeys.map(key=>[key,null])),q:null,...startingFilters(next),highlights:"false",artwork_popular:"false",book_top100:"false",event_top100:"false",fit:"true"}:{}),preset:id||null,window:id?"context":null,start:null,end:null,type:id&&!populated?allKinds:layers,panel:null,browse:null})}
 function setRange(start:number,end:number){change({window:null,start:String(start),end:String(end)})}
 function browse(kind:AtlasType){updateQuery({panel:null,browse:kind,item:null,itemType:null},true)}
 function narrow(start:number,end:number,kind:AtlasType){if(start===end){if(end<range.end)end+=end===-1?2:1;else start-=start===1?2:1}if(start===range.start&&end===range.end){browse(kind);return}change({window:null,start:String(start),end:String(end),highlights:"false",artwork_popular:"false",book_top100:"false",event_top100:"false",fit:"true"})}
 const [navigationScope,setNavigationScope]=useState<{base:string;query:string}>();
 const neighborQuery=new URLSearchParams(navigationScope?.base===requestKey?navigationScope.query:requestKey);
 neighborQuery.delete("type");if(selectedType)neighborQuery.set("type",selectedType);
 const navigation=useRecordNavigation(selected&&allKinds.includes(selectedType as AtlasType)?`atlas?${neighborQuery}`:null,selected,id=>updateQuery({item:id},true));
 function open(item:AtlasItem,scope=requestKey){setNavigationScope({base:requestKey,query:scope});updateQuery({item:item.id,itemType:item.type,panel:null,browse:null},true)}
 function close(){updateQuery({item:null,itemType:null},true)}
 function remove(kind:AtlasType){change({...entityUpdates(kind),type:layers.filter(t=>t!==kind)})}
 function addLayer(kind:AtlasType,filters:URLSearchParams,years:BookRange){change({...entityUpdates(kind,filters),type:[...new Set([...layers,kind])],start:String(years.start),end:String(years.end),panel:null,browse:null})}
 function clearFilters(){changeFilter({...Object.fromEntries(allEntityKeys.map(key=>[key,null])),q:null,creator:null,country:null,country_scope:null,continent:null,region:null,highlights:"false",...(presetID?{preset:null,window:null,start:null,end:null}:{})})}
 const activeFilters=[
  ...(query?[{key:"q",label:`Search: ${query}`,remove:()=>change({q:null})}]:[]),
  ...(presetID?[{key:"preset",label:preset?.name??presetID.replaceAll("-"," "),remove:()=>selectPreset("")}]:[]),
  ...(highlights&&populated?[{key:"highlights",label:"Highlights",remove:()=>changeFilter({highlights:"false"})}]:[]),
  ...allKinds.flatMap(kind=>{const fields=entityFields[kind].filter(field=>field!=="image_only"&&params.getAll(`${kind}_${field}`).some(value=>value!=="false"&&value.trim()));return fields.length?[{key:`${kind}-filters`,label:`${kind==="artwork"?"Artworks":kind==="book"?"Books":"Events"}: ${fields.length} ${fields.length===1?"filter":"filters"}`,remove:()=>changeFilter(entityUpdates(kind))}]:[]}),
  ...(creators.length>3?[{key:"creators",label:`${creators.length} creators`,remove:()=>change({creator:null})}]:creators.map(value=>({key:`creator-${value}`,label:creatorChoices.options.find(option=>option.slug===value)?.name??value.split(":")[1],remove:()=>change({creator:creators.filter(item=>item!==value)})}))),
  ...(region?[{key:"region",label:metadata?.regions.find(option=>option.slug===region)?.name??region,remove:()=>change({region:null})}]:[]),
  ...[{key:"country",values:countries,options:geography.countries},{key:"continent",values:continents,options:metadata?.continents??[]}].flatMap(group=>group.values.length>3?[{key:group.key,label:`${group.values.length} ${group.key==="country"?"countries":"continents"}`,remove:()=>change({[group.key]:null})}]:group.values.map(value=>({key:`${group.key}-${value}`,label:group.options.find(option=>option.slug===value)?.name??value,remove:()=>change({[group.key]:group.values.filter(item=>item!==value)})}))),
 ];
 const {focused,position,ticks}=atlasTimelineScale(range,bounds,width);
 const loadingRange=data?.range.start!==range.start||data?.range.end!==range.end;
 return <ExplorerFrame ref={shell} className="explorer all-explorer" aria-labelledby="all-timeline-title">
  {geography.error&&<p className="save-message" role="status">Some filter choices could not be loaded. <button onClick={()=>setRetry(v=>v+1)}>Retry filters</button></p>}
  <AtlasFilters searchRef={search} query={query} onQuery={value=>changeFilter({q:value||null},false)} onReset={reset} resetLabel="Show starting points" searchLabel="Search the timeline" placeholder="Title, creator or event" columns={5} activeCount={activeFilters.filter(filter=>filter.key!=="q").length}>
   <div className="all-period-filter">
    <MultiSelectFilter label="Period or theme" allLabel="All periods & themes" single values={presetID?[presetID]:[]} options={(metadata?.presets??[]).map(p=>({slug:p.id,name:p.name,group:p.group,detail:`${bookYearLabel(p.period.start)}–${bookYearLabel(p.period.end)}`,description:p.startingScope,searchText:p.description}))} onChange={values=>selectPreset(values[0]??"")} unavailable={Boolean(metaError)} retry={()=>setRetry(v=>v+1)} helpText="Explore connected art, books and events. Each starting point sets the years and a focus you can change."/>
   </div>
   <MultiSelectFilter label="Creators" allLabel="All creators" values={creators} {...creatorChoices} onChange={values=>changeFilter({creator:values})} helpText="Choose painters and book authors together. Artworks and books match the selected people; events keep the historical context."/>
   <MultiSelectFilter label="Continents" allLabel="All continents" values={continents} options={metadata?.continents??[]} onChange={values=>changeFilter({continent:values})}/>
   <MultiSelectFilter label={artworkCountries?"Artwork countries":"Countries"} allLabel="All countries" values={countries} options={geography.countries} unavailable={Boolean(geography.error)} retry={()=>setRetry(v=>v+1)} onChange={values=>changeFilter({country:values})} helpText={artworkCountries?"Country focus for artworks. Books and events retain the period context. Historical states remain separate.":"Recorded country associations across all layers. Multiple countries include matches from any selected country. Historical states remain separate."}/>
   <AtlasSelect label="Region" value={region} onChange={value=>changeFilter({region:value||null})} options={[{value:"",label:"All regions"},...(metadata?.regions??[]).map(r=>({value:r.slug,label:r.name}))]}/>
   <AtlasCheckbox label="Highlights" checked={highlights} onChange={checked=>changeFilter({highlights:String(checked)})}/>
  </AtlasFilters>
  <ActiveFilters filters={activeFilters} onClear={clearFilters} searchRef={search}/>
  <div className={`timeline-dark${populated?"":" all-empty-canvas"}`}>
   {metaError&&<p role="alert">Periods could not be loaded. <button onClick={()=>setRetry(v=>v+1)}>Retry periods</button></p>}
   {populated?<>
    <TimelineHeader className="all-canvas-heading"
      status={busy?"Loading entries…":error?"Couldn’t load":`${data?.total.toLocaleString("en-GB")??0} entries`}
      zoom={<TimelineZoomOut disabled={!focused&&validRange&&!presetID} title="Show all years and keep layers and filters" onClick={()=>selectPreset("")}/>}
      controls={<>
        <TimelinePopover className="all-view-context" label={preset?.name??"View details"}>
          {preset&&<><h2>{preset.name}</h2><p>{preset.description}</p><p className="all-scope-description">{preset.startingScope}</p><p>Main period: {bookYearLabel(preset.period.start)}–{bookYearLabel(preset.period.end)}. Wider context: {bookYearLabel(preset.context.start)}–{bookYearLabel(preset.context.end)}.</p></>}
          {creators.length>0&&<p>Artworks and books by the selected creators. Their work gives cultural context; individual pictures may have other subjects.</p>}
          {countries.length>0&&<div className="all-country-focus"><p>{artworkCountries?`Artwork focus: ${countries.length} ${countries.length===1?"country":"countries"}. Books and events keep the period context.`:`Country filters apply to all entries.`} <button onClick={()=>change({country:null,country_scope:null})}>{preset?.focus?.global||!preset?"Show all countries":"Use full period focus"}</button></p><label><input type="checkbox" checked={!artworkCountries} onChange={event=>change({country_scope:event.target.checked?null:"artwork"})}/><span>Apply countries to books and events too</span></label></div>}
          <button onClick={reset}>Clear</button>
        </TimelinePopover>
        <fieldset className="all-layer-switches"><legend>Show</legend>{(metadata?.types??[]).map(kind=><label key={kind.key}><input type="checkbox" checked={layers.includes(kind.key)} onChange={event=>event.target.checked?change({type:allKinds.filter(value=>value===kind.key||layers.includes(value))}):remove(kind.key)}/><span>{kind.name}</span></label>)}</fieldset>
      </>}>
      <h1 className="time-title" data-bce={displayRange.start<0||displayRange.end<0} id="all-timeline-title" tabIndex={-1}>{bookYearLabel(displayRange.start)}<span aria-hidden="true">—</span><span className="sr-only"> to </span>{bookYearLabel(displayRange.end)}</h1>
    </TimelineHeader>
    <TimelineGrid stageRef={stage} busy={busy} ticks={ticks.map(t=>({key:t.year,label:t.label,position:position(t.year)}))}>
     {error?<div className="state-panel" role="alert"><h2>We couldn’t load this view</h2><p>{error}</p><button onClick={()=>setRetry(v=>v+1)}>Retry</button> <button onClick={reset}>Reset view</button></div>:data?.lanes.filter(lane=>layers.includes(lane.key)).map(lane=><Lane key={lane.key} lane={lane} range={range} position={position} width={width} busy={busy} loadingRange={loadingRange} selected={selected} select={open} narrow={narrow} browse={()=>browse(lane.key)} isolated={layers.length===1} onIsolate={()=>change({type:layers.length===1?allKinds:[lane.key],panel:null,browse:null})} galleryQuery={result?.key??requestKey}/>)}
    </TimelineGrid>
    <p className="sr-only" id="all-timeline-help">Select an entry for details. Select a busy period or edit the years to zoom every lane to that interval. Zoom out returns to all years and keeps your layers and filters. Select a lane heading to open its entries for the selected years.</p>
    <TimelineRangeControls start={range.start} end={range.end} minimum={bounds.start} maximum={bounds.end} onChange={setRange} onPreview={setRangePreview} omitYearZero inputPrefix="All " formatYear={bookYearLabel} endpoints={[bookYearLabel(bounds.start),bookYearLabel(bounds.end)]} scale={{position:year=>bookTickPosition(year,bounds,linearFrom),yearAt:position=>bookYearAtPosition(position,bounds,linearFrom),markers:[linearFrom,1700].map(year=>({year,label:String(year)}))}}/>
   </>:metadata?<AllStartingPoints metadata={metadata} select={id=>selectPreset(id)}/>:<div className="all-start"><h1 id="all-timeline-title">Explore a moment in history</h1>{!metaError&&<LoadingIndicator label="Loading starting points…"/>}</div>}

  </div>
  {metadata&&allKinds.includes(browseKind!)&&<AtlasContentPicker key={browseKind??"add"} metadata={metadata} range={range} layers={layers} initialType={browseKind??"artwork"} browse={Boolean(browseKind)} filterQuery={requestKey} close={()=>updateQuery({panel:null,browse:null},true)} addLayer={addLayer} open={open}/>}
  {!panel&&!browseKind&&selected&&selectedType==="book"&&<BookDrawer id={selected} items={[]} navigation={navigation} close={close} select={id=>updateQuery({item:id},true)} fallbackFocusId="all-timeline-title"/>}
  {!panel&&!browseKind&&selected&&selectedType==="event"&&<EventDrawer id={selected} navigation={navigation} close={close} fallbackFocusId="all-timeline-title"/>}
  {!panel&&!browseKind&&selected&&selectedType==="artwork"&&<AllArtworkDrawer id={selected} close={close} navigation={navigation}/>}
 </ExplorerFrame>;
}
