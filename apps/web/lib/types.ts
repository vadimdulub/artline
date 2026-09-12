export type Movement = {
  slug: string;
  name: string;
  color: string;
};

export type TimelineArtist = {
  id: string;
  slug: string;
  name: string;
  start_year: number;
  end_year: number;
  date_display: string;
  movement: Movement;
  countries: string[];
  artwork_count: number;
  status: "draft" | "review" | "published";
};

export type TimelineBin = {
  start_year: number;
  end_year: number;
  movement: string;
  color: string;
  count: number;
};

export type TimelineResponse = {
  range: { start: number; end: number };
  mode: "individual" | "density";
  items: TimelineArtist[];
  bins: TimelineBin[];
  total: number;
  popular_only: boolean;
  periods: { start_year: number; end_year: number; count: number }[];
};

export type Artwork = {
  id: string;
  slug: string;
  title: string;
  alternate_title: string | null;
  date_display: string;
  creation_year_start: number | null;
  creation_year_end: number | null;
  date_precision: string;
  work_type: string;
  unlinked_creator_label?: string | null;
  cultural_context?: string | null;
  object_form?: string | null;
  description_md?: string | null;
  medium_text: string | null;
  dimensions_text: string | null;
  accession_number: string | null;
  creation_place_unknown_reason: string | null;
  creation_place_display: string | null;
  current_location_text: string | null;
  media_url: string | null;
  alt_text: string | null;
  rights_status: string | null;
  attribution_text: string | null;
  representative_order: number | null;
  status: string;
  revision: number;
  attribution_role: string;
  source_page_url: string | null;
  license_label: string | null;
  license_url: string | null;
  location_checked_at: string | null;
  citations: Citation[];
  holding?: MuseumRef | null;
  display?: DisplayEvidence | null;
};

export type Citation = { field_name: string; source_name: string; source_url: string; evidence_note?: string };
export type ArtistWorksPage = { items: Artwork[]; years: { year: number; count: number }[]; total: number; undated_count: number; matching_total: number; next_cursor: string; range_start: number; range_end: number; groups: { year: number | null; start_index: number; count: number; has_uncertain_dates: boolean }[] };
export type Influence = { id: string; name: string; slug: string | null; direction: "incoming" | "outgoing"; relationship_type: string; evidence_level: string; evidence_note: string; citations: Citation[] };

export type ArtistDetail = {
  id: string;
  slug: string;
  display_name: string;
  sort_name: string;
  timeline_start_year: number;
  timeline_end_year: number;
  timeline_display: string;
  timeline_basis: string;
  biography_md: string | null;
  status: string;
  revision: number;
  entity_type: string;
  aliases: string[];
  influences: Influence[];
  movement: Movement;
  countries: string[];
  artworks: Artwork[];
  citations: Array<{
    field_name: string;
    source_name: string;
    source_url: string;
    evidence_note?: string;
  }>;
};

export type CatalogueArtist = {
  id: string;
  slug: string;
  display_name: string;
  timeline_start_year: number;
  timeline_end_year: number;
  timeline_display: string;
  status: string;
  revision: number;
  updated_at: string;
};

export type PublicationValidation = {
  artist_id: string;
  ready: boolean;
  revision: number;
  issues: Array<{
    path: string;
    code: string;
    message: string;
  }>;
};

export type CoverageSummary = {
  by_status: Record<string, number>;
  nordic_artists: number;
  asian_artists: number;
  missing_representative_works: number;
  missing_biography: number;
  total_artists: number;
};

export type TimelineFacets = {
  regions: { slug: string; name: string; count: number }[];
  movements: Array<{ slug: string; name: string; color?: string; count: number }>;
  countries: Array<{ slug: string; name: string; count: number }>;
};

export type MuseumRef = { id: string; slug: string; name: string };
export type MuseumVenue = MuseumRef & { city: string; country: string; region: string; visit_url: string };
export type DisplayEvidence = MuseumRef & { venue_id: string; venue_name: string; state: "on_view" | "not_on_view" | "unknown" | "stale"; context: string | null; gallery: string | null; checked_at: string; source_url: string };
export type MuseumSelection = { kind: "owner" | "museum"; position: number; reason: string; source_url: string | null; checked_at: string | null };
export type MuseumWork = Pick<Artwork, "id" | "slug" | "title" | "date_display" | "media_url" | "alt_text" | "rights_status" | "unlinked_creator_label" | "cultural_context" | "object_form"> & {
  artists: (MuseumRef & { role: string })[]; selections: MuseumSelection[]; display: DisplayEvidence | null;
};
export type MuseumArtwork = Artwork & Pick<MuseumWork, "artists" | "selections">;
export type Museum = MuseumRef & {
  kind: "museum" | "historic_site" | "foundation"; description: string; website_url: string | null; status: string;
  venues: MuseumVenue[]; work_count: number; holding_count: number; on_view_count: number;
  highlight_count: number; must_see_count: number; owner_revision: number; cover: MuseumWork | null;
};
export type MuseumFacets = { regions: { slug: string; name: string }[]; countries: { slug: string; name: string }[]; artists: { slug: string; name: string }[]; movements: { slug: string; name: string }[] };
export type MuseumPage = { items: Museum[]; total: number; next_cursor: string; facets: MuseumFacets };
export type MuseumWorksPage = { items: MuseumWork[]; total: number; next_cursor: string; facets: MuseumFacets };
