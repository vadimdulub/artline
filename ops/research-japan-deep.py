#!/usr/bin/env python3
"""Bounded Japanese painting research from the Met Open Access collection."""
import argparse, concurrent.futures, hashlib, json, re, time
from pathlib import Path
from urllib.parse import urlencode
import requests

ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'docs/research/japan-deep-20260917'
API='https://collectionapi.metmuseum.org/public/collection/v1'
QUERIES=['hanging scroll','handscroll','folding screen','Japanese painting','fan painting']
PAINT_OBJECTS=re.compile(r'(?:painting|hanging scroll|handscroll|screen|album|fan)',re.I)

def now():return time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
def sha(b):return hashlib.sha256(b).hexdigest()
def save_new(path,data):
    path.parent.mkdir(parents=True,exist_ok=True);raw=data if isinstance(data,bytes) else json.dumps(data,ensure_ascii=False,sort_keys=True,indent=2).encode()
    if path.exists():
        if path.read_bytes()!=raw:raise ValueError('Immutable evidence differs: '+str(path))
    else:path.write_bytes(raw)
def get(url,params=None):
    for attempt in range(6):
        try:res=requests.get(url,params=params,headers={'User-Agent':'Artline/1.0 selected museum collection research'},timeout=(10,45))
        except requests.RequestException:
            if attempt==5:raise
            time.sleep(min(60,5*(attempt+1)));continue
        if res.status_code not in (403,429,500,502,503):res.raise_for_status();return res
        time.sleep(min(60,5*(attempt+1)))
    res.raise_for_status()

def discover():
    ids=set();receipts=[]
    for q in QUERIES:
        res=get(API+'/search',{'q':q,'hasImages':'true'});raw=res.content;data=res.json()
        save_new(RUN/'met/search'/f'{sha(q.encode())[:16]}.json',raw)
        receipts.append({'query':q,'url':res.url,'retrieved_at':now(),'sha256':sha(raw),'count':data.get('total')})
        ids.update(data.get('objectIDs') or [])
    save_new(RUN/'met-search-index-v2.json',{'queries':receipts,'unique_object_ids':sorted(ids),'count':len(ids),'bounded_method':'Union of five format-oriented Met search queries; two overbroad exploratory queries are retained in the earlier index but explicitly excluded before further requests.'})
    print('unique leads',len(ids))

def fetch_one(oid):
    path=RUN/'met/objects'/f'{oid}.json'
    if path.exists():return json.loads(path.read_text())
    try:res=get(API+f'/objects/{oid}')
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code==404:
            row={'objectID':oid,'unavailable':404};save_new(path,row);return row
        raise
    save_new(path,res.content);return res.json()

def objects():
    ids=json.loads((RUN/'met-search-index-v2.json').read_text())['unique_object_ids'];out=[]
    for start in range(0,len(ids),40):
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
            out.extend(ex.map(fetch_one,ids[start:start+40]))
        print('objects',min(start+40,len(ids)),'/',len(ids),flush=True);time.sleep(1.1)
    save_new(RUN/'met-object-index.json',{'ids':[x.get('objectID') for x in out],'count':len(out),'retrieved_at':now()})

def select():
    records=[];held=[]
    for p in sorted((RUN/'met/objects').glob('*.json')):
        x=json.loads(p.read_text());reason=None
        culture=' '.join(str(x.get(k) or '') for k in ('culture','country','period'))
        artist=str(x.get('artistDisplayName') or '').strip();qid=(x.get('artistWikidata_URL') or '').rstrip('/').split('/')[-1]
        if x.get('department')!='Asian Art' or not re.search(r'Japan',culture,re.I):reason='Not explicitly Japanese in the museum record'
        elif x.get('classification')!='Paintings' or not PAINT_OBJECTS.search(str(x.get('objectName') or '')):reason='Not a museum-classified painting in a selected painted-work format'
        elif not artist or re.search(r'unknown|anonymous|unidentified|workshop|school of|attributed',artist,re.I):reason='Anonymous, unknown, or held attribution excluded from this named-creator import'
        elif not re.fullmatch(r'Q\d+',qid):reason='Named creator lacks exact authority crosswalk'
        elif not re.search(r'\bJapanese\b',str(x.get('artistDisplayBio') or ''),re.I):reason='Museum creator biography does not explicitly identify Japanese context'
        elif not isinstance(x.get('objectEndDate'),int) or x['objectEndDate']>1970:reason='Date unknown, crosses cutoff, or after 1970'
        elif not x.get('isPublicDomain') or not x.get('primaryImage'):reason='No Met public-domain primary image'
        if reason:held.append({'object_id':x.get('objectID'),'title':x.get('title'),'reason':reason});continue
        records.append({'source':'Metropolitan Museum of Art Open Access API','source_url':x['objectURL'],'api_url':API+f"/objects/{x['objectID']}",'object_id':str(x['objectID']),'accession':x.get('accessionNumber'),'title':x.get('title') or 'Title not recorded','object_name':x.get('objectName'),'culture':x.get('culture'),'period':x.get('period'),'date_display':x.get('objectDate'),'year_start':x.get('objectBeginDate'),'year_end':x.get('objectEndDate'),'artist_name':artist,'artist_qid':qid,'artist_begin':int(x['artistBeginDate']) if str(x.get('artistBeginDate') or '').lstrip('-').isdigit() else None,'artist_end':int(x['artistEndDate']) if str(x.get('artistEndDate') or '').lstrip('-').isdigit() else None,'artist_role':x.get('artistRole'),'institution':'The Metropolitan Museum of Art','institution_qid':'Q160236','image_url':x['primaryImage'],'image_small':x.get('primaryImageSmall'),'rights':x.get('rightsAndReproduction'),'credit_line':x.get('creditLine'),'repository_receipt':str(p.relative_to(ROOT))})
    # Exact accessions and object IDs are physical-object keys. Cap at 12 per
    # creator to preserve breadth before any image transfer.
    records.sort(key=lambda x:(x['artist_name'],x['year_start'],int(x['object_id'])))
    counts={};selected=[]
    for x in records:
        n=counts.get(x['artist_qid'],0)
        if n>=12:held.append({'object_id':x['object_id'],'title':x['title'],'reason':'Outside bounded twelve-work-per-creator selection'});continue
        counts[x['artist_qid']]=n+1;selected.append(x)
    save_new(RUN/'selected-met-records.json',{'records':selected,'held':held,'selected':len(selected),'creators':len(counts),'selection_at':now(),'rules':['Named creator with exact authority crosswalk','Met explicitly identifies Japanese context and a painted-work format','Known museum date ends by 1970','Met marks object public domain and supplies a primary image','At most twelve objects per creator']})
    print('selected',len(selected),'creators',len(counts),'held',len(held))

def authorities():
    rows=json.loads((RUN/'selected-met-records.json').read_text())['records'];qids=sorted({x['artist_qid'] for x in rows})
    res=get('https://www.wikidata.org/w/api.php',{'action':'wbgetentities','ids':'|'.join(qids),'props':'labels|aliases|claims|descriptions','languages':'en|ja|mul','format':'json','maxlag':5});raw=res.content;save_new(RUN/'artist-authorities-response.json',raw)
    data=res.json()['entities'];out=[]
    def ids(e,p):
        return [v['mainsnak']['datavalue']['value']['id'] for v in e.get('claims',{}).get(p,[]) if v.get('rank')!='deprecated' and v.get('mainsnak',{}).get('datavalue',{}).get('type')=='wikibase-entityid']
    def year(e,p):
        vals=[]
        for v in e.get('claims',{}).get(p,[]):
            try:vals.append(int(v['mainsnak']['datavalue']['value']['time'][1:5]))
            except (KeyError,ValueError,TypeError):pass
        return vals[0] if len(set(vals))==1 else None
    for q in qids:
        e=data[q];samples=[x for x in rows if x['artist_qid']==q];names={x['artist_name'] for x in samples};labels=[v['value'] for v in e.get('labels',{}).values()]
        if 'Q5' not in ids(e,'P31'):raise ValueError(q+' is not a human authority')
        out.append({'qid':q,'name':e.get('labels',{}).get('en',e.get('labels',{}).get('mul',{})).get('value') or sorted(names)[0],'source_names':sorted(names),'labels':labels,'birth':year(e,'P569') or samples[0]['artist_begin'],'death':year(e,'P570') or samples[0]['artist_end'],'countries':ids(e,'P27'),'occupations':ids(e,'P106'),'entity':e})
    save_new(RUN/'artist-authorities.json',{'records':out,'receipt':{'url':res.url,'retrieved_at':now(),'sha256':sha(raw)},'validation':'Every selected creator is a Wikidata human and the Met supplies the exact creator crosswalk plus an explicit Japanese biography.'});print('authorities',len(out))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['discover','objects','select','authorities']);a=p.parse_args();globals()[a.phase]()
