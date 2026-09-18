#!/usr/bin/env python3
"""Review country/collection identity and prepare selected licensed reproductions."""
import argparse,collections,hashlib,importlib.util,json,re,time
from pathlib import Path
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
from PIL import Image,ImageOps,ImageDraw
s=importlib.util.spec_from_file_location('country',Path(__file__).with_name('research-country-rounds.py'));x=importlib.util.module_from_spec(s);s.loader.exec_module(x)

def bio_index(code):
    index={}
    for path in (x.BASE/code/'biography-captures').glob('*.json'):
        d=json.loads(path.read_text());query=d['data'].get('query',{});pages={p['title']:p for p in query.get('pages',{}).values()}
        redirects={r['from']:r['to'] for r in [*query.get('normalized',[]),*query.get('redirects',[])]}
        for item in d['requested']:
            title=item['title'];seen=set()
            while title in redirects and title not in seen:seen.add(title);title=redirects[title]
            p=pages.get(title)
            if p and p.get('extract'):index[item['qid']]={'title':title,'url':p.get('fullurl') or 'https://en.wikipedia.org/wiki/'+title.replace(' ','_'),'intro':p['extract'].split('\n\n')[0][:1800],'receipt':d['receipt']}
    return index

def introductory_affiliations(text):
    # Restrict to biographical role wording. A place of birth, museum address or
    # later sentence mentioning another artist cannot supply nationality.
    first=text[:700]
    match=re.search(r'\b(?:was|is|were)\s+(?:a|an)\s+(.{0,180}?)(?:painter|artist|iconographer|printmaker|engraver|draughtsman|illustrator|photographer|sculptor)\b',first,re.I)
    phrase=match[1] if match else ''
    labels={word for word in ['Dutch','Greek','Russian','French','German','English','British','Flemish','Belgian','Austrian','Danish','Italian','Spanish','Finnish','Portuguese','American','Swiss','Polish','Ukrainian','Swedish','Norwegian','Czech','Hungarian','Romanian','Lithuanian','Belarusian','Latvian','Estonian'] if re.search(r'\b'+word+r'\b(?![- ]born)',phrase,re.I)}
    if re.search(r'\bpainter from (?:the )?Northern Netherlands\b',first,re.I):labels.add('Dutch')
    if 'Southern Netherlands' in first or 'Flemish' in phrase:labels.add('Flemish')
    return labels

def website(inst):
    url=inst['website_url'];parsed=urlparse(url);assert parsed.scheme=='https' and parsed.hostname and parsed.hostname not in ('localhost','127.0.0.1') and not parsed.hostname.endswith('.local')
    key=hashlib.sha256(url.encode()).hexdigest();folder=x.BASE/'museum-websites';path=folder/(key+'.json')
    if path.exists():return json.loads(path.read_text())
    result={'url':url,'at':x.r.core.now(),'verified':False}
    try:
        response=requests.get(url,timeout=(15,35),headers={'User-Agent':'Artline research (https://github.com/vadimdulub/artline)'},stream=True)
        chunks=[];size=0
        for chunk in response.iter_content(65536):
            chunks.append(chunk);size+=len(chunk)
            if size>3_000_000:raise ValueError('Website evidence exceeded bounded capture')
        raw=b''.join(chunks);response.close();result.update(status=response.status_code,resolved_url=response.url,bytes=len(raw),sha256=x.r.core.sha(raw))
        x.save(folder/(key+'.html'),raw)
        if response.status_code!=200:raise ValueError('Official website not currently readable')
        soup=BeautifulSoup(raw,'html.parser');result['page_title']=soup.title.get_text(' ',strip=True) if soup.title else ''
        for node in soup(['script','style','noscript']):node.decompose()
        text=x.r.norm(soup.get_text(' ',strip=True))
        entity=json.loads((x.r.RUN/'entities'/(inst['wikidata_id']+'.json')).read_text())['entity']
        names=[inst['name'],*x.r.labels(entity),*[v.get('text','') for v in x.r.values(entity,'P1448') if isinstance(v,dict)]]
        matched=next((n for n in names if len(x.r.norm(n))>=8 and x.r.norm(n) in text),None)
        if not matched:raise ValueError('Official website identity needs manual multilingual review')
        result.update(verified=True,matched_name=matched)
    except (requests.RequestException,ValueError) as e:result['reason']=str(e)[:250]
    x.save(path,result);return result

def country_review(code,number):
    run=x.BASE/code/f'round-{number:02d}';delivery=run/'delivery'
    if (delivery/'country-collection-review.json').exists():return
    bios=bio_index(code);approved=[];held=[];sites={}
    records=[r for path in sorted((run/'selected').glob('*.json')) for r in json.loads(path.read_text())['selected']]
    for record in records:
        cq=record['creator_qid'];evidence=x.artist_country(record['creator_entity'],code);bio=bios.get(cq);reason=None
        if not evidence:reason='country_affiliation_not_corroborated'
        if evidence and evidence.get('requires_biographical_affiliation_corroboration') and not bio:
            reason='historical_polity_requires_explicit_cultural_biography'
        if bio:
            named=introductory_affiliations(bio['intro']);expected=x.COUNTRIES[code]['adjective']
            if named and expected not in named:reason='wikipedia_biography_requires_country_context'
            elif evidence and evidence.get('requires_biographical_affiliation_corroboration') and expected not in named:
                reason='historical_polity_requires_explicit_cultural_biography'
            elif evidence:evidence={**evidence,'wikipedia_country_crosscheck':{'url':bio['url'],'receipt':bio['receipt'],'explicit_role_affiliations':sorted(named),'source_excerpt':bio['intro'][:300]}}
        inst=record['collection']['institution']
        if not reason and inst.get('new_institution'):
            q=inst['wikidata_id']
            if q not in sites:sites[q]=website(inst)
            if not sites[q]['verified']:reason='new_collection_official_website_review'
        if reason:held.append({'qid':record['qid'],'painter':record['creator_label'],'institution':inst['name'],'reason':reason});continue
        copied={**record,'country_evidence':evidence}
        source_titles=[v.get('text','').strip() for v in x.r.values(record['entity'],'P1476') if isinstance(v,dict) and v.get('text','').strip()]
        copied['titles']=list(dict.fromkeys([*record['titles'],*source_titles]))
        if not re.search(r'\w',copied['title']) or re.fullmatch(r'Q\d+',copied['title']):
            if source_titles:copied.update(title=source_titles[0],title_evidence='Explicit Wikidata P1476 source-language title; placeholder label was not treated as artwork title.')
            else:
                held.append({'qid':record['qid'],'painter':record['creator_label'],'institution':inst['name'],'reason':'source_artwork_title_missing'});continue
        if inst.get('new_institution'):copied['official_collection_website_evidence']=sites[inst['wikidata_id']]
        approved.append(copied)
    for slug,rows in x.collections_module(approved).items():x.save(delivery/'selected'/(slug+'.json'),{'selected':rows,'deferred':[]})
    result={'at':x.r.core.now(),'country':code,'round':number,'initial_candidates':len(records),'approved_metadata':len(approved),'approved_qids':[r['qid'] for r in approved],'held':held,'official_websites':sites,'held_counts':dict(collections.Counter(r['reason'] for r in held))}
    x.save(delivery/'country-collection-review.json',result);print(code,number,'country/collection approved',len(approved),'held',len(held),flush=True)

def images(code,number):
    country_review(code,number);delivery=x.BASE/code/f'round-{number:02d}'/'delivery'
    s=importlib.util.spec_from_file_location('images',x.ROOT/'ops/prepare-wikimedia-catalogue-images.py');im=importlib.util.module_from_spec(s);s.loader.exec_module(im)
    im.r.RUN=delivery;archive=Path('/Users/vadimdulub/Library/Application Support/Artline/source-images')/x.SESSION_NAME
    if x.CAMPAIGN:archive=archive/x.CAMPAIGN
    im.r.BACKUPS=archive/code/f'round-{number:02d}'
    im.main()
    prepared=[json.loads(p.read_text()) for p in sorted((delivery/'ready').glob('*.json'))]
    thumbs=[p for p in prepared if p['image']]
    cols=5;width=250;height=210;canvas=Image.new('RGB',(cols*width,max(1,(len(thumbs)+cols-1)//cols)*height),'#f0eee9');draw=ImageDraw.Draw(canvas)
    for i,p in enumerate(thumbs):
        source=x.ROOT/'apps/web/public'/p['image']['path'].lstrip('/')
        with Image.open(source) as photo:tile=ImageOps.contain(photo.convert('RGB'),(width-14,height-45));left=(i%cols)*width+(width-tile.width)//2;top=(i//cols)*height;canvas.paste(tile,(left,top))
        text=p['record']['qid']+' '+p['record']['creator_label'][:24]
        draw.text(((i%cols)*width+5,(i//cols)*height+height-40),text,fill='#111111')
        draw.text(((i%cols)*width+5,(i//cols)*height+height-24),p['record']['title'][:36],fill='#111111')
    dest=delivery/'contact-sheet.jpg';canvas.save(dest,quality=85)
    summary={'at':x.r.core.now(),'ready':len(prepared),'images':len(thumbs),'outcomes':dict(collections.Counter(p['image_outcome'] for p in prepared)),'contact_sheet':str(dest),'ready_hashes':{p.name:x.r.core.sha(p.read_bytes()) for p in sorted((delivery/'ready').glob('*.json'))}}
    x.save(delivery/'image-preparation.json',summary);print(code,number,'prepared',len(prepared),'images',len(thumbs),'contact sheet',dest,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['review','images']);p.add_argument('--country',choices=x.COUNTRIES,required=True);p.add_argument('--round',type=int,required=True);a=p.parse_args();assert 1<=a.round<=20
    country_review(a.country,a.round) if a.command=='review' else images(a.country,a.round)
