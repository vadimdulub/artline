"use client";
import { useState } from "react";
import { mapSymbolPaths, type MapKind } from "@/lib/map";

export function MapSymbol({ kind }: { kind: MapKind }) {
  return <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{mapSymbolPaths[kind].map(path => <path key={path} d={path} />)}</svg>;
}
export function MapImage({ src, alt, kind, compact = false }: { src: string; alt: string; kind: MapKind; compact?: boolean }) {
  const [failed, setFailed] = useState(false);
  return failed ? <span className="map-image-unavailable"><MapSymbol kind={kind} />{!compact && <small>Image unavailable</small>}</span> : <img src={src} alt={alt} loading="lazy" onError={() => setFailed(true)} />;
}
