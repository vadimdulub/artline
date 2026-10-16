-- Institutional publishing is deliberately independent of the historical catalogue.
ALTER TABLE member_accounts ADD COLUMN google_hosted_domain text NOT NULL DEFAULT '';
CREATE TABLE museum_staff_domains (
 institution_id uuid NOT NULL REFERENCES institutions(id),
 domain text NOT NULL CHECK(domain = lower(domain) AND domain ~ '^[a-z0-9][a-z0-9.-]*\.[a-z]{2,}$'),
 evidence_url text NOT NULL CHECK(evidence_url ~ '^https://'),
 approved_at timestamptz NOT NULL DEFAULT now(),
 revoked_at timestamptz,
 PRIMARY KEY(institution_id,domain)
);
-- Domains are approved by the operator using institutional evidence, never by a claimant.
CREATE TABLE museum_staff_members (
 institution_id uuid NOT NULL REFERENCES institutions(id),
 member_id uuid NOT NULL REFERENCES member_accounts(id),
 verified_email text NOT NULL,
 joined_at timestamptz NOT NULL DEFAULT now(),
 revoked_at timestamptz,
 PRIMARY KEY(institution_id,member_id)
);
CREATE INDEX museum_staff_members_account ON museum_staff_members(member_id,institution_id);
CREATE TABLE museum_publications (
 id uuid PRIMARY KEY,
 institution_id uuid NOT NULL REFERENCES institutions(id),
 kind text NOT NULL CHECK(kind IN ('artwork','exhibition','guide','profile')),
 draft jsonb NOT NULL CHECK(jsonb_typeof(draft)='object'),
 published jsonb CHECK(published IS NULL OR jsonb_typeof(published)='object'),
 version integer NOT NULL DEFAULT 1 CHECK(version>0),
 updated_at timestamptz NOT NULL DEFAULT now(),
 published_at timestamptz,
 updated_by uuid NOT NULL REFERENCES member_accounts(id),
 CHECK((published IS NULL) = (published_at IS NULL))
);
CREATE INDEX museum_publications_page ON museum_publications(institution_id,kind,id);
CREATE INDEX museum_publications_public_page ON museum_publications(institution_id,kind,id) WHERE published IS NOT NULL;
CREATE UNIQUE INDEX museum_publications_one_profile ON museum_publications(institution_id) WHERE kind='profile';
CREATE TABLE museum_publication_history (
 id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 publication_id uuid NOT NULL REFERENCES museum_publications(id),
 member_id uuid NOT NULL REFERENCES member_accounts(id),
 action text NOT NULL CHECK(action IN ('save','publish','unpublish')),
 version integer NOT NULL,
 document jsonb NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX museum_publication_history_record ON museum_publication_history(publication_id,id DESC);
