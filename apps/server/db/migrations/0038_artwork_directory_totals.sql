-- Exact, transactional totals for unfiltered and undated artwork browsing.
-- Source rows remain authoritative; title/image-filtered counts use indexed queries.
-- Run in one transaction. Reads stay available while the initial snapshot is built.
LOCK TABLE artworks IN SHARE ROW EXCLUSIVE MODE;
CREATE TABLE artwork_directory_totals (
 status text NOT NULL,
 undated boolean NOT NULL,
 total bigint NOT NULL CHECK(total>=0),
 PRIMARY KEY(status,undated)
);
INSERT INTO artwork_directory_totals(status,undated,total)
 SELECT status,creation_year_start IS NULL AND creation_year_end IS NULL,count(*)
 FROM artworks WHERE status<>'archived' GROUP BY 1,2;
CREATE FUNCTION maintain_artwork_directory_totals() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE old_undated boolean; new_undated boolean;
BEGIN
 IF TG_OP='UPDATE' AND ROW(OLD.status,OLD.creation_year_start IS NULL AND OLD.creation_year_end IS NULL)
  IS NOT DISTINCT FROM ROW(NEW.status,NEW.creation_year_start IS NULL AND NEW.creation_year_end IS NULL) THEN RETURN NULL; END IF;
 IF TG_OP<>'INSERT' AND OLD.status<>'archived' THEN
  old_undated:=OLD.creation_year_start IS NULL AND OLD.creation_year_end IS NULL;
  UPDATE artwork_directory_totals SET total=total-1 WHERE status=OLD.status AND undated=old_undated;
 END IF;
 IF TG_OP<>'DELETE' AND NEW.status<>'archived' THEN
  new_undated:=NEW.creation_year_start IS NULL AND NEW.creation_year_end IS NULL;
  INSERT INTO artwork_directory_totals(status,undated,total) VALUES(NEW.status,new_undated,1)
   ON CONFLICT(status,undated) DO UPDATE SET total=artwork_directory_totals.total+1;
 END IF;
 RETURN NULL;
END $$;
CREATE TRIGGER artwork_directory_totals_insert_delete AFTER INSERT OR DELETE ON artworks
 FOR EACH ROW EXECUTE FUNCTION maintain_artwork_directory_totals();
CREATE TRIGGER artwork_directory_totals_update AFTER UPDATE OF status,creation_year_start,creation_year_end ON artworks
 FOR EACH ROW EXECUTE FUNCTION maintain_artwork_directory_totals();
