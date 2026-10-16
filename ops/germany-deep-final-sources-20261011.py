"""Additional selected holdings. All sources retained; no current-display assertion."""
import runpy,re,json
from urllib.parse import urljoin
b=runpy.run_path('ops/germany-deep-facts-20261011.py');m=b['m'];soup=b['soup'];add=b['add'];museum=b['museum'];M=b['M'];F=b['F'];H=b['H']
def guard(fn,*args):
    try:fn(*args)
    except Exception as e:H.append(dict(parser=fn.__name__,args=args,reason=type(e).__name__+': '+str(e)[:180]));print('HOLD',fn.__name__,str(e)[:180],flush=True)
def karlsruhe(url):
    mu=museum('de-kunsthalle-karlsruhe','Staatliche Kunsthalle Karlsruhe','Karlsruhe','Baden-Württemberg','https://www.kunsthalle-karlsruhe.de/kunstwerke/');s,p=soup(url);d={dt.get_text(' ',strip=True):dt.find_next_sibling('dd').get_text(' ',strip=True)for dt in s.select('dt')if dt.find_next_sibling('dd')};im=next((x['url']for x in p['links']if'Klein/JPEG'in x['text']),None)
    f=add(mu,d['Titel'],d['Künstler*in'],d.get('Entstehungszeit',''),url,url.rstrip('/').rsplit('/',1)[-1],im,'; '.join(x for x in [d.get('Technik'),d.get('Material')]if x),d.get('Maße Bildträger'),d.get('Inventarnummer'),source_receipt=p['receipt'],source_fields=d)
    if f and'Public Domain'in p['text']:f.update(rights_status='public_domain',rights_label='Public Domain (museum object download label)',creator_credit='Staatliche Kunsthalle Karlsruhe')
def mainz(url):
    mu=museum('de-landesmuseum-mainz','Landesmuseum Mainz','Mainz','Rhineland-Palatinate','https://guide.landesmuseum-mainz.de/');s,p=soup(url);im=s.find('img',src=lambda x:x and'.0x500.'in x)
    if not im:raise ValueError('No labelled object reproduction')
    cap=im.get('alt','');box=im.find_parent(class_='responsiveContentContainer');credit=box.select_one('.image-subtext');credit=credit.get_text(' ',strip=True)if credit else cap
    # The artwork title precedes the image; the page h1 is an editorial slogan.
    title=im.find_previous(['h2','h3','h4','h5']);title=title.get_text(' ',strip=True)if title else''
    if title in ['Audio','']:title=p['text'].split('Audio\n')[-1].split('\n')[0]
    ma=re.search(r',\s*((?:um |nach |vor |ca\. )?\d{4}(?:\s*[-–/]\s*\d{1,4})?)(?:,|$)',cap)
    if not ma:raise ValueError('Cannot distinguish creator and creation date from caption: '+cap)
    cr=cap[:ma.start()].strip();dt=ma[1];inv=re.search(r'Inv\.?\s*(?:Nr\.?)?\s*([^,;]+)',cap,re.I);rid=inv[1].strip()if inv else url.rstrip('/').rsplit('/',1)[-1]
    f=add(mu,title,cr,dt,url,rid,urljoin(url,im['src']),accession=inv[1].strip()if inv else None,source_receipt=p['receipt'],original_caption=cap,creator_credit=credit,rights_label=credit,holding_note='Landesmuseum Mainz official collection guide')
    if f:
        rest=cap[ma.end():].strip();f['medium']=rest.split(',')[0]or None
        if any(x in cr for x in ['Lehmbruck','Roeder','Hack']):f['work_type']='sculpture_or_applied_art'
        if 'Lehmbruck'in cr:f.update(image_eligible=False,date_evidence_note='Work/model year does not establish the casting date of this museum bronze.')
        if 'Nach Albrecht'in cr or'nach Albrecht'in cr:f['date_evidence_note']='Qualified after-Dürer attribution and after-1507 date preserved. Main website has a different workshop/date formulation; do not collapse into an autograph Dürer.'
def wallraf(url,label):
    mu=museum('de-wallraf-richartz','Wallraf-Richartz-Museum & Fondation Corboud','Cologne','North Rhine-Westphalia','https://www.wallraf.museum/');s,p=soup(url);base=s.find('base')['href'];im=next(x for x in s.select('img[alt]')if 'WRM'in x['alt']);cap=im['alt'];lab=label.replace('–','-');cr,tail=lab.split(':',1)
    if re.search(r',\s*(?:um )?\d{4}',cr):cr,dt=cr.rsplit(', ',1);title=tail.strip()
    else:
        ma=re.search(r',\s*((?:um |ca\. )?\d{4}.*)$',tail);assert ma,label;title=tail[:ma.start()].strip();dt=ma[1]
    inv=re.search(r'Inv\.\s*Nr\.?\s*([^.;]+)',cap);f=add(mu,title,cr,dt,url,inv[1]if inv else url.rstrip('/').split('/')[-2],urljoin(base,im['src']),accession=inv[1]if inv else None,source_receipt=p['receipt'],original_caption=cap,creator_credit=cap.split('Foto:')[-1].strip()if'Foto:'in cap else'Wallraf-Richartz-Museum & Fondation Corboud',rights_label='Museum reproduction; '+(cap.split('Foto:')[-1].strip()if'Foto:'in cap else'no open reuse licence stated'))
    if f and any(x in cr for x in ['Lucchesisch','Kölnisch']):f['creator']='Unknown maker ('+cr+')'
    if f and any(x in title for x in ['Triptychon','Altar','diptychon']):f['view_label']='Complete museum-supplied photograph of the multipart work; photographed state preserved'
def stuttgart(url):
    mu=museum('de-staatsgalerie-stuttgart','Staatsgalerie Stuttgart','Stuttgart','Baden-Württemberg','https://www.staatsgalerie.de/de/sammlung');s,p=soup(url);d={}
    for item in s.select('.object-content__metadata-item'):
        k=item.select_one('.object-content__metadata-item-label');v=item.select_one('.object-content__metadata-item-value')
        if k and v:d[k.get_text(' ',strip=True)]=v.get_text(' ',strip=True)
    cr=d.get('Personen','').split('Künstler / Künstlerin')[0].strip();im=next((i['url']for i in p['images']if'/iiif/'in i['url']or'digitaler-katalog/image'in i['url']),None)
    f=add(mu,d['Titel'],cr,d.get('Datierung',''),url,d['Inventarnummer'],im,'; '.join(x for x in [d.get('Technik'),d.get('Material')]if x),d.get('Maße'),d['Inventarnummer'],source_receipt=p['receipt'],source_fields=d,holding_note=d.get('Hinweis','Staatsgalerie Stuttgart collection record'))
    if f:
        f['work_type']='drawing'if d.get('Medium')=='Zeichnung'else'painting'
        if 'Public Domain Mark 1.0'in p['text']:f.update(rights_label='Public Domain Mark 1.0',rights_status='public_domain',license_url='https://creativecommons.org/publicdomain/mark/1.0/')
def folkwang(rid):
    url='https://sammlung-online.museum-folkwang.de/eMP/eMuseumPlus?module=collection&objectId='+rid+'&service=ExternalInterface&viewType=detailView';mu=museum('de-museum-folkwang','Museum Folkwang','Essen','North Rhine-Westphalia','https://www.museum-folkwang.de/');s,p=soup(url);t=p['text'].splitlines();d={}
    for k in ['Obj_Title1_S:','Obj_Title2_S:','Obj_Dating_S:','Obj_IdentNr_S:','Obj_Material_S:','Obj_Crate_S:','Obj_Creditline_S:','Obj_AccNote_S (Erwerb):']:
        if k in t:d[k]=t[t.index(k)+1]
    title=d['Obj_Title1_S:'];im=next(i['url']for i in p['images']if i['alt']==title);f=add(mu,title,'Vincent van Gogh',d['Obj_Dating_S:'],url,rid,im,d.get('Obj_Material_S:'),d.get('Obj_Crate_S:'),d.get('Obj_IdentNr_S:'),source_receipt=p['receipt'],source_fields=d,alternate_title=d.get('Obj_Title2_S:'),holding_note=d.get('Obj_AccNote_S (Erwerb):'))
    if f:f['creator_credit']=d.get('Obj_Creditline_S:','Museum Folkwang')
def dresden(rid):
    url='https://skd-online-collection.skd.museum/Details/Index/'+rid;s,p=soup(url);title=s.find('h2',string=lambda x:x and x.strip()!='Eine Übersicht zu allen Museen').get_text(' ',strip=True);t=p['text'].splitlines();d={}
    for k in ['Ort, Datierung','Material und Technik','Abmessungen','Museum','Inventarnummer']:
        d[k]=t[t.index(k)+1]
    col=d['Museum'];assert col in ['Albertinum','Gemäldegalerie Alte Meister'],col;slug='de-albertinum'if col=='Albertinum'else'de-gemaeldegalerie-alte-meister-dresden';mu=museum(slug,col+' Dresden'if col!='Albertinum'else'Albertinum – Galerie Neue Meister','Dresden','Saxony','https://skd-online-collection.skd.museum/');cr=t[t.index(title)+1];cr=re.sub(r'\s*\(\d{4}-\d{4}\)','',cr)
    st=str(s);ma=re.search(r'let medien = (\[.*?\]);',st,re.S);med=json.loads(ma[1]);first=med[0];im=urljoin(url,first['LargeImageUrl']);f=add(mu,title,cr,d['Ort, Datierung'],url,rid,im,d['Material und Technik'],d['Abmessungen'],d['Inventarnummer'],source_receipt=p['receipt'],source_fields=d,source_image_fields=first)
    if f:f.update(rights_label='Freier Zugang – Rechte vorbehalten / In Copyright',creator_credit='Staatliche Kunstsammlungen Dresden; '+str(first.get('Reproduktion','')),license_url='https://rightsstatements.org/page/InC/1.0/')
def hamburg():
    url='https://online-sammlung.hamburger-kunsthalle.de/en/objekt/HK-5161/wanderer-ueber-dem-nebelmeer';mu=museum('de-hamburger-kunsthalle','Hamburger Kunsthalle','Hamburg','Hamburg','https://www.hamburger-kunsthalle.de/');s,p=soup(url);im=next(i['url']for i in p['images']if'/multimedia-files/'in i['url']);f=add(mu,'Wanderer über dem Nebelmeer','Caspar David Friedrich','um 1817',url,'HK-5161',im,accession='HK-5161',source_receipt=p['receipt'],date_evidence_note='Museum catalogue dates this work circa 1817; common 1818 labels must not silently replace this evidence.',holding_note='Stiftung Hamburger Kunstsammlungen; loan held by Hamburger Kunsthalle',creator_credit='Hamburger Kunsthalle / Stiftung Hamburger Kunstsammlungen; photo Elke Walford')
if __name__=='__main__':
    a=m.h.load(m.RUN/'local-reference-audit.json.gz');urls=list(dict.fromkeys(x['source_url']for x in a['citations']if x.get('source_url')and'kunsthalle-karlsruhe.de/kunstwerke/'in x['source_url']))[:12];urls.append('https://www.kunsthalle-karlsruhe.de/kunstwerke/Matthias-Gr%C3%BCnewald/Heilige-M%C3%A4rtyrerin-Hl-Bibiana-oder-Hl-Lucia/BD84AEB34B78909078ECCC9D527CF935/')
    for u in urls:guard(karlsruhe,u)
    for u in ['https://guide.landesmuseum-mainz.de/1-og/schau-depot/','https://guide.landesmuseum-mainz.de/2og/moderne/']:
        p=m.page(u)
        for x in p['links']:
            if x['url'].startswith(u)and x['url']!=u and '#'not in x['url']and'einfuehrung'not in x['url']and'dionysosflasche'not in x['url']:guard(mainz,x['url'])
    for era in ['mittelalter','barock','19-jahrhundert']:
        s,p=soup('https://wallraf.museum/sammlungen/'+era+'/meisterwerke/');base=s.find('base')['href']
        for a in s.select('a[href]'):
            if'/das-meisterwerk/'in a['href']and a.get_text(' ',strip=True):guard(wallraf,urljoin(base,a['href']),a.get_text(' ',strip=True))
    for tail in ['strassenszene-friedrichstrasse-berlin','landschaft-4','schuetzengraben']:guard(stuttgart,'https://www.staatsgalerie.de/de/sammlung-digital/'+tail)
    for rid in ['3018','3019']:guard(folkwang,rid)
    for rid in ['241946','372144']:guard(dresden,rid)
    guard(hamburg);b['finish']('final-sources')
