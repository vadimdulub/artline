-- Image bytes live in a dedicated private object bucket, never in the catalogue.
CREATE TABLE museum_uploads (
 id uuid PRIMARY KEY,
 institution_id uuid NOT NULL REFERENCES institutions(id),
 storage_key text NOT NULL UNIQUE,
 content_type text NOT NULL CHECK(content_type IN ('image/jpeg','image/png')),
 width integer NOT NULL CHECK(width>0),
 height integer NOT NULL CHECK(height>0),
 byte_size integer NOT NULL CHECK(byte_size>0 AND byte_size<=10485760),
 uploaded_by uuid NOT NULL REFERENCES member_accounts(id),
 created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX museum_uploads_institution ON museum_uploads(institution_id,id);
CREATE INDEX museum_publications_published_image ON museum_publications(institution_id,(published->>'image_id')) WHERE published IS NOT NULL;
