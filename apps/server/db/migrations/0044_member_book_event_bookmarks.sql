-- Private saves reference existing catalogue records without changing them.
CREATE TABLE member_book_bookmarks (
  member_id uuid NOT NULL REFERENCES member_accounts(id) ON DELETE CASCADE,
  book_id text NOT NULL REFERENCES book_records(id) ON DELETE CASCADE,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (member_id, book_id)
);
CREATE INDEX member_book_bookmarks_page_idx
  ON member_book_bookmarks(member_id, created_at DESC, book_id DESC);
CREATE INDEX member_book_bookmarks_book_idx ON member_book_bookmarks(book_id);

CREATE TABLE member_event_bookmarks (
  member_id uuid NOT NULL REFERENCES member_accounts(id) ON DELETE CASCADE,
  event_id text NOT NULL REFERENCES event_records(id) ON DELETE CASCADE,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (member_id, event_id)
);
CREATE INDEX member_event_bookmarks_page_idx
  ON member_event_bookmarks(member_id, created_at DESC, event_id DESC);
CREATE INDEX member_event_bookmarks_event_idx ON member_event_bookmarks(event_id);
