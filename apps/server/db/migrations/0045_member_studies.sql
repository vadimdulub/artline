-- Private, bounded study documents. Catalogue metadata is never modified.
-- References keep a dated snapshot for reproducible research and exports.
CREATE TABLE member_studies (
  member_id uuid NOT NULL REFERENCES member_accounts(id) ON DELETE CASCADE,
  id uuid NOT NULL,
  title text NOT NULL CHECK (length(title) BETWEEN 1 AND 180),
  role text NOT NULL CHECK (role IN ('research','teaching','exhibitions')),
  updated_at timestamptz NOT NULL DEFAULT now(),
  records jsonb NOT NULL DEFAULT '[]'::jsonb
    CHECK (jsonb_typeof(records)='array' AND jsonb_array_length(records)<=200),
  PRIMARY KEY (member_id,id)
);
CREATE INDEX member_studies_page_idx ON member_studies(member_id,updated_at DESC,id);

-- Alphabetical keyset pages within one member account.
CREATE INDEX member_studies_title_idx ON member_studies(member_id,lower(title) COLLATE "C",id);
