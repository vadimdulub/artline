"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { apiRequest, errorMessage, safeSourceURL } from "@/lib/api";
import type { AtlasArtwork } from "@/lib/atlas";
import { RecordDrawer } from "./RecordDrawer";
import { ArtworkViewer } from "./ArtworkViewer";
import { ArtworkLocation } from "./ArtworkLocation";
import { ArtworkDescription } from "./ArtworkDescription";
import { SourceList } from "./ArtistRecord";
import styles from "./Books.module.css";

export function AllArtworkDrawer({ id, close }: { id: string; close: () => void }) {
 const [result, setResult] = useState<{ id: string; data?: AtlasArtwork; error?: string }>();
 const [retry, setRetry] = useState(0);
 useEffect(() => {const controller=new AbortController();apiRequest<AtlasArtwork>(`atlas/artworks/${encodeURIComponent(id)}`,{signal:controller.signal}).then(data=>setResult({id,data})).catch(error=>{if(!controller.signal.aborted)setResult({id,error:errorMessage(error)})});return()=>controller.abort();},[id,retry]);
 const work=result?.id===id?result.data:undefined, error=result?.id===id?result.error:undefined;
 return <RecordDrawer label="Artwork details" closeLabel="Close artwork details" recordKey={id} title="Artwork" close={close} fallbackFocusId="all-timeline-title">
  {work?<div className={styles.drawerContent}><header className={styles.bookHeading}><p>{work.creators.length?work.creators.map((creator,index)=><span key={`${creator.id}-${creator.role}`}>{index>0&&", "}<Link href={`/artists/${creator.slug}`}>{creator.name}</Link>{creator.role!=="primary"&&` (${creator.role.replaceAll("_"," ")})`}</span>):work.unlinked_creator_label??"Creator not recorded"}</p><h2>{work.title}</h2><p>{work.date_display}</p></header>
   <ArtworkViewer work={work}/>
   {work.creators.length>0&&<section className={styles.creators}><h3>Creators</h3>{work.creators.map(creator=><p key={`${creator.id}-${creator.role}`}><Link href={`/artists/${creator.slug}`}>{creator.name}</Link><br/>{creator.years}</p>)}</section>}
   <div className="artwork-details"><dl><div><dt>Creation dates</dt><dd>{work.date_display}</dd></div><div><dt>Held at</dt><dd>{work.holding?<Link href={`/museums/${work.holding.slug}`}>{work.holding.name}</Link>:"Not established"}</dd></div><div><dt>Medium</dt><dd>{work.medium_text??work.work_type.replaceAll("_"," ")}</dd></div><div><dt>Image rights</dt><dd>{work.license_label??work.rights_status??"Not reviewed"}{work.license_url&&<> · <a href={safeSourceURL(work.license_url)} target="_blank" rel="noreferrer">Licence</a></>}</dd></div></dl></div>
   <ArtworkLocation work={work}/><ArtworkDescription work={work} detailPath={`atlas/artworks/${id}`}/><section className="sources-section"><h3>Sources</h3><SourceList citations={work.citations}/></section>
  </div>:<div className={styles.drawerState} role={error?"alert":"status"}>{error?<><h2>Artwork unavailable</h2><p>{error}</p><button onClick={()=>setRetry(v=>v+1)}>Retry artwork</button></>:"Opening artwork…"}</div>}
 </RecordDrawer>;
}
