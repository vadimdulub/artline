#!/usr/bin/env python3
"""Read-only delivery/status/country audit using exact application membership."""
import argparse,collections,importlib.util,json
from pathlib import Path
from PIL import Image
s=importlib.util.spec_from_file_location('m',Path(__file__).with_name('apply-country-round.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
CORE=m.m.core;BASE=m.x.BASE
SOURCE_PREFIX='overnight%' if m.x.SESSION_NAME=='overnight-countries-20260913' else m.x.SESSION_NAME+'%'
def audit(target,phase,session_index=None):
 dest=BASE/'final-audit'/phase/(target+'.json');assert not dest.exists()
 ip=Path(session_index) if session_index else BASE/'session-application-index-final.json'
 if session_index:assert ip.exists(),'Explicit session index is missing; do not fall back to an older snapshot'
 elif not ip.exists():ip=BASE/'session-application-index.json'
 index=json.loads(ip.read_text());owned=index['targets'][target];ids=owned['new_artwork_ids'];aids=owned['new_artist_ids']
 with m.m.r.base.connect(target=='production') as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY');db.execute("SET LOCAL statement_timeout='180s'")
  works=db.execute("SELECT w.id::text,w.slug,w.status,w.published_at,artline_creation_scope(w.creation_year_start,w.creation_year_end,w.date_precision) cutoff,artline_has_selection_evidence(w.id) selection_evidence,EXISTS(SELECT 1 FROM artwork_artists aa WHERE aa.artwork_id=w.id) linked_creator,EXISTS(SELECT 1 FROM artwork_location_assertions la WHERE la.artwork_id=w.id AND la.claim_type='display') display_claim FROM artworks w WHERE id=ANY(%s::uuid[])",(ids,)).fetchall();assert len(works)==len(ids)
  artists=db.execute("SELECT a.id::text,a.slug,a.entity_type,a.status,a.published_at,coalesce((SELECT jsonb_agg(c.country_code ORDER BY c.country_code) FROM artist_countries c WHERE c.artist_id=a.id AND c.relationship_type='cultural_affiliation'),'[]') cultural_countries FROM artists a WHERE id=ANY(%s::uuid[])",(aids,)).fetchall();assert len(artists)==len(aids)
  if 'media_ids' in owned:media=db.execute('SELECT * FROM media_assets WHERE id=ANY(%s::uuid[]) ORDER BY id',(owned['media_ids'],)).fetchall();assert len(media)==len(owned['media_ids'])
  else:media=db.execute("SELECT DISTINCT ma.* FROM media_assets ma JOIN media_rights_evidence e ON e.media_id=ma.id JOIN sources s ON s.id=e.source_id WHERE s.slug=ANY(%s) ORDER BY ma.id",(['overnight-country-images-20260913','overnight-dutch-met-images-20260913','overnight-greek-primary-images-20260913','overnight-tzanes-met-primary-20260913','overnight-cabral-selected-images-20260913','overnight-finnish-primary-selected-images-20260913','overnight-kmska-selected-images-20260913'],)).fetchall()
  global_counts=dict(artwork_status=[dict(r) for r in db.execute('SELECT status,count(*) n FROM artworks GROUP BY status ORDER BY status')],artist_status=[dict(r) for r in db.execute('SELECT status,count(*) n FROM artists GROUP BY status ORDER BY status')],country_gaps=db.execute("SELECT count(*) FILTER(WHERE status='review' AND NOT EXISTS(SELECT 1 FROM artist_countries c WHERE c.artist_id=a.id AND c.relationship_type='cultural_affiliation')) missing_cultural,count(*) FILTER(WHERE status='review' AND NOT EXISTS(SELECT 1 FROM artist_countries c WHERE c.artist_id=a.id)) missing_any FROM artists a").fetchone(),reviewed_country_identities=db.execute("SELECT count(DISTINCT c.entity_id) n FROM citations c JOIN sources s ON s.id=c.source_id WHERE c.entity_type='artist' AND c.field_name IN ('geography','museum_country_review_20260913','smk_country_review_20260913') AND s.slug LIKE %s",(SOURCE_PREFIX,)).fetchone()['n'])
  invalid_fks=db.execute("SELECT conrelid::regclass::text table_name,conname FROM pg_constraint WHERE contype='f' AND NOT convalidated").fetchall()
  duplicate_citations=db.execute("SELECT c.entity_type,c.source_record_id,c.source_url,s.slug source_slug,c.evidence_note FROM citations c JOIN sources s ON s.id=c.source_id WHERE c.field_name='duplicate_identity' AND s.slug LIKE %s ORDER BY c.entity_type,s.slug,c.source_record_id",(SOURCE_PREFIX,)).fetchall()
 assert not invalid_fks
 assert all(w['status'] in ('review','archived') and w['published_at'] is None and w['cutoff'] in ('eligible','review') and w['linked_creator'] and not w['display_claim'] for w in works)
 assert all(w['selection_evidence'] for w in works if w['status']=='review')
 assert all(a['status'] in ('review','archived') and a['published_at'] is None and a['cultural_countries'] for a in artists)
 checks=[];held=[]
 for im in media:
  if not im['verified_at'] or im['rights_status'] not in ('public_domain','cc0','cc_by','cc_by_sa','licensed'):held.append(dict(id=str(im['id']),path=im['storage_path'],rights_status=im['rights_status']));continue
  assert im['alt_text'].strip() and im['license_url'] and im['creator_credit'] and im['source_page_url']
  p=m.x.ROOT/'apps/web/public'/im['storage_path'].lstrip('/');raw=p.read_bytes();assert len(raw)==im['byte_size']<=100000 and CORE.sha(raw)==im['checksum_sha256']
  with Image.open(p) as photo:assert photo.size==(im['width'],im['height']);photo.verify()
  checks.append(dict(id=str(im['id']),path=im['storage_path'],sha256=im['checksum_sha256'],bytes=len(raw)))
 result=dict(at=CORE.now(),target=target,phase=phase,scope='Read-only database audit plus local derivative file integrity. Production HTTP/GCS verification is recorded in each completed delivery receipt; this file does not claim a new production audit when target=local.',global_catalogue=global_counts,gross_new_artworks=len(works),own_work_status=dict(collections.Counter(w['status'] for w in works)),own_active_cutoff=dict(collections.Counter(w['cutoff'] for w in works if w['status']=='review')),gross_new_artists=len(artists),own_artist_status=dict(collections.Counter(a['status'] for a in artists)),own_artist_types=dict(collections.Counter(a['entity_type'] for a in artists)),all_own_artists_have_cultural_country=True,all_own_records_unpublished=True,all_own_works_have_creator=True,no_own_current_display_claims=True,all_active_own_works_have_selection_evidence=True,unvalidated_foreign_keys=invalid_fks,usable_media=len(checks),held_media=held,media_integrity=checks,duplicate_citation_counts=dict(collections.Counter(c['entity_type'] for c in duplicate_citations)),duplicate_evidence=duplicate_citations)
 CORE.save_new(dest,result);print('Delivery audit',target,{k:result[k] for k in ('gross_new_artworks','own_work_status','own_active_cutoff','gross_new_artists','own_artist_types','usable_media','duplicate_citation_counts')},flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--target',choices=['local','production'],required=True);p.add_argument('--phase',required=True);p.add_argument('--session-index',type=Path);a=p.parse_args();assert all(c.isalnum() or c in '-_' for c in a.phase);audit(a.target,a.phase,a.session_index)
