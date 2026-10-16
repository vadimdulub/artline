-- Existing and new studies remain private until their owner enables sharing.
-- Revocation clears the token; publishing again generates a fresh link.
ALTER TABLE member_studies ADD COLUMN IF NOT EXISTS share_token uuid;
CREATE UNIQUE INDEX IF NOT EXISTS member_studies_share_token_idx
    ON member_studies (share_token) WHERE share_token IS NOT NULL;
