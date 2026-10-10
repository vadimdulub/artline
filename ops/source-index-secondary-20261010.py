#!/usr/bin/env python3
"""Normalize fresh exact-object pages for additional source-backed image delivery."""
import importlib.util,json,re,gzip,hashlib,argparse
from pathlib import Path
from urllib.parse import urlsplit,urljoin,parse_qs
from collections import defaultdict,Counter
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('resolution',Path(__file__).with_name('source-index-resolve-20261010.py'));r=importlib.util.module_from_spec(s);s.loader.exec_module(r);m=r.m;n=r.n;RUN=r.RUN
PROVIDERS={'getty','russian-museum','rijksmuseum','saam','wikiart','domain:collection.pushkinmuseum.art','goulandris','benaki','domain:ebyzantinemuseum.gr','leventis','krakow','domain:api-zbiory.mnk.pl','domain:cyfrowe-api.mnw.art.pl','nationalmuseum','domain:digitalarchive.npm.gov.tw'}
PROVIDERS.update({'chicago','byzantine-thessaloniki'})
# Individually read native creation statements; historical events and acquisition dates excluded.
BXM_DATES={
 '247':('signed and dated in 1666',1666,1666),'251':('workshop of the beginning of the 17th century',1601,1700),
 '229':('dating from about the middle of the 15th c.',1401,1500),'26':('Painted by Defterevon Sifnios. 1825.',1825,1825),
 '218':('Chronology: 2nd half of `17th c.',1651,1700),'232':('This 14th century bilateral icon',1301,1400),
 '67':('Saint Nicholas enthroned, dated in 17th c.',1601,1700),'110':('dated by inscription to 1233/1234',1233,1234),
 '12':('Painting with the Last Judgment, September 15, 1855.',1855,1855),'228':('dated to the first half of the 15th century',1401,1450),
 '227':('dated to the second quarter of the 15th c.',1426,1450),'252':('workshop of the17th century',1601,1700),
 '104':('Signed and dated: "Kontoglou 1925"',1925,1925),'48':('it was dated to the 15th century',1401,1500),
 '22':('Copper engraving coming from Moscow and dated in 1849.',1849,1849),'219':('Chronology: 2nd half of 14th c.',1351,1400),
 '34':('double-sided icon, which dates in the mid-13th c.',1201,1300),'230':('Dated in the 15th century.',1401,1500),
 '62':('this icon was painted in 1679',1679,1679),'248':('workshop in the third quarter of the 14th century',1351,1375),
 '81':('Copper engraving, 1819.',1819,1819),'37':('a typical example of Coptic art of the 17th c.',1601,1700),
 '64':('icon executed in a Cypriot workshop, at the early 13th c.',1201,1300),'231':('dated in the first half of the 15th century',1401,1450),
 '217':('Chronology: 1738',1738,1738),'56':('Portable icon painted by a mid-15th c. Cretan artist.',1401,1500),
 '46':('Second half of the 17th c.',1651,1700),'238':('Both sides of the icon were painted in the 14th century.',1301,1400),
 '235':('This 14th century icon',1301,1400),'115':('Part of a wall painting dated in the 18th c.',1701,1800),
 '250':('The work bears the date 1679',1679,1679),'111':('The painting, dated in the 13th c.',1201,1300),
 '112':('belongs in the mid-13th c. painting layer',1201,1300),'220':('Chronology:19th century',1801,1900),
 '246':('The work is dated in 1675',1675,1675),'114':('was painted in the mid-15th century',1401,1500),
 '216':('Chronology: 2nd half 16th c.',1551,1600),
}

def soup(page):return BeautifulSoup(gzip.decompress((m.ROOT/page['receipt']['body_path']).read_bytes()),'html.parser')
def ld(sp):
    out=[]
    for x in sp.select('script[type="application/ld+json"]'):
        try:
            d=json.loads(x.string or x.get_text());out.extend(d if isinstance(d,list) else d.get('@graph',[d]))
        except (ValueError,TypeError):continue
    return out
def bounds(text):
    t=re.sub(r'^Около\s+','circa ',str(text or ''),flags=re.I);parsed=n.date_parse(t)
    if parsed[0] is not None:return parsed
    century=re.fullmatch(r'(?:(?:Начало|Конец|Середина|Первая половина|Вторая половина|Первая четверть|Вторая четверть|Третья четверть|Последняя четверть)\s+)?([IVX]+)\s+век[а]?[.]?',t,re.I)
    if century:
        roman=century[1].upper();values={'I':1,'V':5,'X':10};c=sum(-values[v] if i+1<len(roman) and values[v]<values[roman[i+1]] else values[v] for i,v in enumerate(roman));return (c-1)*100+1,c*100,'century'
    years=re.fullmatch(r'((?:1[0-9]{3})(?:\s*[-–—]\s*1[0-9]{3})?)\s*гг?\.?',t)
    if years:return n.date_parse(years[1])
    return parsed
def nuxt(sp):
    a=json.loads(sp.select_one('#__NUXT_DATA__').string)
    def dec(i,depth=0):
        assert depth<30
        if i<0:return None
        v=a[i]
        if isinstance(v,dict):return {k:dec(x,depth+1) for k,x in v.items()}
        if isinstance(v,list):return [dec(x,depth+1) if isinstance(x,int) else x for x in v]
        return v
    ids=[v for node in a if isinstance(node,dict) for k,v in node.items() if k.startswith('objectPage-') and v>=0]
    assert len(set(ids))==1;return dec(ids[0])

def parse(page,w):
    p=page['provider'];sp=soup(page);source=page['url'];obj={};native_id=None;scheme=None;title=None;image=None;accession=None;date=None;medium=None;dimensions=None;creators=[];rights=None;license_url=None;image_open=False;status=None;policy=None;credit=p
    if p=='getty':
        objs=[x for x in ld(sp) if x.get('@type') in ('Painting','VisualArtwork','Sculpture','CreativeWork') and x.get('url')==source];assert len(objs)==1;obj=objs[0];title=obj['name'];native_id=source.rstrip('/').split('/')[-1];scheme='getty-object';accession=(obj.get('identifier') or [None])[0];date=obj.get('temporal');medium=obj.get('material');dimensions=obj.get('size');creators=[x['name'] for x in obj.get('creator',[])];image=obj.get('thumbnailUrl');credit=' '.join(obj.get('creditText',[]));license_url=(obj.get('license') or '').replace('http:','https:');rights=BeautifulSoup(credit,'html.parser').get_text(' ',strip=True)
        image_open=license_url==n.CC0 and 'Images provided here' in credit and 'Open Content' in credit
        credit=BeautifulSoup(credit,'html.parser').get_text(' ',strip=True)
        if image and '/full/!300,300/' in image:image=image.replace('/full/!300,300/','/full/!1200,1200/')
        status='cc0'
    elif p=='russian-museum':
        objs=[x for x in ld(sp) if x.get('@type')=='VisualArtwork' and x.get('url')==source];assert len(objs)==1;obj=objs[0];title=obj['name'];native_id=source.split('/data/collections/',1)[1].removesuffix('/index.php');scheme='russian-museum-object';accession=next((x['value'] for x in obj.get('identifier',[]) if x.get('propertyID')=='Инвентарный номер'),None);date=obj.get('dateCreated');medium=obj.get('artMedium');creators=[x['name'] for x in obj.get('creator',[])];image=obj.get('image');rights='© Государственный Русский музей; no independent reuse licence asserted';license_url=source;status='restricted';lo,hi,_=bounds(date);image_open=hi is not None and hi<=1955;policy='Existing user-approved Russian museum image workflow; exact object and source creation bounds by 1955. Original restrictions retained separately from user approval.'
        gallery=sp.select_one('img.rsImg[src]');assert not image or (urlsplit(image).netloc=='rusmuseumvrm.ru' and gallery and urlsplit(image).path.rsplit('/',1)[0]==urlsplit(urljoin(source,gallery['src'])).path.rsplit('/',1)[0])
    elif p=='wikiart':
        obj=page['wikiart_metadata'];title=obj['title'];native_id=str(obj['_id']);scheme='wikiart-native-id';date=str(obj.get('year') or '');creators=[obj.get('artistName')];image=page.get('image');rights=page['image_rights'];license_url='https://www.wikiart.org/en/terms-of-use';image_open=True;status='public_domain' if page['public_domain'] else 'restricted';policy='User-approved WikiArt source policy, 6 October 2026. Per-image source rights retained; approval is separate from a copyright-holder licence.'
        assert r.canon('https://www.wikiart.org'+obj['paintingUrl'])==r.canon(source)
    elif p=='rijksmuseum':
        obj=nuxt(sp);title=obj['title'];native_id=obj['objectNodeId'];scheme='rijks-native-node';accession=obj['objectNumber'];imageinfo=obj.get('micrioImage') or {};image='https://iiif.micr.io/'+imageinfo['micrioId']+'/full/!1200,1200/0/default.jpg' if imageinfo.get('micrioId') else None
        props={x.get('name'):x.get('values') for block in obj['dataTab']['components'] for x in block.get('properties',[]) if x.get('name') and x.get('type')=='TextValue'}
        date='; '.join(props.get('Dating',[]));medium='; '.join(props.get('Physical description',[]));dimensions='; '.join(obj.get('dimensions',[]));creators=props.get('Creation',[]);rights='; '.join(props.get('Copyright',[]));license_url=n.PDM;status='public_domain';image_open=bool(imageinfo.get('isDownloadable') and 'creativecommons.org/publicdomain/mark/1.0/' in rights);rights=BeautifulSoup(rights,'html.parser').get_text(' ',strip=True)
        # Always request the complete image region, never the website's focus crop.
    elif p=='saam':
        objs=[x for x in ld(sp) if x.get('@type')=='VisualArtwork' and x.get('url')==source];assert len(objs)==1;obj=objs[0];title=obj['name'];native_id=source.rstrip('/').rsplit('-',1)[-1];scheme='saam-object';image=obj.get('image');creators=[x['name'] for x in obj.get('creator',[])];medium='; '.join(obj.get('artMedium',[]));license_url=n.CC0;status='cc0'
        grant=sp.find(string=lambda x:x and x.strip()=='Free to use');image_open=bool(grant and len(grant.parent.parent.select('svg'))==2);rights='Free to use — Creative Commons CC0 symbols on this exact object page' if image_open else 'No object-specific free-use label'
        im=next((x for x in sp.select('img[src]') if x['src']==image),None);assert im and title in im.get('alt','');obj['selected_image_alt']=im['alt'];obj['rights_label_html']=str(grant.parent.parent) if grant else None
        # Cataloguing values are left untouched; the source caption remains evidence.
    elif p=='domain:collection.pushkinmuseum.art':
        data=json.loads(sp.select_one('#my-app-state').string.replace('&q;','"').replace('&a;','&').replace('&s;',"'"));objs=[v for k,v in data.items() if k.startswith('/api/entity/OBJECT/')];assert len(objs)==1;obj=objs[0];assert not obj.get('deleted');native_id=str(obj['id']);assert '/entity/OBJECT/'+native_id in source;scheme='european-pushkin-kamis-object'
        attrs={x['attribute']:x for x in obj['data']};values=lambda k:'; '.join(attrs.get(k,{}).get('value',[]));title=values('object_title');accession=values('record_id');date=values('create_date4');medium='; '.join(filter(None,[values('material'),values('techniq')]));dimensions=values('dimensions');creators=[x['title'] for x in attrs.get('author',{}).get('data',[])];image=urljoin(source,obj['image'])+'?w=1000&h=1000' if obj.get('image') else None
        primary=[x for x in obj.get('images',[]) if x.get('main')];assert len(primary)==1 and primary[0]['path']==obj['image'];rights='© Государственный музей изобразительных искусств им. А.С. Пушкина. Все права защищены.';license_url=source;status='restricted';lo,hi,_=bounds(date);image_open=hi is not None and hi<=1955;policy='Existing user-approved Russian museum image workflow; exact object and source creation bounds by 1955. Source restrictions retained.'
    elif p=='benaki':
        native_id=parse_qs(urlsplit(source).query)['id'][0];scheme='benaki-object';title=sp.select_one('h1').get_text(' ',strip=True);tag=sp.select_one('img.bena-app-default-image[src]');bind=sp.select_one('a[data-collection-item-id="'+native_id+'"][data-collection-src-image]');assert tag and bind and tag['src']==bind['data-collection-src-image'];image=urljoin(source,tag['src']);description=sp.select_one('.bena-body').get_text(' ',strip=True)
        # Only explicit creation-period wording is interpreted; acquisition years in prose are ignored.
        centuries=re.findall(r'\b(\d{1,2})(?:ου|ος|ο)\s+αι\.',description);date=(centuries[-1]+'th century') if centuries else None
        lo,hi,_=bounds(date);rights='Copyright © Benaki Museum. All rights reserved.';license_url=source;status='restricted';image_open=hi is not None and hi<=1955;policy='Existing user-approved Greek museum image workflow; exact native object, authentic primary image and explicit creation century by 1955. Actual restrictions retained.';obj=dict(title=title,description=description,image_tag=str(tag),binding_tag=str(bind))
    elif p=='goulandris':
        spec=importlib.util.spec_from_file_location('goulandris_parser',m.ROOT/'ops/museum-expansion-goulandris-20261006.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g);raw=gzip.decompress((m.ROOT/page['receipt']['body_path']).read_bytes());obj=g.fields(raw);title=obj['translated_title'] or obj['title'];native_id=g.source_id(source);scheme='goulandris-object';date=obj['date'];medium=obj['medium'];dimensions=obj['dimensions'];creators=[obj['creator']];images=[x['href'] for x in sp.select('a.artwork__display-image[href]') if not re.search(r'detail|verso|reverse|-BACK-',x['href'],re.I)];assert len(images)==1,'Multiple complete source views';image=images[0];years=g.creation_date(date);physical=g.PRINT_CREATION.get(native_id)
        if physical:assert physical[0] in obj['medium_notes'];years=g.creation_date(physical[1]);date=physical[1]
        image_open=bool(years and years[1]<=1955);rights='Copyright © Basil & Elise Goulandris Foundation; '+'; '.join(obj['rights']);license_url=source;status='restricted';policy='Existing user-approved Greek museum image workflow; exact object/version and explicit source creation bounds by 1955. Actual restrictions retained.'
    elif p in ('krakow','domain:api-zbiory.mnk.pl','domain:cyfrowe-api.mnw.art.pl'):
        native_id=source.rstrip('/').rsplit('/',1)[-1];assert native_id.isdigit();krakow=p!='domain:cyfrowe-api.mnw.art.pl';api='https://api-zbiory.mnk.pl' if krakow else 'https://cyfrowe-api.mnw.art.pl'
        if p=='krakow':data,rc=n.f.get(api+'/api/object/'+native_id,True);obj=data['data'];obj['_fresh_api_receipt']=rc
        else:obj=json.loads(gzip.decompress((m.ROOT/page['receipt']['body_path']).read_bytes()))['data']
        assert str(obj['id'])==native_id;scheme='mnk-current-object' if krakow else 'mnw-current-object-2026';title=obj['title'];accession=obj.get('noEvidence');date='; '.join(x['name'] for x in obj.get('createDates',[]));medium='; '.join(x['name'] for x in obj.get('techniques',[])+obj.get('materials',[]));dimensions=obj.get('dimensionText');creators=[x['name'] for x in obj.get('authors',[])];rights='; '.join(x.get('name','') for x in obj.get('copyrights',[]));copyrights=obj.get('copyrights',[]);image_open=bool(copyrights and any(x.get('name','').casefold()=='domena publiczna' for x in copyrights) and not any(x.get('restricted') for x in copyrights));status='public_domain';license_url=n.PDM
        photo=obj.get('image') or {};cdn='https://cdn-zbiory.mnk.pl' if krakow else 'https://cyfrowe-cdn.mnw.art.pl';image=cdn+'/upload/cache/multimedia_detail/'+photo['filePath']+'.'+photo['extension'] if photo.get('filePath') and photo.get('extension') in ('jpg','jpeg','png') else None;credit=(obj.get('owner') or {}).get('name') or p
    elif p=='nationalmuseum':
        obj=json.loads(sp.select_one('#__NEXT_DATA__').string)['props']['pageProps']['data']['item'];native_id=re.search(r'/item/(\d+)',source)[1];scheme='nationalmuseum-object';title=obj['ObjTitleMainTxt'];accession=obj.get('ObjInventoryNumberTxt');date=obj.get('ObjDateGroupTxt');medium=obj.get('ObjMaterialTechniqueTxt');default=obj.get('DefaultImage','');assert re.fullmatch(r'multimedia/\d+/multimedia-\d+\.large\.jpg',default)
        assert any(x.get('src')=='/'+default for x in sp.select('img[src]'));hits=[(a,v) for a in obj.get('ObjMultimediaRef',{}).get('Items',[]) for v in a.get('Multimedia',[]) if v.get('full')==default];assert len(hits)==1;a,photo=hits[0];rights=a.get('MulRightsTxt','').strip();assert a.get('InternetVoc',{}).get('LabelTxt')=='Public' and photo.get('mime')=='image/jpeg' and not a.get('MulPhotographicalCopyrightTxt','').strip();license_url=n.PDM if rights=='Public Domain, '+n.PDM else 'https://creativecommons.org/licenses/by-sa/4.0/' if rights=='CC BY SA, https://creativecommons.org/licenses/by-sa/4.0/' else None;image_open=bool(license_url);status='public_domain' if license_url==n.PDM else 'cc_by_sa';credit=a.get('MulPhotocreditTxt','').strip();assert credit or status=='public_domain';image=urljoin(source,'/'+default)
    elif p=='chicago':
        native_id=re.search(r'/artworks/(\d+)',source)[1];scheme='chicago-artwork';title=sp.select_one('h1').get_text(' ',strip=True)
        candidates=[a for a in sp.select('[data-gallery-img-iiifid]') if a.get('data-gallery-img-credit','').strip()=='CC0 Public Domain Designation'];assert candidates,'No exact-image CC0 grant'
        primary=page['meta']['og:image'][0];match=[a for a in candidates if primary.startswith(a['data-gallery-img-iiifid']+'/full/')];assert len(match)==1;tag=match[0];image=tag['data-gallery-img-iiifid']+'/full/!1200,1200/0/default.jpg';assert tag.get('data-gallery-img-download-url','').startswith(tag['data-gallery-img-iiifid']+'/full/')
        image_open=True;status='cc0';license_url=n.CC0;rights=tag['data-gallery-img-credit'];credit='The Art Institute of Chicago';obj=dict(native_title=title,selected_image_tag=str(tag),open_graph_image=primary)
    elif p=='domain:ebyzantinemuseum.gr':
        native_id=parse_qs(urlsplit(source).query)['id'][0];scheme='bxm-exhibit';titles=sp.select('h2');assert len(titles)==1;title=titles[0].get_text(' ',strip=True);description=' '.join(x.get_text(' ',strip=True) for x in sp.select('.description'));assert native_id in BXM_DATES,'Explicit object creation date remains unestablished in this pass';anchor,lo,hi=BXM_DATES[native_id];assert ' '.join(anchor.split()) in ' '.join(description.split()),'Reviewed creation wording changed'
        primary_id=urlsplit(page['meta']['og:image'][0]).path.split('/')[-1].split('_')[0];images=[x for x in sp.select('img[src]') if urlsplit(x['src']).netloc=='www.psfiles.gr' and urlsplit(x['src']).path.split('/')[-1].split('_')[0]==primary_id];assert len(images)==1,'Unique rendered primary museum image unavailable';image=images[0]['src']
        date=str(lo) if lo==hi else str(lo)+'–'+str(hi);image_open=True;rights='© Byzantine and Christian Museum; native copyright retained';license_url='https://www.ebyzantinemuseum.gr/?i=bxm.en.terms';status='restricted';credit='Byzantine and Christian Museum, Athens';policy='User-approved Greek museum image workflow. Exact native object, primary photograph and individually read source creation statement by 1955; actual source restrictions preserved.';obj=dict(description=description,date_anchor=anchor,image_tag=str(images[0]))
    elif p=='byzantine-thessaloniki':
        native_id=urlsplit(source).path.rstrip('/').split('/')[-1];scheme='mbp-exhibit';title=sp.select_one('.single-item-main-title h1').get_text(' ',strip=True);props={a.get_text(' ',strip=True):a.parent.select_one('.toggle-content').get_text(' ',strip=True) for a in sp.select('h3') if a.parent.select_one('.toggle-content')};accession=props.get('Code');date=props.get('Chronology');dimensions=props.get('Dimensions');medium=props.get('Material of Construction')
        im=[x for x in ld(sp) if x.get('@type')=='ImageObject' and x.get('@id')==source+'#primaryimage'];assert len(im)==1;image=im[0]['contentUrl'];assert image==page['meta']['og:image'][0].strip() and any(x['src']==image for x in sp.select('img[src]'));lo,hi,_=bounds(date)
        if hi is None:
            centuries=re.findall(r'(\d+)(?:th|st|nd|rd)\s*(?:century|c\.)',date or '',re.I)
            if centuries:lo=(min(map(int,centuries))-1)*100+1;hi=max(map(int,centuries))*100
        image_open=hi is not None and hi<=1955;rights='© Museum of Byzantine Culture; native copyright retained';license_url=source;status='restricted';credit='Museum of Byzantine Culture, Thessaloniki';policy='User-approved Greek museum image workflow. Exact native object and explicit Chronology field by 1955; actual source restrictions retained.';obj=dict(native_properties=props,primary_image=im[0],reviewed_date_bounds=[lo,hi]);date=str(lo)+'–'+str(hi) if lo is not None else date
    elif p=='domain:digitalarchive.npm.gov.tw':
        native_id=parse_qs(urlsplit(source).query)['id'][0];scheme='npm-painting-object';gallery=sp.select_one('#gallery');assert gallery;ims=gallery.select('img[data-image-id]');assert ims and ims[0].get('title')=='main';im=ims[0];title=im['alt'];image=urljoin(source,im['src']);assert im['src']==im['data-image'];download=sp.select_one('#a_download');assert download and 'CC0' in download.get_text() and '100萬' in download.get_text();assert any('creativecommons.org/publicdomain/zero/1.0/' in a['href'] for a in sp.select('a[href]'));image_open=True;rights='CC0 — museum 1-megapixel image; the separate 6-megapixel tier is CC BY 4.0';license_url=n.CC0;status='cc0';credit='National Palace Museum, Taipei';obj=dict(primary_image_tag=str(im),cc0_download_tag=str(download),rights_links=page['rights_links'],selected_image_name=im.get('data-image-name'),source_title=title)
        model=next((sc.get_text() for sc in sp.select('script') if 'const modelList =' in sc.get_text()),None);assert model;models=json.loads(re.search(r'const modelList\s*=\s*(\[.*?\]);',model,re.S)[1]);sizes=[x for x in models if x['ImageName']==im.get('data-image-name')];assert len(sizes)==1 and sizes[0]['Width']*sizes[0]['Height']<=8_000_000;obj['image_dimensions_and_tier']=sizes[0]
        if sizes[0]['Width']*sizes[0]['Height']>1_100_000:
            grants=[a for a in sp.select('a[href]') if 'creativecommons.org/licenses/by/4.0/' in a['href']];assert grants;rights='CC BY 4.0 — museum 6-megapixel image tier';license_url='https://creativecommons.org/licenses/by/4.0/';status='cc_by';credit=title+'; National Palace Museum, Taipei; CC BY 4.0; www.npm.gov.tw'
    else:raise ValueError('Provider requires its own exact-object parser')
    lo,hi,precision=bounds(date);f=dict(native_id=native_id,scheme=scheme,accession=accession,titles=[title],dates=dict(display=date,start=lo,end=hi),date_precision=precision,medium=medium,dimensions=dimensions,page=source,creator_labels=creators,creator_authorities=[],qualified_creators=[],raw_creator_data=creators,image=image,image_open=image_open,image_rights=rights,rights_status=status,rights_basis=policy or 'Explicit reuse grant attached to the exact native museum object image; source rights retained.',license_url=license_url,credit=credit,institution_id=w['current_institution_id'],work_type=w['work_type'],holding_qualified=False)
    return f,obj

def run(wanted=None):
    inv=m.load(RUN/'inventory.json.gz');ws={w['id']:w for w in inv['artworks']};identifiers=defaultdict(list);citations=defaultdict(list)
    for e in inv['identifiers']:identifiers[e['entity_id']].append(e)
    for c in inv['citations']:citations[c['entity_id']].append(c)
    primary={x['artwork_id']:x for x in m.load(RUN/r.RESOLUTION)['rows'] if x['state'] in ('new','existing')}
    pages=[m.load(p) for p in sorted((RUN/'object-pages').glob('*.gz'))];out=[];held=[];chosen=set()
    if wanted:
        previous=m.load(sorted(RUN.glob('secondary-resolution-*.json.gz'))[-1]);out=[x for x in previous['rows'] if x['provider'] not in wanted];held=[x for x in previous['held'] if x['provider'] not in wanted];chosen={x['artwork_id'] for x in out}
    for page in pages:
        if page['provider'] not in (wanted or PROVIDERS) or page['state']!='captured':continue
        ids=sorted({b['entity_id'] for b in page['index_bindings'] if b['entity_type']=='artwork'})
        if len(ids)!=1 or ids[0] not in ws:continue
        w=ws[ids[0]];aid=w['id'];dest=RUN/'secondary-native'/page['provider'].replace(':','_')/(page['source_index_id']+'.json.gz')
        if w['primary_media_id'] or w['status']=='archived' or aid in chosen or primary.get(aid,{}).get('image_candidate'):continue
        try:
            f,obj=parse(page,w);assert f['titles'][0]
            urls={r.canon(e['canonical_url']) for e in identifiers[aid] if e.get('canonical_url')};source=r.canon(page['url']);strong=source in urls or any(e['scheme']==f['scheme'] and e['external_id']==str(f['native_id']) for e in identifiers[aid])
            title_match=r.norm(w['title']) in {r.norm(x) for x in f['titles']}
            cited=any(r.canon(c['source_url'])==source for c in citations[aid])
            if page['provider']=='rijksmuseum' and cited:
                record_id=(obj.get('objectNodeUri') or '').rsplit('/',1)[-1]
                strong=strong or any(r.canon(c['source_url'])==source and c.get('source_record_id')==record_id for c in citations[aid])
            if not strong:assert cited and title_match,'Exact native identifier or title-matched object-page citation unavailable'
            if f.get('accession') and w['accession_number']:assert r.norm(f['accession'])==r.norm(w['accession_number']),'Accession mismatch'
            if page['provider']=='wikiart':assert title_match,'WikiArt title/version changed'
            assert f['image'] and f['image_open'],'No approved exact-object image established'
            record=dict(provider=page['provider'],key=f['native_id'],state='captured',facts=f,raw=obj,receipt=page['receipt'],source_index_ids=[page['source_index_id']],index_bindings=page['index_bindings'])
            if dest.exists() and m.load(dest)!=record:dest=dest.with_name(dest.name.replace('.json.gz','-'+hashlib.sha256(json.dumps(record,sort_keys=True,ensure_ascii=False).encode()).hexdigest()[:16]+'.json.gz'))
            m.save(dest,record)
            rr=dict(provider=page['provider'],key=f['native_id'],native_file=str(dest.relative_to(m.ROOT)),artwork_id=aid,state='existing',title=w['title'],matched_ids=[aid],identity_basis=['Exact indexed native object URL on the existing external identifier' if strong else 'Exact object-page citation plus matching native title','No native accession conflict'],creator_links=[],unlinked_creator_label=None,image_candidate=True,field_updates={},source_index_ids=[page['source_index_id']])
            out.append(rr);chosen.add(aid)
        except Exception as e:held.append(dict(source_index_id=page['source_index_id'],artwork_id=aid,provider=page['provider'],reason=type(e).__name__+': '+str(e)))
    # Iterations preserve earlier decisions; a later complete run gets its own numbered artifact.
    number=len(list(RUN.glob('secondary-resolution-*.json.gz')))+1;name=f'secondary-resolution-{number:03d}.json.gz';m.save(RUN/name,dict(at=m.now(),rows=out,held=held,counts=dict(Counter(x['provider'] for x in out))));print(name,'selected',len(out),'held',len(held),dict(Counter(x['provider'] for x in out)),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--providers',nargs='+');args=parser.parse_args();run(set(args.providers) if args.providers else None)
