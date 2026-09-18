#!/usr/bin/env python3
"""Select a bounded known-artist FNG expansion; preserve source uncertainty and review status."""
import argparse,collections,importlib.util,json,re,uuid
from pathlib import Path
import psycopg
from psycopg.rows import dict_row
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('fng',ROOT/'ops/overnight-fng-images.py');fng=importlib.util.module_from_spec(s);s.loader.exec_module(fng);core=fng.core
RUN=ROOT/'docs/research/overnight-images-20260915/fng-new';BACKUP=Path.home()/'Library/Application Support/Artline/backups/overnight-images-20260915/fng-new'
SOURCE='overnight-fng-selected-primary-20260915'
def aid(oid):return str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.local/night-selected-fng/'+str(oid)))
def title(o):return next((o['title'].get(lang) for lang in ('en','fi','sv') if o['title'].get(lang)),None)
def norm(v):return fng.norm(v or '')
def facts(o):return {k:o.get(k) for k in ('objectId','responsibleOrganisation','owner','title','yearFrom','yearTo','datePrefix','category','classifications','materials','inventoryNumber','people','children','parents','multimedia','dimensions')}
def candidate(row,institution_id):
    o=row['object'];ar=row['artist'];oid=str(o['objectId']);lo=o['yearFrom'];hi=o.get('yearTo') or lo;circa=(o.get('datePrefix') or {}).get('en')=='circa'
    c={'artwork_id':aid(oid),'slug':'night-fng-'+oid,'title':title(o),'alternate_title':next((t for t in o['title'].values() if t and t!=title(o)),None),
       'creation_year_start':lo,'creation_year_end':hi,'date_precision':('circa' if lo==hi else 'circa_range') if circa else ('exact' if lo==hi else 'range'),
       'date_display':('circa ' if circa else '')+(str(lo) if lo==hi else str(lo)+'–'+str(hi)),
       'work_type':row['work_type'],'status':'review','research_candidate':True,'accession_number':o['inventoryNumber'],
       'primary_media_id':None,'current_institution_id':institution_id,'external_id':oid,'source_id':None,'fng_people':[ar['external_id']],
       'roles':['primary'],'artist':ar['display_name'],'artist_slug':ar['slug'],'popular':row.get('popular',False),'provider':'night-fng','scheme':'fng-object',
       'target_ids':{'local':aid(oid)},'institution_ids':{'local':institution_id},'artist_authority':ar['external_id'],'raw_object':facts(o)}
    fng.source_match(c,o)
    return c

def build():
    p=RUN/'plan.json'
    if p.exists():return json.loads(p.read_text())
    leads=json.loads((RUN/'after-local-duplicate-check.json').read_text());held=[];accepted=[]
    receipt=json.loads((RUN.parent/'fng/objects-current.receipt.json').read_text())
    with fng.ro('postgres://localhost/artline') as db:
        inst=db.execute("SELECT id::text FROM institutions WHERE wikidata_id='Q2983474' AND status<>'archived'").fetchall();assert len(inst)==1;iid=inst[0]['id']
        # Institution-scoped accessions include records linked through assertions or object identifiers, even if archived or creator-unmapped.
        existing=db.execute("""SELECT DISTINCT a.id::text,a.title,a.alternate_title,a.accession_number,
          (SELECT external_id FROM external_identifiers e WHERE e.entity_type='artwork' AND e.entity_id=a.id AND e.scheme='fng-object') fng_id
          FROM artworks a WHERE a.current_institution_id=%s OR a.id IN
          (SELECT artwork_id FROM artwork_location_assertions WHERE institution_id=%s) OR a.id IN
          (SELECT entity_id FROM external_identifiers WHERE entity_type='artwork' AND scheme='fng-object')""",(iid,iid)).fetchall()
        core.save_new(BACKUP/'local-preimages.json',existing)
        by_accession=collections.defaultdict(list);ids=set()
        for e in existing:
            if e['accession_number']:by_accession[norm(e['accession_number'])].append(e['id'])
            if e['fng_id']:ids.add(e['fng_id'])
        popular={r['artist_id'] for r in db.execute('SELECT artist_id::text FROM artist_discovery_selection WHERE is_popular').fetchall()}
        seen_acc=set();seen_oid=set()
        for row in leads:
            oid=str(row['object']['objectId']);acc=norm(row['object'].get('inventoryNumber'));row['popular']=row['artist']['id'] in popular
            try:
                if oid in ids or oid in seen_oid:raise ValueError('Existing or duplicate FNG object ID')
                if not acc or by_accession.get(acc) or acc in seen_acc:raise ValueError('Missing or colliding institution accession')
                c=candidate(row,iid)
                if not c['title']:raise ValueError('Missing source title')
                # Do not create duplicate object URLs stored under another identifier scheme.
                url='https://kokoelma.kansallisgalleria.fi/en/object/'+oid
                if db.execute("SELECT 1 FROM external_identifiers WHERE entity_type='artwork' AND canonical_url=ANY(%s)",([url,url.replace('/en/','/fi/'),url.replace('/en/','/sv/')],)).fetchone():raise ValueError('Existing canonical object URL')
                accepted.append(c);seen_oid.add(oid);seen_acc.add(acc)
            except ValueError as exc:held.append({'source_object_id':oid,'reason':str(exc)})
    accepted.sort(key=lambda c:(not c['popular'],c['work_type']!='painting',c['artist'],c['title'],c['external_id']))
    data={'at':core.now(),'records':accepted,'metadata_capture':receipt,'production_pending':True,'policy':'Known established FNG artist authorities; source-typed works, bounded source dates, exact CC0 preferred media; no biography or nationality inference. All new objects remain in review.'}
    core.save_new(p,data);core.save_new(RUN/'plan-manifest.json',{'sha256':core.sha(p.read_bytes()),'count':len(accepted)});core.save_new(RUN/'final-held.json',held)
    print('FNG new reviewed plan',len(accepted),'types',dict(collections.Counter(c['work_type'] for c in accepted)),'held',len(held),flush=True)
    return data

def apply(target):
    data=build();assert core.sha((RUN/'plan.json').read_bytes())==json.loads((RUN/'plan-manifest.json').read_text())['sha256'];dsn='postgres://localhost/artline' if target=='local' else core.cloud_dsn()
    with psycopg.connect(dsn,autocommit=True,row_factory=dict_row) as db:
        inst=db.execute("SELECT id::text FROM institutions WHERE wikidata_id='Q2983474' AND status<>'archived'").fetchall();assert len(inst)==1;iid=inst[0]['id'];out=[];sid=None
        known={r['id']:r for r in db.execute('SELECT id::text,title,status,accession_number,creation_year_start,creation_year_end,date_precision,work_type FROM artworks WHERE id=ANY(%s::uuid[])',([c['artwork_id'] for c in data['records']],)).fetchall()}
        for c in data['records']:
            o=c['raw_object'];fng.source_match(c,o);object_url='https://kokoelma.kansallisgalleria.fi/en/object/'+c['external_id']
            if c['artwork_id'] in known:
                old=known[c['artwork_id']];assert old['status']=='review' and all(old[k]==c[k] for k in ('title','accession_number','creation_year_start','creation_year_end','date_precision','work_type'))
                out.append({'artwork_id':c['artwork_id'],'outcome':'already_present'});continue
            with db.transaction(),db.pipeline():
                db.execute('SELECT pg_advisory_xact_lock(559220260915)')
                artist=db.execute("SELECT a.id::text,a.slug FROM artists a JOIN external_identifiers e ON e.entity_type='artist' AND e.entity_id=a.id AND e.scheme='fng-person' AND e.external_id=%s WHERE a.status<>'archived'",(c['artist_authority'],)).fetchall();assert len(artist)==1 and artist[0]['slug']==c['artist_slug']
                existing=db.execute('SELECT id::text,title,status,accession_number FROM artworks WHERE id=%s',(c['artwork_id'],)).fetchone()
                if existing:
                    assert existing['title']==c['title'] and existing['status']=='review' and existing['accession_number']==c['accession_number'];out.append({'artwork_id':c['artwork_id'],'outcome':'already_present'});continue
                assert not db.execute("SELECT 1 FROM external_identifiers WHERE entity_type='artwork' AND ((scheme='fng-object' AND external_id=%s) OR canonical_url=%s)",(c['external_id'],object_url)).fetchone(),'Object exists; needs cross-database reconciliation'
                assert not db.execute("SELECT 1 FROM slug_redirects WHERE entity_type='artwork' AND (old_slug=%s OR entity_id=%s)",(c['slug'],c['artwork_id'])).fetchone()
                peers=db.execute("""SELECT a.id::text,a.title,a.alternate_title,a.accession_number,
                    (SELECT external_id FROM external_identifiers e WHERE e.entity_type='artwork' AND e.entity_id=a.id AND e.scheme='fng-object') fng_id
                    FROM artworks a JOIN (
                      SELECT id FROM artworks WHERE current_institution_id=%s AND accession_number=%s
                      UNION SELECT artwork_id FROM artwork_artists WHERE artist_id=%s
                    ) requested ON requested.id=a.id""",(iid,c['accession_number'],artist[0]['id'])).fetchall()
                for old in peers:
                    if norm(old['accession_number'])==norm(c['accession_number']):raise ValueError('Accession collision at import')
                    if not old['fng_id'] and {norm(old['title']),norm(old['alternate_title'])} & {norm(v) for v in o['title'].values() if v}:raise ValueError('Unresolved title collision at import')
                if sid is None:
                    db.execute("INSERT INTO sources(slug,name,source_type,base_url,terms_url) VALUES(%s,'Finnish National Gallery: selected source-verified works','museum_api','https://kokoelma.kansallisgalleria.fi/api/v1/objects',%s) ON CONFLICT(slug) DO NOTHING",(SOURCE,fng.LICENCE));sid=db.execute('SELECT id FROM sources WHERE slug=%s',(SOURCE,)).fetchone()['id']
                material='; '.join(m.get('en') or m.get('fi') or m.get('sv') or '' for m in o.get('materials',[])) or None
                db.execute("""INSERT INTO artworks(id,slug,title,alternate_title,normalized_title,date_display,creation_year_start,creation_year_end,date_precision,work_type,medium_text,current_institution_id,accession_number,status,research_candidate,created_by,updated_by)
                    VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'review',true,%s,%s)""",(c['artwork_id'],c['slug'],c['title'],c['alternate_title'],norm(c['title']),c['date_display'],c['creation_year_start'],c['creation_year_end'],c['date_precision'],c['work_type'],material,iid,c['accession_number'],core.ACTOR,core.ACTOR))
                db.execute("INSERT INTO artwork_artists(artwork_id,artist_id,attribution_role,attribution_note) VALUES(%s,%s,'primary','Exact unqualified primary artist authority in current FNG object record; no biography changes.')",(c['artwork_id'],artist[0]['id']))
                db.execute("INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at) VALUES('artwork',%s,'fng-object',%s,%s,%s,%s)",(c['artwork_id'],c['external_id'],object_url,sid,data['metadata_capture']['retrieved_at']))
                db.execute("""INSERT INTO artwork_location_assertions(artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state)
                    VALUES(%s,'holding',%s,'collection',%s,%s,%s,%s,'accepted')""",(c['artwork_id'],iid,sid,object_url,'Current museum export: '+o['responsibleOrganisation']+'; owner '+o['owner']+'; accession '+c['accession_number']+'. Holding only; not a current-display claim.',data['metadata_capture']['retrieved_at']))
                db.execute("INSERT INTO citations(entity_type,entity_id,source_id,field_name,source_record_id,source_url,evidence_note,retrieved_at,created_by) VALUES('artwork',%s,%s,'official_object_identity',%s,%s,%s,%s,%s)",(c['artwork_id'],sid,c['external_id'],object_url,json.dumps({'primary_record':o,'metadata_capture':data['metadata_capture'],'metadata_license':fng.LICENCE,'date_note':'Display formatting preserves structured museum date bounds and explicit circa qualifier; no inferred creation year.'},ensure_ascii=False),data['metadata_capture']['retrieved_at'],core.ACTOR))
                out.append({'artwork_id':c['artwork_id'],'outcome':'inserted'})
            if len(out)%100==0:print(target,len(out),'of',len(data['records']),flush=True)
        verified=db.execute("SELECT count(*) n,count(*) FILTER(WHERE status='review' AND published_at IS NULL AND research_candidate AND artline_has_selection_evidence(id)) ok FROM artworks WHERE id=ANY(%s::uuid[])",([c['artwork_id'] for c in data['records']],)).fetchone();assert verified['n']==verified['ok']==len(data['records'])
        receipt=RUN/(target+'-metadata-verified.json')
        if not receipt.exists():core.save_new(receipt,{'at':core.now(),'counts':verified,'records':out})
        print(target,'verified',verified,flush=True)
    if target=='local':prepare_manifest(data,iid)
    else:raise SystemExit('Production metadata complete. Reconcile candidate target_ids/institution_ids before image upload; local receipts are preserved.')

def prepare_manifest(data,iid):
    if (RUN/'candidates.json').exists():
        previous=json.loads((RUN/'candidates.json').read_text())
        assert {c['artwork_id'] for c in previous['candidates']}=={c['artwork_id'] for c in data['records']}
        return
    accepted=[]
    for c in data['records']:
        o=c['raw_object'];im,url=fng.source_match(c,o);credit=c['artist']+'; Finnish National Gallery'
        if im.get('photographer_name'):credit+='; photograph: '+im['photographer_name']
        raw=facts(o);raw['multimedia']=[im];x={k:v for k,v in c.items() if k!='raw_object'}
        x.update(source_image_url=url,page='https://kokoelma.kansallisgalleria.fi/en/object/'+c['external_id'],raw={'object':raw,'metadata_capture':data['metadata_capture']},
          policy_url=fng.LICENCE,rights_status='cc0',license_label='CC0 1.0',checked_at=data['at'],creator_credit=credit,
          attribution_text=f"{c['artist']}. {c['title']}. {credit}. CC0 ({fng.LICENCE}). Full-frame proportional resize and JPEG compression.",
          source_name='Finnish National Gallery',source_record_url='https://kokoelma.kansallisgalleria.fi/en/object/'+c['external_id'],image_url=url,image_license='CC0 1.0',image_license_url=fng.LICENCE,
          rights_statement='CC0',creator=c['artist'],creation_date=c['date_display'],source_object_id=c['external_id'],rights_verified_at=data['at'])
        core.save_new(RUN/'selected/night-fng'/(c['artwork_id']+'.json'),x);accepted.append(x)
    core.save_new(RUN/'candidates.json',{'created_at':core.now(),'candidates':accepted,'production_metadata_pending':True})
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['plan','apply']);p.add_argument('--target',choices=['local','cloud'],default='local');a=p.parse_args();RUN.mkdir(parents=True,exist_ok=True);BACKUP.mkdir(parents=True,exist_ok=True);build() if a.phase=='plan' else apply(a.target)
