#!/usr/bin/env python3
"""Read-only production audit and complete directory/gap ledger for this batch."""
import collections,csv,gzip,importlib.util,json,sys
from pathlib import Path
s=importlib.util.spec_from_file_location('campaign',Path(__file__).with_name('switzerland-southern-cone-1000-20261011.py'))
c=importlib.util.module_from_spec(s);s.loader.exec_module(c);d=c.d
PHASES=['CH-wave1','CH-wave2','CH-rietberg','AR-wave1','UY-wave1','PY-wave1']

def audit(version):
    rows=[];receipts={};pins={};evidence={};image_rejections={}
    for path in c.RUN.glob('*/visual-review.json'):
        image_rejections.update(d.load(path).get('rejection_reasons',{}))
    for phase in PHASES:
        p,pin=d.pinned(phase);receipt=d.load(c.RUN/phase/'applied.json')
        assert receipt['plan_sha256']==pin and len(p['records'])==receipt['new_artworks']
        assert all(r['before'] is None for r in p['records'])
        assert p['input_sha256']==d.sha((c.RUN/phase/'input-records.json.gz').read_bytes())
        rows.extend(dict(r,phase=phase) for r in p['records']);receipts[phase]=receipt;pins[phase]=pin
    ids=[r['artwork_id'] for r in rows];assert len(ids)==len(set(ids))==1000
    assert len({r['key'] for r in rows})==1000
    for r in rows:
        digest=r['evidence']['sha256']
        if digest in evidence:continue
        key=d.sha(r['evidence']['url'].encode());path=c.RUN/'captures'/(key+'.json.gz')
        rc=d.load(path);raw=gzip.decompress(path.with_name(key+'.body.gz').read_bytes())
        assert rc['status']==200 and d.sha(raw)==rc['sha256']==digest
        evidence[digest]=dict(url=rc['url'],bytes=len(raw),retrieved_at=rc['retrieved_at'])
    ledgers={country:list(csv.DictReader((c.OLD/country/'institution-reconciliation.csv').open())) for country in ['CH','AR','UY','PY']}
    scopes=set(r['institution_id'] for r in rows)
    for values in ledgers.values():
        for row in values:scopes.update(x for x in row['candidate_institution_ids'].split(';') if x)
    with d.connect() as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        states=d.snapshot(db,ids)
        citations=list(db.execute("SELECT entity_id::text,source_record_id,source_url,source_id::text,evidence_note FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND field_name='switzerland_southern_cone_museum_coverage_20261011'",(ids,)))
        external=list(db.execute("SELECT entity_id::text,scheme,external_id FROM external_identifiers WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(ids,)))
        inst={x['id']:x for x in db.execute('SELECT i.id::text,i.name,i.status,p.name city,p.country_code FROM institutions i LEFT JOIN places p ON p.id=i.place_id WHERE i.id=ANY(%s::uuid[])',(list(scopes),))}
        count_query="SELECT current_institution_id::text id,count(*) count FROM artworks WHERE current_institution_id=ANY(%s::uuid[]) AND status<>'archived' GROUP BY current_institution_id"
        counts={x['id']:x['count'] for x in db.execute(count_query,(list(scopes),))}
        query_plan=db.execute('EXPLAIN (FORMAT JSON) '+count_query,(list(scopes),)).fetchone()
        media_ids=[x['artwork']['primary_media_id'] for x in states.values() if x['artwork']['primary_media_id']]
        media={x['v']['id']:x['v'] for x in db.execute('SELECT to_jsonb(m) v FROM media_assets m WHERE id=ANY(%s::uuid[])',(media_ids,))}
        rights=list(db.execute('SELECT media_id::text,source_checksum,source_image_url,rights_basis FROM media_rights_evidence WHERE media_id=ANY(%s::uuid[])',(media_ids,)))
    assert len(states)==1000
    bycite=collections.defaultdict(list)
    for x in citations:bycite[x['entity_id']].append(x)
    nativekeys={(x['entity_id'],x['scheme'],x['external_id']) for x in external}
    bycountry=collections.Counter();bytype=collections.Counter();byphase=collections.Counter();image_ids=[]
    gaps=[];catalogue=[]
    for r in rows:
        state=states[r['artwork_id']];a=state['artwork'];institution=inst[r['institution_id']]
        assert a['status']=='review' and a['research_candidate'] and a['published_at'] is None
        assert a['title']==r['title'] and a['creation_year_start']==r['first'] and a['creation_year_end']==r['last']
        assert a['date_precision']==r['precision'] and a['date_display']==(r.get('date_display') or 'Date unknown')
        assert a['accession_number']==r.get('accession_number') and a['current_institution_id']==r['institution_id']
        assert (a['id'],r['scheme'],r['source_id']) in nativekeys
        assert any(x['source_record_id']==r['source_id'] and x['source_url']==r['source_url'] and json.loads(x['evidence_note'])['plan_sha256']==pins[r['phase']] for x in bycite[a['id']])
        assert any(x['claim_type']=='holding' and x['institution_id']==r['institution_id'] and x['review_state']=='accepted' and not x['superseded_by'] for x in state['holdings'])
        assert not any(x['claim_type']=='on_view' for x in state['holdings'])
        if r['artist_id']:assert any(x['artist_id']==r['artist_id'] for x in state['creators'])
        else:assert a['unlinked_creator_label']==(r.get('creator_label') or '').strip() or (not r.get('creator_label') and a['unlinked_creator_label'] is None)
        expected_country='CH' if r['provider'].startswith('swiss-') else 'AR' if r['provider'].startswith('argentina-') else 'UY' if r['provider'].startswith('uruguay-') else 'PY'
        assert institution['country_code']==expected_country and institution['city']
        bycountry[expected_country]+=1;bytype[a['work_type']]+=1;byphase[r['phase']]+=1
        record=dict(country=expected_country,museum=r['museum'],artwork_id=a['id'],title=a['title'],creator_label=r.get('creator_label'),date_display=a['date_display'],native_id=r['source_id'],inventory=a['accession_number'],source_url=r['source_url'],source_sha256=r['evidence']['sha256'],image_attached=bool(a['primary_media_id']))
        catalogue.append(record)
        if a['primary_media_id']:
            m=media[a['primary_media_id']];assert 0<m['byte_size']<=100000
            content=(d.ROOT/'apps/web/public'/m['storage_path'].lstrip('/')).read_bytes()
            assert len(content)==m['byte_size'] and d.sha(content)==m['checksum_sha256']
            assert any(x['media_id']==m['id'] and x['source_checksum'] for x in rights)
            uploads=list(c.RUN.glob('*/uploads/'+a['id']+'.json'))
            assert uploads and any(d.load(p)['public_bytes_verified'] and d.load(p)['sha256']==m['checksum_sha256'] for p in uploads)
            image_ids.append(a['id'])
        else:
            gap=image_rejections.get(a['id']) or ('Native public-domain image endpoint returned HTTP 403; provider stopped. Independent approved WikiArt matching found no secure image.' if r['provider']=='swiss-basel' else r.get('image_gap') or 'Image preparation or visual-review outcome recorded under the source phase; unaccepted images not attached.')
            gaps.append(dict(**record,gap=gap))
    assert dict(bycountry)==dict(CH=900,AR=35,UY=50,PY=15)
    for country,values in ledgers.items():
        for row in values:
            if country=='PY' and row['directory_id'] in ['museo-nacional-de-bellas-artes','rmi-4294','icom-d2a2b0f57f2e3601']:
                row['candidate_institution_ids']=next(r['institution_id'] for r in rows if r['provider']=='paraguay-mnba-portal');row['identity_status']='Official SNC address/city and MNBA collection catalogue identity reconciled'
            candidates=[v for v in row['candidate_institution_ids'].split(';') if v];delivered=[r for r in rows if r['institution_id'] in candidates]
            row['active_catalogue_items']=sum(counts.get(v,0) for v in candidates)
            row['new_artworks_this_1000_batch']=len(delivered)
            row['images_this_1000_batch']=sum(r['artwork_id'] in image_ids for r in delivered)
            if delivered:row['object_coverage']='Additional object records delivered; full museum holdings remain incomplete';row['collection_review']='Source object records verified in additional 1000-artwork pass'
        out=c.RUN/country/('institution-reconciliation-'+version+'.csv');out.parent.mkdir(parents=True,exist_ok=True)
        with out.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(values[0]));w.writeheader();w.writerows(values)
    for name,items in [('catalogue-manifest',catalogue),('image-gaps',gaps)]:
        if items:
            with (c.RUN/(name+'-'+version+'.csv')).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(items[0]));w.writeheader();w.writerows(items)
    report=dict(at=d.now(),target='production',new_artworks=1000,new_artworks_by_country=bycountry,new_artworks_by_phase=byphase,new_artworks_by_type=bytype,
        verified_primary_images=len(image_ids),image_gaps=len(gaps),image_artwork_ids=image_ids,
        museums={iid:dict(inst[iid],new_artworks=sum(r['institution_id']==iid for r in rows),active_catalogue_items=counts[iid]) for iid in {r['institution_id'] for r in rows}},
        new_review_records=1000,published_records=0,current_display_claims=0,local_database_connections=0,local_database_changes=0,
        selected_source_hashes_verified=len(evidence),source_evidence=evidence,phase_receipts=receipts,scoped_query_plan=query_plan,
        validation='Exact planned object identities, source citations and checksums, native IDs, status/date/attribution preservation, accepted holdings, country placement, primary image bytes and rights evidence checked in a repeatable-read production transaction.',
        remaining_limitations=['Image access and source-policy gaps are explicit; metadata count does not imply complete image coverage.','Directory source entries overlap and are not unique museum totals. Nationwide collection coverage remains incomplete.','Scoped query plan on current production is not a ten-million-row load test.'])
    d.save(c.RUN/('production-verification-'+version+'.json'),report)
    print(json.dumps({k:report[k] for k in ['new_artworks','new_artworks_by_country','verified_primary_images','image_gaps','selected_source_hashes_verified']}),flush=True)

if __name__=='__main__':audit(sys.argv[1])
