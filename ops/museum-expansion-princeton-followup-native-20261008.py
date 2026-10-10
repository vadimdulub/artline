#!/usr/bin/env python3
"""Bounded Princeton follow-up discovery; reuse literal source parsers unchanged."""
import argparse, importlib.util, json, time
from pathlib import Path
from urllib.parse import urlencode

def module(name, file):
    s=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v

f=module('facts','museum-expansion-princeton-facts-20261007.py')
selected=module('selected','museum-expansion-princeton-selected-20261007.py')
n=f.n;m=f.m;PRIOR=n.RUN;RUN=m.RUN/'native/princeton-followup';IID=n.IID;ref=n.ref;checked=n.checked
QUEUE=RUN/'selected-metadata-queue-001.json'
n.n.SITES['princeton-followup']=n.BASE
last_request=0
def capture(url):
    global last_request
    delay=3-(time.monotonic()-last_request)
    if delay>0:time.sleep(delay)
    try:return n.n.capture('princeton-followup',url)
    finally:last_request=time.monotonic()
n.capture=capture
f.RUN=RUN;f.QUEUE=QUEUE

def indexes():
    assert not list((RUN/'errors-001').glob('*.json'))
    queries=[('oil-canvas-%03d'%k,'"Oil on canvas"',24*(k-1)) for k in range(9,13)]+[('watercolor-%03d'%k,'watercolor',24*(k-1)) for k in range(1,3)]
    for key,q,offset in queries:
        url=n.BASE+'/search?'+urlencode(dict(q=q,type='artobjects',size=24,**{'from':offset}))
        try:
            x=n.save_capture(RUN/'indexes-001'/(key+'.json.gz'),url,documentation_reference=ref(PRIOR/'api-docs-search-001.json.gz'),selection='Bounded six-page follow-up: oil on canvas pages9–12 and watercolor pages1–2. No exhaustive capture or images; no keyword/date/holding assumption.')
            rows=n.search_hits(x);print(json.dumps(dict(index=key,total=x['data']['hits']['total'],rows=len(rows))),flush=True)
        except Exception as e:
            m.save(RUN/'errors-001'/(key+'.json'),dict(at=m.now(),url=url,error=repr(e),policy='Stop first failure; no automatic retry or bypass.'));raise

def queue():
    assert not QUEUE.exists()
    prior=m.load(PRIOR/'selected-metadata-queue-001.json');old={r['source_id'] for r in prior['selected']+prior['held']};rows={};overlap=[]
    for path in sorted((RUN/'indexes-001').glob('*.json.gz')):
        for hit in n.search_hits(m.load(path)):
            sid=hit['_id'];lead=dict(kind='search',reference=ref(path),source_record=hit)
            if sid in old:overlap.append(dict(source_id=sid,reference=ref(path)));continue
            if sid not in rows:rows[sid]=dict(source_id=sid,data=hit['_source'],index_references=[lead])
            else:assert rows[sid]['data']==hit['_source'];rows[sid]['index_references'].append(lead)
    chosen=[];held=[]
    for sid,row in rows.items():
        reasons=selected.prefilter(row['data']);date=row['data'].get('displaydate')
        if not date or date.casefold() in ['undated','date unknown']:reasons.append('No literal creation date; bounded follow-up selects known-date objects only, without inferring from maker life')
        if len(chosen)>=80:reasons.append('Bounded80-object metadata research limit reached')
        row.update(url=n.BASE+'/objects/'+sid,existing_pending=None,priority=False,date_screen='Literal date selected for full object, version and holding review')
        if reasons:held.append(dict(row,state='index_hold',reasons=reasons))
        else:chosen.append(dict(row,state='selected_metadata_research_only',number=len(chosen)+1))
    m.save(QUEUE,dict(at=m.now(),parser_reference=ref(Path(__file__).resolve()),selected=chosen,held=held,prior_overlap=overlap,prior_queue_reference=ref(PRIOR/'selected-metadata-queue-001.json'),policy='Metadata research only. All388 previous source IDs excluded, including unresolved holds. No images, database mutations or inferred creation dates.'))
    print(json.dumps(dict(selected=len(chosen),held=len(held),prior_overlap=len(overlap))),flush=True)

def objects():
    q=m.load(QUEUE);checked(q['parser_reference']);assert not list((RUN/'errors-001').glob('*.json'))
    for row in q['selected']:
        try:
            x=n.save_capture(RUN/'objects-001'/('object-%03d.json.gz'%row['number']),row['url'],number=row['number'],index=row,queue_reference=ref(QUEUE));assert str(x['data']['objectid'])==row['source_id'] and x['data']['type']=='artobject'
            print(json.dumps(dict(number=row['number'],id=row['source_id'],title=x['data']['displaytitle'],date=x['data'].get('displaydate'))),flush=True)
        except Exception as e:
            m.save(RUN/'errors-001'/('object-%03d.json'%row['number']),dict(at=m.now(),url=row['url'],error=repr(e),policy='Stopped first failure; no retry or bypass.'));raise
    m.save(RUN/'selected-capture-001.json',dict(at=m.now(),queue_reference=ref(QUEUE),objects=[ref(p) for p in sorted((RUN/'objects-001').glob('*.json.gz'))],images=0))

def facts():
    dest=RUN/'native-candidates-001.json.gz';assert not dest.exists()
    paths=sorted((RUN/'objects-001').glob('*.json.gz'));assert len(paths)==len(m.load(QUEUE)['selected'])
    rows=[f.parse(p) for p in paths]
    m.save(dest,dict(at=m.now(),rows=rows,parser_reference=ref(Path(__file__).resolve()),dependencies=f.dependencies()+[ref(Path(selected.__file__).resolve())],queue_reference=ref(QUEUE),partial=False))
    print(json.dumps(dict(rows=len(rows),date_holds=sum(bool(r['facts']['date_issue']) for r in rows))),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['indexes','queue','objects','facts']);globals()[p.parse_args().command]()
