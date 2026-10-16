-- Bounded pages and institution/object lookups over the exhibition catalogue.
CREATE INDEX exhibitions_active_page_idx ON exhibitions (coalesce(start_year,-2147483648) DESC,id DESC) WHERE status<>'archived';
CREATE INDEX exhibition_sources_provider_event_idx ON exhibition_source_records (source_key,exhibition_id);
CREATE INDEX exhibitions_active_state_idx ON exhibitions (event_state,id) WHERE status<>'archived';
