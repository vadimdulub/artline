#!/usr/bin/env python3
"""Read selected Nasjonalmuseet objects by exact inventory; never infer display."""
import argparse,collections,importlib.util,json,re
from pathlib import Path
from urllib.parse import quote,urljoin
s=importlib.util.spec_from_file_location('primary',Path(__file__).with_name('research-german-primary-objects.py'));p=importlib.util.module_from_spec(s);s.loader.exec_module(p)
x=p.x

def capture(code,number):
    run=x.BASE/code/f'round-{number:02d}'/'delivery';dest=run/'norwegian-primary-review.json'
    if dest.exists():return
    out=[]
    for path in sorted((run/'ready').glob('*.json')):
        r=json.loads(path.read_text())['record'];acc=r.get('accession')
        if not acc or r['collection']['institution']['name']!='National Museum, Oslo':continue
        q=r['qid'];target=run/'norwegian-primary'/(q+'.json')
        if target.exists():out.append(json.loads(target.read_text()));continue
        e={'qid':q,'at':x.r.core.now(),'museum':'nasjonalmuseet','review':'primary_review_required','ready_sha256':x.r.core.sha(path.read_bytes())}
        try:
            url='https://www.nasjonalmuseet.no/en/collection/object/'+quote(acc,safe='')
            soup,receipt=p.page(url,p.ROOT/'nasjonalmuseet',q)
            fields={}
            for dt in soup.select('.description-list dt'):
                dd=dt.find_next_sibling('dd')
                if dd:fields[dt.get_text(' ',strip=True).rstrip(':')]=dd.get_text(' ',strip=True)
            head=soup.select_one('.collection-object-header');assert head,'Object header missing'
            title=head.select_one('h1');makers=[]
            for li in head.select('.collection-object-header__info > li'):
                for a in li.select('a[href*="/producer/"]'):
                    role=li.select_one('.collection-object-header__role')
                    makers.append({'name':a.get_text(' ',strip=True),'url':urljoin(url,a['href']),'role':role.get_text(' ',strip=True) if role else ''})
            names={x.r.norm(n) for n in x.r.labels(r['creator_entity'])}
            creator_match=len(makers)==1 and x.r.norm(makers[0]['name']) in names and not makers[0]['role']
            accession_match=x.r.norm(fields.get('Inventory no.',''))==x.r.norm(acc)
            single=fields.get('Cataloguing level')=='Single object'
            e.update(receipt=receipt,human_url=url,object={'title':title.get_text(' ',strip=True) if title else None,'creator':'; '.join(m['name'] for m in makers),'makers':makers,'accession':fields.get('Inventory no.'),'date':fields.get('Creation date'),'type':fields.get('Object type'),'fields':fields},creator_match=creator_match,accession_match=accession_match,single_object=single,review='primary_object_and_creator_corroborated' if creator_match and accession_match and single else 'primary_review_required',basis='Exact museum inventory and explicit primary maker name matched to source aliases. Cataloguing level retained. Web-page on-display text is not converted to a display assertion. Metadata capture does not grant image rights.')
        except Exception as error:e['reason']=str(error)[:350]
        x.save(target,e);out.append(e);print(code,number,q,e['review'],e.get('object',{}).get('date'),flush=True)
    x.save(dest,{'at':x.r.core.now(),'records':out,'counts':dict(collections.Counter(e['review'] for e in out))})

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--country',required=True,choices=x.COUNTRIES);a.add_argument('--round',type=int,required=True);v=a.parse_args();capture(v.country,v.round)
