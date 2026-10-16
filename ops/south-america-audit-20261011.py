#!/usr/bin/env python3
"""Scoped read-only verification, exact object manifest, and museum research ledger."""
import argparse,collections,csv,gzip,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('campaign',Path(__file__).with_name('south-america-1000-20261011.py'));c=importlib.util.module_from_spec(s);s.loader.exec_module(c);d=c.d
PHASES=['BR-final','CL-final','CO-wave1','PE-wave1','EC-wave1','AR-wave1','UY-wave1','breadth-wave1','VE-wave1','VE-link']

def csvsave(path,rows):
    if not rows:return
    import io
    out=io.StringIO();w=csv.DictWriter(out,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows);raw=out.getvalue().encode();path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():assert path.read_bytes()==raw
    else:path.write_bytes(raw)

def audit(version):
    records=[];receipts={};pins={};hashes={}
    for phase in PHASES:
        p,pin=d.pinned(phase);receipt=d.load(c.RUN/phase/'applied.json');assert receipt['plan_sha256']==pin
        assert receipt['new_artworks']==sum(not r['before'] for r in p['records'])
        assert p['input_sha256']==d.sha((c.RUN/phase/'input-records.json.gz').read_bytes())
        assert (c.RUN/phase/'geography-applied.json').exists()
        records.extend(dict(r,phase=phase) for r in p['records']);receipts[phase]=receipt;pins[phase]=pin
    ids=[r['artwork_id'] for r in records];new=[r for r in records if not r['before']]
    assert len(ids)==len(set(ids)) and len(new)>=1000
    assert len({r['key'] for r in records})==len(records)
    assert set(c.COUNTRIES).issubset({r['country_code'] for r in new})
    for r in records:
        digest=r['evidence']['sha256']
        if digest in hashes:continue
        key=d.sha(r['evidence']['url'].encode());p=c.RUN/'captures'/(key+'.json.gz');rc=d.load(p)
        raw=gzip.decompress(p.with_name(key+'.body.gz').read_bytes());assert rc['status']==200 and d.sha(raw)==digest==rc['sha256']
        hashes[digest]=dict(url=rc['url'],retrieved_at=rc['retrieved_at'],bytes=len(raw))
    with d.connect() as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        states=d.snapshot(db,ids);assert len(states)==len(records)
        cites=list(db.execute("SELECT entity_id::text,source_record_id,source_url,evidence_note FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND field_name=%s",(ids,d.CITATION_FIELD)))
        keys={(v['entity_id'],v['scheme'],v['external_id']) for v in db.execute("SELECT entity_id::text,scheme,external_id FROM external_identifiers WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(ids,))}
        allinst=list(db.execute('SELECT i.id::text,i.name,i.slug,i.status,i.website_url,p.name city,p.country_code FROM institutions i LEFT JOIN places p ON p.id=i.place_id'))
        inst={r['id']:r for r in allinst};scopes=sorted({r['institution_id'] for r in records})
        query="SELECT current_institution_id::text id,count(*) n FROM artworks WHERE current_institution_id=ANY(%s::uuid[]) AND status<>'archived' GROUP BY current_institution_id"
        counts={r['id']:r['n'] for r in db.execute(query,(scopes,))};queryplan=db.execute('EXPLAIN (FORMAT JSON) '+query,(scopes,)).fetchone()
        mids=[x['artwork']['primary_media_id'] for x in states.values() if x['artwork']['primary_media_id']]
        media={r['v']['id']:r['v'] for r in db.execute('SELECT to_jsonb(m) v FROM media_assets m WHERE id=ANY(%s::uuid[])',(mids,))}
        rights=list(db.execute('SELECT media_id::text,source_checksum,rights_basis FROM media_rights_evidence WHERE media_id=ANY(%s::uuid[])',(mids,)))
    bycite=collections.defaultdict(list)
    for x in cites:bycite[x['entity_id']].append(x)
    manifest=[];gaps=[];images=[];countries=collections.Counter();territories=collections.Counter()
    for r in records:
        x=states[r['artwork_id']];a=x['artwork'];i=inst[r['institution_id']];isnew=not r['before']
        assert a['current_institution_id']==r['institution_id'] and i['country_code']==r['country_code'] and i['city']
        assert (a['id'],r['scheme'],r['source_id']) in keys
        assert any(v['source_record_id']==r['source_id'] and v['source_url']==r['source_url'] and json.loads(v['evidence_note'])['plan_sha256']==pins[r['phase']] for v in bycite[a['id']])
        assert any(v['claim_type']=='holding' and v['institution_id']==r['institution_id'] and v['review_state']=='accepted' and not v['superseded_by'] for v in x['holdings'])
        assert not any(v['claim_type']=='on_view' for v in x['holdings'])
        if isnew:
            assert a['status']=='review' and a['research_candidate'] and a['published_at'] is None
            assert a['title']==r['title'] and a['date_display']==r['date_display']
            assert a['creation_year_start']==r['first'] and a['creation_year_end']==r['last']<=1970 and a['date_precision']==r['precision']
            assert a['accession_number']==r.get('accession_number')
            if r['artist_id']:assert any(v['artist_id']==r['artist_id'] for v in x['creators'])
            else:assert (a['unlinked_creator_label'] or '')==(r.get('creator_label') or '').strip()
            if r.get('territory_code'):territories[r['territory_code']]+=1
            else:countries[r['country_code']]+=1
        else:
            before=r['before']['artwork'];allowed={'current_institution_id','primary_media_id','revision','updated_at','updated_by'}
            assert {k:v for k,v in a.items() if k not in allowed}=={k:v for k,v in before.items() if k not in allowed}
            assert x['creators']==r['before']['creators']
        out=dict(action='new' if isnew else 'existing holding/image enrichment',country=r['country_code'],territory=r.get('territory_code',''),museum=r['museum'],artwork_id=a['id'],title=a['title'],creator_label=r.get('creator_label'),date_display=a['date_display'],source_record_id=r['source_id'],inventory=a['accession_number'],source_url=r['source_url'],source_sha256=r['evidence']['sha256'],image_attached=bool(a['primary_media_id']),phase=r['phase'])
        manifest.append(out)
        if a['primary_media_id']:
            m=media[a['primary_media_id']];raw=(d.ROOT/'apps/web/public'/m['storage_path'].lstrip('/')).read_bytes();assert 0<len(raw)==m['byte_size']<=100000 and d.sha(raw)==m['checksum_sha256']
            assert any(v['media_id']==m['id'] and v['source_checksum'] for v in rights)
            up=d.load(c.RUN/r['phase']/'uploads'/(a['id']+'.json'));assert up['public_bytes_verified'] and up['sha256']==m['checksum_sha256'];images.append(a['id'])
        else:gaps.append(dict(**out,gap=r.get('image_gap') or ('Source creation is after the existing 1955 image cutoff.' if r['last']>1955 else 'Native reproduction has no verified permitted reuse; an approved exact object/version image match remains unresolved.')))
    report=dict(at=d.now(),target='production',new_artworks=len(new),new_artworks_by_country=countries,additional_territories=territories,existing_artworks_enriched=len(records)-len(new),new_primary_images=len(images),image_artwork_ids=images,new_artworks_without_images=sum(x['action']=='new' for x in gaps),new_review_records=len(new),publication_changes=0,current_display_claims=0,local_database_connections=0,local_database_changes=0,verified_source_hashes=len(hashes),source_evidence=hashes,phase_receipts=receipts,institutions={iid:dict(inst[iid],active_catalogue_items=counts[iid],new_artworks=sum(r['institution_id']==iid and not r['before'] for r in records)) for iid in scopes},scoped_query_plan=queryplan,limits=['Country breadth does not mean complete museum holdings.','Directory entries may overlap; no unique nationwide museum total is claimed.','Source rights, casting/loan/date and translation/version holds remain explicit.','Production query plan is not a ten-million-row load test.'])
    d.save(c.RUN/('production-verification-'+version+'.json'),report);d.save(c.RUN/('institution-audit-'+version+'.json.gz'),allinst)
    csvsave(c.RUN/('catalogue-manifest-'+version+'.csv'),manifest);csvsave(c.RUN/('image-gaps-'+version+'.csv'),gaps)
    print(json.dumps({k:report[k] for k in ['new_artworks','new_artworks_by_country','additional_territories','existing_artworks_enriched','new_primary_images','verified_source_hashes']}),flush=True)

def ledgers(version):
    report=d.load(c.RUN/('production-verification-'+version+'.json'));inst=d.load(c.RUN/('institution-audit-'+version+'.json.gz'));newby=report['institutions'];allrows=[];counts={}
    enriched=collections.Counter(r['institution_id'] for phase in PHASES for r in d.pinned(phase)[0]['records'] if r['before'])
    for co in c.COUNTRIES:
        rows=[]
        if co in ['AR','UY','PY']:
            old=c.PREVIOUS/co/'institution-reconciliation-final.csv'
            for x in csv.DictReader(old.open()):
                rows.append(dict(country=co,directory_id=x['directory_id'],name=x['name'],locality=x.get('locality',''),source_url=x.get('directory_url',''),evidence_sha256=x.get('source_sha256',''),source_family='Earlier reconciled research: '+x.get('source',''),prior_evidence_file=str(old.relative_to(d.ROOT)),prior_candidate_ids=x.get('candidate_institution_ids',''),prior_identity_status=x.get('identity_status',''),prior_object_coverage=x.get('object_coverage',''),prior_collection_review=x.get('collection_review','')))
        else:
            path=c.RUN/co/'directory.json.gz'
            if path.exists():
                for x in d.load(path)['records']:rows.append(dict(country=co,directory_id=x['directory_id'],name=x['name'],locality=x.get('locality',''),source_url=x['directory_url'],evidence_sha256=x['evidence']['sha256'],source_family='Ibermuseos public registry',prior_evidence_file=str(path.relative_to(d.ROOT))))
        supplemental=c.RUN/co/'native-directory.json.gz'
        reviewed=c.RUN/co/'native-directory-reviewed.json.gz'
        if reviewed.exists():supplemental=reviewed
        if supplemental.exists():
            for x in d.load(supplemental)['records']:rows.append(dict(country=co,directory_id=x['directory_id'],name=x['name'],locality=x.get('locality',''),source_url=x['source_url'],evidence_sha256=x['evidence']['sha256'],source_family=x['source_family'],prior_evidence_file=str(supplemental.relative_to(d.ROOT))))
        # Delivered collection authorities are retained even when missing from a directory.
        for iid,i in newby.items():
            if i['country_code']==co:rows.append(dict(country=co,directory_id='delivered-'+iid,name=i['name'],locality=i['city'],source_url='',evidence_sha256='',source_family='Verified delivered institution; object-level citations in manifest',prior_evidence_file='catalogue-manifest-'+version+'.csv'))
        for r in rows:
            for key in ['prior_candidate_ids','prior_identity_status','prior_object_coverage','prior_collection_review']:r.setdefault(key,'')
            prior_ids=set(r['prior_candidate_ids'].split(';'))-{''}
            candidates=[i for i in inst if (i['id'] in prior_ids and i['country_code'] in [None,co]) or (i['country_code']==co and d.norm(i['name'])==d.norm(r['name']))]
            if r['directory_id'].startswith('delivered-'):candidates=[i for i in inst if i['id']==r['directory_id'].removeprefix('delivered-')]
            r['candidate_institution_ids']=';'.join(i['id'] for i in candidates);r['identity_status']=(r['prior_identity_status'] or 'Exact delivered/placed name or explicit ID') if len(candidates)==1 else 'Institution identity requires reconciliation'
            r['new_artworks_this_batch']=sum(newby.get(i['id'],{}).get('new_artworks',0) for i in candidates)
            r['existing_artworks_enriched_this_batch']=sum(enriched[i['id']] for i in candidates)
            r['object_coverage']='Selected source-backed objects delivered or enriched; complete holdings still incomplete' if r['new_artworks_this_batch'] or r['existing_artworks_enriched_this_batch'] else 'Individual eligible object sources unresolved or not selected in this bounded pass'
            r['directory_completeness']='Source entries may overlap; these are research rows, not unique museums or complete collection coverage'
        assert rows,co
        csvsave(c.RUN/co/('institution-reconciliation-'+version+'.csv'),rows);counts[co]=len(rows);allrows.extend(rows)
    csvsave(c.RUN/('institution-reconciliation-'+version+'.csv'),allrows)
    territory_rows=[]
    for r in d.load(c.RUN/'GF/native-directory-reviewed.json.gz')['records']:
        candidates=[i for i in newby.values() if i['country_code']=='FR' and i['city']=='Cayenne' and i['name']==r['name']+' (Cayenne)']
        assert len(candidates)<=1
        territory_rows.append(dict(country='FR',territory='GF',directory_id=r['directory_id'],name=r['name'],source_url=r['source_url'],source_sha256=r['evidence']['sha256'],candidate_institution_ids=';'.join(i['id'] for i in candidates),new_artworks_this_batch=sum(i['new_artworks'] for i in candidates),object_coverage='One selected Joconde object delivered; complete holdings still incomplete' if candidates else 'Individual eligible object sources unresolved',directory_completeness='Two researched leads; not a complete territorial register'))
    csvsave(c.RUN/'GF'/('institution-reconciliation-'+version+'.csv'),territory_rows)
    d.save(c.RUN/('directory-summary-'+version+'.json'),dict(rows_by_country=counts,total_rows=len(allrows),additional_territory_rows={'GF':len(territory_rows)},unique_museums=None,nationwide_artwork_coverage_complete=False))
    print('Museum research ledger',counts,flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['audit','ledgers']);p.add_argument('version');a=p.parse_args();globals()[a.action](a.version)
