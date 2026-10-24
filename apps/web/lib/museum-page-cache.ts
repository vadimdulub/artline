// A short-lived, bounded browser cache of catalogue pages, never session data.
// The server still checks membership before rendering the museum directory.
const lifetime = 60_000;
const maxBytes = 1 << 20;
const pages = new Map<string, { data: unknown; expires: number; bytes: number }>();
let bytes = 0;
let listening = false;

function cacheKey(path: string | null) {
  if (!path || typeof window === "undefined") return null;
  const [resource, query = ""] = path.split("?");
  if (resource !== "museums") return null;
  const params = new URLSearchParams(query); params.sort();
  return `museums?${params}`;
}

export function clearMuseumPageCache() { pages.clear(); bytes = 0; }

export function cachedMuseumPage<T>(path: string | null): T | undefined {
  const key = cacheKey(path), entry = key ? pages.get(key) : undefined;
  if (!key || !entry) return undefined;
  pages.delete(key);
  if (Date.now() >= entry.expires) { bytes -= entry.bytes; return undefined; }
  pages.set(key, entry);
  return entry.data as T;
}

export function rememberMuseumPage(path: string | null, data: unknown) {
  const key = cacheKey(path);
  if (!key) return;
  const size = JSON.stringify(data).length * 2;
  if (size > maxBytes) return;
  if (!listening) {
    window.addEventListener("artline:session-expired", clearMuseumPageCache);
    listening = true;
  }
  const old = pages.get(key);
  if (old) { bytes -= old.bytes; pages.delete(key); }
  while (pages.size >= 8 || bytes + size > maxBytes) {
    const oldest = pages.keys().next().value!;
    bytes -= pages.get(oldest)!.bytes; pages.delete(oldest);
  }
  pages.set(key, { data, bytes: size, expires: Date.now() + lifetime });
  bytes += size;
}
