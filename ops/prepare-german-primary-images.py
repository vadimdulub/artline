#!/usr/bin/env python3
"""Prepare bounded, licensed museum reproductions for already-imported objects."""
import argparse,importlib.util,io,json,os,re
from pathlib import Path
from urllib.parse import urlparse
import requests
from PIL import Image,ImageOps,ImageDraw
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('apply-country-round.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
CORE=m.m.core
PROVIDER=os.environ.get('ARTLINE_PRIMARY_PROVIDER','german');assert PROVIDER in ('german','nationalmuseum','german-reviewed-v2')

def prepare(code,number):
    delivery=m.x.BASE/code/f'round-{number:02d}'/'delivery';run=delivery/('primary-images' if PROVIDER=='german' else 'primary-images-'+PROVIDER)
    if (run/'preparation.json').exists():return
    review=json.loads((delivery/('nationalmuseum-primary-v2-review.json' if PROVIDER=='nationalmuseum' else 'german-primary-review.json')).read_text());selected=[]
    for e in review['records']:
        q=e['qid']
        if PROVIDER=='german-reviewed-v2' and not e.get('eligible_for_selected_image'):
            qa=json.loads((delivery/'quality-review.json').read_text());override=qa.get('metadata_overrides',{}).get(q,{})
            date=override.get('date',{});source_date=e.get('object',{}).get('date','')
            if qa.get('approved') and e.get('creator_match') and e.get('accession_match') and e.get('image_rights_corroborated') and re.fullmatch(r'\d{4}',source_date) and date.get('eligible') and date.get('first')==date.get('last')==int(source_date):
                proof=delivery/override['evidence_file'];assert CORE.sha(proof.read_bytes())==override['evidence_sha256']
                e={**e,'eligible_for_selected_image':True,'date_match':True,'reviewed_date_override':override,'prior_review_preserved':'Original source review remains immutable; exact museum date was separately approved during core QA.'}
        if not e.get('eligible_for_selected_image'):continue
        receipts=[delivery/'applied'/t/(q+'.json') for t in ('local','production')]
        if PROVIDER=='german-reviewed-v2':
            # Preparation may precede serial delivery. Application still requires
            # both real import receipts and a fresh no-image database preflight.
            qa=json.loads((delivery/'quality-review.json').read_text());assert qa['approved']
            if q in qa.get('held_records',{}) or q in qa.get('held_images',{}):continue
            ready=json.loads((delivery/'ready'/(q+'.json')).read_text())
            if ready.get('image'):continue
            assert e['review']=='primary_object_and_creator_corroborated'
        elif not all(p.exists() for p in receipts):continue
        if any(p.exists() and json.loads(p.read_text())['image_attached'] for p in receipts):continue
        selected.append(e)
    assert len(selected)<=80
    selection_path=run/'selected.json'
    if selection_path.exists():
        saved=json.loads(selection_path.read_text());assert saved['selected']==selected
    else:CORE.save_new(selection_path,{'at':CORE.now(),'selected':selected,'selection_basis':'Reviewed country-round metadata with exact primary museum accession/maker, compatible pre-1971 source dating and museum rights evidence. Versioned preparation may precede serial delivery; attachment requires both actual import receipts and a fresh no-image database preflight.'})
    images=[]
    for e in selected:
        q=e['qid'];dest=run/'prepared'/(q+'.json')
        if dest.exists():images.append(json.loads(dest.read_text()));continue
        record=json.loads((delivery/'ready'/(q+'.json')).read_text())['record'];obj=e['object'];url=obj['image_url']
        qa=json.loads((delivery/'quality-review.json').read_text());record.update({k:v for k,v in qa.get('metadata_overrides',{}).get(q,{}).items() if k in ('date','title','work_type')})
        if not record['date']['eligible']:continue
        assert urlparse(url).scheme=='https' and urlparse(url).hostname in ('cdn.staedelmuseum.de','www.kunsthalle-karlsruhe.de','collection.nationalmuseum.se')
        original=Path('/Users/vadimdulub/Library/Application Support/Artline/source-images')/m.x.SESSION_NAME/m.x.CAMPAIGN/code/f'round-{number:02d}'/'primary'/(q+'.jpg');rp=run/'downloads'/(q+'.json')
        if original.exists():
            raw=original.read_bytes();receipt=json.loads(rp.read_text());assert CORE.sha(raw)==receipt['sha256']
        else:
            response=requests.get(url,timeout=(15,60));response.raise_for_status()
            resolution=None
            if response.headers.get('Content-Type','').startswith('application/json'):
                resolved=response.json();assert isinstance(resolved,str) and resolved.startswith('https://www.kunsthalle-karlsruhe.de/wp-content/kunstwerk/highres/')
                resolution={'url':response.url,'sha256':CORE.sha(response.content),'resolved_image_url':resolved,'retrieved_at':CORE.now()}
                response=requests.get(resolved,timeout=(15,60));response.raise_for_status()
            raw=response.content;assert len(raw)<10_000_000
            with Image.open(io.BytesIO(raw)) as photo:assert photo.format=='JPEG';photo.verify()
            receipt={'url':response.url,'retrieved_at':CORE.now(),'sha256':CORE.sha(raw),'bytes':len(raw),'status':response.status_code,'content_type':response.headers.get('Content-Type'),'resolution':resolution};CORE.save_new(original,raw);CORE.save_new(rp,receipt)
        encoded,w,h,quality=CORE.compress(raw);sha=CORE.sha(encoded);path='/assets/artworks/imported/'+m.x.SESSION_NAME+'/'+e['museum']+'/'+q.lower()+'-'+sha[:16]+'.jpg';CORE.save_new(m.x.ROOT/'apps/web/public'/path.lstrip('/'),encoded)
        cc0=e['museum']=='karlsruhe';lic='https://creativecommons.org/publicdomain/zero/1.0/' if cc0 else 'https://creativecommons.org/publicdomain/mark/1.0/';label='CC0' if cc0 else 'Public domain';credit=record['creator_label']+'; '+obj['credit']
        im={'key':q,'media_id':m.m.uid(m.x.SESSION_NAME+'/primary-image/'+q+'/'+sha),'path':path,'sha256':sha,'bytes':len(encoded),'width':w,'height':h,'quality':quality,'title':record['title'],'artist':record['creator_label'],'page':e['receipt']['url'],'provider_name':obj['credit'],'source_slug':m.x.SESSION_NAME+'-'+e['museum']+'-images','source_name':obj['credit']+' — selected museum reproductions','source_root':'https://'+urlparse(e['receipt']['url']).hostname+'/','source_image_url':url,'rights_status':'cc0' if cc0 else 'public_domain','license_label':label,'license_url':lic,'creator_credit':credit,'attribution_text':record['title']+'. '+credit+'. '+label+' ('+lic+'). Full-frame resize and JPEG compression.','download':receipt,'checked_at':CORE.now(),'adapter_version':PROVIDER+'-primary-images-v1','identity':{'choice':{'page':{'title':obj['accession']},'receipt':e['receipt']},'identity_basis':e['rights_basis']+' Primary museum accession and maker match; compatible source creation dating. No current-display assertion.','primary':e}}
        CORE.save_new(dest,im);images.append(im);print(code,number,'primary image prepared',q,flush=True)
    canvas=Image.new('RGB',(1250,max(1,(len(images)+4)//5)*220),'#f0eee9');draw=ImageDraw.Draw(canvas)
    for i,im in enumerate(images):
        with Image.open(m.x.ROOT/'apps/web/public'/im['path'].lstrip('/')) as photo:tile=ImageOps.contain(photo.convert('RGB'),(240,170));left=i%5*250;top=i//5*220;canvas.paste(tile,(left+(250-tile.width)//2,top));draw.text((left+5,top+176),im['key']+' '+im['artist'][:21],fill='black');draw.text((left+5,top+195),im['title'][:35],fill='black')
    sheet=run/'contact-sheet.jpg';sheet.parent.mkdir(parents=True,exist_ok=True);canvas.save(sheet,quality=90)
    CORE.save_new(run/'preparation.json',{'at':CORE.now(),'images':len(images),'contact_sheet_sha256':CORE.sha(sheet.read_bytes()),'prepared_hashes':{p.name:CORE.sha(p.read_bytes()) for p in (run/'prepared').glob('*.json')}});print(code,number,'primary images ready for actual visual review',len(images),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--country',default='DE',choices=m.x.COUNTRIES);p.add_argument('--round',type=int,required=True);a=p.parse_args();assert 1<=a.round<=20;prepare(a.country,a.round)
