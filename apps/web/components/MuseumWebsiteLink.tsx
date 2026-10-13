import { safeSourceURL } from "@/lib/api";

export function MuseumWebsiteLink({ url, name }: { url?: string | null; name: string }) {
  const href = safeSourceURL(url);
  if (!href || href === "#") return null;
  return <a className="museum-website-link" href={href} target="_blank" rel="noopener noreferrer" aria-label={`${name} official website (opens in a new tab)`} title="Official museum website">
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M14 4h6v6m0-6L10 14" /><path d="M10 4H5a1 1 0 0 0-1 1v14a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-5" /></svg>
  </a>;
}
