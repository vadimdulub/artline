"use client";

import Image from "next/image";
import { useState } from "react";
import styles from "./ExhibitionImage.module.css";

export function ExhibitionImage({ src, alt, width = 700, height = 700, portrait = false, eager = false }: {
  src?: string | null; alt: string; width?: number; height?: number; portrait?: boolean; eager?: boolean;
}) {
  const [failedSource, setFailedSource] = useState<string | null>(null);
  return <span className={portrait ? styles.portrait : styles.image}>
    {src && src !== failedSource
      ? <Image src={src} alt={alt} width={width} height={height} loading={eager ? "eager" : "lazy"} unoptimized onError={() => setFailedSource(src)} />
      : <span className={styles.unavailable}>Image not available</span>}
  </span>;
}
