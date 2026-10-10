"""Retain verified selected metadata when the source image is unavailable."""
import importlib.util, json, re, sys, uuid, collections
from pathlib import Path
from psycopg.types.json import Jsonb

s = importlib.util.spec_from_file_location('key', Path.cwd()/'ops/painter-key-artworks-20261008.py')
m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
target, action = sys.argv[1:]; assert target in ('local', 'production')
OP = 'painter-key-artworks-20261008-metadata'
uid = lambda name: str(uuid.uuid5(uuid.NAMESPACE_URL, OP+'/'+name))
norm = lambda value: re.sub(r'\W', '', value.casefold())
planfile = target+'-metadata-gap-plan.json.gz'

if action == 'plan':
    gapq = {r['external_id'] for r in m.base.load(m.RUN/(target+'-blocked-image-metadata-gaps.json'))}
    candidates = [r for r in m.base.load(m.RUN/'gap-reviewed-plan.json.gz') if r['artist_qid'] in gapq]
    entities = {k:v for p in (m.RUN/'entities').glob('*.json') for k,v in m.base.load(p).get('entities',{}).items()}
    lives = {k:v for p in (m.RUN/'artist-entities').glob('*.json') for k,v in m.base.load(p).get('entities',{}).items()}
    ready, held = [], []
    with m.base.connect(target) as db:
        for row in candidates:
            artists = db.execute("SELECT a.id,a.slug,a.display_name,k.artist_id selected FROM external_identifiers e JOIN artists a ON a.id=e.entity_id LEFT JOIN artist_key_artworks k ON k.artist_id=a.id WHERE e.entity_type='artist' AND e.scheme='wikidata' AND e.external_id=%s AND a.status<>'archived'", (row['artist_qid'],)).fetchall()
            if len(artists)!=1 or artists[0]['selected']:
                held.append(dict(work=row['work_qid'],reason='artist_identity_or_existing_selection')); continue
            artist = artists[0]; row.update(artist_id=str(artist['id']),artist_slug=artist['slug'],artist_name=artist['display_name'])
            life = lives.get(row['artist_qid']); bounds = {}
            if life is None: held.append(dict(work=row['work_qid'],reason='missing_life_evidence')); continue
            for prop in ('P569','P570'):
                values = [c.get('mainsnak',{}).get('datavalue',{}).get('value',{}) for c in life.get('claims',{}).get(prop,[]) if c.get('rank')!='deprecated']
                bounds[prop] = [int(v['time'][1:5]) for v in values if v.get('precision',0)>=9 and v.get('time','').startswith('+')]
            if (bounds['P569'] and row['year']<min(bounds['P569'])+8) or (bounds['P570'] and row['year']>max(bounds['P570'])):
                held.append(dict(work=row['work_qid'],reason='creator_life_date_conflict',bounds=bounds)); continue
            row['creator_life_evidence'] = bounds
            works = db.execute("SELECT w.*,aa.attribution_role,e.external_id wikidata,i.external_id institution_wikidata FROM artwork_artists aa JOIN artworks w ON w.id=aa.artwork_id LEFT JOIN external_identifiers e ON e.entity_type='artwork' AND e.entity_id=w.id AND e.scheme='wikidata' LEFT JOIN external_identifiers i ON i.entity_type='institution' AND i.entity_id=w.current_institution_id AND i.scheme='wikidata' WHERE aa.artist_id=%s", (row['artist_id'],)).fetchall()
            global_ids = db.execute("SELECT entity_type,entity_id FROM external_identifiers WHERE scheme='wikidata' AND external_id=%s", (row['work_qid'],)).fetchall()
            matches = {str(w['id']):w for w in works if w['wikidata']==row['work_qid']}
            if global_ids and (len(global_ids)!=1 or global_ids[0]['entity_type']!='artwork' or str(global_ids[0]['entity_id']) not in matches):
                held.append(dict(work=row['work_qid'],reason='existing_global_object_needs_reconciliation')); continue
            if not matches:
                inventory = {norm(v) for v in row['inventory'] if isinstance(v,str)}
                matches = {str(w['id']):w for w in works if w['institution_wikidata'] in row['collections'] and w['accession_number'] and norm(w['accession_number']) in inventory}
            if len(matches)>1: held.append(dict(work=row['work_qid'],reason='multiple_objects')); continue
            old = next(iter(matches.values()), None)
            if old:
                if old['status']=='archived' or old['attribution_role']!='primary' or old['wikidata'] not in (None,row['work_qid']) or old['creation_year_start']!=row['year'] or old['creation_year_end'] not in (None,row['year']) or old['date_precision'] not in ('exact','circa'):
                    held.append(dict(work=row['work_qid'],reason='existing_object_date_or_identity_conflict')); continue
                row['target'] = dict(artwork_id=str(old['id']),slug=old['slug'],new=False)
            else:
                labels = {norm(v['value']) for v in entities[row['work_qid']].get('labels',{}).values()}
                if any(norm(w['title']) in labels for w in works): held.append(dict(work=row['work_qid'],reason='possible_duplicate_title')); continue
                row['target'] = dict(artwork_id=str(uuid.uuid5(uuid.NAMESPACE_URL,row['source_url']+'#artline-key-artwork')),slug='key-artwork-'+row['work_qid'].lower(),new=True)
            ready.append(row)
    m.save(planfile, ready); m.save(target+'-metadata-gap-held.json',held)
    print(target,'ready',len(ready),'new',sum(r['target']['new'] for r in ready),'held',held)
elif action == 'apply':
    rows = m.base.load(m.RUN/planfile); counts = collections.Counter()
    assert not (m.RUN/(target+'-metadata-gap-receipt.json')).exists()
    with m.base.connect(target,readonly=False) as db:
        db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
        source = db.execute("SELECT id FROM sources WHERE slug='wikidata'").fetchone()['id']
        actor='local-european-research'
        assert db.execute('SELECT 1 FROM editor_accounts WHERE user_id=%s',(actor,)).fetchone()
        ids=[r['target']['artwork_id'] for r in rows]; artists=[r['artist_id'] for r in rows]
        before=db.execute('SELECT * FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id',(ids,)).fetchall()
        keys=db.execute('SELECT * FROM artist_key_artworks WHERE artist_id=ANY(%s::uuid[])',(artists,)).fetchall(); assert not keys
        m.base.save(m.BACKUP/(target+'-metadata-gap-before.json.gz'),dict(artworks=before,keys=keys))
        before_byid={str(r['id']):r for r in before}
        for row in rows:
            t=row['target']; aw=t['artwork_id']; old=before_byid.get(aw)
            assert (old is None)==t['new']
            ext=db.execute("SELECT entity_type,entity_id FROM external_identifiers WHERE scheme='wikidata' AND external_id=%s",(row['work_qid'],)).fetchall()
            assert not ext or (len(ext)==1 and ext[0]['entity_type']=='artwork' and str(ext[0]['entity_id'])==aw)
            assert db.execute("SELECT 1 FROM external_identifiers WHERE entity_type='artist' AND entity_id=%s AND scheme='wikidata' AND external_id=%s",(row['artist_id'],row['artist_qid'])).fetchone()
            if old:
                assert old['status']!='archived' and old['creation_year_start']==row['year'] and old['creation_year_end'] in (None,row['year']) and old['date_precision'] in ('exact','circa')
                assert db.execute("SELECT 1 FROM artwork_artists WHERE artwork_id=%s AND artist_id=%s AND attribution_role='primary'",(aw,row['artist_id'])).fetchone()
                counts['existing_artworks_preserved']+=1
            else:
                assert row['year']<=1970
                db.execute("""INSERT INTO artworks(id,slug,title,normalized_title,date_display,creation_year_start,creation_year_end,date_precision,work_type,status,created_by,updated_by,research_candidate)
                    VALUES (%s,%s,%s,lower(%s),%s,%s,%s,'exact',%s,'review',%s,%s,true)""",(aw,t['slug'],row['title'],row['title'],str(row['year']),row['year'],row['year'],'painting' if 'Q3305213' in row['types'] else 'unknown',actor,actor))
                db.execute("INSERT INTO artwork_artists(artwork_id,artist_id,attribution_role,attribution_note) VALUES (%s,%s,'primary',%s)",(aw,row['artist_id'],'Exact unqualified source creator '+row['artist_qid']+' in '+row['source_url']))
                counts['new_review_artworks']+=1
            db.execute("INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at) VALUES ('artwork',%s,'wikidata',%s,%s,%s,now()) ON CONFLICT (entity_type,entity_id,scheme) DO NOTHING",(aw,row['work_qid'],row['source_url'],source))
            evidence=dict(operation=OP,artist_qid=row['artist_qid'],artwork_qid=row['work_qid'],source_revision=row['entity_revision'],recorded_year=row['year'],creator_life_evidence=row['creator_life_evidence'],source_collection_ids=row['collections'],source_inventory=row['inventory'],holding_not_reconciled=True,display_not_claimed=True,image_available=False,image_status='Source download unavailable; no image attachment',publication_preserved=True,selection_policy='Source-backed editorial representative; no museum-highlight designation claimed')
            db.execute("INSERT INTO citations(id,entity_type,entity_id,field_name,source_id,source_url,evidence_note,retrieved_at,created_by) VALUES (%s,'artwork',%s,'key_artwork_research',%s,%s,%s,now(),%s)",(uid('citation/'+row['work_qid']),aw,source,row['source_url'],json.dumps(evidence,ensure_ascii=False),actor))
            db.execute("INSERT INTO artist_key_artworks(artist_id,artwork_id,attribution_role,selection_basis,source_urls,evidence_json,selection_batch) VALUES (%s,%s,'primary','editorial_representative',%s,%s,%s)",(row['artist_id'],aw,[row['source_url']],Jsonb(evidence),OP))
            counts['key_selections_added']+=1
        after=db.execute('SELECT * FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id',(ids,)).fetchall()
        for row in after:
            old=before_byid.get(str(row['id']))
            assert row==old if old else row['status']=='review' and row['primary_media_id'] is None
        m.base.save(m.BACKUP/(target+'-metadata-gap-after.json.gz'),dict(artworks=after,keys=db.execute('SELECT * FROM artist_key_artworks WHERE artist_id=ANY(%s::uuid[]) ORDER BY artist_id',(artists,)).fetchall()))
    m.save(target+'-metadata-gap-receipt.json',dict(at=m.base.now(),counts=dict(counts),plan_sha256=m.base.digest(m.RUN/planfile),publication_changes=0,existing_metadata_changes=0,image_attachments=0))
    print(target,dict(counts))
else: raise ValueError(action)
