-- Country discovery includes documented artwork production independently of a
-- named artist. These reverse lookups keep that branch scoped by country/place.
CREATE INDEX places_country_id_idx ON places(country_code, id);
CREATE INDEX artwork_places_place_artwork_idx ON artwork_places(place_id, artwork_id);
