#!/usr/bin/env python3
"""Primary Städel/Karlsruhe checks for selected country-round objects only."""
import argparse,collections,importlib.util,json,re,time
from pathlib import Path
from urllib.parse import urljoin,urlparse
import requests
from bs4 import BeautifulSoup

s=importlib.util.spec_from_file_location('country',Path(__file__).with_name('research-country-rounds.py'))
x=importlib.util.module_from_spec(s);s.loader.exec_module(x)
ROOT=x.SESSION_BASE/'primary-museums'
POLICIES={'staedel':'https://sammlung.staedelmuseum.de/de/konzept','karlsruhe':'https://www.kunsthalle-karlsruhe.de/en/cc0/'}

def page(url,folder,key):
    rawpath=folder/(key+'.html');receiptpath=folder/(key+'.receipt.json')
    if rawpath.exists():
        raw=rawpath.read_bytes();receipt=json.loads(receiptpath.read_text());assert x.r.core.sha(raw)==receipt['sha256'];return BeautifulSoup(raw,'html.parser'),receipt
    time.sleep(1)
    response=requests.get(url,timeout=(15,45),headers={'User-Agent':'Artline/1.0 (https://github.com/vadimdulub/artline; selected catalogue research)'})
    response.raise_for_status();assert len(response.content)<5_000_000
    receipt={'url':response.url,'retrieved_at':x.r.core.now(),'sha256':x.r.core.sha(response.content),'bytes':len(response.content),'status':response.status_code}
    x.save(rawpath,response.content);x.save(receiptpath,receipt)
    return BeautifulSoup(response.content,'html.parser'),receipt

def parse(soup,museum,url):
    fields={}
    if museum=='staedel':
        for dl in soup.select('dl'):
            for dt in dl.select('dt'):
                dd=dt.find_next_sibling('dd')
                if dd:fields[dt.get_text(' ',strip=True)]=dd.get_text(' ',strip=True)
        structured=[json.loads(t.string) for t in soup.find_all('script',type='application/ld+json') if t.string]
        obj=next((o for o in structured if isinstance(o,dict) and o.get('@type')=='ImageObject'),{})
        return {'fields':fields,'title':fields.get('Title'),'creator':fields.get('Painter'),'accession':fields.get('Inventory Number'),'date':obj.get('dateCreated'),'image_url':obj.get('image'),'rights':fields.get('Picture Copyright'),'credit':fields.get('Creditline'),'structured':obj}
    for tr in soup.select('tr'):
        cells=tr.find_all(['th','td'],recursive=False)
        if len(cells)==2:fields[cells[0].get_text(' ',strip=True)]=cells[1].get_text(' ',strip=True)
    images=[urljoin(url,a['href']) for a in soup.select('a[href]') if 'Klein/JPEG' in a.get_text(' ',strip=True)]
    return {'fields':fields,'title':fields.get('Titel'),'creator':fields.get('Künstler*in'),'accession':fields.get('Inventarnummer'),'date':fields.get('Entstehungszeit'),'image_url':images[0] if len(images)==1 else None,'rights':'Conditional CC0 policy for out-of-copyright works','credit':'Staatliche Kunsthalle Karlsruhe'}

def capture(code,number):
    delivery=x.BASE/code/f'round-{number:02d}'/'delivery';out=[]
    for path in sorted((delivery/'ready').glob('*.json')):
        prepared=json.loads(path.read_text());r=prepared['record'];museum={'Q163804':'staedel','Q658725':'karlsruhe'}.get(r['collection']['qid'])
        if not museum:continue
        dest=delivery/'german-primary'/(r['qid']+'.json')
        if dest.exists():out.append(json.loads(dest.read_text()));continue
        urls=[u for u in x.r.values(r['entity'],'P973') if isinstance(u,str) and urlparse(u).hostname==('sammlung.staedelmuseum.de' if museum=='staedel' else 'www.kunsthalle-karlsruhe.de')]
        result={'qid':r['qid'],'country':code,'round':number,'museum':museum,'at':x.r.core.now(),'ready_sha256':x.r.core.sha(path.read_bytes()),'review':'primary_review_required'}
        try:
            assert len(urls)==1,'Single exact primary object URL required'
            soup,receipt=page(urls[0],ROOT/museum,r['qid']);obj=parse(soup,museum,urls[0]);result.update(object=obj,receipt=receipt)
            names={x.r.norm(n) for n in x.r.labels(r['creator_entity'])};maker=re.sub(r'\s*\(\d{4}\)\s*$','',obj.get('creator') or '')
            creator_match=x.r.norm(maker) in names
            explicit_birth=re.search(r'\((\d{4})\)\s*$',obj.get('creator') or '')
            if explicit_birth and x.r.year(r['creator_entity'],'P569')!=int(explicit_birth[1]):creator_match=False
            accession_match=x.r.norm(obj.get('accession') or '')==x.r.norm(r['accession'] or '') and bool(r['accession'])
            years=[int(y) for y in re.findall(r'(?<!\d)(?:1\d{3}|20\d{2})(?!\d)',str(obj.get('date') or ''))]
            date_match=bool(years) and r['date']['first'] is not None and max(years)>=r['date']['first'] and min(years)<=r['date']['last'] and max(years)<=1970
            result.update(creator_match=creator_match,accession_match=accession_match,date_match=date_match)
            if creator_match and accession_match:result['review']='primary_object_and_creator_corroborated'
            policy,policy_receipt=page(POLICIES[museum],ROOT/museum,'rights-policy');result['policy_receipt']=policy_receipt
            death=x.r.year(r['creator_entity'],'P570')
            policy_text=policy.get_text(' ',strip=True)
            rights=(obj.get('rights')=='Public Domain') if museum=='staedel' else ('CC0' in policy_text and death is not None and death<=1955 and bool(obj.get('image_url')))
            result.update(image_rights_corroborated=rights,rights_basis='Explicit per-object Public Domain declaration and museum reuse policy.' if museum=='staedel' else 'Museum CC0 policy for out-of-copyright collection reproductions, official selected-object image download, and documented creator death by 1955; no blanket rights assumption for protected works.',creator_death_year=death,eligible_for_selected_image=bool(creator_match and accession_match and date_match and rights and not prepared['image']))
        except Exception as error:result['reason']=str(error)[:350]
        x.save(dest,result);out.append(result);print(code,number,museum,r['qid'],result['review'],'image eligible',result.get('eligible_for_selected_image',False),flush=True)
    x.save(delivery/'german-primary-review.json',{'at':x.r.core.now(),'records':out,'counts':dict(collections.Counter(r['review'] for r in out))})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--country',default='DE',choices=x.COUNTRIES);p.add_argument('--round',type=int,required=True);a=p.parse_args();assert 1<=a.round<=20;capture(a.country,a.round)
