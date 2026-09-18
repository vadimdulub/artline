#!/usr/bin/env python3
"""Read selected Hungarian National Gallery object pages; no image scraping."""
import argparse, collections, importlib.util, json, re
from pathlib import Path
from urllib.parse import urlparse
s=importlib.util.spec_from_file_location('p',Path(__file__).with_name('research-german-primary-objects.py'));p=importlib.util.module_from_spec(s);s.loader.exec_module(p)
x=p.x

def capture(code,number):
    run=x.BASE/code/f'round-{number:02d}'/'delivery';dest=run/'hungarian-primary-review.json'
    if dest.exists():return
    out=[]
    for path in sorted((run/'ready').glob('*.json')):
        r=json.loads(path.read_text())['record']
        urls=[u for u in x.r.values(r['entity'],'P973') if isinstance(u,str) and urlparse(u).hostname=='en.mng.hu' and u.startswith('https://en.mng.hu/artworks/')]
        if not urls:continue
        q=r['qid'];target=run/'hungarian-primary'/(q+'.json')
        if target.exists():out.append(json.loads(target.read_text()));continue
        e=dict(qid=q,at=x.r.core.now(),museum='hungarian-national-gallery',review='primary_review_required',ready_sha256=x.r.core.sha(path.read_bytes()))
        try:
            # New numeric permalink and established slug may coexist in P973.
            # Inspect one explicit descriptive object URL, never a search hit.
            slugs=[u for u in urls if not u.rstrip('/').rsplit('/',1)[-1].isdigit()]
            candidates=list(dict.fromkeys(slugs or urls));assert len(candidates)==1,'Ambiguous primary object links'
            soup,receipt=p.page(candidates[0],p.ROOT/'mng',q);fields={};maker=None;bio=None
            for tr in soup.select('tr'):
                cells=tr.find_all(['th','td'],recursive=False)
                if len(cells)!=2:continue
                key=cells[0].get_text(' ',strip=True);fields[key]=cells[1].get_text(' ',strip=True)
                if key=='Artist':
                    a=cells[1].select_one('.author__name');b=cells[1].select_one('.author__bio');maker=a.get_text(' ',strip=True) if a else None;bio=b.get_text(' ',strip=True) if b else None
            h=soup.select_one('h1.headline__title');assert h,'Object title missing'
            for a in h.select('.author__name'):a.decompose()
            title=h.get_text(' ',strip=True);acc=fields.get('Inventory number');names={x.r.norm(n) for n in x.r.labels(r['creator_entity'])}
            match=bool(maker) and x.r.norm(maker) in names
            key=lambda v:re.sub(r'[^a-z0-9]','',str(v).lower())
            acc_match=bool(acc) and (key(acc)==key(r.get('accession')) if r.get('accession') else x.r.norm(title) in {x.r.norm(t) for t in r['titles']})
            e.update(receipt=receipt,human_url=receipt['url'],object=dict(title=title,creator=maker,creator_biography=bio,accession=acc,date=fields.get('Date'),type=fields.get('Object type'),fields=fields),creator_match=match,accession_match=acc_match,accession_missing_in_source=not bool(r.get('accession')),review='primary_object_and_creator_corroborated' if match and acc_match else 'primary_review_required',basis='Explicit source-linked museum object page, exact primary maker alias and inventory (or exact title where source inventory missing). Newly found inventories require reviewed override and duplicate lookup before import. No inferred display or image rights.')
        except Exception as error:e['reason']=str(error)[:350]
        x.save(target,e);out.append(e);print(code,number,q,e['review'],e.get('object',{}).get('date'),flush=True)
    x.save(dest,dict(at=x.r.core.now(),records=out,counts=dict(collections.Counter(e['review'] for e in out))))

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--country',required=True,choices=x.COUNTRIES);a.add_argument('--round',type=int,required=True);v=a.parse_args();capture(v.country,v.round)
