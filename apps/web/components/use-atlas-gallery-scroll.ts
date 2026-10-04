"use client";

import { useCallback, type RefObject } from "react";
import type { AtlasLane, AtlasResponse } from "@/lib/atlas";
import { useGalleryScroll } from "./use-gallery-scroll";

export function useAtlasGalleryScroll(strip: RefObject<HTMLUListElement | null>, lane: AtlasLane, query: string, busy: boolean) {
  const readPage = useCallback((response: AtlasResponse) => {
    const next = response.lanes.find(item => item.key === lane.key);
    if (!next) throw new Error("Missing gallery entries");
    return next;
  }, [lane.key]);
  return useGalleryScroll(strip, lane, query, busy, "atlas", `after_${lane.key}`, readPage);
}
