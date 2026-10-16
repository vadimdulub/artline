"use client";
import { useEffect, useRef, useState } from "react";
import { museumImageURL, type MuseumDocument } from "@/lib/museum-studio";
import styles from "./MuseumStudio.module.css";
type ImageFields = Pick<MuseumDocument, "image_id" | "image_url" | "image_alt" | "image_credit">;
export function MuseumImageField({ slug, document, change, busy, onBusy }: { slug: string; document: MuseumDocument; change: (fields: Partial<ImageFields>) => void; busy: boolean; onBusy: (busy: boolean) => void }) {
  const [uploading, setUploading] = useState(false), [error, setError] = useState("");
  const request = useRef<AbortController | null>(null);
  useEffect(() => () => { request.current?.abort(); }, []);
  const src = museumImageURL(slug, document);
  async function upload(file?: File) {
    if (!file) return;
    if (file.size > 10 * 1024 * 1024 || !["image/jpeg", "image/png"].includes(file.type)) { setError("Choose a JPEG or PNG image up to 10 MB."); return; }
    request.current?.abort(); const controller = new AbortController(); request.current = controller;
    setUploading(true); onBusy(true); setError("");
    try {
      const response = await fetch(`/api/museum-studio/${slug}/images`, { method: "POST", body: file, headers: { "content-type": file.type }, signal: controller.signal });
      const result = await response.json(); if (!response.ok) throw new Error(result.error?.message || "The image could not be uploaded. Please try again.");
      if (!controller.signal.aborted) change({ image_id: result.id, image_url: "" });
    } catch (e) { if (!controller.signal.aborted) setError((e as Error).message); }
    finally { if (request.current === controller) { setUploading(false); onBusy(false); request.current = null; } }
  }
  return <section className={styles.imageFields} aria-label="Image and credit"><h3>Image <span className={styles.requirement}>Optional</span></h3><p className={styles.note}>Upload a JPEG or PNG up to 10 MB (20 million pixels), or use an image link. The complete image will fit in its frame.</p>
    <label className={styles.field}><span>Upload image <span className={styles.requirement}>Optional</span></span><input type="file" accept="image/jpeg,image/png" disabled={busy || uploading} onChange={e => { const file = e.target.files?.[0]; e.target.value = ""; void upload(file); }} /></label>
    {uploading && <div role="status" className={styles.uploadStatus}>Uploading and preparing image… <button type="button" onClick={() => request.current?.abort()}>Cancel upload</button></div>}
    {error && <p role="alert">{error}</p>}
    {!!src && <figure className={styles.uploadPreview}>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={src} alt={document.image_alt || "Selected image preview"} referrerPolicy="no-referrer" /><figcaption><button type="button" disabled={busy || uploading} onClick={() => change({ image_id: "", image_url: "" })}>Remove image</button><span>Image description and credit are required when using an image.</span></figcaption></figure>}
    {!document.image_id && <label className={styles.field}><span>Image URL <span className={styles.requirement}>Optional</span></span><input type="url" maxLength={2048} value={document.image_url} disabled={busy || uploading} placeholder="https://" onChange={e => change({ image_url: e.target.value, image_id: "" })} /></label>}
    <div className={styles.fields}><label className={styles.field}><span>Image description <span className={styles.requirement}>{src ? "Required" : "Optional"}</span></span><input maxLength={1000} required={!!src} value={document.image_alt} onChange={e => change({ image_alt: e.target.value })} /></label><label className={styles.field}><span>Image credit and rights <span className={styles.requirement}>{src ? "Required" : "Optional"}</span></span><input maxLength={1000} required={!!src} value={document.image_credit} onChange={e => change({ image_credit: e.target.value })} /></label></div>
  </section>;
}
