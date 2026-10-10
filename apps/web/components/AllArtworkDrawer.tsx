"use client";

import { BookmarkButton } from "./Bookmarks";
import Link from "next/link";
import { artworkDate, displayMetadata } from "@/lib/display-metadata";
import { useEffect, useState } from "react";
import { apiRequest, errorMessage } from "@/lib/api";
import type { AtlasArtwork } from "@/lib/atlas";
import { RecordDrawer } from "./RecordDrawer";
import { LoadingIndicator } from "./LoadingIndicator";
import { ArtworkFacts } from "./ArtworkFacts";
import { ArtworkViewer } from "./ArtworkViewer";
import { RecordArrows, type RecordNavigation } from "./RecordNavigation";
import { ArtworkLocation } from "./ArtworkLocation";
import { ArtworkDescription } from "./ArtworkDescription";
import { SourceList } from "./ArtistRecord";
import styles from "./Books.module.css";

export function AllArtworkDrawer({ id, close, navigation, fallbackFocusId = "all-timeline-title" }: { id: string; fallbackFocusId?: string; close: () => void; navigation?: RecordNavigation }) {
 const [result, setResult] = useState<{ id: string; attempt: number; data?: AtlasArtwork; error?: string }>();
 const [retry, setRetry] = useState(0);
 useEffect(() => {const controller=new AbortController();apiRequest<AtlasArtwork>(`atlas/artworks/${encodeURIComponent(id)}`,{signal:controller.signal}).then(data=>{if(!controller.signal.aborted)setResult({id,attempt:retry,data})}).catch(error=>{if(!controller.signal.aborted)setResult({id,attempt:retry,error:errorMessage(error)})});return()=>controller.abort();},[id,retry]);
 const loading=result?.id!==id||result.attempt!==retry;
 const work=result?.data, error=!loading?result?.error:undefined;
 const creator=work&&(work.creators.length?work.creators.map((creator,index)=><span key={`${creator.id}-${creator.role}`}>{index>0&&", "}<Link href={`/artists/${creator.slug}`}>{creator.name}</Link>{creator.role!=="primary"&&` (${creator.role.replaceAll("_"," ")})`}</span>):displayMetadata(work.unlinked_creator_label));
 const arrows=navigation?{...navigation,busy:navigation.busy||loading}:undefined;
 return <RecordDrawer label="Artwork details" closeLabel="Close artwork details" recordKey={id} title={loading?"Opening artwork…":"Artwork"} navigation={arrows&&<RecordArrows navigation={arrows} noun="artwork"/>} close={close} fallbackFocusId={fallbackFocusId}>
  {work?<div className={styles.drawerContent} aria-busy={loading}>{creator && <p className="artwork-creator">{creator}</p>}
   <div className="bookmark-record-actions"><BookmarkButton kind="artwork" id={work.id} title={work.title} /></div>
   <ArtworkViewer work={work} creator={creator} navigation={arrows}/>
   <header className={`${styles.bookHeading} ${styles.artworkHeading}`}><h2 aria-live="polite">{work.title}</h2>{artworkDate(work) && <p>{artworkDate(work)}</p>}</header>
   {work.creators.length>0&&<section className={styles.creators}><h3>Creators</h3>{work.creators.map(creator=><p key={`${creator.id}-${creator.role}`}><Link href={`/artists/${creator.slug}`}>{creator.name}</Link> <BookmarkButton kind="artist" id={creator.id} title={creator.name} compact /><br/>{creator.years}</p>)}</section>}
   <div className="artwork-details"><ArtworkFacts work={work}/></div>
   <ArtworkLocation work={work}/><ArtworkDescription work={work} detailPath={`atlas/artworks/${work.id}`}/>{work.citations.length>0&&<section className="sources-section"><h3>Sources</h3><SourceList citations={work.citations}/></section>}
  </div>:<div className={styles.drawerState} role={error?"alert":"status"}>{error?<><h2>Artwork unavailable</h2><p>{error}</p><button onClick={()=>setRetry(v=>v+1)}>Retry artwork</button></>:<LoadingIndicator label="Opening artwork…"/>}</div>}
 </RecordDrawer>;
}
