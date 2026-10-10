#!/usr/bin/env python3
"""Resolve every indexed object supported by native museum adapters; read-only."""
import argparse,importlib.util,json,gzip,hashlib,re,requests,io,csv,threading,time
from pathlib import Path
from collections import defaultdict,Counter
from urllib.parse import urlsplit,unquote,urlencode,parse_qs
from concurrent.futures import ThreadPoolExecutor,as_completed
from bs4 import BeautifulSoup

s=importlib.util.spec_from_file_location('catalogue',Path(__file__).with_name('source-index-catalogue-20261010.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
s=importlib.util.spec_from_file_location('legacy',Path(__file__).with_name('source-index-native-20261009.py'));old=importlib.util.module_from_spec(s);s.loader.exec_module(old)
f=old.f; f.RUN=m.RUN
RUN=m.RUN; ROOT=m.ROOT; CACHE=Path.home()/'Library/Application Support/Artline/research'/m.OP
CC0='https://creativecommons.org/publicdomain/zero/1.0/';PDM='https://creativecommons.org/publicdomain/mark/1.0/'
IIDS={'smk':'ee9976cf-63a1-48f7-9e34-eb5444e0486c','cleveland':'729385eb-92b0-4cc8-9229-1ac3a46aee1f','mia':'9d7ff4ab-bbef-5ecc-836c-f7ed18b6bda9','walters':'d7fa70fa-a918-511f-8cc0-eeff020ceaea','moma':'038c9af4-f059-50ae-aae5-085fcabc8842'}
FNG_ORGS={'Kansallisgalleria / Ateneumin taidemuseo':'688a05df-a339-5dde-9fd0-4263559553f1','Kansallisgalleria / Sinebrychoffin taidemuseo':'6f2f70d1-457b-57b5-9f1a-ac72f1525524','Kansallisgalleria / Nykytaiteen museo Kiasma':'c7a61cfd-dea3-5890-b419-5782fee9b45f'}


def configure():
    RUN.mkdir(parents=True,exist_ok=True)
    m.save(RUN/'inherited-source-access-holds.json',m.load(m.PREVIOUS/'inherited-source-access-holds.json'))
    for p in (m.PREVIOUS/'access-holds').glob('*.json'):
        m.save(RUN/'access-holds'/('inherited-'+p.name),m.load(p))
    for p in m.PREVIOUS.glob('image-host-hold-*.json'):m.save(RUN/p.name,m.load(p))


def refs():
    found=defaultdict(lambda:defaultdict(list))
    patterns={'smk':r'/artwork/image/([^/?#]+)','fng':r'/object/(\d+)','mia':r'/art/(\d+)','moma':r'/collection/works/(\d+)','walters':r'/(?:art|object)/([\d.]+[A-Z]?)','cleveland':r'/art/([\d.]+[a-zA-Z]?)'}
    ledger=[]
    for r in m.resources():
        p=r['provider_id'];parts=urlsplit(r['url']);match=re.search(patterns.get(p,r'(?!)'),unquote(parts.path))
        key=match[1] if match else None
        if p=='smk' and parts.path.rstrip('/')=='/api/v1/art':
            values=parse_qs(parts.query).get('object_number',[])
            if len(values)==1 and ',' not in values[0]:key=values[0]
        if key:found[p][key].append(r)
        ledger.append(dict(source_index_id=r['id'],provider=p,object_reference=key,resolution='native_object' if key else 'other_provider_or_reference'))
    return found,ledger


def date_parse(text):
    text=' '.join(str(text or '').split()); x=re.fullmatch(r'(?:(?:c\.?|ca\.?|circa|about|Circa|Ca\.)\s*)?(\d{3,4})(?:\s*[-–—/]\s*(\d{3,4}))?',text)
    if x:
        lo=int(x[1]);hi=int(x[2] or x[1]);c=bool(re.match(r'(?:c|about)',text,re.I));return lo,hi,('circa' if lo==hi else 'circa_range') if c else ('exact' if lo==hi else 'range')
    x=re.fullmatch(r'(\d{1,2})(?:st|nd|rd|th) century',text,re.I)
    if x:return (int(x[1])-1)*100+1,int(x[1])*100,'century'
    return None,None,'unknown'


def type_for(labels,medium=''):
    text=' '.join(labels).casefold();med=medium.casefold()
    for kind,terms in [('painting',['painting','maleri','watercolor','akvarel']),('drawing',['drawing','tegning']),('print',['print','grafik','træsnit','radering','etching','lithograph','woodcut','engraving']),('icon',['icon painting'])]:
        if any(t in text for t in terms):return 'painting' if kind=='icon' else kind
    if not text or 'unknown' in text:
        if any(t in med for t in ['oil on','olie på','tempera on']):return 'painting'
    return None


def common(provider,o):
    if provider in ('smk','cleveland'):
        parsed=dict(o)
        if provider=='smk':parsed['titles']=[x for x in o.get('titles',[]) if isinstance(x.get('title'),str) and x['title'].strip()]
        v=old.native_fields(provider,parsed);v.update(institution_id=IIDS[provider],raw_creator_data=o.get('production',[]) if provider=='smk' else o.get('creators',[]),classification=o.get('object_names',[]) if provider=='smk' else [o.get('type','')],holding_qualified=bool(provider=='cleveland' and o.get('legal_status')!='accessioned'))
        labels=[x.get('name','') for x in o.get('object_names',[])] if provider=='smk' else [o.get('type','')]
        v['work_type']=type_for(labels,v.get('medium') or '')
        ds=v['dates'];lo,hi,pr=date_parse(ds.get('display'))
        v['date_precision']=pr if (lo,hi)==(ds['start'],ds['end']) else ('range' if ds['start'] is not None and ds['end'] is not None else 'unknown')
        if provider=='smk':
            v['creator_authorities']=[{'scheme':'smk-person','external_id':x.get('creator_lref'),'label':x.get('creator')} for x in o.get('production',[]) if x.get('creator_lref')]
        else:v['creator_authorities']=[{'scheme':'cleveland-creator','external_id':str(x['id']),'label':x.get('description')} for x in o.get('creators',[]) if x.get('id')]
        v['scheme']='smk-object' if provider=='smk' else 'cleveland-object'
        v['license_url']=PDM if provider=='smk' else CC0
        return v
    if provider=='mia':
        lo,hi,precision=date_parse(o.get('dated'));location=(o.get('Cache_Location') or '').replace('\\','/');rendition=o.get('Primary_RenditionNumber') or ''
        image='https://img.artsmia.org/web_objects_cache/'+location+'/'+rendition[:-4]+'_800.jpg' if re.fullmatch(r'\d+(?:/\d+)*',location) and location.split('/')[-1]==str(o['id']) and re.fullmatch(r'[A-Za-z0-9_-]+\.jpg',rendition) else None
        return dict(native_id=str(o['id']),scheme='mia-object',accession=o.get('accession_number'),titles=[o['title']],dates=dict(display=o.get('dated'),start=lo,end=hi),date_precision=precision,medium=o.get('medium'),dimensions=o.get('dimension'),page='https://collections.artsmia.org/art/'+str(o['id']),creator_labels=[o.get('artist')],creator_authorities=[],raw_creator_data=dict(artist=o.get('artist'),life_date=o.get('life_date'),nationality=o.get('nationality')),qualified_creators=[o.get('artist')] if re.search(r'\b(attributed|after|workshop|school|follower|circle|possibly|probably)\b',o.get('artist') or '',re.I) else [],image=image,image_rights=o.get('rights_type'),image_open=o.get('rights_type')=='Public Domain' and not o.get('restricted') and not o.get('image_copyright') and o.get('image')=='valid' and o.get('public_access')==1 and o.get('Rights_Image_Display')=='Full',license_url=PDM,credit=o.get('creditline'),institution_id=IIDS[provider],classification=o.get('classification'),work_type=type_for([o.get('classification','')],o.get('medium','')),holding_qualified=bool(re.search(r'\b(loan|lent by|private collection|deaccession)\b',o.get('creditline') or '',re.I)))
    if provider=='fng':
        people=[v for v in o.get('people',[]) if v.get('role',{}).get('en')=='Artist'];photos=[v for v in o.get('multimedia',[]) if v.get('isRiaDisplayImage')];photo=photos[0] if len(photos)==1 else {};im=photo.get('jpg',{}).get('1000');lo=o.get('yearFrom');hi=o.get('yearTo') or lo;prefix=(o.get('datePrefix') or {}).get('en');precision=('circa' if lo==hi else 'circa_range') if prefix=='circa' else ('exact' if lo==hi else 'range') if lo is not None and hi is not None and prefix in (None,'') else 'unknown';titles=[v for k,v in o.get('title',{}).items() if v]
        if o.get('title',{}).get('en'):titles=[o['title']['en']]+[x for x in titles if x!=o['title']['en']]
        medium='; '.join(x.get('en') or x.get('fi') or '' for x in o.get('materials',[]));labels=[x.get('en') or '' for x in o.get('classifications',[])]
        return dict(native_id=str(o['objectId']),scheme='fng-object',accession=o.get('inventoryNumber'),titles=titles,dates=dict(display=('circa ' if prefix=='circa' else (prefix+' ' if prefix else ''))+(str(lo) if lo==hi else str(lo)+'–'+str(hi)) if lo is not None else None,start=lo,end=hi),date_precision=precision,medium=medium,dimensions=None,page='https://kokoelma.kansallisgalleria.fi/en/object/'+str(o['objectId']),creator_labels=[' '.join(x.get(k) or '' for k in ['firstName','familyName']).strip() for x in people],creator_authorities=[dict(scheme='fng-person',external_id=str(x['id']),label=' '.join(x.get(k) or '' for k in ['firstName','familyName']).strip()) for x in people],raw_creator_data=people,qualified_creators=[x for x in people if x.get('attribution')],image='https://kokoelma.kansallisgalleria.fi'+im if im and re.fullmatch(r'/media-assets/\d+/jpg/1000/[\w.-]+',im) else None,image_rights=photo.get('license'),image_open=photo.get('license')=='CC0',license_url=CC0,credit='Finnish National Gallery'+('; photograph: '+photo['photographer_name'] if photo.get('photographer_name') else ''),institution_id=FNG_ORGS.get(o.get('responsibleOrganisation')),responsible_organisation=o.get('responsibleOrganisation'),owner=o.get('owner'),classification=labels,work_type=type_for(labels,medium),holding_qualified=not (o.get('owner') or '').startswith('Suomen valtio'),multipart=bool(o.get('children') or o.get('parents')))
    raise ValueError(provider)


def save_object(provider,key,obj,receipt,resources):
    dest=RUN/'native'/provider/(hashlib.sha256(key.encode()).hexdigest()+'.json.gz')
    if dest.exists():return
    facts=common(provider,obj)
    m.save(dest,dict(provider=provider,key=key,state='captured',facts=facts,raw=obj,receipt=receipt,source_index_ids=[x['id'] for x in resources],index_bindings=[b for x in resources for b in x['artline_bindings']]))


def smk(targets):
    keys=sorted(targets)
    for off in range(0,len(keys),35):
        batch=keys[off:off+35]
        if all((RUN/'native/smk'/(hashlib.sha256(k.encode()).hexdigest()+'.json.gz')).exists() for k in batch):continue
        url='https://api.smk.dk/api/v1/art?'+urlencode({'object_number':','.join(batch)})
        try:
            data,rc=f.get(url,True);found={o['object_number']:o for o in data['items']}
            for key in batch:
                if key in found:
                    try:save_object('smk',key,found[key],rc,targets[key])
                    except Exception as e:m.save(RUN/'native-holds/smk'/('parse-'+hashlib.sha256(key.encode()).hexdigest()+'.json'),dict(key=key,error=repr(e),receipt=rc))
                else:m.save(RUN/'native-holds/smk'/(hashlib.sha256(key.encode()).hexdigest()+'.json'),dict(key=key,reason='Object missing from exact native batch response',receipt=rc))
        except Exception as e:
            m.save(RUN/'native-holds/smk'/('batch-v2-'+hashlib.sha256(','.join(batch).encode()).hexdigest()+'.json'),dict(keys=batch,error=repr(e)))
        print('SMK native objects',min(off+35,len(keys)),'/',len(keys),flush=True)


def individual(provider,targets):
    for n,(key,rr) in enumerate(sorted(targets.items()),1):
        dest=RUN/'native'/provider/(hashlib.sha256(key.encode()).hexdigest()+'.json.gz');hold=RUN/'native-holds'/provider/(hashlib.sha256(key.encode()).hexdigest()+'.json')
        if dest.exists() or hold.exists():continue
        try:
            if provider=='mia':url='https://search.artsmia.org/id/'+key
            else:url='https://openaccess-api.clevelandart.org/api/artworks/?'+urlencode({'accession_number':key,'limit':3})
            data,rc=f.get(url,True)
            if provider=='mia':obj=data;assert str(obj['id'])==key
            else:
                assert len(data['data'])==1;obj=data['data'][0];assert obj['accession_number']==key
            save_object(provider,key,obj,rc,rr)
        except Exception as e:m.save(hold,dict(key=key,source_index_ids=[v['id'] for v in rr],error=repr(e)))
        if n%50==0:print(provider,'native objects',n,'/',len(targets),flush=True)


def fng(targets):
    import ijson
    url='https://kokoelma.kansallisgalleria.fi/api/v1/objects';path=CACHE/'fng-objects.json';receipt=RUN/'datasets/fng-export-receipt.json';CACHE.mkdir(parents=True,exist_ok=True)
    if not receipt.exists():
        with requests.get(url,headers={'User-Agent':f.UA},timeout=(15,120),stream=True) as response:
            response.raise_for_status();assert 'application/json' in response.headers.get('Content-Type','')
            hasher=hashlib.sha256();size=0;temp=path.with_suffix('.part')
            with temp.open('wb') as out:
                for chunk in response.iter_content(262144):
                    size+=len(chunk);assert size<800_000_000;hasher.update(chunk);out.write(chunk)
            temp.replace(path)
            m.save(receipt,dict(url=url,retrieved_at=m.now(),path=str(path),bytes=size,sha256=hasher.hexdigest(),http_status=response.status_code))
    rc=m.load(receipt)
    assert m.m.sha(path)==rc['sha256']
    found=set()
    with path.open('rb') as stream:
        for o in ijson.items(stream,'item',use_float=True):
            key=str(o['objectId'])
            if key in targets:save_object('fng',key,o,rc,targets[key]);found.add(key)
    for key in set(targets)-found:m.save(RUN/'native-holds/fng'/(hashlib.sha256(key.encode()).hexdigest()+'.json'),dict(key=key,reason='Indexed object absent from current official public export',receipt=rc))
    print('FNG native objects',len(found),'/',len(targets),flush=True)


def run(providers):
    configure();rr,ledger=refs();m.save(RUN/'native-resource-resolution-v2.json.gz',ledger)
    print('Selected native objects',dict((k,len(v)) for k,v in rr.items()),flush=True)
    with ThreadPoolExecutor(max_workers=4) as pool:
        fs={pool.submit(smk if p=='smk' else fng if p=='fng' else lambda rows,p=p:individual(p,rows),rr[p]):p for p in providers}
        for job in as_completed(fs):
            p=fs[job]
            try:job.result();print('Completed native metadata',p,flush=True)
            except Exception as e:print('Provider error',p,repr(e),flush=True);m.save(RUN/'native-holds'/(p+'-run.json'),dict(provider=p,error=repr(e),at=m.now()))
    print('Native captured',dict(Counter(p.parent.name for p in (RUN/'native').glob('*/*.json.gz'))),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['fetch']);p.add_argument('--providers',nargs='+',default=['smk','fng','mia','cleveland']);a=p.parse_args();run(a.providers)
