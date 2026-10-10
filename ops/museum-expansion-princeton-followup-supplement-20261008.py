#!/usr/bin/env python3
"""Two more bounded watercolor pages, preserving the first follow-up queue."""
import argparse, json
from pathlib import Path
from urllib.parse import urlencode
import importlib.util
s=importlib.util.spec_from_file_location('d',Path(__file__).with_name('museum-expansion-princeton-followup-native-20261008.py'));d=importlib.util.module_from_spec(s);s.loader.exec_module(d)
m=d.m;n=d.n;RUN=d.RUN;QUEUE=RUN/'selected-metadata-queue-002.json';ref=d.ref
def indexes():
    assert (RUN/'selected-capture-001.json').exists(), 'Keep source capture serial'
    assert not list((RUN/'errors-001').glob('*.json'))
    for k in [3,4]:
        key='watercolor-%03d'%k;url=n.BASE+'/search?'+urlencode(dict(q='watercolor',type='artobjects',size=24,**{'from':24*(k-1)}))
        try:
            x=n.save_capture(RUN/'indexes-002'/(key+'.json.gz'),url,documentation_reference=ref(d.PRIOR/'api-docs-search-001.json.gz'),selection='Two further24-result pages; bounded metadata selection, no images.');rows=n.search_hits(x);print(json.dumps(dict(index=key,rows=len(rows))),flush=True)
        except Exception as e:m.save(RUN/'errors-001'/(key+'.json'),dict(at=m.now(),url=url,error=repr(e),policy='Stop first failure, no bypass.'));raise
def queue():
    assert not QUEUE.exists();old=set()
    for p in [d.PRIOR/'selected-metadata-queue-001.json',d.QUEUE]:
        q=m.load(p);old.update(r['source_id'] for r in q['selected']+q['held'])
    rows={};overlap=[]
    for path in sorted((RUN/'indexes-002').glob('*.json.gz')):
        for hit in n.search_hits(m.load(path)):
            sid=hit['_id'];lead=dict(kind='search',reference=ref(path),source_record=hit)
            if sid in old:overlap.append(dict(source_id=sid,reference=ref(path)));continue
            if sid not in rows:rows[sid]=dict(source_id=sid,data=hit['_source'],index_references=[lead])
            else:assert rows[sid]['data']==hit['_source'];rows[sid]['index_references'].append(lead)
    chosen=[];held=[];offset=len(m.load(d.QUEUE)['selected'])
    for sid,row in rows.items():
        reasons=d.selected.prefilter(row['data']);date=row['data'].get('displaydate')
        if not date or date.casefold() in ['undated','date unknown','n.d.']:reasons.append('No literal creation date; no life-date inference')
        if len(chosen)>=24:reasons.append('Bounded supplemental24-object limit')
        row.update(url=n.BASE+'/objects/'+sid,existing_pending=None,priority=False,date_screen='Literal source date for full object review')
        if reasons:held.append(dict(row,state='index_hold',reasons=reasons))
        else:chosen.append(dict(row,state='selected_metadata_research_only',number=offset+len(chosen)+1))
    m.save(QUEUE,dict(at=m.now(),parser_reference=ref(Path(__file__).resolve()),selected=chosen,held=held,prior_overlap=overlap,prior_queue_references=[ref(d.QUEUE),ref(d.PRIOR/'selected-metadata-queue-001.json')],policy='Bounded supplemental metadata research only; previous selected and held identities excluded.'))
    print(json.dumps(dict(selected=len(chosen),held=len(held),overlap=len(overlap))),flush=True)
def objects():
    q=m.load(QUEUE);d.checked(q['parser_reference']);assert not list((RUN/'errors-001').glob('*.json'))
    for row in q['selected']:
        try:
            x=n.save_capture(RUN/'objects-002'/('object-%03d.json.gz'%row['number']),row['url'],number=row['number'],index=row,queue_reference=ref(QUEUE));assert str(x['data']['objectid'])==row['source_id'] and x['data']['type']=='artobject';print(json.dumps(dict(number=row['number'],id=row['source_id'],title=x['data']['displaytitle'],date=x['data'].get('displaydate'))),flush=True)
        except Exception as e:m.save(RUN/'errors-001'/('object-%03d.json'%row['number']),dict(at=m.now(),url=row['url'],error=repr(e),policy='Stop first failure, no retry.'));raise
    m.save(RUN/'selected-capture-002.json',dict(at=m.now(),queue_reference=ref(QUEUE),objects=[ref(p) for p in sorted((RUN/'objects-002').glob('*.json.gz'))],images=0))
def parse(path):
    x=m.load(path);d.f.QUEUE=d.checked(x['queue_reference']);return d.f.parse(path)
def facts():
    dest=RUN/'native-candidates-001.json.gz';assert not dest.exists()
    paths=sorted((RUN/'objects-001').glob('*.json.gz'))+sorted((RUN/'objects-002').glob('*.json.gz'));assert len(paths)==sum(len(m.load(p)['selected']) for p in [d.QUEUE,QUEUE]);rows=[parse(p) for p in paths]
    m.save(dest,dict(at=m.now(),rows=rows,parser_reference=ref(Path(__file__).resolve()),dependencies=d.f.dependencies()+[ref(Path(d.__file__).resolve()),ref(Path(d.selected.__file__).resolve())],queue_references=[ref(d.QUEUE),ref(QUEUE)],partial=False));print(json.dumps(dict(rows=len(rows),date_holds=sum(bool(r['facts']['date_issue']) for r in rows))),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['indexes','queue','objects','facts']);globals()[p.parse_args().command]()
