import importlib.util,json,uuid,hashlib,html,re,sys,collections
from pathlib import Path
from psycopg.types.json import Jsonb
s=importlib.util.spec_from_file_location('key',Path.cwd()/'ops/painter-key-artworks-20261008.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
OP='painter-key-artworks-20261008';target=sys.argv[1];assert target in ['local','production'];path=m.RUN/('gap-production-plan-v3.json.gz' if target=='production' else 'gap-final-plan-v2.json.gz');rows=m.base.load(path)
review=m.base.load(m.RUN/('visual-review-production.json' if target=='production' else 'visual-review.json'));assert review['passed'] and review['plan_sha256']==m.base.digest(path)
if target=='production':assert m.base.load(m.RUN/'upload-verification.json')['passed']
assert not (m.RUN/(target+'-gap-receipt.json')).exists(),'Already applied'
plain=lambda v:html.unescape(re.sub('<[^>]*>','',v or '')).strip()
uid=lambda name:str(uuid.uuid5(uuid.NAMESPACE_URL,OP+'/'+name))
with m.base.connect(target,readonly=False) as db:
 db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
 sources={r['slug']:r['id'] for r in db.execute("SELECT id,slug FROM sources WHERE slug IN ('wikidata','wikimedia-commons')")};assert len(sources)==2
 actor='local-european-research';assert db.execute('SELECT 1 FROM editor_accounts WHERE user_id=%s',(actor,)).fetchone()
 ids=[r['targets'][target]['artwork_id'] for r in rows];artistids=[r['artist_id'] for r in rows]
 before_art=db.execute('SELECT * FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id',(ids,)).fetchall();before_keys=db.execute('SELECT * FROM artist_key_artworks WHERE artist_id=ANY(%s::uuid[]) ORDER BY artist_id',(artistids,)).fetchall()
 m.base.save(m.BACKUP/(target+('-gap-v3-before.json.gz' if target=='production' else '-gap-before.json.gz')),dict(artworks=before_art,keys=before_keys));beforebyid={str(r['id']):r for r in before_art}
 # Recheck global authority uniqueness and artist/object snapshots under the shared ingestion lock.
 ext={r['external_id']:str(r['entity_id']) for r in db.execute("SELECT external_id,entity_id FROM external_identifiers WHERE scheme='wikidata' AND external_id=ANY(%s)",([r['work_qid'] for r in rows],))}
 for r in rows:
  t=r['targets'][target];old=beforebyid.get(t['artwork_id'])
  assert (old is None)==t['new'],('changed existence',r['work_qid'])
  assert r['work_qid'] not in ext or ext[r['work_qid']]==t['artwork_id'],('authority conflict',r['work_qid'])
  if old:assert str(old['primary_media_id'])==str(t['primary_media_id']) and old['status']==t['status'] and old['date_precision'] in ['exact','circa'] and old['creation_year_start']==r['year'] and old['creation_year_end'] in [None,r['year']],('stale artwork',r['work_qid'])
 counts=collections.Counter()
 for r in rows:
  t=r['targets'][target];aw=t['artwork_id'];prepared=r['prepared'];ext=r['image_info'].get('extmetadata',{});source_page=r['image_info']['descriptionurl'];media=t['primary_media_id']
  if media is None:
   media=uid('media/'+r['work_qid']+'/'+prepared['sha256']);credit=' · '.join(x for x in [plain(ext.get('Artist',{}).get('value')),plain(ext.get('Credit',{}).get('value')),r['license_label'],'Wikimedia Commons'] if x)
   db.execute('''INSERT INTO media_assets(id,storage_kind,storage_path,source_page_url,provider_name,mime_type,width,height,byte_size,checksum_sha256,alt_text,rights_status,license_label,license_url,creator_credit,attribution_text,retrieved_at,verified_at,verified_by)
     VALUES (%s,'local',%s,%s,'Wikimedia Commons','image/jpeg',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),now(),%s)''',(media,prepared['path'],source_page,prepared['width'],prepared['height'],prepared['byte_size'],prepared['sha256'],r['title']+' — '+r['artist_name'],r['rights_status'],r['license_label'],ext.get('LicenseUrl',{}).get('value'),plain(ext.get('Artist',{}).get('value')),credit,actor))
   evidence=dict(operation=OP,identity='Exact Wikidata creator P170 and image P18, unqualified primary creator; Commons file metadata; reviewed selected image',source_entity=r['source_url'],entity_revision=r['entity_revision'],file=r['commons_file'],image_info=r['image_info'],prepared=prepared)
   db.execute('''INSERT INTO media_rights_evidence(media_id,source_id,source_record_id,source_checksum,source_image_url,policy_url,rights_basis,adapter_version,checked_at,evidence_json)
     VALUES (%s,%s,%s,%s,%s,'https://commons.wikimedia.org/wiki/Commons:Licensing',%s,%s,now(),%s)''',(media,sources['wikimedia-commons'],r['commons_file'],hashlib.sha256(json.dumps(r['image_info'],sort_keys=True).encode()).hexdigest(),prepared['download_url'],r['license_label'],OP,Jsonb(evidence)))
   counts['images_attached']+=1
  if t['new']:
   worktype='painting' if 'Q3305213' in r['types'] else 'unknown'
   db.execute('''INSERT INTO artworks(id,slug,title,normalized_title,date_display,creation_year_start,creation_year_end,date_precision,work_type,primary_media_id,status,created_by,updated_by,research_candidate)
     VALUES (%s,%s,%s,lower(%s),%s,%s,%s,'exact',%s,%s,'review',%s,%s,true)''',(aw,t['slug'],r['title'],r['title'],str(r['year']),r['year'],r['year'],worktype,media,actor,actor))
   db.execute("INSERT INTO artwork_artists(artwork_id,artist_id,attribution_role,attribution_note) VALUES (%s,%s,'primary',%s)",(aw,r['artist_id'],'Unqualified creator statement in '+r['source_url']+'; exact existing artist authority '+r['artist_qid']))
   counts['new_review_artworks']+=1
  elif t['primary_media_id'] is None:
   db.execute('UPDATE artworks SET primary_media_id=%s,revision=revision+1,updated_by=%s,updated_at=now() WHERE id=%s AND primary_media_id IS NULL',(media,actor,aw));counts['existing_artworks_illustrated']+=1
  else:counts['existing_images_preserved']+=1
  if t.get('link_creator'):
   assert re.sub(r'\W','',t['original_creator_label'].casefold())==re.sub(r'\W','',r['artist_name'].casefold())
   db.execute("INSERT INTO artwork_artists(artwork_id,artist_id,attribution_role,attribution_note) VALUES (%s,%s,'primary',%s)",(aw,r['artist_id'],'Verified original creator label '+t['original_creator_label']+' against exact artwork/creator authorities '+r['work_qid']+' / '+r['artist_qid']+'; original object-level label retained.'))
   counts['creator_links_reconciled']+=1
  db.execute('INSERT INTO artwork_media(artwork_id,media_id,sort_order,view_label) VALUES (%s,%s,0,%s) ON CONFLICT DO NOTHING',(aw,media,'Selected reproduction'))
  db.execute("INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at) VALUES ('artwork',%s,'wikidata',%s,%s,%s,now()) ON CONFLICT (entity_type,entity_id,scheme) DO NOTHING",(aw,r['work_qid'],r['source_url'],sources['wikidata']))
  note=dict(operation=OP,artist_qid=r['artist_qid'],artwork_qid=r['work_qid'],source_revision=r['entity_revision'],recorded_year=r['year'],source_collection_ids=r['collections'],source_inventory=r['inventory'],holding_not_reconciled=True,display_not_claimed=True,publication_preserved=True)
  db.execute("INSERT INTO citations(id,entity_type,entity_id,field_name,source_id,source_url,evidence_note,retrieved_at,created_by) VALUES (%s,'artwork',%s,'key_artwork_research',%s,%s,%s,now(),%s)",(uid('citation/'+r['work_qid']),aw,sources['wikidata'],r['source_url'],json.dumps(note,ensure_ascii=False),actor))
  evidence=dict(**note,artist_slug=r['artist_slug'],artwork_slug=t['slug'],artwork_title=r['title'],selection_policy='Source-backed illustrated representative; no museum-highlight designation claimed',image_available=True)
  changed=db.execute("""INSERT INTO artist_key_artworks(artist_id,artwork_id,attribution_role,selection_basis,source_urls,evidence_json,selection_batch)
    VALUES (%s,%s,'primary','editorial_representative',%s,%s,%s)
    ON CONFLICT (artist_id) DO UPDATE SET artwork_id=EXCLUDED.artwork_id,attribution_role=EXCLUDED.attribution_role,selection_basis=CASE WHEN artist_key_artworks.artwork_id=EXCLUDED.artwork_id THEN artist_key_artworks.selection_basis ELSE EXCLUDED.selection_basis END,source_urls=CASE WHEN artist_key_artworks.artwork_id=EXCLUDED.artwork_id THEN ARRAY(SELECT DISTINCT u FROM unnest(artist_key_artworks.source_urls||EXCLUDED.source_urls) u) ELSE EXCLUDED.source_urls END,evidence_json=CASE WHEN artist_key_artworks.artwork_id=EXCLUDED.artwork_id THEN artist_key_artworks.evidence_json||EXCLUDED.evidence_json ELSE EXCLUDED.evidence_json END,selection_batch=EXCLUDED.selection_batch,selected_at=now()
    WHERE artist_key_artworks.artwork_id=EXCLUDED.artwork_id OR NOT EXISTS(SELECT 1 FROM artworks w WHERE w.id=artist_key_artworks.artwork_id AND w.primary_media_id IS NOT NULL AND w.status<>'archived')
    RETURNING id""",(r['artist_id'],aw,[r['source_url'],source_page],Jsonb(evidence),OP+'-gap')).fetchone()
  counts['key_selections_added_or_improved']+=bool(changed)
 after=db.execute('SELECT * FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id',(ids,)).fetchall()
 for row in after:
  old=beforebyid.get(str(row['id']))
  if old:
   changed={k for k in old if old[k]!=row[k]};assert changed<= {'primary_media_id','revision','updated_by','updated_at'},changed
  else:assert row['status']=='review'
 keys=db.execute('SELECT * FROM artist_key_artworks WHERE artist_id=ANY(%s::uuid[]) ORDER BY artist_id',(artistids,)).fetchall();m.base.save(m.BACKUP/(target+('-gap-v3-after.json.gz' if target=='production' else '-gap-after.json.gz')),dict(artworks=after,keys=keys))
m.save(target+'-gap-receipt.json',dict(at=m.base.now(),counts=dict(counts),plan_sha256=m.base.digest(path),publication_changes=0,existing_metadata_changes=0));print(target,dict(counts),flush=True)
