#!/usr/bin/env python3
"""Read-only reconciliation of explicit WikiArt relationships for the Top 100."""
import collections,importlib.util,re
from pathlib import Path
from urllib.parse import urljoin
s=importlib.util.spec_from_file_location('m',Path(__file__).with_name('cesi-top100-20261010.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def main():
    assert (m.RUN/'discovery-summary.json').exists()
    b=m.load(m.RUN/'baseline.json.gz');top={a['record']['id']:a['record'] for a in b['artists'] if a['discovery'] and a['discovery']['is_popular']};leads=[];coverage=[]
    for aid,artist in top.items():
        correction=m.RUN/'indexes-corrections'/(aid+'.json.gz')
        ix=m.load(correction if correction.exists() else m.RUN/'indexes'/(aid+'.json.gz'))
        if ix['state']!='captured':coverage.append(dict(artist_id=aid,name=artist['display_name'],state=ix['state'],explicit_relations=0));continue
        url=ix['profiles'][0];raw,receipt=m.capture(url);assert receipt['status']==200
        sp=m.BeautifulSoup(raw,'html.parser');n=0
        for field,kind,reverse in [('Teachers','teacher_of',True),('Pupils','teacher_of',False),('Influenced by','influenced',True),('Influenced on','influenced',False)]:
            node=sp.find(string=re.compile(r'^\s*'+re.escape(field)+r':\s*$'))
            if node is None:continue
            for link in node.parent.parent.select('a[href]'):
                href=urljoin(url,link['href']).rstrip('/')
                if not href.startswith('https://www.wikiart.org/en/'):continue
                leads.append(dict(cohort_artist_id=aid,cohort_artist_name=artist['display_name'],other_url=href,other_label=link.get_text(' ',strip=True),relationship_type=kind,other_is_source=reverse,source_url=url,source_field=field,receipt=receipt));n+=1
        coverage.append(dict(artist_id=aid,name=artist['display_name'],state='reviewed',explicit_relations=n))
    urls=sorted({r['other_url'] for r in leads});cross=collections.defaultdict(set);artists={}
    with m.connect() as db:
        for batch in m.chunks(urls):
            for r in db.execute("SELECT e.canonical_url,to_jsonb(a) artist FROM external_identifiers e JOIN artists a ON a.id=e.entity_id WHERE e.entity_type='artist' AND e.scheme='wikiart-artist' AND e.canonical_url=ANY(%s) AND a.status<>'archived'",(batch,)):
                cross[r['canonical_url'].rstrip('/')].add(r['artist']['id']);artists[r['artist']['id']]=r['artist']
        existing=[r['v'] for r in db.execute('SELECT to_jsonb(i) v FROM influence_claims i WHERE source_artist_id=ANY(%s::uuid[]) OR target_artist_id=ANY(%s::uuid[])',(list(top),list(top)))]
    keys={(r['source_artist_id'],r['target_artist_id'],r['relationship_type']) for r in existing};labels={(m.norm(r['source_label']),r['target_artist_id'],r['relationship_type']) for r in existing};selected={};held=[];already=[]
    for r in leads:
        ids=cross[r['other_url']]
        if len(ids)!=1:r['hold']='Missing or ambiguous exact artist profile identity';held.append(r);continue
        other=next(iter(ids));src,dst=(other,r['cohort_artist_id']) if r['other_is_source'] else (r['cohort_artist_id'],other);key=src,dst,r['relationship_type'];source_name=(artists|top)[src]['display_name']
        r.update(source_artist_id=src,target_artist_id=dst,source_label=source_name)
        if src==dst:r['hold']='Self relation';held.append(r)
        elif key in keys or (m.norm(source_name),dst,r['relationship_type']) in labels:already.append(r)
        else:selected.setdefault(key,[]).append(r)
    candidates=[dict(source_artist_id=k[0],target_artist_id=k[1],relationship_type=k[2],evidence=v) for k,v in selected.items()]
    m.save(m.RUN/'top100-connection-audit-final.json.gz',dict(at=m.now(),coverage=coverage,existing=existing,candidates=candidates,already_present=already,held=held,artists=artists))
    print('Top 100 relationship audit:',len(leads),'explicit source assertions;',len(candidates),'missing pairs;',len(already),'already present;',len(held),'identity holds')
    for r in candidates:print(r['relationship_type'],(artists|top)[r['source_artist_id']]['display_name'],'->',(artists|top)[r['target_artist_id']]['display_name'])
if __name__=='__main__':main()
