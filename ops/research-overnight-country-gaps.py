#!/usr/bin/env python3
"""Twenty bounded reviews of existing museum-named painters lacking country.

Read-only discovery: source name + exact closed lifespan + human identity,
then explicit country wording in both Wikidata and Wikipedia biography.
No country inference from birthplace, names, museum location or citizenship.
"""
import argparse,collections,importlib.util,json,time
from pathlib import Path
from urllib.parse import urlencode

s=importlib.util.spec_from_file_location('g',Path(__file__).with_name('review-overnight-country-gaps.py'));g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
m=g.m;RUN=m.x.BASE/'country-gap-followup'/'closed-identity-research'

def roster():
    dest=RUN/'roster.json'
    if dest.exists():return json.loads(dest.read_text())
    rows=json.loads((m.x.BASE/'country-gap-followup/closed-museum-identity-targets.json').read_text())['artists']
    rows=[a for a in rows if a['birth_year']<=1970 and 0<=a['death_year']-a['birth_year']<=125]
    rows.sort(key=lambda a:(not bool(a['authorities']),a['birth_year'],a['display_name']))
    scopes=[dict(round=n+1,artists=rows[n::20],question='Identify source-named museum painters by full name/aliases and closed life dates; investigate explicit cultural affiliation, disputed dates and duplicate person identities.') for n in range(20)]
    result=dict(at=m.m.core.now(),artists=len(rows),rounds=scopes,policy='Existing real painters only; no DB writes. Museum source chronology and source links must be reviewed before any later country/authority proposal. No automatic merges.')
    m.m.core.save_new(dest,result);return result

def search(a):
    path=RUN/'person-searches'/(a['id']+'.json')
    if path.exists():return json.loads(path.read_text())
    query=a['display_name']
    data,receipt=m.x.r.fetch('https://www.wikidata.org/w/api.php?'+urlencode(dict(action='wbsearchentities',search=query,language='en',uselang='en',type='item',limit=5,format='json',maxlag=5)))
    qids=[r['id'] for r in data.get('search',[])];entities,receipts=m.x.r.entities(qids) if qids else ({},{})
    matches=[];holds=[]
    for q,e in entities.items():
        if e.get('id')!=q or not any(v.get('id')=='Q5' for v in m.m.r.values(e,'P31') if isinstance(v,dict)):continue
        names={m.f.names.namekey(v) for v in m.m.r.labels(e)};expected={m.f.names.namekey(v) for v in [a['display_name'],*a['aliases']]}
        if not names&expected:continue
        birth=m.m.r.year(e,'P569');death=m.m.r.year(e,'P570')
        if (birth,death)!=(a['birth_year'],a['death_year']):
            holds.append(dict(qid=q,reason='Full-name candidate has incomplete or conflicting life dates',source_birth=birth,source_death=death));continue
        matches.append(dict(qid=q,name=m.m.r.label(e),birth=birth,death=death,description=e.get('descriptions',{}).get('en',{}).get('value',''),entity_receipt=receipts[q],wikipedia_title=e.get('sitelinks',{}).get('enwiki',{}).get('title')))
    result=dict(at=m.m.core.now(),artist=a,query=query,search_receipt=receipt,matches=matches,holds=holds,decision='unique_closed_identity_candidate' if len(matches)==1 else 'unresolved_or_multiple_source_identities')
    m.m.core.save_new(path,result);return result

def biographies(candidates,run):
    requested=[dict(qid=c['matches'][0]['qid'],title=c['matches'][0]['wikipedia_title']) for c in candidates if len(c['matches'])==1 and c['matches'][0]['wikipedia_title']]
    requested=list({r['qid']:r for r in requested}.values());bios={}
    for start in range(0,len(requested),20):
        part=requested[start:start+20];path=run/'biographies'/f'{start:04d}.json'
        if path.exists():d=json.loads(path.read_text())
        else:
            data,receipt=m.x.r.fetch('https://en.wikipedia.org/w/api.php?'+urlencode(dict(action='query',format='json',titles='|'.join(x['title'] for x in part),prop='extracts|info',exintro=1,explaintext=1,inprop='url',redirects=1,maxlag=5)))
            d=dict(requested=part,data=data,receipt=receipt);m.m.core.save_new(path,d)
        query=d['data'].get('query',{});pages={p['title']:p for p in query.get('pages',{}).values()};redirects={x['from']:x['to'] for x in [*query.get('normalized',[]),*query.get('redirects',[])]}
        for item in part:
            title=item['title'];seen=set()
            while title in redirects and title not in seen:seen.add(title);title=redirects[title]
            p=pages.get(title)
            if p and p.get('extract'):bios[item['qid']]=dict(url=p.get('fullurl'),intro=p['extract'].split('\n\n')[0][:1800],receipt=d['receipt'])
    return bios

def research(n):
    scope=roster()['rounds'][n-1];run=RUN/f'round-{n:02d}';dest=run/'research.json'
    if dest.exists():print('Country gap scope',n,'already captured',flush=True);return
    results=[];failures=[];consecutive_failures=0
    for index,a in enumerate(scope['artists'],1):
        try:
            results.append(search(a));consecutive_failures=0
        except Exception as e:
            failure=dict(artist_slug=a['slug'],at=m.m.core.now(),error=type(e).__name__,reason=str(e)[:250]);failures.append(failure);failure_path=run/'failures'/(a['id']+'.json')
            if not failure_path.exists():m.m.core.save_new(failure_path,failure)
            consecutive_failures+=1
            print('Country source deferred',n,a['display_name'],str(e)[:100],flush=True)
            if consecutive_failures>=3:raise RuntimeError('Three consecutive source failures: circuit pause required before resuming cached research') from e
        if index%10==0:print('Country gap scope',n,'searched',index,'/',len(scope['artists']),'exact life/name candidates',sum(len(r['matches'])==1 for r in results),flush=True)
    bios=biographies(results,run);proposals=[];holds=[]
    for r in results:
        if len(r['matches'])!=1:holds.append(dict(slug=r['artist']['slug'],reason=r['decision']));continue
        c=r['matches'][0];bio=bios.get(c['qid']);labels=g.labels(c['description']);biolabels=g.biography_labels(bio['intro']) if bio else {};codes=set(labels.values())&set(biolabels.values())
        if not codes:holds.append(dict(slug=r['artist']['slug'],qid=c['qid'],reason='Explicit cultural affiliation not corroborated by biography',description=c['description'],description_labels=labels,biography_labels=biolabels));continue
        proposals.append(dict(artist=r['artist'],candidate=c,country_codes=sorted(codes),description_affiliations=labels,biography_affiliations=biolabels,wikipedia_evidence=bio,search_receipt=r['search_receipt'],decision='Research proposal only; refresh both DB identities, primary museum creator evidence and global authority ownership before applying'))
    result=dict(at=m.m.core.now(),round=n,scope_size=len(scope['artists']),searched=len(results),unique_closed_candidates=sum(len(r['matches'])==1 for r in results),country_proposals=proposals,holds=holds,source_failures=failures,completed=not failures)
    m.m.core.save_new(dest,result);print('Country gap scope',n,'complete proposals',len(proposals),'holds',len(holds),'failures',len(failures),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--round',type=int);a=p.parse_args()
    for n in ([a.round] if a.round else range(1,21)):research(n)
