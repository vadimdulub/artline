#!/usr/bin/env python3
"""Attach corroborated primary country/object citations; retain review and dates."""
import argparse,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('m',Path(__file__).with_name('apply-country-round.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

def cite(code,number,target):
    m.configure(code,number);run=m.m.r.RUN;dest=run/('primary-research-citations-'+target+'.json')
    if dest.exists():return
    assert (run/'verification.json').exists()
    gp=m.x.BASE/code/'getty-primary-review.json';getty=json.loads(gp.read_text()) if gp.exists() else {'records':[]};people={}
    for e in getty['records']:
        if e['review']=='explicit_affiliation_corroborated':people.setdefault(e['qid'],[]).append(e)
    artifacts=[];snapshot=[];seen=set()
    for receiptpath in sorted((run/'applied'/target).glob('Q*.json')):
        receipt=json.loads(receiptpath.read_text());record=json.loads((run/'ready'/receiptpath.name).read_text())['record'];q=record['qid'];cq=record['creator_qid']
        if cq not in seen:
            seen.add(cq)
            for e in people.get(cq,[]):artifacts.append({'entity_type':'artist','entity_id':receipt['artist_id'],'qid':cq,'field':'geography_primary_authority','source_slug':m.x.SESSION_NAME+'-getty-ulan','source_name':'Getty ULAN — primary artist cultural affiliations','source_type':'authority_data','root':'https://vocab.getty.edu/ulan/','record_id':e['getty_id'],'url':'https://vocab.getty.edu/ulan/'+e['getty_id'],'retrieved_at':e['source']['retrieved_at'],'evidence':e})
        for folder in ('german-primary','nationalmuseum-primary-v2','polish-primary-v2','norwegian-primary','smk-primary','hungarian-primary','webumenia-primary','swiss-primary','swiss-primary-v2','met-primary','met-primary-v2','british-reviewed'):
            primary=run/folder/receiptpath.name
            if primary.exists():
                e=json.loads(primary.read_text())
                if e['review']=='primary_object_and_creator_corroborated':artifacts.append({'entity_type':'artwork','qid':q,'field':'official_object_identity','source_slug':m.x.SESSION_NAME+'-'+e['museum']+'-objects','source_name':record['collection']['institution']['name']+' — official selected object metadata','source_type':'collection_page','root':record['collection']['institution'].get('website_url') or e['receipt']['url'],'record_id':e['object']['accession'],'url':e['receipt']['url'],'retrieved_at':e['receipt'].get('retrieved_at') or e['receipt'].get('at'),'evidence':e})
    with m.m.r.base.connect(target=='production') as db:
        for item in artifacts:
            with db.transaction():
                db.execute('SELECT pg_advisory_xact_lock(559220260914)')
                row=db.execute("SELECT entity_id::text FROM external_identifiers WHERE entity_type=%s AND scheme='wikidata' AND external_id=%s",(item['entity_type'],item['qid'])).fetchone()
                if item['entity_type']=='artist' and item.get('entity_id'):
                    # Closed person matching can reuse an existing catalogue
                    # profile whose Wikidata identifier has not been attached.
                    # Use the verified import receipt, never a fuzzy lookup.
                    assert not row or row['entity_id']==item['entity_id']
                    eid=item['entity_id']
                else:assert row;eid=row['entity_id']
                table='artists' if item['entity_type']=='artist' else 'artworks'
                entity=db.execute('SELECT status,published_at FROM '+table+' WHERE id=%s',(eid,)).fetchone();assert entity and entity['status']=='review' and entity['published_at'] is None
                sid=m.m.source(db,item['source_slug'],item['source_name'],item['source_type'],item['root'])
                exists=db.execute('SELECT 1 FROM citations WHERE entity_type=%s AND entity_id=%s AND source_id=%s AND field_name=%s AND source_record_id=%s',(item['entity_type'],eid,sid,item['field'],item['record_id'])).fetchone()
                if not exists:m.m.r.base.insert(db,'citations',{'entity_type':item['entity_type'],'entity_id':eid,'field_name':item['field'],'source_id':sid,'source_record_id':item['record_id'],'source_url':item['url'],'retrieved_at':item['retrieved_at'],'created_by':m.m.ACTOR,'evidence_note':json.dumps({'research_evidence':item['evidence'],'interpretation':'Primary cultural affiliation/object evidence only. Existing review status, dates, creator roles and display assertions unchanged.'},ensure_ascii=False)})
                snapshot.append({'entity_type':item['entity_type'],'entity_id':eid,'qid':item['qid'],'source_url':item['url'],'field':item['field'],'already_existed':bool(exists)})
    m.m.core.save_new(dest,{'at':m.m.core.now(),'target':target,'country':code,'round':number,'citations':snapshot});print(code,number,target,'primary citations',len(snapshot),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--country',required=True,choices=m.x.COUNTRIES);p.add_argument('--round',type=int,required=True);p.add_argument('--target',required=True,choices=['local','production']);a=p.parse_args();assert 1<=a.round<=20;cite(a.country,a.round,a.target)
