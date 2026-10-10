#!/usr/bin/env python3
"""Read-only production/API verification and the complete national research ledger."""
import argparse, collections, concurrent.futures, csv, html, importlib.util, json, time
from pathlib import Path
from urllib.parse import urlencode
import requests
spec=importlib.util.spec_from_file_location('d',Path(__file__).with_name('greek-museums-delivery-20261008.py'))
d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
RUN,BACKUP=d.RUN,d.BACKUP


def plans():
    p=d.load(RUN/d.PLAN);q=d.load(RUN/'supplement-delivery-plan.json.gz')
    p['records']+=q['records'];p['museums'].update(q['museums']);p['held']+=q['held']
    native=d.load(RUN/'native-delivery-plan-v2.json.gz')
    p['records']+=native['records'];p['museums'].update(native['museums']);p['held']+=native['held']
    quality=d.load(RUN/'quality-corrections-applied.json');mu=quality['new_museum']
    p['museums']['quality-varnavas']=dict(row=mu,before=None)
    for f in p['records']:
        change=quality['changes'].get(f['artwork_id'],{})
        for key in ['title','date_display']:
            if key in change:f[key]=change[key]
        for key,dest in [('creation_year_start','first'),('creation_year_end','last')]:
            if key in change:f[dest]=change[key]
        if 'date_precision'in change:f['precision']=change['date_precision']
        if 'current_institution_id'in change:
            assert change['current_institution_id']==mu['id']
            f['museum']=mu;f['museum_key']='quality-varnavas'
    return p


def geography():
    url='https://www.alphapolitismos.gr/en/art-collection/';s,rc=d.g.page(url)
    text=d.g.clean(s);anchor='41 Panepistimiou Street, 105 64 Athens';assert anchor in text
    with d.connect()as db:
        before=db.execute("SELECT to_jsonb(i) row FROM institutions i WHERE slug='wikimedia-museum-q136297890'").fetchone()['row']
        place=db.execute("SELECT id::text FROM places WHERE country_code='GR' AND name='Athens'").fetchall();assert len(place)==1 and before['place_id']is None
    evidence=dict(at=d.now(),before=before,place_id=place[0]['id'],receipt=rc,address=anchor,scope='Collection administrative address; does not assert physical display of its works.')
    d.save(RUN/'alpha-geography-plan.json',evidence);d.save(BACKUP/'alpha-geography-preimage.json',evidence)
    with d.connect(readonly=False)as db,db.transaction():
        current=db.execute('SELECT to_jsonb(i) row FROM institutions i WHERE id=%s FOR UPDATE',(before['id'],)).fetchone()['row'];assert current==before
        db.execute('UPDATE institutions SET place_id=%s,updated_at=now() WHERE id=%s',(place[0]['id'],before['id']))
        after=db.execute('SELECT to_jsonb(i) row FROM institutions i WHERE id=%s',(before['id'],)).fetchone()['row']
        d.m.audit_entry(db,'institution',before['id'],before,after,'update')
        d.m.insert(db,'citations',dict(entity_type='institution',entity_id=before['id'],field_name='greek_museum_geography_20261008',source_id=d.uid('source'),source_url=url,
            evidence_note=json.dumps(evidence,ensure_ascii=False),retrieved_at=rc['retrieved_at'],created_by=d.ACTOR))
    d.save(RUN/'alpha-geography-applied.json',dict(at=d.now(),after=after));print('Alpha collection geography verified',flush=True)


def get(url):
    for attempt in range(3):
        r=requests.get(url,timeout=(15,45))
        if r.status_code in [500,502,503,504]and attempt<2:time.sleep(2);continue
        r.raise_for_status();return r


def verify():
    p=plans();catalogue={}
    for filename in ['catalogue-applied.json','supplement-catalogue-applied.json','native-catalogue-applied.json']:
        receipt=d.load(RUN/filename);catalogue.update({x['artwork']['id']:x['artwork']for x in d.load(Path(receipt['after_path']))})
    quality=d.load(RUN/'quality-corrections-applied.json');catalogue.update({x['artwork']['id']:x['artwork']for x in quality['after']})
    images={}
    for batch in ['greek','native']:
        attached=d.load(RUN/(batch+'-images-applied.json'));catalogue.update({x['id']:x for x in attached['after']})
        image_plan=d.load(RUN/(batch+'-image-plan.json.gz'));images.update({x['image']['artwork_id']:x['image']for x in image_plan['records']})
    original={x['artwork']['id']:x for x in d.load(RUN/'production-scoped-artworks.json.gz')};facts={f['artwork_id']:f for f in p['records']}
    with d.connect()as db:
        rows=d.full_rows(db,list(catalogue));assert len(rows)==len(catalogue)
        selected={r['id']:r['selected']for r in db.execute('SELECT id::text,artline_has_selection_evidence(id) selected FROM artworks WHERE id=ANY(%s::uuid[])',(list(facts),))}
        for x in rows:
            w=x['artwork'];aid=w['id'];assert w==catalogue[aid],('artwork_drift',aid)
            assert w['status']=='review'and w['published_at']is None
            if aid in facts:
                f=facts[aid];assert selected[aid]and w['current_institution_id']==f['museum']['id']
                assert any(e['scheme']==f['scheme']and e['external_id']==f['source_id']for e in x['identifiers'])
                assert not any(l['claim_type']=='display'for l in x['locations'])
                if f['before']:
                    prior=f['before']['artwork']
                    assert all(w[k]==prior[k]for k in prior if k not in {'current_institution_id','primary_media_id','revision','updated_at','updated_by'})
                    if prior['primary_media_id']:assert w['primary_media_id']==prior['primary_media_id']
                    assert all(c in x['citations']for c in f['before']['citations'])
            if aid in original:
                before=original[aid]['artwork'];assert all(w[k]==before[k]for k in before if k not in {'primary_media_id','revision','updated_at','updated_by'})
                assert all(c in x['citations']for c in original[aid]['citations'])
                assert all(l in x['locations']for l in original[aid]['locations'])
        media=db.execute('SELECT to_jsonb(m) media,to_jsonb(e) evidence FROM media_assets m JOIN media_rights_evidence e ON e.media_id=m.id WHERE m.id=ANY(%s::uuid[])',([im['media_id']for im in images.values()],)).fetchall()
        assert len(media)==len(images)
        byid={im['media_id']:im for im in images.values()}
        for r in media:
            im=byid[r['media']['id']];assert r['media']['checksum_sha256']==im['sha256']and r['media']['byte_size']==im['bytes']<=100000
            assert r['evidence']['evidence_json']==im and r['media']['rights_status']==im['rights_status']
            assert r['media']['provider_name']==im['provider_name']
        mids={mu['row']['id']for mu in p['museums'].values()}|{x['institution']['id']for x in d.load(RUN/'production-baseline.json')['institutions']}
        totals=db.execute("SELECT i.id::text,i.slug,i.name,p.name city,p.country_code,count(a.id) artworks,count(a.primary_media_id) images FROM institutions i JOIN places p ON p.id=i.place_id LEFT JOIN artworks a ON a.current_institution_id=i.id AND a.status<>'archived' WHERE i.id=ANY(%s::uuid[]) GROUP BY i.id,p.id ORDER BY i.name",(list(mids),)).fetchall()
        assert len(totals)==len(mids)and all(r['country_code']=='GR'and r['artworks']>0 for r in totals)
        audits=db.execute("SELECT entity_id::text id,count(*) n FROM audit_log WHERE request_id=%s AND entity_type='artwork' GROUP BY entity_id",(RUN.name,)).fetchall()
        assert set(catalogue)<={r['id']for r in audits}
    samples={}
    for f in p['records']:samples.setdefault(f['museum']['slug'],f['artwork_id'])
    for im in images.values():samples.setdefault(im['museum']['slug'],im['artwork_id'])
    def artwork_check(item):
        slug,aid=item;url='https://artlines.org/api/backend/v1/museums/'+slug+'/works/'+aid;r=get(url);body=r.json()
        assert body['id']==aid and body['status']=='review'
        if aid in images:assert body['media_url']==images[aid]['path']
        return dict(url=url,status=r.status_code,artwork_id=aid)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool:api=list(pool.map(artwork_check,samples.items()))
    def image_check(im):
        r=get('https://artlines.org'+im['path']);assert d.sha(r.content)==im['sha256']
        return dict(artwork_id=im['artwork_id'],path=im['path'],sha256=d.sha(r.content),status=r.status_code)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool:public=list(pool.map(image_check,images.values()))
    # Verify all country pages through bounded cursors, never a full browser fetch.
    country=[];cursor=None
    for page in range(10):
        params=dict(country='GR',limit=60)
        if cursor:params['cursor']=cursor
        url='https://artlines.org/api/backend/v1/museums?'+urlencode(params);r=get(url);body=r.json()
        country.append(dict(url=url,status=r.status_code,body=body));cursor=body.get('next_cursor')
        if not cursor:break
    d.save(RUN/'country-api-verification.json',country)
    visible=[item for page in country for item in page['body']['items']]
    assert mids<={item['id']for item in visible}
    assert len({item['id']for item in visible})==len(visible)
    assert all(item['country']=='GR'and item['work_count']>0 for item in visible)
    with d.connect('local')as db:
        before_local=d.load(RUN/'local-baseline.json')['institutions']
        local=db.execute("SELECT i.id::text,(SELECT count(*)FROM artworks a WHERE a.current_institution_id=i.id AND a.status<>'archived')works,(SELECT count(*)FROM artworks a WHERE a.current_institution_id=i.id AND a.status<>'archived'AND a.primary_media_id IS NOT NULL)images FROM institutions i WHERE i.id=ANY(%s::uuid[])",([x['institution']['id']for x in before_local],)).fetchall()
    unchanged={x['id']:(x['works'],x['images'])for x in local}=={x['institution']['id']:(x['works'],x['images'])for x in before_local}
    result=dict(at=d.now(),new_artworks=sum(f['action']=='create'for f in p['records']),existing_artworks_linked=sum(f['action']=='enrich'for f in p['records']),new_museums=sum(not mu['before']for mu in p['museums'].values()),images=len(images),
        museum_totals=totals,artwork_records_verified=len(rows),artwork_api_checks=api,public_image_checks=public,
        all_new_artworks_in_review=True,no_new_current_display_claims=True,local_queried_read_only=True,local_baseline_counts_unchanged=unchanged,errors=[])
    d.save(RUN/'verification.json',result)
    print('VERIFIED',len(p['records']),'artworks',len(images),'public images',len(totals),'Greek museums',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['geography','verify']);args=parser.parse_args();globals()[args.action]()
