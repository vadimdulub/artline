"""Selected, reviewed source fields; no artist lifetimes used as object dates."""
import collections,gzip,importlib.util,json,re,sys
from bs4 import BeautifulSoup
spec=importlib.util.spec_from_file_location('b','ops/balkans-deep-20261011.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
MUSEUMS={
 'bg-national-gallery-sofia':('National Gallery, Bulgaria','Sofia','BG','https://nationalgallery.bg/collections/'),
 'bg-museum-christian-art-sofia':('Museum of Christian Art – National Gallery','Sofia','BG','https://nationalgallery.bg/collections/bulgarian-art-v-xix-century/'),
 'bg-ruse-art-gallery':('Ruse Art Gallery','Ruse','BG','https://ruseartgallery.bg/en/'),
 'bg-sofia-city-art-gallery':('Sofia City Art Gallery','Sofia','BG','https://sghg.bg/живопис/'),
 'bg-dimitar-dobrovich-sliven':('Dimitar Dobrovich Art Gallery','Sliven','BG','https://gallerysliven.com/'),
 'bg-kazanlak-art-gallery':('Art Gallery Kazanlak','Kazanlak','BG','https://www.artgallerykazanlak.com/en/'),
 'bg-ahinora-museum':('Ahinora Museum – Art Gallery Kazanlak','Kazanlak','BG','https://www.artgallerykazanlak.com/en/exhibitions/ahinora/'),
 'mk-museum-contemporary-art-skopje':('Museum of Contemporary Art, Skopje','Skopje','MK','https://msu.mk/'),
}
def soup(url):
    p=m.page(url);assert p['receipt']['status']==200
    return BeautifulSoup(gzip.decompress((m.ROOT/p['receipt']['body_path']).read_bytes()),'html.parser'),p
def date(v):
    raw=(v or '').strip();t=raw.lower().replace('–','-').replace('—','-').replace('/','-').replace('(?)','').strip()
    t=re.sub(r'^(ca\.?|circa|c\.|околу|около)\s*','',t);circa=t!=raw.lower().replace('–','-').replace('—','-').replace('/','-').strip()
    a=b=None;precision='unknown'
    if re.fullmatch(r'\d{1,2}\.\d{1,2}\.\d{4}',t):a=b=int(t[-4:]);precision='exact'
    elif re.fullmatch(r'\d{3,4}',t):a=b=int(t);precision='circa'if circa else'exact'
    elif re.fullmatch(r'\d{4}s',t):a=int(t[:4]);b=a+9;precision='range'
    elif re.fullmatch(r'\d{4}-\d{1,4}',t):
        x,y=t.split('-');a=int(x);b=int(y)if len(y)==4 else int(x[:4-len(y)]+y);precision='circa_range'if circa else'range'
    elif re.fullmatch(r'(?:early |mid |late |second half of the |first half of the )?\d{1,2}(?:th|st|nd|rd)(?:-(?:early |late )?\d{1,2}(?:th|st|nd|rd))?\s*(?:c\.|century)',t):
        nums=list(map(int,re.findall(r'\d+',t)));a=(nums[0]-1)*100+1;b=nums[-1]*100;precision='century'if len(nums)==1 else'range'
    elif re.fullmatch(r'before \d{4}',t):b=int(t[-4:]);precision='before'
    if a is not None and b is not None:assert a<=b,raw
    return dict(start=a,end=b,precision=precision,date_display=raw or'Creation date unknown')
def kind(medium):
    v=(medium or'').lower()
    for terms,k in [(['woodcut','etching','aquatint','engraving','дрворез','акватинта','литограф','бакрорез'],'print'),(['watercolor','watercolour','акварел'],'watercolor'),(['pastel','пастел','pencil','chalk','charcoal','ink','туш','молив','цртеж'],'drawing'),(['bronze','marble','plaster','terracotta','stone','бронза'],'sculpture')]:
        if any(t in v for t in terms):return k
    return 'painting'if any(t in v for t in ['oil','tempera','масло','маслени','темпера'])else'unknown'
def fact(key,mu,title,creator,dt,source,record,image=None,medium=None,dimensions=None,accession=None,**extra):
    d=date(dt);return dict(key=key,museum_slug=mu,title=title,creator=creator,**d,work_type=kind(medium),medium=medium,dimensions=dimensions,accession=accession,source_url=source,source_record_id=str(record),locator='Exact source object caption / inventory',image_url=image,image_eligible=bool(image and d['end']is not None and d['end']<=1955),view_label='Complete source reproduction; proportional resizing without cropping',**extra)
def national_bg():
    rows=m.h.load(m.RUN/'national-gallery-bg-highlights.json');out=[];held=[]
    icon_dates={91:'11th–18th c.',95:'late 12th c.',96:'13th c.',97:'13th–14th c.',98:'13th–17th c.',102:'13th–18th c.',104:'13th–18th c.',106:'mid 14th c.',107:'late 14th c.',108:'second half of the 16th c.',109:'1566',110:'early 17th c.',111:'ca. 1600',112:'15th–16th c.',113:'late 15th–early 16th c.',114:'1617',115:'16th–17th c.',116:'early 18th c.',117:'second half of the 18th c.',118:'1811',119:'1823',120:'1838',121:'19th c.',122:'1857'}
    for i,r in enumerate(rows):
        bits=r['title'].split('|');medium=r['description'];creator=None;accession=None
        if 91<=i<=122:
            if i not in icon_dates:held.append(dict(index=i,reason='Another side or detail of the same physical icon; no duplicate artwork.'));continue
            dt=icon_dates[i];title=bits[0];title=re.sub(r', (?:late |mid |early |second half of the )?(?:\d{1,4}).*$','',title)
            if i==102:title='Christ Pantocrator with Prophets – The Holy Virgin Gorgoepikoos with Prophets'
            if i==116:creator='Dionysius from Fourna'
            if i==118:creator='Bansko Art School; Hristo Dimitrov from Samokov; Dimitar Molerov; icon painter from the Zahariev family (components separately attributed)'
            if i==120:creator='Priest Dimitar Kanchov from Tryavna'
            mu='bg-museum-christian-art-sofia'
        else:
            creator=re.sub(r'\([^)]*\)','',bits[0]).strip(' ,');creator=re.sub(r', (?:Italy|France|Russia|Germany|UK|Croatia|Czech Republic|Dutch School.*|Bulgaria/France|Bosnia and Herzegovina)$','',creator)
            text=bits[1];mm=re.search(r',\s*((?:(?:ca\.?|circa|before)\s*)?\d{3,4}(?:[–-]\d{3,4})?s?(?: and \d{4}s)?)$',text)
            title=text[:mm.start()]if mm else text;dt=mm[1]if mm else''
            if i==124:dt='1830–1849' # source explicitly says 1830s and 1840s
            if i>=123:
                medium=bits[2];match=re.search(r'Inv\. No\. (.*?)(?:\. Added|$)',r['title']);accession=match[1]if match else None
            mu='bg-national-gallery-sofia'
        d=date(dt)
        if d['end']and d['end']>1970:held.append(dict(index=i,reason='After/crossing the 1970 creation cutoff',caption=r));continue
        f=fact('nationalgallery.bg/'+r['source_record_id'],mu,title,creator,dt,r['source_url'],r['source_record_id'],r['image_url'],medium=medium,accession=accession,source_receipt=r['source_receipt'],original_caption=r)
        if 91<=i<=122 and any(t in medium for t in ['Two-sided','Side A']):f['view_label']='Source photograph of a two-sided icon; other sides/details are the same physical object'
        out.append(f)
    return out,held
def ruse():
    result=[]
    for tail in ['founders','bulgarian-art-20th-century']:
        url='https://ruseartgallery.bg/en/exhibitions/exhibitions-from-the-fund/'+tail+'/'
        s,p=soup(url)
        for n in s.select('.eltdf-pli-text'):
            creator=n.select_one('h4');title=n.select_one('.eltdf-pli-excerpt')
            if not creator or not title:continue
            parent=n
            while parent.parent and not parent.select_one('img'):parent=parent.parent
            img=parent.select_one('img');label=title.get_text(' ',strip=True);ma=re.search(r',\s*(\d{4})$',label)
            if not ma or int(ma[1])>1970:continue
            image=img.get('src');a=img.find_parent('a')
            if a and re.search(r'\.(jpg|jpeg|png)$',a.get('href',''),re.I):image=a['href']
            result.append(fact('ruse/'+m.h.sha(image.encode())[:18],'bg-ruse-art-gallery',label[:ma.start()],creator.get_text(' ',strip=True),ma[1],url,image,image,source_receipt=p['receipt']))
    return result
def sofia_sliven():
    result=[];url='https://sghg.bg/живопис/';s,p=soup(url)
    for slide in s.select('.slide-inner'):
        title=slide.select_one('h2');ar=slide.select_one('.section-author');a=slide.select_one('a.popup-image')
        if not(title and ar and a):continue
        label=title.get_text(' ',strip=True);match=re.search(r'\b(\d{4})\b',label)
        if not match or int(match[1])>1970:continue
        f=fact('sghg/'+m.h.sha(a['href'].encode())[:18],'bg-sofia-city-art-gallery',label.split(match[1])[0].strip(' ,('),ar.get_text(' ',strip=True),match[1],url,a['href'],a['href'],source_receipt=p['receipt'],original_caption=label)
        if 'Цветан Игнатовски'in label:f.update(creator_credit='Tsvetan Ignatovski',rights_label='Sofia City Art Gallery; photograph credited to Tsvetan Ignatovski; all rights reserved')
        result.append(f)
    url='https://gallerysliven.com/kolekcia/fond-zhivopis/';s,p=soup(url)
    for img in s.select('img[alt]'):
        label=img['alt'];match=re.match(r'(.+?) – (.+), (\d{4}) г\.',label)
        if not match or '-500x500'in img.get('src',''):continue
        result.append(fact('sliven/'+m.h.sha(img['src'].encode())[:18],'bg-dimitar-dobrovich-sliven',match[2],match[1],match[3],url,img['src'],img['src'],source_receipt=p['receipt'],original_caption=label))
    return result
def kazanlak():
    out=[];held=[]
    for item in m.h.load(m.RUN/'kazanlak-pre1956-index.json')['response']['items']:
        s,p=soup(item['url']);article=s.select_one('article.artwork')or s.select_one('article');text=article.get_text('\n',strip=True);lines=text.splitlines()
        def field(label):
            i=lines.index(label);return lines[i+1]if i+1<len(lines)else''
        title=item['title_line'];dt=field('Година на създаване');med=field('Техника');acc=field('Инвентарен #');dim=field('Размери');ma=re.search(r',\s*\d{4}$',title);title=title[:ma.start()]if ma else title
        img=article.select_one('img');image=img['src'];srcset=img.get('srcset','')
        if srcset:image=srcset.split(',')[-1].strip().split()[0]
        f=fact('kazanlak/'+str(item['id']),'bg-kazanlak-art-gallery',title,item['author_text'],dt,item['url'],item['id'],image,medium=med,dimensions=dim,accession=acc,source_receipt=p['receipt'],original_caption=text)
        if f['end'] and f['end']>1970:
            held.append(dict(fact=f,reason='Individual object date exceeds 1970; discovery API date filter did not exclude this object.'));continue
        if f['end'] is None:f['image_hold']='Unparsed or unknown object creation date; image held.'
        out.append(f)
    url='https://www.artgallerykazanlak.com/en/exhibitions/ahinora/';p=m.page(url)
    out.append(fact('kazanlak/ahinora-1925','bg-ahinora-museum','Ahinora','Ivan Milev','1925',url,'ahinora-1925',p['images'][0]['url'],source_receipt=p['receipt'],identity_note='1925 version; the source explicitly distinguishes the earlier 1922 version.'))
    return out,held
def msu():
    rows=m.h.load(m.RUN/'msu-selected-object-metadata.json');out=[];held=[]
    for file in sorted((m.RUN/'msu-artists').glob('*.json')):
        a=m.h.load(file)
        if not a['response'].get('gallery'):
            v=a['response'];rows.append(dict(creator=v['title'],artist_id=file.stem,media=dict(id='featured-'+file.stem,url=v['image']),source_url=a['receipt']['url'],receipt=a['receipt'],description=BeautifulSoup(v['description'],'html.parser').get_text('\n',strip=True)))
    for r in rows:
        lines=[x.strip()for x in r['description'].splitlines()if x.strip()and x.strip()!=',']
        # The first line after the creator biography header is the object title.
        i=next((i for i,x in enumerate(lines[:4])if re.match(r'^\d{4}[,\s]',x)),None)
        if i is None or i+2>=len(lines):held.append(dict(row=r,reason='Unparsed object caption'));continue
        label=lines[i+1];ma=re.search(r',\s*(\d{4}(?:/\d{4})?(?: \(\?\))?)$',label)
        title=label[:ma.start()]if ma else label;dt=ma[1]if ma else lines[i+2];mid=i+2 if ma else i+3
        d=date(dt)
        if d['end']is None or d['end']>1970:held.append(dict(source_url=r['source_url'],reason='Date outside selected scope or unparsed',date=dt));continue
        med=lines[mid]if mid<len(lines)else None;acc=re.search(r'Инве[нт]*тарен бр\.:\s*(\d+)',r['description'])
        f=fact('msu/'+r['media']['id'],'mk-museum-contemporary-art-skopje',title,r['creator'],dt,r['source_url'],r['media']['id'],r['media']['url'],medium=med,accession=acc[1]if acc else None,source_receipt=r['receipt'],original_caption=r['description'].split('Биографија')[0])
        if 'upscayl' in f['image_url'].lower():f.update(image_eligible=False,image_hold='Source file identifies an upscaled version; authentic unaltered source required.')
        if r['media']['id']=='14828':f['date_evidence_note']='Object caption says 1935; filename says 1925. Caption preferred; discrepancy preserved.'
        out.append(f)
    return out,held
def main():
    facts,held=national_bg();facts+=ruse()+sofia_sliven();ka,kh=kazanlak();facts+=ka;held+=kh;ms,hold=msu();facts+=ms;held+=hold
    unique={}
    for f in facts:
        if f['key'] in unique:
            prior=unique[f['key']]
            assert all(prior[k]==f[k]for k in ['title','creator','start','end','museum_slug','image_url'])
            prior.setdefault('additional_sources',[]).append(f['source_url'])
        else:unique[f['key']]=f
    facts=list(unique.values())
    museums=[dict(slug=k,name=v[0],city=v[1],country_code=v[2],website_url=v[3])for k,v in MUSEUMS.items()]
    m.h.save(m.RUN/'selection-wave1.json',dict(at=m.h.now(),records=facts,held=held,museums=museums,user_authorization='User requested the same deep research and artwork-image delivery for Greece, Bulgaria and Macedonia, 11 October 2026. Existing pre-1956 selected museum-source image workflow continued; actual source restrictions remain recorded separately.'))
    print('FACTS',len(facts),'IMAGE CANDIDATES',sum(x['image_eligible']for x in facts),'HOLDS',len(held),collections.Counter(x['museum_slug']for x in facts))
if __name__=='__main__':main()
