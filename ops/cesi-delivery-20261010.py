#!/usr/bin/env python3
"""Reconcile, pin, deliver and verify the Cesi/Top 100 research selection."""
import argparse,base64,collections,concurrent.futures,gzip,hashlib,importlib.util,json,re,subprocess
from pathlib import Path
from urllib.parse import urlsplit
from psycopg import sql
from psycopg.types.json import Jsonb
from PIL import Image
import requests
from google.cloud import storage
from google.api_core.exceptions import PreconditionFailed
s=importlib.util.spec_from_file_location('campaign',Path(__file__).with_name('cesi-top100-20261010.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
s=importlib.util.spec_from_file_location('core',Path(__file__).with_name('enrich-artwork-images.py'));core=importlib.util.module_from_spec(s);s.loader.exec_module(core)
C='07441bd8-6663-4e16-963d-f16fc6cd35ba'
PERSONAL='https://artline.local/personal-artwork-collection'
def batch(db,table,rows):
    if not rows:return
    keys=list(rows[0]);assert all(list(r)==keys for r in rows)
    cols=sql.SQL(',').join(map(sql.Identifier,keys));q=sql.SQL('INSERT INTO {} ({}) SELECT {} FROM jsonb_populate_recordset(NULL::{},%s)').format(sql.Identifier(table),cols,cols,sql.Identifier(table))
    for rr in m.chunks(rows,200):db.execute(q,(Jsonb(rr),))
def snapshot(db,ids):
    out={r['v']['id']:dict(artwork=r['v'],creators=[],attachments=[],holdings=[]) for r in db.execute('SELECT to_jsonb(a) v FROM artworks a WHERE id=ANY(%s::uuid[]) ORDER BY id',(ids,))}
    for table,key in [('artwork_artists','creators'),('artwork_media','attachments'),('artwork_location_assertions','holdings')]:
        for r in db.execute(sql.SQL('SELECT artwork_id::text,to_jsonb(a) v FROM {} a WHERE artwork_id=ANY(%s::uuid[]) ORDER BY artwork_id,to_jsonb(a)::text').format(sql.Identifier(table)),(ids,)):out[r['artwork_id']][key].append(r['v'])
    return out
def backup():
    rows=json.loads(subprocess.check_output(['gcloud','sql','backups','list','--instance=artline-postgres','--project=artline-508319','--limit=40','--format=json'],text=True));row=next(r for r in rows if r.get('description')=='Before Cesi and Top 100 catalogue expansion 20261010');assert row['status']=='SUCCESSFUL'
    m.save(m.RUN/'cloud-backup.json',row);m.save(m.BACKUP/'cloud-backup.json',row);print('Recovery backup verified',row['id'],flush=True)
def sourcekey(r):return urlsplit(r['source_url']).hostname
def sourceid(r):return m.uid('source/'+sourcekey(r))
def visual():
    result={}
    for p in sorted((m.RUN/'visual-review').glob('*.json')):
        for r in m.load(p)['decisions']:
            old=result.get(r['artwork_id'])
            if old:
                assert old['sha256']==r['sha256'], 'Visual decisions refer to different files'
                if old['decision']=='hold':continue
            result[r['artwork_id']]=r
    return result
def plan(phase):
    folder=m.RUN/phase;assert not (folder/'plan.json.gz').exists()
    if phase=='top100':
        assert m.load(m.RUN/'discovery-summary.json')['artists']==101
        assert len(list((m.RUN/'discovery-v2').glob('*.json.gz')))==101
        assert m.load(m.RUN/'existing-primary-image-hashes.json.gz')['counts']=={'hashed':24975}
        location_review=m.load(m.RUN/'institution-label-review.json')
        assert (m.RUN/'duplicate-image-review.json').exists()
    reviewed_connections=m.load(m.RUN/'top100-reviewed-connections.json')['rows'] if phase=='top100' else []
    rows=m.load(m.RUN/'cesi-candidates.json')['rows'] if phase=='cesi' else [r for r in m.safe_rows() if r['artist_id']!=C]
    reviews=visual();base=m.load(m.RUN/'baseline.json.gz');baseline={w['id']:w for w in base['artworks']};held=[];selected=[]
    urls=sorted({r['source_url'] for r in rows});mids=sorted({r['institution_id'] for r in rows if r['institution_id']});titles=sorted({m.norm(r['title']) for r in rows});inventories=sorted({r['accession'] for r in rows if r.get('accession')})
    with m.connect() as db:
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        possible=[];ext=[];cit=[]
        for us in m.chunks(urls):
            ext+=db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND canonical_url=ANY(%s)",(us,)).fetchall()
            cit+=db.execute("SELECT entity_id::text,source_url FROM citations WHERE entity_type='artwork' AND source_url=ANY(%s)",(us,)).fetchall()
        keys=[dict(scheme=r['scheme'],external_id=r['source_id']) for r in rows]
        for ks in m.chunks(keys):ext+=db.execute("SELECT e.entity_id::text,e.scheme,e.external_id,e.canonical_url FROM jsonb_to_recordset(%s) x(scheme text,external_id text) JOIN external_identifiers e USING(scheme,external_id) WHERE e.entity_type='artwork'",(Jsonb(ks),)).fetchall()
        for ims in m.chunks(mids,20):
            possible+=db.execute('SELECT id::text,title,normalized_title,alternate_title,accession_number,current_institution_id::text,unlinked_creator_label FROM artworks WHERE current_institution_id=ANY(%s::uuid[]) AND (normalized_title=ANY(%s) OR accession_number=ANY(%s))',(ims,titles,inventories)).fetchall()
        ids={r['artwork_id'] for r in rows}|{e['entity_id'] for e in ext}|{e['entity_id'] for e in cit}|{r['id'] for r in possible}
        if phase=='cesi':ids|={'41916ac4-9aaf-4ca0-af10-55ff3d12ba28','b5f6c0c0-78be-49ab-abfd-02bb413328b2'}
        artist_ids={r['record']['id'] for r in base['artists']}|{r[k] for r in reviewed_connections for k in ['source_artist_id','target_artist_id']}
        current=snapshot(db,sorted(ids));artists={r['v']['id']:r['v'] for r in db.execute('SELECT to_jsonb(a) v FROM artists a WHERE id=ANY(%s::uuid[])',(sorted(artist_ids),))}
        for relation in reviewed_connections:assert_no_relation(db,relation)
        institutions={r['v']['id']:r['v'] for r in db.execute('SELECT to_jsonb(i) v FROM institutions i WHERE id=ANY(%s::uuid[])',(mids,))}
    byurl=collections.defaultdict(set);bykey=collections.defaultdict(set)
    for e in ext:
        bykey[e['scheme'],e['external_id']].add(e['entity_id'])
        if e['canonical_url']:byurl[e['canonical_url']].add(e['entity_id'])
    for e in cit:byurl[e['source_url']].add(e['entity_id'])
    urlcounts=collections.Counter(r['source_url'] for r in rows);used=set()
    hashes=m.load(m.RUN/'duplicate-image-review.json') if (m.RUN/'duplicate-image-review.json').exists() else {}
    for original in rows:
        r=dict(original);aid=r['artwork_id'];matches=set(bykey[r['scheme'],r['source_id']])
        if urlcounts[r['source_url']]==1:matches|=byurl[r['source_url']]
        if aid in current:matches.add(aid)
        candidates=[x for x in possible if x['current_institution_id']==r['institution_id'] and (m.norm(x['title'])==m.norm(r['title']) or (r.get('accession') and m.norm(x['accession_number'])==m.norm(r['accession'])))]
        if candidates:matches|={x['id'] for x in candidates}
        reason=None
        if len(matches)>1:reason='Multiple existing object identities'
        elif matches:
            match=next(iter(matches))
            if r['state']=='new':reason='Potential pre-existing source, museum title or accession; retained for reconciliation'
            elif match!=aid:reason='Existing source identity differs'
        if r['state']=='existing':
            before=current.get(aid)
            if not before or before['artwork']['status']=='archived':reason='Existing object missing or archived'
            elif any(str(before['artwork'].get(k))!=str(baseline[aid].get(k)) for k in ['title','creation_year_start','creation_year_end','date_precision','current_institution_id','primary_media_id']):reason='Existing identity fields changed since baseline'
            if before and r['add_holding'] and any(h['claim_type']=='holding' and h['review_state']=='accepted' and not h['superseded_by'] for h in before['holdings']):reason='An accepted holding is already present'
        if aid in used:reason='Selected source rows converge on one object'
        if r['state']=='new' and hashes.get(aid,{}).get('decision')=='hold':reason='Similar reproduction to existing or selected object; duplicate/version review required'
        im=None
        if r['image_needed']:
            p=m.RUN/'prepared'/(aid+'.json')
            if phase=='top100':assert p.exists(), 'Image preparation incomplete'
            if p.exists():
                prepared=m.load(p);review=reviews.get(aid)
                if phase=='top100' and prepared['state']=='prepared':
                    assert review, 'Visual review incomplete'
                    if r['state']=='new':assert aid in hashes, 'Duplicate review incomplete'
                if review and review['decision']=='hold':reason='Visual/object review hold: '+review['note']
                if prepared['state']=='prepared' and review and review['decision']=='accept':
                    assert prepared['sha256']==review['sha256']==m.sha(Path(prepared['path']).read_bytes());assert prepared['source_url']==r['source_url'];im=dict(prepared,view_label=review.get('view_label','Full source reproduction'),visual_note=review['note'])
                elif r['state']=='new' and r['provider']=='wikiart':reason='Selected highlight reproduction not visually accepted'
            elif r['state']=='new' and r['provider']=='wikiart':reason='Selected image not prepared'
        if not im and not r['add_holding'] and r['state']=='existing':reason='No remaining supported enrichment'
        if r['institution_id']:
            assert r['institution_id'] in institutions and institutions[r['institution_id']]['status']!='archived'
            if phase=='top100':
                label=r['fields'].get('Location')
                if label in location_review['held']:reason='Institution-label review: '+location_review['held'][label]
                else:assert location_review['accepted'][label]==r['institution_id'], 'Institution mapping not reviewed'
        if phase=='top100' and not r['fields'].get('Media') and (r['fields'].get('Genre')=='advertisement' or re.search(r'illustration for (?:literary )?review',r['title'],re.I)):
            reason='Printed design/illustration lacks physical original versus edition evidence'
        if phase=='top100' and re.search(r'woodblock|wood[ -]?cut|lithograph|etching|engraving|linocut|screen[ -]?print',r['fields'].get('Media',''),re.I):
            reason='Print medium needs physical edition/object identity review'
        if reason:held.append(dict(artwork_id=aid,title=r['title'],reason=reason,matched_ids=sorted(matches)));continue
        used.add(aid);r['image']=im;r['before']=current.get(aid);selected.append(r)
    supplements=[];artist_changes=[];influences=reviewed_connections
    if phase=='cesi':
        portrait='41916ac4-9aaf-4ca0-af10-55ff3d12ba28';pregnant='b5f6c0c0-78be-49ab-abfd-02bb413328b2'
        pr=m.load(m.RUN/'cesi-portrait-source-review.json');old=Path(m.ROOT/pr['original_capture']);assert m.sha(gzip.decompress(old.read_bytes()))==pr['original_sha256']
        assert current[portrait]['artwork']['unlinked_creator_label']=='Cesi Bartolomeo' and not current[portrait]['creators']
        supplements.append(dict(artwork_id=portrait,before=current[portrait],updates=dict(work_type='painting',creation_year_start=1580,creation_year_end=1607,date_precision='circa_range',date_display='ca 1580–ca 1607',medium_text='Oil on canvas',accession_number='278'),creator_link=dict(artist_id=C,attribution_role='attributed_to',attribution_note='ICCD preferred attribution to Cesi, based on stylistic analysis. Earlier Cantarini and Daniele Crespi attributions preserved in the source; object-level label retained.'),source_url='https://catalogo.cultura.gov.it/detail/HistoricOrArtisticProperty/1200864560',receipt=dict(retrieved_at=pr['retrieved_at'],sha256=pr['original_sha256']),note='Individually reviewed archived official ICCD evidence captured 5 October 2026. Explicit source creation range, type, medium and inventory; not a new source retrieval. Existing accepted holding and original creator label preserved.'))
        native=m.load(m.RUN/'cesi-native/338503.json');d=native['data'];assert d['objectDate']=='1576–1629' and d['artistDisplayName']=='Bartolomeo Cesi'
        description=current[pregnant]['artwork']['description_md'].replace('1556–1629','1576–1629')
        supplements.append(dict(artwork_id=pregnant,before=current[pregnant],updates=dict(creation_year_start=1576,creation_year_end=1629,date_precision='range',date_display='1576–1629',description_md=description),creator_link=None,source_url=d['objectURL'],receipt=native['receipt'],note='Deep Cesi metadata review: current Met object date is 1576–1629; preserve previous imported 1556–1629 in audit. Existing image, creator, holding and status unchanged.'))
        url='https://www.getty.edu/art/collection/person/103KWN';raw,rc=m.capture(url)
        bio="Bartolomeo Cesi (Bologna, 1556–1629) was a painter and draftsman whose religious art emphasized clarity, restraint and close study from life. He trained with Nosadella. His carefully prepared figure drawings supported altarpieces and frescoes for Bolognese religious institutions. The Getty relates his sober compositions to Counter-Reformation devotional ideals. In 1599 he joined Ludovico Carracci in seeking a separate painters’ guild in Bologna; in 1620 he became drawing master of the Accademia degli Ardenti.\n\n[Source: J. Paul Getty Museum]("+url+"). Further object-level attributions and uncertain dates are recorded separately."
        assert artists[C]['biography_md'] is None
        artist_changes.append(dict(artist_id=C,before=artists[C],updates=dict(biography_md=bio),source_url=url,receipt=rc))
        with m.connect() as db:
            existing=db.execute("SELECT to_jsonb(i) v FROM influence_claims i WHERE target_artist_id=%s AND relationship_type='teacher_of' AND status<>'archived'",(C,)).fetchall()
        if not any('nosadella' in x['v']['source_label'].lower() or x['v']['source_artist_id']=='0af21a33-1348-43ac-8bd4-f42b5b44540a' for x in existing):
            influences.append(dict(source_artist_id=None,source_label='Nosadella',target_artist_id=C,relationship_type='teacher_of',evidence_level='documented',confidence='high',evidence_note='Getty Museum biography explicitly identifies Nosadella as Cesi’s teacher. Source name retained; no unsupported automatic authority merge.',status='review',source_url=url,receipt=rc))
    selected_ids={r['artist_id'] for r in selected}|({C} if phase=='cesi' else set())|{r[k] for r in influences for k in ['source_artist_id','target_artist_id'] if r[k]}
    plan=dict(at=m.now(),phase=phase,rows=selected,held=held,supplements=supplements,artist_changes=artist_changes,influences=influences,artists={k:v for k,v in artists.items() if k in selected_ids},institutions=institutions,authorization='User requested deep Cesi review and additions, then maximum supported artwork, picture and connection enrichment for the existing Top 100. Production catalogue writes; local catalogue read-only.',policy='New records remain review. Unknown dates and qualified attributions explicit. Existing images, statuses and date metadata preserved except the two individually reviewed Cesi corrections. Holdings are not current display.')
    m.save(folder/'plan.json.gz',plan);digest=m.sha((folder/'plan.json.gz').read_bytes());m.save(folder/'pin.json',dict(sha256=digest));m.save(m.BACKUP/phase/'plan-and-preimages.json.gz',plan)
    print(phase,'pinned',len(selected),'records',sum(r['state']=='new' for r in selected),'new',sum(bool(r['image']) for r in selected),'images',sum(r['add_holding'] for r in selected),'holdings','held',len(held),'supplements',len(supplements),flush=True)
def pinned(phase):
    folder=m.RUN/phase;p=folder/'plan.json.gz';digest=m.load(folder/'pin.json')['sha256'];assert m.sha(p.read_bytes())==digest;return m.load(p),digest
def upload(phase):
    plan,digest=pinned(phase);bucket=storage.Client(project='artline-508319',credentials=core.GcloudCredentials()).bucket(core.BUCKET)
    def one(r):
        im=r['image'];dest=m.RUN/phase/'uploads'/(r['artwork_id']+'.json')
        if dest.exists():d=m.load(dest);assert d['plan_sha256']==digest;return
        raw=Path(im['path']).read_bytes();assert m.sha(raw)==im['sha256'] and len(raw)<=100000
        blob=bucket.blob(im['storage_path'].lstrip('/'));blob.metadata={'sha256':im['sha256'],'operation':m.OP};blob.cache_control='public,max-age=31536000,immutable'
        try:blob.upload_from_string(raw,content_type='image/jpeg',if_generation_match=0)
        except PreconditionFailed:pass
        blob.reload();assert blob.size==len(raw) and blob.md5_hash==base64.b64encode(hashlib.md5(raw).digest()).decode()
        response=requests.get('https://artlines.org'+im['storage_path'],timeout=(15,60));response.raise_for_status();assert m.sha(response.content)==im['sha256']
        m.save(dest,dict(at=m.now(),artwork_id=r['artwork_id'],plan_sha256=digest,sha256=im['sha256'],generation=blob.generation,public_verified=True))
    rows=[r for r in plan['rows'] if r['image']]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for i,_ in enumerate(pool.map(one,rows),1):
            if i%100==0:print('Uploaded and publicly verified',i,'/',len(rows),flush=True)
    print('Uploads verified',len(rows),flush=True)

def validate_after(plan,after):
    for r in plan['rows']:
        aid=r['artwork_id'];a=after[aid]['artwork'];im=r['image']
        if r['state']=='new':
            assert a['title']==r['title'] and a['status']=='review' and a['published_at'] is None
            date=r['date'] or {};assert (a['creation_year_start'],a['creation_year_end'])==(date.get('first'),date.get('last'))
            links=after[aid]['creators'];assert len(links)==1 and links[0]['artist_id']==r['artist_id'] and links[0]['attribution_role']==r['attribution_role']
        else:
            old=r['before'];permitted={'updated_at','updated_by','revision'}
            if im:permitted.add('primary_media_id')
            if r['add_holding']:permitted.add('current_institution_id')
            assert {k:v for k,v in a.items() if k not in permitted}=={k:v for k,v in old['artwork'].items() if k not in permitted},('Unrelated artwork change',aid)
            assert after[aid]['creators']==old['creators']
            for am in old['attachments']:assert am in after[aid]['attachments']
            for h in old['holdings']:assert h in after[aid]['holdings']
        if im:
            assert a['primary_media_id']==im['media_id'];assert any(x['media_id']==im['media_id'] for x in after[aid]['attachments'])
        if r['add_holding']:
            assert a['current_institution_id']==r['institution_id']
            assert any(h['claim_type']=='holding' and h['institution_id']==r['institution_id'] and h['review_state']=='accepted' for h in after[aid]['holdings'])
    for r in plan['supplements']:
        aid=r['artwork_id'];a=after[aid]['artwork'];allowed=set(r['updates'])|{'updated_at','updated_by','revision'}
        assert {k:v for k,v in a.items() if k not in allowed}=={k:v for k,v in r['before']['artwork'].items() if k not in allowed}
        for k,v in r['updates'].items():assert a[k]==v
        assert after[aid]['attachments']==r['before']['attachments'] and after[aid]['holdings']==r['before']['holdings']
        if r['creator_link']:assert any(x['artist_id']==C and x['attribution_role']==r['creator_link']['attribution_role'] for x in after[aid]['creators'])
        else:assert after[aid]['creators']==r['before']['creators']

def assert_no_relation(db,r):
    existing=db.execute("SELECT id FROM influence_claims WHERE target_artist_id=%s AND relationship_type=%s AND status<>'archived' AND (source_artist_id=%s OR lower(source_label)=lower(%s))",(r['target_artist_id'],r['relationship_type'],r['source_artist_id'],r['source_label'])).fetchall()
    assert not existing, 'Relationship already exists or changed after review'

def json_strings(value):
    if isinstance(value,str):yield value
    elif isinstance(value,dict):
        for child in value.values():yield from json_strings(child)
    elif isinstance(value,list):
        for child in value:yield from json_strings(child)

def apply(phase):
    plan,digest=pinned(phase);folder=m.RUN/phase
    if (folder/'applied.json').exists():assert m.load(folder/'applied.json')['plan_sha256']==digest;print('Already applied: zero writes');return
    assert m.load(m.RUN/'cloud-backup.json')['status']=='SUCCESSFUL'
    rows=plan['rows'];ids=[r['artwork_id'] for r in rows]+[r['artwork_id'] for r in plan['supplements']];assert len(ids)==len(set(ids))
    for r in rows:
        if r['image']:
            rc=m.load(folder/'uploads'/(r['artwork_id']+'.json'));assert rc['public_verified'] and rc['plan_sha256']==digest
    sources={}
    for r in rows+plan['supplements']+plan['artist_changes']+plan['influences']:
        key=sourcekey(r);sources[sourceid(r)]=dict(id=sourceid(r),slug=m.OP+'-'+key.replace('.','-'),name=('WikiArt' if key=='www.wikiart.org' else key)+' — Cesi and Top 100 source review',source_type='collection_page',base_url='https://'+key,adapter_key=m.OP,priority=10)
    data=collections.defaultdict(list)
    with m.connect(write=True) as db:
        db.execute("SELECT set_config('artline.actor_user_id',%s,true)",(m.ACTOR,));db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
        db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(ids,)).fetchall()
        before=snapshot(db,ids);expected={r['artwork_id']:r['before'] for r in rows+plan['supplements'] if r.get('before')};assert before==expected,'Concurrent object edits or unexpected existing object'
        actual={r['v']['id']:r['v'] for r in db.execute('SELECT to_jsonb(a) v FROM artists a WHERE id=ANY(%s::uuid[]) ORDER BY id FOR SHARE',(list(plan['artists']),))};assert actual==plan['artists'],'Artist changed'
        inst={r['v']['id']:r['v'] for r in db.execute('SELECT to_jsonb(i) v FROM institutions i WHERE id=ANY(%s::uuid[]) ORDER BY id FOR SHARE',(list(plan['institutions']),))};assert inst==plan['institutions'],'Institution changed'
        for relation in plan['influences']:assert_no_relation(db,relation)
        m.save(m.BACKUP/phase/'locked-preimages.json.gz',dict(plan_sha256=digest,artworks=before,artists=actual,institutions=inst))
        existing_sources={str(x['id']) for x in db.execute('SELECT id FROM sources WHERE id=ANY(%s::uuid[])',(list(sources),))};batch(db,'sources',[v for k,v in sources.items() if k not in existing_sources])
        existing_ext={(r['scheme'],r['external_id']):str(r['entity_id']) for r in db.execute("SELECT scheme,external_id,entity_id FROM external_identifiers WHERE entity_type='artwork' AND scheme=ANY(%s) AND external_id=ANY(%s)",(sorted({r['scheme'] for r in rows}),[r['source_id'] for r in rows]))}
        entity_schemes={(str(x['entity_id']),x['scheme']) for x in db.execute("SELECT entity_id,scheme FROM external_identifiers WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(ids,))}
        for r in rows:
            aid=r['artwork_id'];sid=sourceid(r);im=r['image'];date=r['date'] or {}
            if r['state']=='new':
                data['artworks'].append(dict(id=aid,slug='wikiart-'+r['source_id'] if r['provider']=='wikiart' else m.OP+'-'+m.sha(r['source_id'].encode())[:18],title=r['title'],normalized_title=m.norm(r['title']),date_display=date.get('display') or 'Date unknown',creation_year_start=date.get('first'),creation_year_end=date.get('last'),date_precision=date.get('precision') or 'unknown',work_type=r['work_type'],medium_text=r['fields'].get('Media'),dimensions_text=r['fields'].get('Dimensions'),accession_number=r.get('accession'),description_md=r.get('editorial_note') or None,status='review',research_candidate=True,created_by=m.ACTOR,updated_by=m.ACTOR))
                data['artwork_artists'].append(dict(artwork_id=aid,artist_id=r['artist_id'],attribution_role=r['attribution_role'],representative_order=1,attribution_note=r['creator']+'. '+r['identity_basis']+' '+r['source_url']))
            key=(r['scheme'],r['source_id'])
            if key in existing_ext:assert existing_ext[key]==aid
            elif (aid,r['scheme']) not in entity_schemes:
                data['external_identifiers'].append(dict(id=m.uid('external/'+r['scheme']+'/'+r['source_id']),entity_type='artwork',entity_id=aid,scheme=r['scheme'],external_id=r['source_id'],canonical_url=r['source_url'],source_id=sid,retrieved_at=r['receipt']['retrieved_at']))
            note={k:v for k,v in r.items() if k not in ['before','image']};note.update(plan_sha256=digest,confidence_interpretation='Editorial assessment, not a calibrated probability',current_display_claim=False)
            data['citations'].append(dict(id=m.uid('citation/'+phase+'/'+aid),entity_type='artwork',entity_id=aid,field_name='cesi_top100_source_review',source_id=sid,source_record_id=r['source_id'],source_url=r['source_url'],evidence_note=json.dumps(note,ensure_ascii=False),retrieved_at=r['receipt']['retrieved_at'],created_by=m.ACTOR))
            if r['add_holding']:
                data['artwork_location_assertions'].append(dict(id=m.uid('holding/'+aid),artwork_id=aid,claim_type='holding',institution_id=r['institution_id'],context='collection',source_id=sid,source_url=r['source_url'],evidence_note=json.dumps(dict(source_label=r['fields'].get('Location'),source_sha256=r['receipt']['sha256'],confidence=.94 if r['provider']=='wikiart' else .98,basis='Exact reviewed artwork and explicit collection connection. Institution labels reconciled against existing records. Holdings only, not current display.',plan_sha256=digest),ensure_ascii=False),checked_at=r['receipt']['retrieved_at'],review_state='accepted'))
            if im:
                credit='WikiArt; '+r['artist_name'] if r['provider']=='wikiart' else plan['institutions'][r['institution_id']]['name']+'; '+r['artist_name']
                if 'grenoble' in r['source_url']:credit+='; VILLE DE GRENOBLE / MUSÉE DE GRENOBLE-J.L. LACROIX'
                data['media_assets'].append(dict(id=im['media_id'],storage_kind='local',storage_path=im['storage_path'],source_page_url=r['source_url'],provider_name='WikiArt' if r['provider']=='wikiart' else plan['institutions'][r['institution_id']]['name'],mime_type='image/jpeg',width=im['width'],height=im['height'],byte_size=im['bytes'],checksum_sha256=im['sha256'],alt_text=r['title']+' — '+r['artist_name'],rights_status=r['rights_status'],license_label=r['rights_label'],license_url=r['license_url'],creator_credit=credit,attribution_text=r['title']+'. '+credit+'. Proportional resizing and JPEG compression; source frame preserved.',retrieved_at=im['download']['retrieved_at'],verified_at=m.now(),verified_by=m.ACTOR))
                data['media_rights_evidence'].append(dict(media_id=im['media_id'],source_id=sid,source_record_id=r['source_id'],source_checksum=r['receipt']['sha256'],source_image_url=r['image_url'],policy_url=r['license_url'],rights_basis=r['rights_basis'],adapter_version=m.OP,checked_at=r['receipt']['retrieved_at'],evidence_json=dict(plan_sha256=digest,source_receipt=r['receipt'],download=im['download'],actual_rights_label=r['rights_label'],identity_confidence=r['identity_confidence'],identity_basis=r['identity_basis'],visual_review=im['visual_note'])))
                data['artwork_media'].append(dict(artwork_id=aid,media_id=im['media_id'],sort_order=0,view_label=im['view_label']))
        for table in ['artworks','artwork_artists','external_identifiers','citations','artwork_location_assertions','media_assets','media_rights_evidence','artwork_media']:
            batch(db,table,data[table]);print(phase,'inserted',table,len(data[table]),flush=True)
        for r in rows:
            if r['image']:db.execute('UPDATE artworks SET primary_media_id=%s,revision=revision+1,updated_by=%s,updated_at=now() WHERE id=%s AND primary_media_id IS NULL',(r['image']['media_id'],m.ACTOR,r['artwork_id']))
        for r in plan['supplements']:
            updates=r['updates'];query=sql.SQL('UPDATE artworks SET {},revision=revision+1,updated_by=%s,updated_at=now() WHERE id=%s').format(sql.SQL(',').join(sql.SQL('{}=%s').format(sql.Identifier(k)) for k in updates));db.execute(query,(*updates.values(),m.ACTOR,r['artwork_id']))
            if r['creator_link']:batch(db,'artwork_artists',[dict(artwork_id=r['artwork_id'],representative_order=1,**r['creator_link'])])
            batch(db,'citations',[dict(id=m.uid('supplement/'+r['artwork_id']),entity_type='artwork',entity_id=r['artwork_id'],field_name='cesi_deep_metadata_review',source_id=sourceid(r),source_url=r['source_url'],evidence_note=json.dumps(dict(plan_sha256=digest,updates=r['updates'],note=r['note'],receipt=r['receipt']),ensure_ascii=False),retrieved_at=r['receipt']['retrieved_at'],created_by=m.ACTOR)])
        for r in plan['artist_changes']:
            db.execute('UPDATE artists SET biography_md=%s,revision=revision+1,updated_by=%s,updated_at=now() WHERE id=%s',(r['updates']['biography_md'],m.ACTOR,r['artist_id']))
            batch(db,'citations',[dict(id=m.uid('biography/'+r['artist_id']),entity_type='artist',entity_id=r['artist_id'],field_name='biography',source_id=sourceid(r),source_url=r['source_url'],evidence_note=json.dumps(dict(plan_sha256=digest,source_receipt=r['receipt'],basis='Original editorial paraphrase of Getty Museum biography; source qualifications preserved.')),retrieved_at=r['receipt']['retrieved_at'],created_by=m.ACTOR)])
        for r in plan['influences']:
            iid=m.uid('influence/'+r['source_label']+'/'+r['target_artist_id']);record={k:v for k,v in r.items() if k not in ['source_url','receipt']};batch(db,'influence_claims',[dict(id=iid,**record,created_by=m.ACTOR,updated_by=m.ACTOR)])
            batch(db,'citations',[dict(id=m.uid('influence-citation/'+iid),entity_type='influence',entity_id=iid,field_name='relationship',source_id=sourceid(r),source_url=r['source_url'],evidence_note=r['evidence_note'],retrieved_at=r['receipt']['retrieved_at'],created_by=m.ACTOR)])
        highlights=[r for r in rows if r['state']=='new' and r['provider']=='wikiart']
        if highlights:
            cid=str(m.uuid.uuid5(m.uuid.NAMESPACE_URL,PERSONAL));c=db.execute('SELECT * FROM curated_collections WHERE id=%s FOR UPDATE',(cid,)).fetchone();assert c and c['curator_kind']=='owner' and c['institution_id'] is None and c['status']!='archived'
            pos=db.execute('SELECT coalesce(max(position),0) n FROM curated_collection_items WHERE collection_id=%s',(cid,)).fetchone()['n'];assert pos+len(highlights)<=100000
            batch(db,'curated_collection_items',[dict(id=m.uid('highlight/'+r['artwork_id']),collection_id=cid,artwork_id=r['artwork_id'],position=pos+i+1,reason=r['selection_basis'],source_id=sourceid(r),source_url=r['source_url'],checked_at=r['receipt']['retrieved_at']) for i,r in enumerate(highlights)])
            db.execute('UPDATE curated_collections SET revision=revision+1,updated_at=now() WHERE id=%s',(cid,))
        after=snapshot(db,ids);validate_after(plan,after)
        batch(db,'audit_log',[dict(id=m.uid('audit/'+phase+'/'+aid),actor_user_id=m.ACTOR,action='cesi_top100_enrichment',entity_type='artwork',entity_id=aid,request_id=m.OP,before_json=before.get(aid),after_json=after[aid]) for aid in ids])
        for r in plan['artist_changes']:
            a=db.execute('SELECT to_jsonb(a) v FROM artists a WHERE id=%s',(r['artist_id'],)).fetchone()['v'];batch(db,'audit_log',[dict(id=m.uid('artist-audit/'+r['artist_id']),actor_user_id=m.ACTOR,action='cesi_biography_review',entity_type='artist',entity_id=r['artist_id'],request_id=m.OP,before_json=r['before'],after_json=a)])
        m.save(m.BACKUP/phase/'transaction-postimages.json.gz',dict(plan_sha256=digest,artworks=after))
    receipt=dict(at=m.now(),target='production',phase=phase,plan_sha256=digest,new_artworks=sum(r['state']=='new' for r in rows),new_images=len(data['media_assets']),new_holding_connections=len(data['artwork_location_assertions']),new_creator_links=len(data['artwork_artists'])+sum(bool(r['creator_link']) for r in plan['supplements']),existing_artworks_enriched=sum(r['state']=='existing' for r in rows)+len(plan['supplements']),artist_biographies=len(plan['artist_changes']),new_teacher_relationships=len(plan['influences']),owner_highlights=len(highlights),publication_changes=0,current_display_claims=0,local_database_changes=0)
    m.save(folder/'applied.json',receipt);print(json.dumps(receipt,indent=2),flush=True)

def verify(phase):
    plan,digest=pinned(phase);assert m.load(m.RUN/phase/'applied.json')['plan_sha256']==digest;ids=[r['artwork_id'] for r in plan['rows']+plan['supplements']]
    with m.connect() as db:
        after=snapshot(db,ids);validate_after(plan,after)
        media=[r['image']['media_id'] for r in plan['rows'] if r['image']];got={r['v']['id']:r['v'] for r in db.execute('SELECT to_jsonb(a) v FROM media_assets a WHERE id=ANY(%s::uuid[])',(media,))};assert len(got)==len(media)
        for r in plan['rows']:
            if r['image']:
                im=r['image'];assert got[im['media_id']]['checksum_sha256']==im['sha256'] and got[im['media_id']]['byte_size']==im['bytes']<=100000
        evidence=db.execute('SELECT count(*) n FROM media_rights_evidence WHERE media_id=ANY(%s::uuid[])',(media,)).fetchone()['n'];assert evidence==len(media)
        if phase=='cesi':
            gotartist=db.execute('SELECT biography_md FROM artists WHERE id=%s',(C,)).fetchone();assert gotartist['biography_md']==plan['artist_changes'][0]['updates']['biography_md']
        for r in plan['influences']:
            iid=m.uid('influence/'+r['source_label']+'/'+r['target_artist_id'])
            got=db.execute('SELECT to_jsonb(i) v FROM influence_claims i WHERE id=%s',(iid,)).fetchone()['v']
            assert all(got[k]==v for k,v in r.items() if k not in ['source_url','receipt'])
            assert db.execute("SELECT 1 FROM citations WHERE entity_type='influence' AND entity_id=%s AND source_url=%s",(iid,r['source_url'])).fetchone()
    verification=m.RUN/phase/'database-verification.json'
    if verification.exists():assert m.load(verification)['plan_sha256']==digest
    else:m.save(verification,dict(at=m.now(),plan_sha256=digest,verified_artworks=len(ids),verified_images=len(media),verified_rights_evidence=evidence,verified_relationships=len(plan['influences']),original_statuses_preserved=True,original_images_preserved=True,original_holdings_preserved=True,local_database_changes=0))
    checks=[];chosen=plan['rows'] if phase=='cesi' else list({r['artist_id']:r for r in plan['rows']}.values())
    def one(r):
        slug=plan['artists'][r['artist_id']]['slug'];url='https://artlines.org/api/backend/v1/artists/'+slug+'/works/'+r['artwork_id'];response=requests.get(url,timeout=(15,60));response.raise_for_status();d=response.json();raw=json.dumps(d,ensure_ascii=False)
        assert r['artwork_id'] in raw and r['title'] in set(json_strings(d))
        if r['image']:assert r['image']['storage_path'] in raw
        return dict(artwork_id=r['artwork_id'],artist_id=r['artist_id'],url=url,status=response.status_code,sha256=m.sha(response.content),image_verified=bool(r['image']))
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:checks=list(pool.map(one,chosen))
    public=m.RUN/phase/'public-verification.json'
    if not public.exists():m.save(public,dict(at=m.now(),checks=checks,scope='Every Cesi addition, or one affected artwork per Top 100 painter; every uploaded image separately passed public byte-hash checks.'))
    relationships=[]
    for r in plan['influences']:
        iid=m.uid('influence/'+r['source_label']+'/'+r['target_artist_id']);slug=plan['artists'][r['target_artist_id']]['slug']
        url='https://artlines.org/api/backend/v1/artists/'+slug;response=requests.get(url,timeout=(15,60));response.raise_for_status()
        claim=next(x for x in response.json()['influences'] if x['id']==iid)
        assert claim['direction']=='incoming' and claim['relationship_type']==r['relationship_type']
        assert any(c['source_url']==r['source_url'] for c in claim['citations'])
        relationships.append(dict(id=iid,url=url,status=response.status_code,sha256=m.sha(response.content)))
    rp=m.RUN/phase/'public-relationship-verification.json'
    if not rp.exists():m.save(rp,dict(at=m.now(),checks=relationships))
    print('Verified',phase,len(ids),'database records',len(media),'images',len(checks),'public object routes',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command');p.add_argument('phase',nargs='?',choices=['cesi','top100']);a=p.parse_args()
    globals()[a.command](a.phase) if a.phase else globals()[a.command]()
