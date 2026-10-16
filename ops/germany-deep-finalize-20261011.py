"""Evidence amendments and three selected independent image matches; no DB access."""
import runpy,json,io,collections
from pathlib import Path
import requests
from PIL import Image,ImageOps,ImageDraw,ImageFont
mod=runpy.run_path('ops/germany-deep-facts-20261011.py');m=mod['m'];x=m.h.load(m.RUN/'selection-reviewed.json')
rc=m.h.load(m.RUN/'albertinum-guide-receipt.json');url=rc['url']
rows=[
 ('Das Kreuz im Gebirge (Tetschener Altar)','Caspar David Friedrich','1807/08','Öl auf Leinwand','115.7 × 111.5 cm','Gal.-Nr. 2197 D',32),
 ('Blick auf Dresden bei Vollmondschein','Johan Christian Dahl','1839','Öl auf Leinwand','78 × 130 cm','Gal.-Nr. 2206 D',34),
 ('Der Brautzug im Frühling','Ludwig Richter','1847','Öl auf Leinwand','93 × 150 cm','Gal.-Nr. 2230',36),
 ('Das Pfirsichglas','Claude Monet','um 1866','Öl auf Leinwand','55.5 × 46 cm','Gal.-Nr. 2525 B',42),
 ('Sandsturm in der Libyschen Wüste','Max Slevogt','1914','Öl auf Leinwand','73.5 × 95.5 cm','Gal.-Nr. 2547',44),
 ('Eisenbahnüberführung Löbtauer Straße in Dresden','Ernst Ludwig Kirchner','1910/26','Öl auf Leinwand','70.5 × 90.5 cm','Inv.-Nr. 99/07',48),
 ('Alte Frau mit Hut','Paula Modersohn-Becker','um 1905','Öl auf Pappe auf Hartfaserplatte','64.5 × 40 cm',None,50),
 ('Gitta Wallerstein','Oskar Kokoschka','1921','Öl auf Leinwand','85 × 60 cm','Inv.-Nr. 2014/04',52),
 ('Der Krieg (Triptychon)','Otto Dix','1929/32','Mischtechnik auf Holz','Central panel 204 × 204 cm; wings each 204 × 102 cm; predella 60 × 204 cm','Gal.-Nr. 3754',54),
]
supp=[]
for title,creator,dt,medium,dims,inv,pg in rows:
    native=inv or'guide-page-50';f=dict(key='albertinum.skd.museum/'+native,museum_slug='de-albertinum',title=title,creator=creator,**mod['date'](dt),medium=medium,dimensions=dims,accession=inv,source_url=url,source_record_id=native,source_receipt=rc,locator=f'Printed page {pg}; complete object caption and credit on printed pp. 68–69 (PDF page 35)',image_url=None,image_eligible=False,work_type='painting',status='review',current_display='Not asserted',holding_review='Museum guide documents Albertinum / Galerie Neue Meister',selection_basis='Selected pre-1971 paintings from the museum’s curated accessible collection guide',view_label='No image selected',rights_status='restricted',rights_label='Museum guide rights retained; metadata transcription only',creator_credit='Albertinum | Galerie Neue Meister, Staatliche Kunstsammlungen Dresden')
    if creator=='Paula Modersohn-Becker':f.update(holding_note='Leihgabe aus Privatbesitz im Albertinum | GNM',holding_review='Private collection loan documented by museum; museum ownership not asserted')
    if creator=='Ernst Ludwig Kirchner':f['date_evidence_note']='The museum gives 1910/26: original work and later reworking, preserved as multiple phases rather than one invented year.'
    if creator=='Otto Dix':f['date_evidence_note']='Museum guide: 1929/32; WikiArt: 1932, completion year. This is the four-panel painting, not the 1924 print portfolio.'
    supp.append(f)
m.h.save(m.RUN/'selection-supplemental.json',dict(records=supp,source=rc,review='Nine eligible paintings. Later works and Reynolds’s comparative Frick Collection portrait excluded; physical sculpture cast dates require separate review.'))
x['records'].extend(supp)
for f in x['records']:
    if f['key']=='www.sammlung.pinakothek.de/0vxogyXx2V':
        f.update(work_type='sculpture',date_evidence_note='Museum dates the work circa 1880/82; exact bronze casting year not stated. Its documented acquisition in 1912 establishes existence before the image cutoff. No casting year invented.')
    if f['museum_slug']=='de-landesmuseum-hannover' and f['accession']in['WM XXIII, 83','KM 25','PAM 983','KA 156/1967','L 029','KM 125/1949','KM 123/1954']:
        f['view_label']='Museum-published detail; complete supplied file retained, no additional cropping.'
    if f['museum_slug']=='de-germanisches-nationalmuseum':f['view_label']='Museum documentation photograph, including colour target / credit strip; original frame retained.'
    if f['museum_slug']=='de-ikonenmuseum-frankfurt':
        if f['accession']=='IH977':f['view_label']='Front view of painted cross; reverse decoration not shown.'
        if f['accession']=='IHM953':f['view_label']='Icon with its metal cover (oklad); source view retained.'
    if f['museum_slug']=='de-alte-pinakothek' and 'Columba'in f['title']:f['view_label']='Central Adoration panel of the St Columba Altarpiece; complete supplied panel image.'
facts={f['key']:f for f in x['records']}
matches=[
 (next(f for f in x['records']if f['museum_slug']=='de-mdbk-leipzig'and'Lebensstufen'in f['title']), 'https://www.wikiart.org/en/caspar-david-friedrich/the-stages-of-life','https://uploads3.wikiart.org/00142/images/caspar-david-friedrich/the-stages-of-life.jpg!Large.jpg','Public domain','public_domain','WikiArt gives 1835; museum caption gives um 1834. Creator, composition, title and explicit Leipzig holding establish the same painting. Museum date retained.','1835'),
 (next(f for f in x['records']if f['museum_slug']=='de-gemaeldegalerie-alte-meister-dresden'),'https://www.wikiart.org/en/raphael/the-sistine-madonna-1513','https://uploads3.wikiart.org/00340/images/raphael/the-sistine-madonna-1513.jpg!Large.jpg','Public domain','public_domain','Exact whole composition, Raphael attribution and explicit Dresden holding match the SKD object. Museum 1512/1513 and WikiArt 1513 retained.','1513'),
 (supp[-1],'https://www.wikiart.org/en/otto-dix/war-1932','https://uploads6.wikiart.org/images/otto-dix/war-1932.jpg!Large.jpg','Otto Dix / Fair Use','restricted','Whole four-panel painting matches museum guide printed pp. 54–57 and inventory Gal.-Nr. 3754; WikiArt explicitly locates it at Galerie Neue Meister, Dresden. Not the 1924 prints.','1932')
]
ind=[]
for f,source,imurl,rights,status,note,wdate in matches:
    p=m.page(source);tag=m.h.sha((f['key']+'independent').encode())[:24];original=m.ORIGINALS/(tag+'.source');rp=m.ORIGINALS/(tag+'.receipt.json');out=m.RUN/'images'/(tag+'.jpg')
    if original.exists():raw=original.read_bytes();receipt=m.h.load(rp);assert m.h.sha(raw)==receipt['sha256']
    else:
        r=requests.get(imurl,timeout=(15,50));r.raise_for_status();raw=r.content;assert len(raw)<30000000
        receipt=dict(url=imurl,final_url=r.url,status=r.status_code,content_type=r.headers.get('Content-Type'),sha256=m.h.sha(raw),bytes=len(raw),retrieved_at=m.h.now(),source_receipt=p['receipt']);original.write_bytes(raw);m.h.save(rp,receipt)
    im=ImageOps.exif_transpose(Image.open(io.BytesIO(raw))).convert('RGB');original_size=im.size;im.thumbnail((1500,1500));quality=88
    while True:
        buf=io.BytesIO();im.save(buf,'JPEG',quality=quality,optimize=True);data=buf.getvalue()
        if len(data)<=100000:break
        if quality>54:quality-=6
        else:im.thumbnail((int(im.width*.86),int(im.height*.86)));quality=82
    out.write_bytes(data);view='Complete WikiArt reproduction; original framing retained, proportional resizing without cropping'
    f.update(image_eligible=True,image_evidence_note=note,independent_image_source=source,independent_image_date=wdate)
    ind.append(dict(key=f['key'],museum_slug=f['museum_slug'],title=f['title'],creator=f['creator'],file=str(out.relative_to(m.RUN)),original_path=str(original),receipt=receipt,sha256=m.h.sha(data),bytes=len(data),width=im.width,height=im.height,original_size=original_size,source_url=source,holding_source_url=f['source_url'],image_url=imurl,view_label=view,rights_status=status,rights_label=rights,creator_credit='Otto Dix / WikiArt'if status=='restricted'else f['creator']+' / WikiArt',identity_note=note,source_date=wdate,editorial_identity_confidence=.98,source_policy='User-approved WikiArt source policy, 6 October 2026; preserved separately from actual rights label. Not a new licence grant.'))
m.h.save(m.RUN/'independent-images.json',ind)
images=m.h.load(m.RUN/'images-prepared-resolved.json')
for im in images:im['view_label']=facts[im['key']]['view_label']
images.extend(ind)
m.h.save(m.RUN/'images-review-candidates.json',images)
x['supplemental_review']='Nine Albertinum paintings added from the museum guide; caption-based and visual image-view labels amended; original evidence retained.'
m.h.save(m.RUN/'selection-final.json',x)
font=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',18);sheet=Image.new('RGB',(1500,740),'#e8e5df');d=ImageDraw.Draw(sheet)
for j,r in enumerate(ind):
    im=Image.open(m.RUN/r['file']);im.thumbnail((470,650));sheet.paste(im,(j*500+(500-im.width)//2,5+(650-im.height)//2));d.text((j*500+10,665),r['title'][:43],font=font,fill='black');d.text((j*500+10,695),r['rights_label'],font=font,fill='black')
sheet.save('/tmp/artline-germany-delivery/independent-contact.jpg')
print('FINAL',len(x['records']),'IMAGES',len(images),'MUSEUMS',len({i['museum_slug']for i in images}))
