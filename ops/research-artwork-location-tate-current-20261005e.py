#!/usr/bin/env python3
"""Selected Tate accession lookups in the public API used by its artwork pages."""
import argparse
import collections
import concurrent.futures
import copy
import importlib.util
import json
import re
import time
from pathlib import Path

spec=importlib.util.spec_from_file_location('p',Path(__file__).with_name('research-artwork-location-primary-20261004.py'))
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p);r=p.r
FIELDS='title,acno,url,allArtists,contributors,dateText,foreignTitle,acquisitionYear,acquisition_text,collection,collection_line,cisStatus,tate_status,creditLine,custodialHistory,dimensions,start_year,end_year,isLoanedOut,onDisplayAtTate,location,location_card,master_images,masterImageStatus,masterImageCC,iiif_id'


def selected():
    ids={v['id'] for v in r.load(r.RUN/'museum-guides-baseline-20261005e.json.gz')['missing']}
    return [v for v in r.load(r.RUN/'primary-plans/tate-review-20261005.json.gz')['claims'] if v['artwork_id'] in ids]


def capture_one(acno):
    assert re.fullmatch(r'[A-Z]+\d+[A-Z]?',acno),acno
    dest=r.RUN/'tate-current-objects-20261005e'/(acno+'.json.gz')
    if dest.exists():return r.load(dest)
    raw,rc=r.capture('https://www.tate.org.uk/api/v2/artworks/',{'acno':acno,'fields':FIELDS},tag='tate-current-api-20261005e',timeout=45)
    data=json.loads(raw) if rc['status']==200 and 'json' in (rc.get('content_type') or '') else None
    obj={'accession':acno,'receipt':rc,'data':data}
    r.save_gz(dest,obj)
    # Two modest, spaced workers, scoped to the existing selected objects.
    time.sleep(1)
    return obj


def capture():
    jobs=sorted({v['object_evidence']['accession_number'] for v in selected()})
    errors=[]
    def run(acno):
        try:return capture_one(acno)
        except Exception as exc:return {'error':str(exc)[:300],'accession':acno}
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for n,result in enumerate(pool.map(run,jobs),1):
            if result.get('error'):errors.append(result)
            elif result['receipt']['status'] in [403,429]:
                raise RuntimeError('Tate access challenge/rate limit; stop and respect source response')
            if n%50==0:print('Current Tate accession metadata',n,'/',len(jobs),'errors',len(errors),flush=True)
    r.save(r.RUN/'tate-current-complete-20261005e.json',{'at':r.now(),'selected':len(jobs),'errors':errors})
    print('Tate complete',len(jobs),'errors',len(errors),flush=True)


def decide(old,obj):
    prior=old['object_evidence'];flags=[]
    if obj.get('acno')!=prior['accession_number']:return ['accession_identity_conflict']
    if p.titlekey(obj.get('title'))!=p.titlekey(prior['title']):flags.append('title_requires_reconciliation')
    if r.namekey(obj.get('allArtists'))!=r.namekey(prior['artist']):flags.append('creator_requires_reconciliation')
    makers=obj.get('contributors') or []
    if len(makers)!=1 or makers[0].get('role_display')!='artist' or makers[0].get('prepend_role_to_name') or makers[0].get('append_role_to_name'):
        flags.append('qualified_or_multiple_creator_relationships')
    if obj.get('collection')!='Tate' or obj.get('collection_line')!='Tate':flags.append('joint_or_other_collection_requires_review')
    if obj.get('cisStatus')!='accessioned work' or obj.get('tate_status')!='live':flags.append('accession_status_requires_review')
    if obj.get('isLoanedOut'):flags.append('currently_marked_loaned_out')
    if re.search(r'\b(?:returned|deaccession\w*|restitu\w*|stolen|missing|destroyed|on loan|lent by)\b',r.norm(obj.get('creditLine'))):flags.append('credit_qualification_requires_review')
    if p.datekey(obj.get('dateText'))!=p.datekey(prior.get('dateText')):flags.append('source_date_wording_changed')
    return flags


def plan():
    assert (r.RUN/'tate-current-complete-20261005e.json').exists()
    claims,holds=[],[]
    for old in selected():
        acno=old['object_evidence']['accession_number']
        path=r.RUN/'tate-current-objects-20261005e'/(acno+'.json.gz')
        if not path.exists():
            holds.append({'artwork_id':old['artwork_id'],'reason':'current_source_unavailable','accession':acno});continue
        data=r.load(path);rc=data['receipt'];items=(data.get('data') or {}).get('items',[])
        if rc['status']!=200 or (data.get('data') or {}).get('meta',{}).get('total_count')!=1 or len(items)!=1:
            holds.append({'artwork_id':old['artwork_id'],'reason':'no_unique_current_accession','accession':acno,'source_receipt':rc});continue
        obj=items[0];flags=decide(old,obj)
        if 'accession_identity_conflict' in flags:
            holds.append({'artwork_id':old['artwork_id'],'reason':flags[0],'source_receipt':rc});continue
        c=copy.deepcopy(old)
        c.update(scheme='tate-accession',external_id=acno,duplicate_native_ids=[old['external_id']],
            source_url=obj['url'],source_receipt=rc,checked_at=rc['retrieved_at'],source_class='primary_current_museum_catalogue',
            object_evidence={'current_object':obj,'historical_identity':old,'qualifications':flags},
            identity_basis=old['identity_basis']+'; exact historical accession crosswalk to current public Tate catalogue, with title, named creator, acquisition and collection status checked',
            review_state='review' if flags else 'accepted',
            limitation='Documented Tate collection association only. No physical branch, current presence, legal ownership transfer or on-view claim. Existing artwork metadata and editorial status are preserved. Image URLs are research links; Tate website clearance is not a reuse licence.')
        if flags:c['limitation']+=' Requires review: '+', '.join(flags)+'.'
        claims.append(c)
    p.output('tate-current-20261005e',claims,holds)
    print('States',collections.Counter(v['review_state']for v in claims),'Flags',collections.Counter(f for v in claims for f in v['object_evidence']['qualifications']),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=['capture','plan']);globals()[parser.parse_args().command]()
