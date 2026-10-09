// Respect an explicit gzip refusal, including when a wildcard allows others.
export function acceptsGzip(header: string | null): boolean {
  const codings = (header ?? "").toLowerCase().split(",").map(value => {
    const [coding, ...parameters] = value.trim().split(";");
    const quality = parameters.map(value => value.trim()).find(value => value.startsWith("q="));
    return { coding, quality: quality ? Number(quality.slice(2)) : 1 };
  });
  const selected = codings.find(value => value.coding === "gzip") ?? codings.find(value => value.coding === "*");
  return !!selected && selected.quality > 0 && selected.quality <= 1;
}
