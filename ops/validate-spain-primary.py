#!/usr/bin/env python3
"""Validate exact museum technical records. Generic landing pages never qualify."""
import collections, hashlib, importlib.util, json, re
from pathlib import Path
from urllib.parse import urlparse
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('r',ROOT/'ops/research-spain-deep.py');r=importlib.util.module_from_spec(s);s.loader.exec_module(r)

def norm(s):return r.w.norm(s)
def acc(s):return re.sub(r'\d+',lambda m:str(int(m[0])),re.sub('[^A-Z0-9]','',s.upper()))
def tokens(s):return sorted(norm(s).split())

def parse(raw,url):
    soup=BeautifulSoup(raw,'html.parser');host=urlparse(url).hostname;title=soup.h1.get_text(' ',strip=True) if soup.h1 else '';out={'url':url,'title':title}
    if host=='www.museunacional.cat':
        out['title']=(soup.title.get_text(' ',strip=True).split(' | ')[0] if soup.title else '')
        out['creators']=[x.get_text(' ',strip=True) for x in soup.select('.field-name-field-piece-authors-author .field-item')]
        features=[x.get_text(' ',strip=True) for x in soup.select('.ds-feature')]
        inventories=[x for x in features if re.match(r'^(?:Inventory number|Número d.inventari|Número de inventario):',x)]
        out['accession']=inventories[0].split(':',1)[1].strip() if len(inventories)==1 else None
        dates=[x for x in features if re.fullmatch(r'(?:c\.|Cap a|Hacia|Circa)?\s*\d{4}(?:\s*[-–]\s*\d{4})?',x)]
        out['date_display']=dates[0] if len(dates)==1 else None
        out['painting']=any(x.get_text(' ',strip=True) in ('Painting','Pintura') for x in soup.select('.ds-detail-tags a'))
    elif host=='www.museoreinasofia.es':
        fields={n.get_text(' ',strip=True):n.find_next_sibling('dd').get_text(' ',strip=True) for n in soup.select('dt') if n.find_next_sibling('dd')}
        out['accession']=fields.get('Registration number') or fields.get('Número de registro')
        out['date_display']=fields.get('Date') or fields.get('Fecha')
        out['medium']=fields.get('Technique') or fields.get('Técnica')
        # Confine attribution to artwork metadata, excluding related cards.
        out['creators']=[n.get_text(' ',strip=True) for n in soup.select('a') if '/collections/artist/' in n.get('href','') or '/colecciones/artista/' in n.get('href','')][:2]
        out['creators']+=list(dict.fromkeys(n.split('(',1)[0].strip() for n in out['creators'] if '(' in n))
        out['painting']=bool(re.search(r'\b(?:oil|óleo|tempera|témpera|acrylic|acrílico)\b',out.get('medium') or '',re.I))
    else:return None
    return out

def main():
    selected=r.load('selected-metadata-final-v2.json')['records'];valid={};held=[]
    for x in selected:
        if x.get('native_primary_validation'):valid[x['qid']]=x['native_primary_validation'];continue
        path=r.RUN/'primary-records'/(x['qid']+'.json')
        if not path.exists():continue
        record=json.loads(path.read_text())
        for page in record['captures']:
            receipt=page['receipt'];raw=(r.RUN/'primary-captures'/(hashlib.sha256(receipt['url'].encode()).hexdigest()+'.html')).read_bytes();assert r.core.sha(raw)==receipt['sha256']
            parsed=parse(raw,receipt['final_url'])
            if not parsed:continue
            names=[norm(t) for t in x['titles'] if len(norm(t))>=6]
            titlematch=bool(parsed['title'] and any(t in norm(parsed['title']) or norm(parsed['title']) in t for t in names))
            invmatch=bool(parsed.get('accession') and acc(parsed['accession']) in {acc(z) for z in x['accessions']})
            creatormatch=any(tokens(a)==tokens(b) or norm(a) in norm(b) and len(norm(a))>8 for a in parsed.get('creators',[]) for b in x['creator_names'])
            if not (invmatch and creatormatch and titlematch and parsed['painting']):
                held.append({'qid':x['qid'],'parsed':parsed,'title_match':titlematch,'inventory_match':invmatch,'creator_match':creatormatch});continue
            years=[int(y) for y in re.findall(r'(?<!\d)(?:1\d{3}|20\d{2})(?!\d)',parsed.get('date_display') or '')]
            conflicts=bool(years and x['date']['first'] is not None and (min(years)!=x['date']['first'] or max(years)!=x['date']['last']))
            valid[x['qid']]={'url':receipt['final_url'],'accession':parsed['accession'],'title':parsed['title'],'creators':parsed['creators'],'source_date_display':parsed.get('date_display'),'source_years':years,'date_differs_from_secondary':conflicts,'source_sha256':receipt['sha256'],'checked_at':receipt['retrieved_at'],'no_current_display_claim':True,'source_record_identity_verified':True}
    r.save('primary-validation.json',{'at':r.core.now(),'records':valid,'held':held,'policy':'Acceptance of collection connection requires exact accession plus creator/title/type from the technical object record. Dates and publication decisions are not changed by this validation.'});r.log('Primary technical records validated',len(valid),'held',len(held))

if __name__=='__main__':main()
