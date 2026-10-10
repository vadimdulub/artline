"""Bounded date-ordered index review using the observed public search form."""
import importlib.util
import json
from pathlib import Path
from urllib.parse import urlencode

spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-larissa-source-20261010.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
m,RUN,q=c.m,c.RUN,c.q

def main():
    d=m.load(RUN/'source-discovery-001.json.gz');known={x['source_id']for x in d['historical_records']}
    action=d['form']['action'];assert action=='/aggregator/portal/collections/larisa_gallery/search'
    assert any(o['value']=='YEAR_ASC'for s in d['form']['selects']for o in s['options'])
    seen=set();pages=[]
    for page in range(1,8):
        url=c.BASE+action+'?'+urlencode({'page.page':page,'resultsMode':'GRID','sortResults':'YEAR_ASC','language':'en'})
        soup,rc=q.q.capture('date-index-page-'+str(page)+'-001',url);rows=c.index(soup)
        assert len(rows)==30 and not seen&{r['source_id']for r in rows};seen.update(r['source_id']for r in rows)
        for row in rows:row['historical_source_match']=row['source_id']in known
        pages.append(dict(page=page,receipt=rc,cards=rows))
        print(json.dumps(dict(page=page,cards=len(rows),existing=sum(r['historical_source_match']for r in rows),first=rows[0]['index_date'],last=rows[-1]['index_date']),ensure_ascii=False),flush=True)
    m.save(RUN/'bounded-date-index-001.json.gz',dict(at=m.now(),pages=pages,cards=210,observed_collection_records=820,discovery_reference=q.s.ref(RUN/'source-discovery-001.json.gz'),script_reference=q.s.ref(Path(__file__).resolve()),
        policy='Seven date-ascending pages only. Index dates are selection leads, not final physical creation dates. Preserve unknown dates and creator lifespans separately; object metadata must establish eligibility. No images downloaded.'))

if __name__=='__main__':main()
