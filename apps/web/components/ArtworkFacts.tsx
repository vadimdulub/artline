import Link from "@/components/MemberLink";
import { safeSourceURL } from "@/lib/api";
import { artworkMedium, displayMetadata } from "@/lib/display-metadata";
import type { Artwork } from "@/lib/types";

export function ArtworkFacts({ work, attribution = false }: { work: Artwork; attribution?: boolean }) {
  const dating = work.date_precision === "unknown" ? undefined : ({ exact: "Exact year", exact_year: "Exact year", circa: "Approximate", range: "Date range", circa_range: "Approximate date range", decade: "Within this decade", century: "Within this century", before: "Before this date", after: "After this date" } as Record<string, string>)[work.date_precision];
  const place = displayMetadata(work.creation_place_display);
  const holding = displayMetadata(work.current_location_text);
  const medium = artworkMedium(work), dimensions = displayMetadata(work.dimensions_text);
  const rights = displayMetadata(work.license_label) ?? displayMetadata(work.rights_status?.replaceAll("_", " "));
  const license = safeSourceURL(work.license_url);
  return <dl>
    {dating && <div><dt>Dating</dt><dd>{dating}</dd></div>}
    {displayMetadata(work.object_form) && <div><dt>Object form</dt><dd>{work.object_form}</dd></div>}
    {displayMetadata(work.cultural_context) && <div><dt>Tradition / school</dt><dd>{work.cultural_context}</dd></div>}
    {place && <div><dt>Made in</dt><dd>{place}</dd></div>}
    {(work.holding || holding) && <div><dt>Held at</dt><dd>{work.holding ? <Link href={`/museums/${work.holding.slug}`}>{work.holding.name}</Link> : holding}</dd></div>}
    {medium && <div><dt>Medium</dt><dd>{medium}</dd></div>}
    {dimensions && <div><dt>Dimensions</dt><dd>{dimensions}</dd></div>}
    {displayMetadata(work.accession_number) && <div><dt>Collection no.</dt><dd>{work.accession_number}</dd></div>}
    {attribution && work.attribution_role && <div><dt>Attribution</dt><dd>{({ primary: "By the artist", workshop: "Workshop", attributed_to: "Attributed to the artist", follower_of: "Follower of the artist", formerly_attributed_to: "Formerly attributed to the artist", circle_of: "Circle of the artist" } as Record<string, string>)[work.attribution_role] ?? work.attribution_role.replaceAll("_", " ")}</dd></div>}
    {(rights || license) && <div><dt>Image rights</dt><dd>{rights}{license && <a className="license-link" href={license} target="_blank" rel="noreferrer">License details</a>}</dd></div>}
  </dl>;
}
