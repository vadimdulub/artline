#!/usr/bin/env python3
"""Selected Commons reproductions corroborated against primary museum objects."""
import argparse,hashlib,importlib.util,io,json,re,os
from pathlib import Path
from urllib.parse import urlencode,urlparse
from PIL import Image,ImageOps,ImageDraw
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('apply-country-round.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
C=m.m.core
FAMILY=os.environ.get('ARTLINE_COMMONS_PRIMARY_FAMILY','nationalmuseum')
assert FAMILY in ('nationalmuseum','polish','norwegian')
PRIMARY_REVIEWS={'nationalmuseum':'nationalmuseum-primary-v2-review.json','polish':'polish-primary-v2-review.json','norwegian':'norwegian-primary-review.json'}

def prepare(code,number):
    delivery=m.x.BASE/code/f'round-{number:02d}'/'delivery';run=delivery/('primary-images-'+FAMILY+'-commons')
    if (run/'preparation.json').exists():return
    assert (delivery/'verification.json').exists()
    reviewed=json.loads((delivery/PRIMARY_REVIEWS[FAMILY]).read_text())['records'];qa=json.loads((delivery/'quality-review.json').read_text());selected=[]
    for e in reviewed:
        q=e['qid'];paths=[delivery/'applied'/t/(q+'.json') for t in ('local','production')]
        if e['review']!='primary_object_and_creator_corroborated' or not all(p.exists() for p in paths):continue
        if any(json.loads(p.read_text())['image_attached'] for p in paths):continue
        ready=json.loads((delivery/'ready'/(q+'.json')).read_text());record=ready['record'];record.update({k:v for k,v in qa.get('metadata_overrides',{}).get(q,{}).items() if k in ('date','title','work_type')})
        if not record['date']['eligible'] or q in qa.get('held_images',{}):continue
        selected.append((e,record))
    assert len(selected)<=80
    fetcher=C.Fetcher(run/'captures');fetcher.session.headers['User-Agent']=m.x.r.SESSION.headers['User-Agent'];C.HOSTS.add('thumb.wikimedia.org');images=[];holds=[]
    for e,record in selected:
        q=record['qid'];output=run/'prepared'/(q+'.json')
        if output.exists():images.append(json.loads(output.read_text()));continue
        try:
            filename=record['images'][0];assert not re.search(r'\b(detail|collage|montage)\b',filename,re.I)
            data,receipt=m.x.r.fetch('https://commons.wikimedia.org/w/api.php?'+urlencode({'action':'query','format':'json','titles':'File:'+filename,'prop':'imageinfo|revisions','iiprop':'url|extmetadata|sha1|size|mime','iiurlwidth':1280,'rvprop':'ids|content','rvslots':'main','maxlag':5}))
            pages=list(data['query']['pages'].values());assert len(pages)==1;page=pages[0];info=page['imageinfo'][0];meta=info['extmetadata'];field=lambda k:meta.get(k,{}).get('value','')
            assert field('LicenseShortName')=='Public domain' and field('Copyrighted')=='False' and not field('Restrictions'),'Per-file rights need individual review'
            markup=page.get('revisions',[{}])[0].get('slots',{}).get('main',{}).get('*','');m.image_review.check_rights_chronology(record,'Public domain',markup)
            # Rendered Artwork templates can supply the exact identity even
            # when the raw file wikitext contains only {{Artwork}}.
            html=field('ObjectName');linked=bool(re.search(r'https?://www\.wikidata\.org/(?:wiki|entity)/'+re.escape(q)+r'(?:[#"/])',html))
            accession=record['accession'];filename_match=bool(accession and m.x.r.norm(accession) in m.x.r.norm(filename))
            if FAMILY=='nationalmuseum':
                assert linked and filename_match,'Rendered object identity and filename accession must both match the exact primary museum record'
                identity_basis='Exact primary museum maker/inventory, Wikidata P18, rendered Commons object QID and filename inventory.'
            else:
                linked_qids=set(re.findall(r'https?://www\.wikidata\.org/(?:wiki|entity)/(Q\d+)(?=[#"/])',html))
                assert not linked_qids or q in linked_qids,'Conflicting rendered Commons object identity'
                artist_html=field('Artist');cq=record['creator_qid']
                artist_link=bool(re.search(r'(?:/wiki/|/entity/|P170[,|])'+re.escape(cq)+r'(?=[#"/\s|,}])',artist_html+' '+markup))
                name_match=any(m.x.r.norm(n) in m.x.r.norm(filename) for n in m.x.r.labels(record['creator_entity']) if len(m.x.r.norm(n).split())>=2)
                assert filename_match and (linked or artist_link or name_match),'Exact primary inventory plus corroborated Commons object/creator identity required'
                identity_basis='Exact primary museum maker and inventory, source P18, exact filename inventory and corroborated rendered object/creator ID or full creator filename. No conflicting rendered object QID.'
            credit=m.image_review.image_credit(meta);original=info['size']<=10_000_000 and info['width']*info['height']<=40_000_000;url=info['url'] if original else info.get('thumburl');assert urlparse(url).hostname in ('upload.wikimedia.org','thumb.wikimedia.org')
            archive=Path('/Users/vadimdulub/Library/Application Support/Artline/source-images')/m.x.SESSION_NAME/m.x.CAMPAIGN/code/f'round-{number:02d}'/(FAMILY+'-commons')/(q+'.original');rp=run/'downloads'/(q+'.json')
            if archive.exists():raw=archive.read_bytes();download=json.loads(rp.read_text());assert C.sha(raw)==download['sha256']
            else:
                raw,headers=fetcher.get(url,10_000_000)
                if original:assert hashlib.sha1(raw).hexdigest()==info['sha1'] and len(raw)==info['size']
                download={'url':url,'retrieved_at':C.now(),'sha256':C.sha(raw),'bytes':len(raw),'original':original,'sha1':info['sha1'],'headers':headers};C.save_new(archive,raw);C.save_new(rp,download)
            encoded,w,h,quality=C.compress(raw);sha=C.sha(encoded);path='/assets/artworks/imported/'+m.x.SESSION_NAME+'/'+FAMILY+'/'+q.lower()+'-'+sha[:16]+'.jpg';C.save_new(m.x.ROOT/'apps/web/public'/path.lstrip('/'),encoded)
            lic='https://creativecommons.org/publicdomain/mark/1.0/';im={'key':q,'media_id':m.m.uid(m.x.SESSION_NAME+'/nationalmuseum-commons/'+q+'/'+sha),'path':path,'sha256':sha,'bytes':len(encoded),'width':w,'height':h,'quality':quality,'title':record['title'],'artist':record['creator_label'],'page':info['descriptionurl'],'provider_name':'Wikimedia Commons / Nationalmuseum','source_slug':m.x.SESSION_NAME+'-nationalmuseum-commons-images','source_name':'Nationalmuseum selected reproductions via Wikimedia Commons','source_root':'https://commons.wikimedia.org/','source_image_url':url,'rights_status':'public_domain','license_label':'Public domain','license_url':lic,'creator_credit':credit,'attribution_text':record['title']+'. '+credit+'. Wikimedia Commons. Public domain ('+lic+'). Full-frame resize and JPEG compression.','download':download,'checked_at':C.now(),'adapter_version':'nationalmuseum-commons-primary-v1','identity':{'choice':{'page':{'title':accession},'receipt':receipt},'identity_basis':'Exact museum object accession and maker authority, Wikidata P18, rendered Commons object QID and filename accession independently cross-checked. Per-file Commons rights/creator chronology checked. No current-display assertion.','primary':e,'commons_page':page,'commons_receipt':receipt}}
            if FAMILY!='nationalmuseum':
                institution=record['collection']['institution']['name']
                im.update(media_id=m.m.uid(m.x.SESSION_NAME+'/'+FAMILY+'-commons/'+q+'/'+sha),provider_name='Wikimedia Commons / '+institution,source_slug=m.x.SESSION_NAME+'-'+FAMILY+'-commons-images',source_name='Selected '+FAMILY+' museum reproductions via Wikimedia Commons',adapter_version=FAMILY+'-commons-primary-v1')
                im['identity']['identity_basis']=identity_basis+' Per-file rights and creator chronology reviewed. No display assertion.'
            C.save_new(output,im);images.append(im);print(code,number,FAMILY,'Commons image',q,flush=True)
        except (AssertionError,ValueError,RuntimeError,m.x.r.requests.RequestException) as error:holds.append({'qid':q,'reason':str(error)[:400]});print(q,'image held',str(error)[:180],flush=True)
    canvas=Image.new('RGB',(1250,max(1,(len(images)+4)//5)*220),'#f0eee9');draw=ImageDraw.Draw(canvas)
    for i,im in enumerate(images):
        with Image.open(m.x.ROOT/'apps/web/public'/im['path'].lstrip('/')) as photo:tile=ImageOps.contain(photo.convert('RGB'),(240,170));left=i%5*250;top=i//5*220;canvas.paste(tile,(left+(250-tile.width)//2,top));draw.text((left+5,top+176),im['key']+' '+im['artist'][:21],fill='black');draw.text((left+5,top+195),im['title'][:35],fill='black')
    sheet=run/'contact-sheet.jpg';sheet.parent.mkdir(parents=True,exist_ok=True);canvas.save(sheet,quality=90)
    C.save_new(run/'preparation.json',{'at':C.now(),'selected_qids':[e['qid'] for e,r in selected],'images':len(images),'holds':holds,'contact_sheet_sha256':C.sha(sheet.read_bytes()),'prepared_hashes':{p.name:C.sha(p.read_bytes()) for p in (run/'prepared').glob('*.json')}});print(code,number,'additional images ready for actual review',len(images),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--country',required=True,choices=m.x.COUNTRIES);p.add_argument('--round',required=True,type=int);a=p.parse_args();prepare(a.country,a.round)
