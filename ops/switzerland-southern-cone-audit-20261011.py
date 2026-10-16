#!/usr/bin/env python3
"""Read-only production verification and per-directory research reconciliation."""
import collections
import csv
import gzip
import importlib.util
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

s=importlib.util.spec_from_file_location('d',Path(__file__).with_name('switzerland-southern-cone-delivery-20261011.py'))
d=importlib.util.module_from_spec(s);s.loader.exec_module(d)
PHASES=['CH-followup','AR-wave1','UY-wave1','PY-wave1','AR-wave2','UY-wave2']
SWISS=d.ROOT/'docs/research/switzerland-india-museums-20261011'
REVISION=sys.argv[1] if len(sys.argv)>1 else 'v3'
assert re.fullmatch(r'v[0-9]+',REVISION)


def urlkey(url):
    p=urlsplit(url or '')
    return p.netloc.lower().removeprefix('www.')+p.path.rstrip('/')


def csvwrite(path,rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def run():
    plans={phase:d.pinned(phase)[0] for phase in PHASES}
    allrows=[r for p in plans.values() for r in p['records']]
    valid_hashes=set()
    for receipt in (d.RUN/'captures').glob('*.json.gz'):
        source=d.load(receipt);body=receipt.with_name(receipt.name.replace('.json.gz','.body.gz'))
        if body.exists() and d.sha(gzip.decompress(body.read_bytes()))==source['sha256']:valid_hashes.add(source['sha256'])
    for phase,p in plans.items():
        assert d.sha((d.RUN/phase/'input-records.json.gz').read_bytes())==p['input_sha256']
        for r in p['records']:
            if r.get('evidence_file'):
                assert d.sha((d.ROOT/r['evidence_file']).read_bytes())==r['evidence']['sha256']
            else:assert r['evidence']['sha256'] in valid_hashes,r['key']
    ids=[r['artwork_id'] for r in allrows]
    attached_images={}
    image_receipts=[]
    for phase in ['AR-wave1','AR-image-followup']:
        receipt=d.load(d.RUN/phase/'images-applied.json');image_receipts.append(receipt)
        for aid in receipt['artwork_ids']:attached_images[aid]=d.load(d.RUN/phase/'images'/(aid+'.json'))
    assert len(ids)==len(set(ids))
    registry=d.load(d.RUN/'institution-registry.json')
    for p in sorted(d.RUN.glob('institution-registry-wave*.json')):registry.update(d.load(p))
    reviewed_map={}
    prior_ids={r['artwork_id']:r['institution_id'] for path in SWISS.glob('CH-wave*/plan.json.gz') for r in d.load(path)['records']}
    for row in csv.DictReader((SWISS/'CH/directory-delivery-ledger.csv').open()):
        matches={prior_ids[x.strip()] for x in row['production_artwork_ids'].split('|') if x.strip() in prior_ids}
        if len(matches)==1:reviewed_map['CH/'+row['directory_id']]=next(iter(matches))
    extra_geography=d.load(d.RUN/'existing-geography/plan.json.gz')
    assert d.sha((d.RUN/'existing-geography/plan.json.gz').read_bytes())==d.load(d.RUN/'existing-geography/plan-pin.json')['sha256']
    for row in extra_geography['reviewed']:reviewed_map[row['country']+'/'+row['basis']['directory_id']]=row['institution_id']
    for p in plans.values():
        for name,i in p['institutions'].items():
            entry=registry[name]
            if entry.get('directory_id'):reviewed_map[entry['country_code']+'/'+entry['directory_id']]=i['id']
    reviewed_map['AR/10223']=plans['AR-wave1']['institutions']['Museo de Arte Latinoamericano de Buenos Aires (Malba)']['id']
    with d.connect() as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        states=d.snapshot(db,ids)
        assert len(states)==len(ids)
        institutions=list(db.execute("SELECT i.id::text,i.name,i.slug,i.website_url,i.status,i.canonical_institution_id::text,p.name city,p.country_code FROM institutions i LEFT JOIN places p ON p.id=i.place_id"))
        country_ids=[i['id'] for i in institutions if i['country_code'] in ['CH','AR','UY','PY'] and i['status']!='archived']
        counts=list(db.execute("SELECT current_institution_id::text id,count(*) artworks,count(primary_media_id) images FROM artworks WHERE current_institution_id=ANY(%s::uuid[]) AND status<>'archived' GROUP BY current_institution_id",(country_ids,)))
        bycount={x['id']:x for x in counts}
        citations=list(db.execute("SELECT entity_id::text,evidence_note FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND field_name='switzerland_southern_cone_museum_coverage_20261011'",(ids,)))
        assert len(citations)==len(ids)
        media=list(db.execute('SELECT a.id::text artwork_id,m.id::text media_id,m.byte_size,m.checksum_sha256,m.source_page_url,m.rights_status FROM artworks a JOIN media_assets m ON m.id=a.primary_media_id WHERE a.id=ANY(%s::uuid[])',(ids,)))
        verification=[]
        for phase,plan in plans.items():
            receipt=d.load(d.RUN/phase/'applied.json')
            assert receipt['plan_sha256']==d.pinned(phase)[1]
            assert (d.RUN/phase/'geography-applied.json').exists()
            for r in plan['records']:
                state=states[r['artwork_id']];a=state['artwork']
                assert a['current_institution_id']==r['institution_id']
                assert any(x['institution_id']==r['institution_id'] and x['claim_type']=='holding' and x['review_state']=='accepted' and not x['superseded_by'] for x in state['holdings'])
                if r['before']:
                    old=r['before']['artwork']
                    changed={'current_institution_id','current_location_text','current_location_unknown_reason','location_checked_at','revision','updated_by','updated_at'}
                    if a['id'] in attached_images:changed.add('primary_media_id')
                    assert {k:v for k,v in a.items() if k not in changed}=={k:v for k,v in old.items() if k not in changed},r['key']
                    assert state['creators']==r['before']['creators']
                    if a['id'] in attached_images:
                        assert all(x in state['attachments'] for x in r['before']['attachments'])
                        assert len(state['attachments'])==len(r['before']['attachments'])+1
                        assert a['primary_media_id']==attached_images[a['id']]['media_id']
                    else:assert state['attachments']==r['before']['attachments']
                else:
                    assert a['status']=='review' and a['published_at'] is None and a['research_candidate']
                    assert (a['creation_year_start'],a['creation_year_end'],a['date_precision'])==(r['first'],r['last'],r['precision'])
                    assert a['date_display']==r['date_display'] and a['title']==r['title']
                    if not r['artist_id']:assert a['unlinked_creator_label']==r['creator_label']
                assert not any(x['claim_type']=='on_view' for x in state['holdings'] if x['source_id']==d.uid('source/'+r['provider']+'/'+r['museum']))
            for name,i in plan['institutions'].items():
                current=next(x for x in institutions if x['id']==i['id'])
                assert current['country_code']==registry[name]['country_code']
                assert bycount[i['id']]['artworks']>0
            verification.append(dict(phase=phase,new=receipt['new_artworks'],existing=receipt['existing_records_enriched'],museums=receipt['by_museum'],held=receipt['held'],unknown_new_dates=sum(not r['before'] and r['first'] is None for r in plan['records']),plan_sha256=receipt['plan_sha256']))
    # No local database connection is used anywhere in this audit.
    for row in extra_geography['reviewed']:
        institution=next(x for x in institutions if x['id']==row['institution_id'])
        assert institution['country_code']==row['country'] and d.norm(institution['city'])==d.norm(row['city'])
    for aid,prepared in attached_images.items():
        actual=next(x for x in media if x['artwork_id']==aid)
        assert actual['media_id']==prepared['media_id'] and actual['byte_size']==prepared['bytes']<=100000
        assert actual['checksum_sha256']==prepared['sha256']
    d.save(d.RUN/f'institution-reconciliation-final-{REVISION}.json.gz',institutions)
    d.save(d.RUN/f'production-verification-{REVISION}.json',dict(at=d.now(),phases=verification,new_artworks=sum(x['new'] for x in verification),existing_enriched=sum(x['existing'] for x in verification),verified_objects=len(ids),museums=len({r['institution_id'] for r in allrows}),existing_museum_geography_repairs=len(extra_geography['reviewed']),images_attached=sum(x['images_attached'] for x in image_receipts),media=media,source_citations=len(citations),local_database_changes=0,publication_changes=0,current_display_claims=0,checks='Pinned plans, source citations, exact artwork metadata/dates, qualified/unlinked makers, preserved existing states and images, authorized image additions, accepted holdings, nonempty institutions and country/city placement.'))
    names=collections.defaultdict(list);websites=collections.defaultdict(list)
    for i in institutions:
        if i['status']=='archived':continue
        names[d.norm(i['name'])].append(i)
        if i['website_url']:websites[urlkey(i['website_url'])].append(i)
    source_totals={};ledger_stats={}
    for country in ['CH','AR','UY','PY']:
        base=SWISS if country=='CH' else d.RUN
        specs=[('national',base/country/'directory.json.gz','')]
        if country in ['UY','PY']:specs.append(('ibermuseos',d.RUN/country/'ibermuseos-directory.json.gz','rmi-'))
        if country=='PY':specs.append(('icom-2024',d.RUN/country/'icom-directory.json.gz',''))
        rows=[];totals={}
        for label,path,prefix in specs:
            source=d.load(path)['records'];totals[label]=len(source)
            for entry in source:
                key=prefix+entry['directory_id']
                def evidence(folder):
                    p=base/country/folder/(key+'.json.gz')
                    return d.load(p) if p.exists() else {}
                detail=evidence('directory-details');native=evidence('native-reviewed') or evidence('native-sites')
                discovery=evidence('collection-reviewed') or evidence('collection-discovery')
                matches=names[d.norm(entry['name'])][:]
                if country+'/'+key in reviewed_map:matches=[next(i for i in institutions if i['id']==reviewed_map[country+'/'+key])]
                if not matches:
                    for u in entry.get('native_websites',[])+native.get('candidates',[]):matches.extend(websites[urlkey(u)])
                matches=[x for x in matches if x['country_code'] in [None,country]]
                matches=list({x['id']:x for x in matches}.values())
                matched=matches[0] if len(matches)==1 else None
                delivered=sum(r['institution_id']==matched['id'] for r in allrows) if matched else 0
                status=('Partial artwork coverage delivered; further object research remains' if delivered else
                        'Existing catalogue institution; collection completeness unverified' if matched and bycount.get(matched['id'],{}).get('artworks',0) else
                        'Unresolved individual object-source gap; no artwork invented')
                rows.append(dict(source=label,directory_id=key,name=entry['name'],locality=entry.get('locality'),country_scope=country,
                                 directory_url=entry['directory_url'],classification=entry.get('classification') or entry.get('country_status') or entry.get('primary_category'),
                                 directory_review=detail.get('result','Directory profile evidence retained'),native_review=native.get('result','Native source gap'),
                                 collection_review=discovery.get('result','Individual object-source review remains'),
                                 candidate_institution_ids=' | '.join(x['id'] for x in matches),identity_status='reviewed directory/native match' if matched else 'ambiguous' if matches else 'unresolved',
                                 active_catalogue_items=bycount.get(matched['id'],{}).get('artworks',0) if matched else 0,
                                 delivered_objects_this_continuation=delivered,object_coverage=status))
        csvwrite(d.RUN/country/'institution-reconciliation.csv',rows)
        source_totals[country]=totals
        ledger_stats[country]=dict(directory_leads=len(rows),with_existing_identity=sum(r['identity_status']=='reviewed directory/native match' for r in rows),source_gap_rows=sum(r['object_coverage'].startswith('Unresolved') for r in rows))
    gaps=[]
    for phase,p in plans.items():
        for x in p['held']:gaps.append(dict(phase=phase,key=x['record']['key'],title=x['record']['title'],reason=x['reason'],source_url=x['record']['source_url']))
        f=d.RUN/phase/'image-enrichment.json.gz'
        if f.exists() and not (d.RUN/phase/'images-applied.json').exists():
            for key,x in d.load(f).items():gaps.append(dict(phase=phase,key=key,title='',reason='Image source matched and rights evidence captured; Commons media host returned 429. Retrieval held; image not attached.',source_url=x['image_source_page_url']))
    csvwrite(d.RUN/'object-and-image-gaps.csv',gaps)
    d.save(d.RUN/f'directory-reconciliation-summary-{REVISION}.json',dict(at=d.now(),source_totals=source_totals,ledgers=ledger_stats,scope='Source-entry counts overlap and include broader cultural institutions and cross-border Swiss-directory leads. They are not unique-museum totals or complete artwork coverage.',paraguay_sponsor_correction='FONDEC sponsor link excluded. native-reviewed and collection-reviewed supersede the initial supplemental outcomes.',capture_integrity='One unrelated municipal refuse-collection page has mismatched receipt/body hashes from concurrent capture. Preserved, excluded from valid object evidence; per-URL process locking now prevents this race. All delivered object evidence is intact.'))
    print(json.dumps(dict(new_artworks=sum(x['new'] for x in verification),existing_enriched=sum(x['existing'] for x in verification),objects=len(ids),museums=len({r['institution_id'] for r in allrows}),source_totals=source_totals,gaps=len(gaps))))


if __name__=='__main__':run()
