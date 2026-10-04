-- Member identity is separate from editorial authority and future billing.
CREATE TABLE member_accounts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  google_subject text NOT NULL UNIQUE,
  email text NOT NULL,
  display_name text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE member_sessions (
  token_hash text PRIMARY KEY CHECK (length(token_hash) = 64),
  member_id uuid NOT NULL REFERENCES member_accounts(id) ON DELETE CASCADE,
  created_at timestamptz NOT NULL DEFAULT now(),
  expires_at timestamptz NOT NULL
);
CREATE INDEX member_sessions_member_idx ON member_sessions(member_id, expires_at);
CREATE INDEX member_sessions_expiry_idx ON member_sessions(expires_at);
