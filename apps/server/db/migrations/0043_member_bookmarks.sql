-- Personal bookmarks do not change catalogue metadata or publication state.
CREATE TABLE member_artist_bookmarks (
  member_id uuid NOT NULL REFERENCES member_accounts(id) ON DELETE CASCADE,
  artist_id uuid NOT NULL REFERENCES artists(id) ON DELETE CASCADE,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (member_id, artist_id)
);
CREATE INDEX member_artist_bookmarks_page_idx
  ON member_artist_bookmarks(member_id, created_at DESC, artist_id DESC);

CREATE TABLE member_artwork_bookmarks (
  member_id uuid NOT NULL REFERENCES member_accounts(id) ON DELETE CASCADE,
  artwork_id uuid NOT NULL REFERENCES artworks(id) ON DELETE CASCADE,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (member_id, artwork_id)
);
CREATE INDEX member_artwork_bookmarks_page_idx
  ON member_artwork_bookmarks(member_id, created_at DESC, artwork_id DESC);

CREATE INDEX member_artist_bookmarks_artist_idx ON member_artist_bookmarks(artist_id);
CREATE INDEX member_artwork_bookmarks_artwork_idx ON member_artwork_bookmarks(artwork_id);
