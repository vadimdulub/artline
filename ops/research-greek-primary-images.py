#!/usr/bin/env python3
"""Bounded Commons image research for exact primary Greek museum objects."""
import argparse,collections,hashlib,importlib.util,json,re,uuid
from pathlib import Path
from urllib.parse import urlencode,urlparse
from bs4 import BeautifulSoup
from PIL import Image,ImageDraw,ImageOps

s=importlib.util.spec_from_file_location('m',Path(__file__).with_name('apply-country-round.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
BASE=m.x.BASE/'greek-primary-catalogues';RUN=BASE/'commons-images';CORE=m.m.core
ORIGINALS=Path('/Users/vadimdulub/Library/Application Support/Artline/source-images/overnight-countries-20260913/greek-primary')
LICENSES={'Public domain':'public_domain','CC0':'cc0','CC BY 2.0':'cc_by','CC BY 3.0':'cc_by','CC BY 4.0':'cc_by','CC BY-SA 2.0':'cc_by_sa','CC BY-SA 2.5':'cc_by_sa','CC BY-SA 3.0':'cc_by_sa','CC BY-SA 4.0':'cc_by_sa'}
def plain(value):return BeautifulSoup(value or '','html.parser').get_text(' ',strip=True)
def acc(value):return value.upper().translate(str.maketrans('ΑΒΕΖΗΙΚΜΝΟΡΤΥΧ','ABEZHIKMNOPTYX'))
def accession_in_text(value,body):
    pattern=re.escape(acc(value)).replace(r'\.',r'[.\s]?').replace(r'\-',r'[-–\s]?')
    return bool(re.search(r'(?<![\w])'+pattern+r'(?![\w/])',acc(body)))

def search():
    targets=json.loads((BASE/'image-research-targets.json').read_text())['targets'];pages={}
    for start in range(0,len(targets),10):
        group=targets[start:start+10];path=RUN/'searches'/f'{start:04d}.json'
        if path.exists():result=json.loads(path.read_text())
        else:
            terms=sorted({v for t in group for v in (t['record']['accession'],acc(t['record']['accession']))})
            query=' OR '.join('"'+v+'"' for v in terms)
            data,receipt=m.x.r.fetch('https://commons.wikimedia.org/w/api.php?'+urlencode(dict(action='query',format='json',generator='search',gsrsearch=query,gsrnamespace=6,gsrlimit=50,prop='imageinfo|revisions',iiprop='url|extmetadata|sha1|size|mime',iiurlwidth=1280,rvprop='ids|content',rvslots='main',maxlag=5)))
            result=dict(query=query,targets=[t['artwork']['slug'] for t in group],data=data,receipt=receipt,truncated=bool(data.get('continue')));CORE.save_new(path,result)
        pages.update({k:dict(page=v,receipt=result['receipt']) for k,v in result['data'].get('query',{}).get('pages',{}).items()})
        print('Greek Commons accession research',min(start+10,len(targets)),'/',len(targets),'unique files',len(pages),flush=True)
    CORE.save_new(RUN/'search-results.json',dict(at=CORE.now(),pages=pages))

def select():
    targets=json.loads((BASE/'image-research-targets.json').read_text())['targets'];pages=json.loads((RUN/'search-results.json').read_text())['pages'];selected=[];holds=[]
    with m.m.r.base.connect(False) as db,db.transaction():
        db.execute('SET TRANSACTION READ ONLY');artists={a['slug']:a for a in m.artist_inventory(db)}
    names={slug:{a['display_name'],*a['aliases']} for slug,a in artists.items()}
    # Multilingual names are discovery aliases only. They do not establish a
    # new person or override the primary museum maker/object identity.
    for path in (m.x.BASE/'GR').glob('round-*/selected/*.json'):
        for w in json.loads(path.read_text())['selected']:
            aliases=m.m.r.labels(w['creator_entity']);keys={m.f.names.namekey(n) for n in aliases}
            for slug in {t['artist_slug'] for t in targets}:
                if keys & {m.f.names.namekey(n) for n in names[slug]}:names[slug].update(aliases)
    counts=collections.Counter()
    for t in sorted(targets,key=lambda t:(t['record']['artist']['birth_year'] is None,t['record']['artist']['birth_year'] or 0,t['artwork']['title'])):
        w=t['record'];artist=artists[t['artist_slug']];options=[]
        for item in pages.values():
            page=item['page'];info=page.get('imageinfo',[{}])[0];meta=info.get('extmetadata',{});field=lambda k:meta.get(k,{}).get('value','');markup=page.get('revisions',[{}])[0].get('slots',{}).get('main',{}).get('*','');body=markup+' '+json.dumps(meta,ensure_ascii=False)
            exact_url=w['source_url'] in body
            accession=accession_in_text(w['accession'],body)
            museum=bool(re.search(r'nationalgallery\.gr|National Gallery.{0,30}(?:Athens|Greece)|Εθνικ.{0,8}Πινακοθήκ|\bQ1167467\b',body,re.I))
            credit=plain(field('Artist'));name_match=m.f.names.namekey(credit) in {m.f.names.namekey(n) for n in names[t['artist_slug']]}
            if not exact_url and not(accession and museum and name_match):continue
            label=field('LicenseShortName')
            if label not in LICENSES or field('Restrictions') or (label=='Public domain' and field('Copyrighted')!='False'):continue
            if not credit or re.search(r'\b(detail|collage|montage)\b',page['title'],re.I):continue
            policy='https://creativecommons.org/publicdomain/mark/1.0/' if label=='Public domain' else field('LicenseUrl').replace('http://','https://')
            if not policy.startswith('https://creativecommons.org/'):continue
            if info.get('mime') not in ('image/jpeg','image/png','image/tiff'):continue
            options.append(dict(page=page,receipt=item['receipt'],info=info,label=label,policy=policy,credit=credit,proof=dict(exact_museum_object_url=exact_url,exact_inventory=accession,museum_context=museum,source_creator_name=name_match)))
        if not options:holds.append(dict(slug=t['artwork']['slug'],reason='No exact object/maker and per-file licensed Commons match'));continue
        if counts[t['artist_slug']]>=8:holds.append(dict(slug=t['artwork']['slug'],reason='Eight selected reproductions per painter cap'));continue
        options.sort(key=lambda x:(not x['proof']['exact_museum_object_url'],x['label'] not in ('Public domain','CC0'),-min(x['info']['width'],x['info']['height']),x['page']['title']))
        choice=options[0];counts[t['artist_slug']]+=1;selected.append(dict(target=t,choice=choice,alternative_files=[x['page']['title'] for x in options[1:]],identity_basis='Exact primary museum object URL cited by Commons, or independently matching museum inventory, museum context and creator name. Source museum maker/object link and date captured separately. Per-file Commons rights, not museum metadata licence.'))
    CORE.save_new(RUN/'selected.json',dict(at=CORE.now(),selected=selected,holds=holds,per_painter=dict(counts)));print('Greek Commons selected',len(selected),'held',len(holds),flush=True)

def prepare():
    selections=json.loads((RUN/'selected.json').read_text())['selected'];fetcher=CORE.Fetcher(RUN/'downloads');CORE.HOSTS.add('thumb.wikimedia.org');images=[]
    for s in selections:
        t=s['target'];w=t['record'];key=w['key'];dest=RUN/'prepared'/(key+'.json')
        if dest.exists():images.append(json.loads(dest.read_text()));continue
        choice=s['choice'];info=choice['info'];original=info['size']<=20_000_000 and info['width']*info['height']<=40_000_000;url=info['url'] if original else info.get('thumburl')
        assert url and urlparse(url).hostname in {'upload.wikimedia.org','thumb.wikimedia.org'}
        original_path=ORIGINALS/(key+('.original' if original else '.commons-thumbnail'));receipt_path=RUN/'download-receipts'/(key+'.json')
        if original_path.exists():raw=original_path.read_bytes();receipt=json.loads(receipt_path.read_text());assert CORE.sha(raw)==receipt['sha256']
        else:
            raw,headers=fetcher.get(url,20_000_000)
            if original:assert len(raw)==info['size'] and hashlib.sha1(raw).hexdigest()==info['sha1']
            receipt=dict(url=url,retrieved_at=CORE.now(),sha256=CORE.sha(raw),bytes=len(raw),kind='original' if original else 'source thumbnail',headers=headers);CORE.save_new(original_path,raw);CORE.save_new(receipt_path,receipt)
        encoded,width,height,quality=CORE.compress(raw);checksum=CORE.sha(encoded);path='/assets/artworks/imported/greek-primary/'+key+'-'+checksum[:16]+'.jpg';CORE.save_new(m.x.ROOT/'apps/web/public'/path.lstrip('/'),encoded)
        image=dict(key=key,artwork_id=t['artwork']['id'],artwork_slug=t['artwork']['slug'],title=w['title'],artist=w['artist']['display_name'],artist_slug=t['artist_slug'],path=path,sha256=checksum,bytes=len(encoded),width=width,height=height,quality=quality,media_id=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.local/greek-primary-image/'+key+'/'+checksum)),page=info['descriptionurl'],source_image_url=url,rights_status=LICENSES[choice['label']],license_label=choice['label'],license_url=choice['policy'],creator_credit=choice['credit'],attribution_text=f"{w['artist']['display_name']}. {w['title']}. Image credit: {choice['credit']}. {plain(info['extmetadata'].get('Attribution',{}).get('value',''))} Wikimedia Commons. {choice['label']} ({choice['policy']}). Full-frame resize and JPEG compression.",checked_at=CORE.now(),download=receipt,identity=s)
        CORE.save_new(dest,image);images.append(image);print('Greek primary image prepared',key,flush=True)
    cols=5;cellw=250;cellh=215;canvas=Image.new('RGB',(cols*cellw,max(1,(len(images)+cols-1)//cols)*cellh),'#f0eee9');draw=ImageDraw.Draw(canvas)
    for n,im in enumerate(images):
        with Image.open(m.x.ROOT/'apps/web/public'/im['path'].lstrip('/')) as source:tile=ImageOps.contain(source.convert('RGB'),(240,165));canvas.paste(tile,((n%cols)*cellw+(cellw-tile.width)//2,(n//cols)*cellh))
        draw.text(((n%cols)*cellw+5,(n//cols)*cellh+170),im['key'][:37],fill='#111111');draw.text(((n%cols)*cellw+5,(n//cols)*cellh+188),im['artist'][:32],fill='#111111')
    path=RUN/'contact-sheet.jpg';path.parent.mkdir(parents=True,exist_ok=True);canvas.save(path,quality=88)
    CORE.save_new(RUN/'preparation.json',dict(at=CORE.now(),images=len(images),contact_sheet_sha256=CORE.sha(path.read_bytes()),prepared_hashes={p.name:CORE.sha(p.read_bytes()) for p in (RUN/'prepared').glob('*.json')}));print('Greek image contact sheet ready for actual visual review',len(images),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['search','select','prepare']);a=p.parse_args();globals()[a.command]()
