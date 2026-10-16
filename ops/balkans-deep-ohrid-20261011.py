"""Selected catalogue icons; prepare locally while production authentication is pending."""
import os,runpy,re
os.environ['ARTLINE_BALKANS_WAVE']='wave3'
b=runpy.run_path('ops/balkans-deep-facts-20261011.py');m=b['m'];fact=b['fact']
d=runpy.run_path('ops/balkans-deep-delivery-20261011.py')
url='https://pubhtml5.com/jjol/ksup/basic/'
p=m.page(url);official=m.page('https://muzejohrid.mk/galerija-na-ikoni/')
mu=dict(slug='mk-icon-gallery-ohrid',name='Icon Gallery, Ohrid',city='Ohrid',country_code='MK',website_url=official['receipt']['url'])
text=m.h.load(m.RUN/'ohrid-icon-catalogue-pages.json')[0]['text']
specs=[(1,'Saint Basil the Great and Saint Nicholas',1045,1050,'Circa 1045–1050','272','110 × 74.5 × 3.5 cm',23),
       (2,'Forty Martyrs of Sebaste',1051,1100,'Second half of the 11th century','14','43.5 × 33 × 2.5 cm',25),
       (3,'Communion of the Apostles',1001,1200,'Late 11th–early 12th century','282','39 × 33 × 2.5 cm',27)]
facts=[]
for n,title,a,z,date,inv,dim,page in specs:
    start=re.search(r'\b'+str(n)+r'\.\s',text).start()
    caption=text[start:start+1100]
    f=fact('ohrid-icons-1999/'+inv,mu['slug'],title,None,'',url,'catalogue-'+str(n),
           'https://online.pubhtml5.com/jjol/ksup/files/large/'+str(page)+'.webp',
           medium='Tempera over gypsum ground on canvas on wood',dimensions=dim,accession=inv,
           original_caption=caption,source_receipt=p['receipt'],
           rights_label='Institute and Museum Ohrid catalogue; photographs credited to Milan Petrović and Milan Džingo; no open reuse licence stated',
           creator_credit='Milan Petrović and Milan Džingo (catalogue photography credit)',
           additional_sources=[dict(url=official['receipt']['url'],receipt=official['receipt'])])
    f.update(start=a,end=z,date_display=date,precision='circa_range'if n==1 else'range',image_eligible=True,
             locator='Milcho Georgievski, Icon Gallery – Ohrid (1999), cat. '+str(n)+'; printed text page '+str(page-5)+', illustration '+str(page-4),
             view_label='Complete illustrated catalogue page; original margins and page number retained; no cropping',
             date_evidence_note='Exact qualified catalogue date retained; numeric bounds conservatively encompass the stated centuries where relevant.')
    facts.append(f)
selection=dict(at=m.h.now(),records=facts,museums=[mu],held=[],user_authorization='Continuation of requested selected Balkan museum artwork and image research.')
m.h.save(m.RUN/'selection-wave3.json',selection)
rows=[dict(fact=f,artwork_id=d['uid']('artwork:'+f['key']),media_id=d['uid']('media:'+f['key']),museum=mu)for f in facts]
prep=dict(at=m.h.now(),target='Local image preparation only; live production identity/preimage plan still required',records=rows,selection_sha256=m.h.sha((m.RUN/'selection-wave3.json').read_bytes()))
m.h.save(m.RUN/'wave3-research-preparation.json',prep)
# The historical file contains three text groups, not individual catalogue pages.
m.h.save(m.RUN/'ohrid-catalogue-index-amendment.json',dict(at=m.h.now(),original_file='ohrid-icon-catalogue-pages.json',correction='page values 1–3 denote public HTML text groups covering viewer pages 1–50, 51–100, 101–117. They are not printed page numbers.',selected_illustrations=[dict(catalogue_number=n,viewer_page=pg,printed_page=pg-4)for n,_,_,_,_,_,_,pg in specs]))
d['images'].__globals__['pinned']=lambda:prep
d['images']()
