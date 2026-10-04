import { countryName, safeSourceURL } from "@/lib/api";

function asRecord(value: unknown): Record<string, unknown> | null {
  return value && typeof value === "object" && !Array.isArray(value) ? value as Record<string, unknown> : null;
}

function text(value: unknown): string | undefined {
  return typeof value === "string" && value.trim() ? value.trim() : undefined;
}

function readableEvidence(evidence: Record<string, unknown>) {
  const lines: string[] = [];
  const add = (label: string, value: unknown) => {
    const content = text(value);
    if (content) lines.push(`${label}: ${content}`);
  };
  const countryEvidence = asRecord(evidence.country_evidence);
  const crosscheck = asRecord(countryEvidence?.wikipedia_country_crosscheck);
  const code = text(evidence.country_code) ?? text(countryEvidence?.country_code);
  if (code) lines.push(`Country affiliation: ${countryName(code)} (${code}).`);
  add("Evidence basis", countryEvidence?.basis ?? evidence.description);
  add("Source description", countryEvidence?.source_description);
  add("Biography cross-check", crosscheck?.source_excerpt);
  if (Array.isArray(countryEvidence?.historical_polity_statements) && countryEvidence.historical_polity_statements.length) lines.push(`Historical-polity statements: ${countryEvidence.historical_polity_statements.length} recorded for discovery context only.`);

  // Display explicit source facts, never the full ingestion receipt or local paths.
  const rights = asRecord(evidence.rights) ?? evidence;
  add("Artwork", evidence.title);
  add("Image rights", text(rights.license_label) ?? text(rights.rights_status)?.replaceAll("_", " "));
  add("Credit", rights.credit ?? rights.attribution_text);
  add("Identity evidence", evidence.identity);
  add("Image preparation", evidence.transformation);
  const checked = text(evidence.checked_at);
  if (checked && /^\d{4}-\d{2}-\d{2}(?:T|$)/.test(checked) && Number.isFinite(Date.parse(checked))) {
    lines.push(`Evidence checked: ${new Intl.DateTimeFormat("en", { dateStyle: "medium", timeZone: "UTC" }).format(new Date(checked))}.`);
  }

  const sourceFields = asRecord(evidence.source_fields);
  const object = asRecord(sourceFields?.object) ?? sourceFields;
  if (object) {
    add("Source title", object.title);
    add("Source date", object.objectDate);
    add("Medium", object.medium);
    add("Collection number", object.accessionNumber);
    add("Credit", object.creditLine);
  }
  const notes = Array.isArray(evidence.notes) ? evidence.notes : [evidence.notes];
  if (text(evidence.editorial_note)) lines.push(text(evidence.editorial_note)!);
  for (const note of notes) {
    const content = text(note);
    if (content) lines.push(content);
  }
  return { lines, licenseURL: safeSourceURL(text(rights.license_url)), imageURL: safeSourceURL(text(evidence.source_image_url) ?? text(evidence.image_url)) };
}

export function EvidenceNote({ note }: { note: string }) {
  let parsed: unknown = note;
  // Some imported notes have been JSON-encoded twice.
  for (let depth = 0; depth < 3 && typeof parsed === "string"; depth++) {
    try { parsed = JSON.parse(parsed) as unknown; } catch { break; }
  }
  const evidence = asRecord(parsed);
  if (!evidence && !Array.isArray(parsed) && !/^\s*(?:\{|\[\s*(?:["{\[]|$))/.test(String(parsed))) return <p>{typeof parsed === "string" ? parsed : note}</p>;
  const { lines, licenseURL, imageURL } = readableEvidence(evidence ?? {});
  return <div className="structured-evidence">
    {lines.map((line, index) => <p key={index}>{line}</p>)}
    {licenseURL && <p><a href={licenseURL} target="_blank" rel="noreferrer">License details</a></p>}
    {imageURL && <p><a href={imageURL} target="_blank" rel="noreferrer">Original source image</a></p>}
    {!lines.length && !licenseURL && !imageURL && <p>See the linked source for supporting information.</p>}
  </div>;
}
