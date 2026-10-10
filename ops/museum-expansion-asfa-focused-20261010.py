"""Preserve bounded full comparator rows and capture exact creator authorities."""
import gzip,importlib.util,json
from pathlib import Path
from bs4 import BeautifulSoup
spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-asfa-common-20261010.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
m,RUN=c.m,c.RUN
ARTISTS=['3b5fbd54-cae2-5e50-a0b3-f70eabf743cd','951faed2-0922-532a-85cc-305f9403a4e0','f6fbb79f-68f7-5abc-8541-f33ae7d091a0']

def artist_state(db):
    out={}
    for key,sql in {'artists':'SELECT to_jsonb(x) row FROM artists x WHERE id=ANY(%s::uuid[]) ORDER BY id','aliases':'SELECT to_jsonb(x) row FROM artist_aliases x WHERE artist_id=ANY(%s::uuid[]) ORDER BY artist_id,id','identifiers':"SELECT to_jsonb(x) row FROM external_identifiers x WHERE entity_type='artist' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id"}.items():out[key]=[x['row'] for x in db.execute(sql,(ARTISTS,))]
    return out

def main():
    p=RUN/'focused-comparators-001.json.gz';assert not p.exists();obs=m.load(RUN/'production-identity-001.json.gz');ids=obs['state']['artwork_ids']
    with c.prod.connect() as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY');snap=c.snapshot(db,ids);artists=artist_state(db)
    m.save(p,dict(at=m.now(),ids=ids,snapshot=snap,artist_ids=ARTISTS,artist_state=artists,identity_reference=c.ref(RUN/'production-identity-001.json.gz'),script_reference=c.ref(Path(__file__).resolve())))
    q=c.module('q','museum-expansion-asfa-source-20261010.py').q;rows=m.load(RUN/'selected-source-records-001.json.gz')['rows'];authorities=[]
    for n in [3,24,33]:
        row=rows[n-1];doc=BeautifulSoup(gzip.decompress((m.ROOT/row['receipt']['body_path']).read_bytes()).decode('utf-8'),'html.parser');group=next(g for g in doc.select('.form-group') if g.select_one('label.control-label') and q.clean(g.select_one('label.control-label').get_text(' ',strip=True))=='Δημιουργός');links=sorted({'https://www.searchculture.gr'+a['href'] for a in group.select('.panel-enrichment a[href]') if a['href'].startswith('/aggregator/persons/')});assert len(links)==1
        url=links[0];doc,rc=q.q.capture('authority-'+url.rsplit('/',1)[-1]+'-001',url);authorities.append(dict(number=n,url=url,title=doc.title.get_text(' ',strip=True),text=doc.get_text(' ',strip=True),receipt=rc,object_reference=row['receipt']))
    m.save(RUN/'creator-source-corroboration-001.json',dict(at=m.now(),rows=authorities,policy='Only links inside literalCreatorfield captured. Sitters notmakers. Three existingartistidentities; no authority/alias changes.'))
    print(json.dumps(dict(focused=len(ids),authority_titles=[x['title'] for x in authorities]),ensure_ascii=False),flush=True)

if __name__=='__main__':main()
