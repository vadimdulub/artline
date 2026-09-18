#!/usr/bin/env python3
"""Preserve Getty ULAN primary identity/cultural-affiliation evidence; no DB writes."""
import argparse, collections, importlib.util, json, re
from pathlib import Path

s=importlib.util.spec_from_file_location('country',Path(__file__).with_name('research-country-rounds.py'))
x=importlib.util.module_from_spec(s);s.loader.exec_module(x)

def capture(code):
    roster=json.loads((x.BASE/code/'roster.json').read_text())['artists'];rows=[]
    for a in roster:
        e=json.loads((x.r.RUN/'entities'/(a['qid']+'.json')).read_text())['entity']
        for authority in x.r.values(e,'P245'):
            if not isinstance(authority,str) or not re.fullmatch(r'\d{9}',authority):continue
            path=x.BASE/code/'getty-primary'/(a['qid']+'-'+authority+'.json')
            if path.exists():rows.append(json.loads(path.read_text()));continue
            result={'qid':a['qid'],'name':a['name'],'getty_id':authority,'country':code,'at':x.r.core.now()}
            try:
                data,receipt=x.r.fetch('https://vocab.getty.edu/ulan/'+authority+'.json')
                identities=[v.get('id','') for v in data.get('equivalent',[])]
                linked=any(re.search(r'/(?:wiki|entity)/'+a['qid']+r'$',u) for u in identities)
                nationalities=[v for v in data.get('classified_as',[]) if any(c.get('id')=='http://vocab.getty.edu/aat/300379842' for c in v.get('classified_as',[]))]
                terms=[v.get('_label','') for v in nationalities]
                expected=x.COUNTRIES[code]['adjective']
                corroborated=any(re.match(re.escape(expected)+r'(?:$| \()',term) for term in terms)
                result.update(source=receipt,label=data.get('_label'),identity_reciprocal=linked,nationalities=nationalities,birth=data.get('born',{}).get('timespan'),death=data.get('died',{}).get('timespan'),review='explicit_affiliation_corroborated' if linked and corroborated else 'primary_identity_or_country_context_requires_review',basis='Getty ULAN cultural/nationality classification, not an inference from birthplace or work location. Additional affiliations retained as source assertions.')
            except Exception as error:result.update(review='source_unavailable',reason=str(error)[:350])
            x.save(path,result);rows.append(result)
            if len(rows)%20==0:print(code,'Getty primary',len(rows),dict(collections.Counter(v['review'] for v in rows)),flush=True)
    result={'at':x.r.core.now(),'country':code,'artists_in_roster':len(roster),'authority_records':len(rows),'counts':dict(collections.Counter(v['review'] for v in rows)),'records':rows}
    x.save(x.BASE/code/'getty-primary-review.json',result);print(code,'Getty complete',result['counts'],flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('country',choices=x.COUNTRIES);capture(p.parse_args().country)
