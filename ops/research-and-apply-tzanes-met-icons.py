#!/usr/bin/env python3
"""Primary Met review of two distinct, undated Tzanès icons and CC0 images.

The API indexing bounds mirror the artist's activity, so artwork dates stay
unknown. An individual historical-object review permits these museum-connected
icons as research candidates, without assigning an eligibility year.
"""
import argparse,base64,hashlib,importlib.util,json,uuid
from pathlib import Path
import requests
from psycopg.types.json import Jsonb
s=importlib.util.spec_from_file_location('r',Path(__file__).with_name('research-dutch-met-images.py'));r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
m=r.m;CORE=r.CORE;RUN=m.x.BASE/'greek-historical/tzanes-met-primary';SOURCE='overnight-tzanes-met-primary-20260913';IDS={'437856':('Q112644476','33.79.14'),'437858':('Q112644184','33.79.15')}
def plan():
    path=RUN/'metadata-plan.json'
    if path.exists():return
    records=[];targets={}
    for oid,(qid,acc) in IDS.items():
        raw=(m.x.BASE/'greek-historical/primary-objects'/f'met-{oid}.body').read_bytes();d=json.loads(raw);receipt=json.loads((m.x.BASE/'greek-historical/primary-objects'/f'met-{oid}.receipt.json').read_text());assert CORE.sha(raw)==receipt['sha256']
        assert d['objectID']==int(oid) and d['artistWikidata_URL'].endswith('/Q1338447') and d['artistNationality']=='Greek'
        assert d['objectDate']=='' and d['artistEndDate']=='1690' and d['isPublicDomain'] is True
        assert d['accessionNumber']==acc
        records.append(dict(object_id=oid,qid=qid,accession=acc,data=d,receipt=receipt,date_review='Explicit primary objectDate blank. Numeric objectBeginDate1636/objectEndDate1690 mirror artist active-by1636/died1690, not independently stated artwork dating. Keep unknown date and research_candidate=true. This named post-Byzantine maker and distinct museum inventory establish a historical object for individual research review, without inventing creation bounds.'))
    for target in ('local','production'):
        with m.m.r.base.connect(target=='production') as db,db.transaction():
            db.execute('SET TRANSACTION READ ONLY')
            artist=db.execute("SELECT to_jsonb(a) row FROM artists a JOIN external_identifiers e ON e.entity_id=a.id AND e.entity_type='artist' WHERE e.scheme='wikidata' AND e.external_id='Q1338447'").fetchone()['row']
            assert artist['status']=='review' and artist['death_year']==1690 and artist['published_at'] is None
            assert db.execute("SELECT 1 FROM artist_countries WHERE artist_id=%s AND country_code='GR' AND relationship_type='cultural_affiliation'",(artist['id'],)).fetchone()
            inst=db.execute("SELECT id::text,slug,name FROM institutions WHERE slug='the-met' AND status='review'").fetchone();assert inst
            existing=db.execute("SELECT to_jsonb(w) work FROM artwork_artists aa JOIN artworks w ON w.id=aa.artwork_id WHERE aa.artist_id=%s AND w.status<>'archived'",(artist['id'],)).fetchall()
            for e in records:
                d=e['data'];assert not any(w['work']['accession_number']==e['accession'] or m.m.r.norm(w['work']['title'])==m.m.r.norm(d['title']) for w in existing)
                assert not db.execute("SELECT 1 FROM external_identifiers WHERE entity_type='artwork' AND ((scheme IN ('met-object','european-met-the-met-object') AND external_id=%s) OR (scheme='wikidata' AND external_id=%s))",(e['object_id'],e['qid'])).fetchone()
                assert not db.execute("SELECT 1 FROM citations c JOIN artworks w ON w.id=c.entity_id WHERE c.entity_type='artwork' AND c.source_url=ANY(%s) AND w.status<>'archived'",([d['objectURL'],'https://www.wikidata.org/wiki/'+e['qid']],)).fetchone()
        targets[target]=dict(artist=artist,institution=inst);CORE.save_new(m.BACKUPS/f'tzanes-met-primary-{target}-preimages.json',dict(artist=artist,institution=inst,works=existing))
    assert targets['local']['artist']['slug']==targets['production']['artist']['slug']
    CORE.save_new(path,dict(at=CORE.now(),records=records,targets=targets));CORE.save_new(RUN/'metadata-manifest.json',dict(at=CORE.now(),plan_sha256=CORE.sha(path.read_bytes()),new_artworks=2,unknown_dates=2,distinct_companion_icons_preserved=True));print('Tzanes metadata plan2 unknown-date icons',flush=True)
def prepare():
    data=json.loads((RUN/'metadata-plan.json').read_text());a=data['targets']['local']['artist'];selected=[]
    for e in data['records']:
        oid=e['object_id'];d=e['data'];selected.append(dict(target=dict(object_id=oid,work=dict(slug='greek-met-'+oid,title=d['title'])),artist=dict(slug=a['slug'],display_name=a['display_name']),evidence=dict(data=d,receipt=e['receipt']),rights_basis='Exact Met object API isPublicDomain=true with primaryImage and accession; museum programme CC0. Two individual post-Byzantine icons reviewed despite blank creation dating; unknown fields and editorial research status retained.'))
    folder=RUN/'round-01'
    if not (folder/'research.json').exists():CORE.save_new(folder/'research.json',dict(at=CORE.now(),selected=selected))
    r.RUN=RUN;r.ORIGINALS=Path('/Users/vadimdulub/Library/Application Support/Artline/source-images/overnight-countries-20260913/tzanes-met');r.prepare(1)
def apply():
    raw=(RUN/'metadata-plan.json').read_bytes();pin=CORE.sha(raw);data=json.loads(raw);assert pin==json.loads((RUN/'metadata-manifest.json').read_text())['plan_sha256']
    folder=RUN/'round-01';prep=json.loads((folder/'preparation.json').read_text());qa=json.loads((folder/'quality-review.json').read_text());assert qa['approved'] and qa['contact_sheet_sha256']==CORE.sha((folder/'contact-sheet.jpg').read_bytes())
    images={}
    for name,checksum in prep['prepared_hashes'].items():
        raw=(folder/'prepared'/name).read_bytes();assert CORE.sha(raw)==checksum;im=json.loads(raw)
        if im['key'] in qa['accepted']:images[im['key']]=im
    bucket=CORE.storage.Client(project='artline-508319',credentials=CORE.GcloudCredentials()).bucket(CORE.BUCKET)
    for im in images.values():
        raw=(m.x.ROOT/'apps/web/public'/im['path'].lstrip('/')).read_bytes();assert CORE.sha(raw)==im['sha256'] and len(raw)<=100000
        blob=bucket.blob(im['path'].lstrip('/'))
        if not blob.exists():blob.metadata=dict(sha256=im['sha256'],license='CC0',museum_object=im['key']);blob.cache_control='public,max-age=31536000,immutable';blob.upload_from_string(raw,content_type='image/jpeg',if_generation_match=0,timeout=60)
        blob.reload();assert blob.md5_hash==base64.b64encode(hashlib.md5(raw).digest()).decode()
    for target in ('local','production'):
        done=RUN/f'{target}-verified.json'
        if done.exists():continue
        ctx=data['targets'][target];artist=ctx['artist'];inst=ctx['institution']
        with m.m.r.base.connect(target=='production') as db:
            with db.transaction():
                db.execute('SELECT pg_advisory_xact_lock(559220260914)');sid=m.m.source(db,SOURCE,'Met primary catalogue: individually reviewed undated Tzanès icons','museum_api','https://collectionapi.metmuseum.org/')
                for e in data['records']:
                    oid=e['object_id'];d=e['data'];aid=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.local/greek-met/'+oid));im=images.get(oid)
                    if db.execute("SELECT 1 FROM citations WHERE entity_type='artwork' AND entity_id=%s AND source_id=%s AND evidence_note LIKE %s",(aid,sid,'%'+pin+'%')).fetchone():continue
                    assert not db.execute("SELECT 1 FROM external_identifiers WHERE scheme IN ('met-object','european-met-the-met-object','wikidata') AND external_id=ANY(%s)",([oid,e['qid']],)).fetchone()
                    m.m.r.base.insert(db,'artworks',dict(id=aid,slug='greek-met-'+oid,title=d['title'],normalized_title=m.m.r.norm(d['title']),date_display='Date unspecified in the museum catalogue',creation_year_start=None,creation_year_end=None,date_precision='unknown',work_type='painting',object_form='icon',medium_text=d['medium'],dimensions_text=d['dimensions'],description_md='Post-Byzantine icon catalogued by The Metropolitan Museum of Art and attributed to Emmanuel Tzanès. The museum does not state an artwork creation date. Record remains in review.',current_institution_id=inst['id'],accession_number=e['accession'],status='review',research_candidate=True,created_by=m.m.ACTOR,updated_by=m.m.ACTOR))
                    m.m.r.base.insert(db,'artwork_artists',dict(artwork_id=aid,artist_id=artist['id'],attribution_role='primary',attribution_note='Exact primary Met maker authority Q1338447; Greek artist biography distinct from artwork date.'))
                    m.m.r.base.insert(db,'artwork_location_assertions',dict(artwork_id=aid,claim_type='holding',institution_id=inst['id'],context='collection',source_id=sid,source_url=d['objectURL'],evidence_note='Exact Met object and distinct inventory. '+d['creditLine']+'. No current display assertion imported.',checked_at=e['receipt']['retrieved_at'],review_state='accepted'))
                    for scheme,value,url in [('met-object',oid,d['objectURL']),('wikidata',e['qid'],'https://www.wikidata.org/wiki/'+e['qid'])]:m.m.r.base.insert(db,'external_identifiers',dict(entity_type='artwork',entity_id=aid,scheme=scheme,external_id=value,canonical_url=url,source_id=sid,retrieved_at=e['receipt']['retrieved_at']))
                    m.m.r.base.insert(db,'citations',dict(entity_type='artwork',entity_id=aid,source_id=sid,field_name='official_object_identity',source_record_id=oid,source_url=d['objectURL'],retrieved_at=e['receipt']['retrieved_at'],created_by=m.m.ACTOR,evidence_note=json.dumps(dict(plan_sha256=pin,primary_evidence=e,review_status='review'),ensure_ascii=False)))
                    if im:
                        mid=im['media_id'];m.m.r.base.insert(db,'media_assets',dict(id=mid,storage_kind='local',storage_path=im['path'],source_page_url=im['page'],provider_name='The Metropolitan Museum of Art',mime_type='image/jpeg',width=im['width'],height=im['height'],byte_size=im['bytes'],checksum_sha256=im['sha256'],alt_text=im['title']+' — '+im['artist'],rights_status='cc0',license_label='CC0',license_url=r.CC0,creator_credit=im['creator_credit'],attribution_text=im['attribution_text'],retrieved_at=im['download']['retrieved_at'],verified_at=im['checked_at'],verified_by=m.m.ACTOR))
                        m.m.r.base.insert(db,'media_rights_evidence',dict(media_id=mid,source_id=sid,source_record_id=oid,source_checksum=e['receipt']['sha256'],source_image_url=im['source_image_url'],policy_url=r.CC0,rights_basis=im['identity']['rights_basis'],adapter_version='tzanes-met-primary-v1',checked_at=im['checked_at'],evidence_json=Jsonb(im)))
                        m.m.r.base.insert(db,'artwork_media',dict(artwork_id=aid,media_id=mid,sort_order=0,view_label='Museum Open Access reproduction'))
                        db.execute('UPDATE artworks SET primary_media_id=%s WHERE id=%s',(mid,aid))
            with db.transaction():
                db.execute('SET TRANSACTION READ ONLY')
                for e in data['records']:
                    w=db.execute("SELECT to_jsonb(w) row,artline_has_selection_evidence(w.id) selected FROM artworks w WHERE slug=%s",('greek-met-'+e['object_id'],)).fetchone();a=w['row'];assert w['selected'] and a['status']=='review' and a['published_at'] is None and a['research_candidate'] and a['date_precision']=='unknown' and a['creation_year_start'] is None and a['creation_year_end'] is None and a['object_form']=='icon' and a['accession_number']==e['accession']
                    assert db.execute('SELECT 1 FROM artwork_artists WHERE artwork_id=%s AND artist_id=%s',(a['id'],artist['id'])).fetchone()
                    assert not db.execute("SELECT 1 FROM artwork_location_assertions WHERE artwork_id=%s AND claim_type='display'",(a['id'],)).fetchone()
                    if e['object_id'] in images:assert a['primary_media_id']==images[e['object_id']]['media_id'] and db.execute('SELECT 1 FROM media_rights_evidence WHERE media_id=%s',(a['primary_media_id'],)).fetchone()
                assert db.execute('SELECT to_jsonb(a) row FROM artists a WHERE id=%s',(artist['id'],)).fetchone()['row']==artist
        CORE.save_new(done,dict(at=CORE.now(),plan_sha256=pin,new_artworks=2,images=len(images),unknown_dates_preserved=2,painter_biography_and_review_preserved=True));print(target,'Tzanes2 verified',flush=True)
    p=RUN/'public-images-verified.json'
    if not p.exists():
        out=[]
        for im in images.values():
            resp=requests.get(m.SITE+im['path'],timeout=90);resp.raise_for_status();assert CORE.sha(resp.content)==im['sha256'];out.append(dict(url=m.SITE+im['path'],status=resp.status_code,sha256=im['sha256']))
        CORE.save_new(p,dict(at=CORE.now(),images=out))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['plan','prepare','apply']);a=p.parse_args();globals()[a.command]()
