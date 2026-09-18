#!/usr/bin/env python3
"""Capture exact selected SMK inventories, preserving roles and date bounds."""
import argparse, collections, importlib.util, json
from pathlib import Path
from urllib.parse import urlencode
s=importlib.util.spec_from_file_location('p',Path(__file__).with_name('research-german-primary-objects.py'));p=importlib.util.module_from_spec(s);s.loader.exec_module(p)
x=p.x

def capture(code,number):
    run=x.BASE/code/f'round-{number:02d}'/'delivery';dest=run/'smk-primary-review.json'
    if dest.exists():return
    out=[]
    for path in sorted((run/'ready').glob('*.json')):
        r=json.loads(path.read_text())['record'];acc=r.get('accession')
        if r['collection']['qid']!='Q671384' or not acc:continue
        q=r['qid'];target=run/'smk-primary'/(q+'.json')
        if target.exists():out.append(json.loads(target.read_text()));continue
        e=dict(qid=q,at=x.r.core.now(),museum='smk',review='primary_review_required',ready_sha256=x.r.core.sha(path.read_bytes()))
        try:
            data,receipt=x.r.fetch('https://api.smk.dk/api/v1/art?'+urlencode({'object_number':acc}))
            objects=data.get('items',[]);assert len(objects)==1 and objects[0]['object_number']==acc,'Exact unique inventory required'
            o=objects[0];names={x.r.norm(n) for n in x.r.labels(r['creator_entity'])};active=[];former=[]
            for maker in o.get('production',[]):
                if maker.get('creator_role')=='Tidligere tilskrevet' or maker.get('creator_qualifier')=='Tidligere tilskrevet':former.append(maker)
                else:active.append(maker)
            maker=active[0] if len(active)==1 else {};name=' '.join(v for v in [maker.get('creator_forename'),maker.get('creator_surname')] if v)
            matched=len(active)==1 and x.r.norm(name) in names and not maker.get('creator_qualifier') and not maker.get('creator_role')
            single=o.get('number_of_parts')==1
            e.update(receipt=receipt,human_url=o.get('frontend_url'),object=dict(title='; '.join(t['title'] for t in o.get('titles',[])),creator=name,accession=acc,date='; '.join(d.get('period','') for d in o.get('production_date',[])),fields=o,makers=active,former_attributions=former),creator_match=matched,accession_match=True,single_object=single,review='primary_object_and_creator_corroborated' if matched and single else 'primary_review_required',basis='Exact selected inventory and current unqualified maker aliases; former attributions retained separately. Museum date ranges preserved as source claims, never invented precise years. No display assertion or image download.')
        except Exception as error:e['reason']=str(error)[:350]
        x.save(target,e);out.append(e);print(code,number,q,e['review'],flush=True)
    x.save(dest,dict(at=x.r.core.now(),records=out,counts=dict(collections.Counter(e['review'] for e in out))))

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--country',required=True,choices=x.COUNTRIES);a.add_argument('--round',type=int,required=True);v=a.parse_args();capture(v.country,v.round)
