-- Preserve history for all editorial mutations, including direct maintenance SQL.
CREATE FUNCTION artline_audit_record() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  INSERT INTO audit_log(action,entity_type,entity_id,before_json,after_json)
  VALUES(lower(TG_OP),TG_ARGV[0],COALESCE(NEW.id,OLD.id),
    CASE WHEN TG_OP='INSERT' THEN NULL ELSE to_jsonb(OLD) END,
    CASE WHEN TG_OP='DELETE' THEN NULL ELSE to_jsonb(NEW) END);
  RETURN COALESCE(NEW,OLD);
END;
$$;
CREATE TRIGGER artists_audit AFTER INSERT OR UPDATE OR DELETE ON artists FOR EACH ROW EXECUTE FUNCTION artline_audit_record('artist');
CREATE TRIGGER artworks_audit AFTER INSERT OR UPDATE OR DELETE ON artworks FOR EACH ROW EXECUTE FUNCTION artline_audit_record('artwork');
CREATE TRIGGER influences_audit AFTER INSERT OR UPDATE OR DELETE ON influence_claims FOR EACH ROW EXECUTE FUNCTION artline_audit_record('influence');

CREATE FUNCTION artline_preserve_slug() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.slug <> OLD.slug THEN
    IF EXISTS(SELECT 1 FROM slug_redirects WHERE entity_type='artist' AND old_slug=NEW.slug AND entity_id<>NEW.id) THEN
      RAISE EXCEPTION 'slug belongs to another record';
    END IF;
    INSERT INTO slug_redirects(entity_type,entity_id,old_slug)
    VALUES('artist',OLD.id,OLD.slug)
    ON CONFLICT(entity_type,old_slug) DO UPDATE SET entity_id=EXCLUDED.entity_id;
  END IF;
  RETURN NEW;
END;
$$;
CREATE TRIGGER artist_slug_history BEFORE UPDATE OF slug ON artists FOR EACH ROW EXECUTE FUNCTION artline_preserve_slug();
