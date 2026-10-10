"""Bounded catalogue metadata discovery before selecting objects or images."""
import gzip
import importlib.util
import json
from pathlib import Path
from urllib.parse import urlencode
from bs4 import BeautifulSoup
spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-chania-source-20261010.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
m,RUN,q=c.m,c.RUN,c.q

def main():
    discovery=m.load(RUN/'source-discovery-001.json.gz');known={r['source_id']for r in discovery['historical_records']}
    action=discovery['form']['action'];assert action=='/aggregator/portal/collections/AMusChania/search'
    assert any(o['value']=='SCORE'for o in discovery['form']['sort_options'])
    pages=[];seen=set()
    for page in range(1,8):
        if page==1:
            rc=discovery['receipt'];soup=BeautifulSoup(gzip.decompress((m.ROOT/rc['body_path']).read_bytes()),'html.parser')
        else:
            url=c.BASE+action+'?'+urlencode({'page.page':page,'resultsMode':'GRID','sortResults':'SCORE','language':'en'})
            soup,rc=q.q.capture('collection-index-page-'+str(page)+'-001',url)
        rows=c.index(soup);assert len(rows)==30 and not seen&{r['source_id']for r in rows}
        seen.update(r['source_id']for r in rows)
        for r in rows:r['historical_source_match']=r['source_id']in known
        pages.append(dict(page=page,receipt=rc,cards=rows))
        print(json.dumps(dict(page=page,historical=sum(r['historical_source_match']for r in rows),cards=len(rows))),flush=True)
    m.save(RUN/'bounded-index-001.json.gz',dict(at=m.now(),pages=pages,cards=210,observed_collection_records=320,
        discovery_reference=q.s.ref(RUN/'source-discovery-001.json.gz'),script_reference=q.s.ref(Path(__file__).resolve()),
        policy='Seven public index pages,210/320records. Metadata discovery only; no automatic eligibility inferred from source type or EKT periods. Select museum-backed art/decorative objects before images; hold plain tools or unclear scope. Existing source objects are comparators, not new additions.'))

if __name__=='__main__':main()
