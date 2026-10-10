"""Fourteen selected decorative-art candidates, with native object evidence."""
import gzip,importlib.util,json,time
from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup
z=importlib.util.spec_from_file_location('q',Path(__file__).with_name('museum-expansion-kazantzakis-selection-20261009.py'));q=importlib.util.module_from_spec(z);z.loader.exec_module(q);m=q.m;RUN=m.RUN/'native/kilkis-review-20261010';q.q.RUN=RUN;q.q.CAP=RUN/'captures';q.q.CAP.mkdir(parents=True,exist_ok=True)
NUMBERS=['8260','1577','4475','1613','1422','4174','9328','11918B','4809','11919','9554','5194','9093A','9549'];old=m.load(m.RUN/'native/kilkis-20261010/selected-index-leads-001.json.gz');cards=[v for p in old['pages']for v in p['cards']];selected=[]
for n in NUMBERS:
 vs=[v for v in cards if v['url'].endswith('-'+n)];assert len(vs)==1 and vs[0]['state']=='other_index_record';selected.append(vs[0])
m.save(RUN/'decorative-selection-001.json',dict(at=m.now(),rows=selected,index_reference=q.s.ref(m.RUN/'native/kilkis-20261010/selected-index-leads-001.json.gz'),rationale='Select the previously missed funerary relief8260 plus individually catalogued figured/decorativeceramics,metalvessels,coins/pendants andjewellery. Excludeplainboundary/inscriptionrecords,weapons,and5044grave-assemblagecomponentsuntilphysicalunitsareclear.14of32remainingcards selected;no quota placeholders.'))
rows=[]
for number,v in enumerate(selected,16):
 sid=v['url'].split('/aggregator/edm/')[1];soup,rc=q.q.capture('selected-'+sid.replace('/','-')+'-001',v['url']);fields,enrichment=q.fields(soup);urls=sorted({urljoin(v['url'],a['href'])for a in soup.select('a[href]')if 'efa-kilkis.gr/artworks/'in a['href']and a['href'].rstrip('/')!='https://www.efa-kilkis.gr/artworks'});assert len(urls)==1,(sid,urls);u=urls[0];native,nrc=q.q.capture('native-'+sid.split('/')[-1]+'-001',u);main=native.find('main')or native;attrs={}
 for el in main.select('.pt-attribute'):
  key=q.clean(el.parent.find('label').get_text(' ',strip=True));assert key not in attrs;attrs[key]=q.clean(el.get_text(' ',strip=True))
 period=q.clean(main.select_one('.CardTitle__subtitle').get_text(' ',strip=True));title=q.clean(main.select_one('.CardTitle__title').get_text(' ',strip=True));description=[q.clean(x.get_text(' ',strip=True))for x in main.select('.ContentBlock__body-inner')];image=soup.find('img',src=lambda v:v and '/thumbnails/edm-record/'+sid in v)
 rows.append(dict(number=number,source_id=sid,source_url=v['url'],native_url=u,title=title,inventory_literal=attrs.get('Αριθμός Έργου'),date_display=period,first=None,last=None,date_precision='unknown',creator_label=None,native_fields=attrs,native_description=description,aggregator_literal=fields,aggregator_enrichment=enrichment,source_receipt=rc,native_receipt=nrc,thumbnail_url=urljoin(v['url'],image['src'])if image else None,review_state='candidate_pending_physical_unit_and_live_identity_review',new_production_record=False));print(json.dumps(dict(number=number,source_id=sid,period=period),ensure_ascii=False),flush=True);time.sleep(.12)
m.save(RUN/'decorative-candidate-facts-001.json.gz',dict(at=m.now(),rows=rows,selection_reference=q.s.ref(RUN/'decorative-selection-001.json'),script_reference=q.s.ref(Path(__file__).resolve()),policy='14selectedoriginalobjectpages and14nativepages. Literaldateperiods;nonumericrangesinvented. Cast/drawn/copiedimagesorrelateditemsnotnewphysicalartworks. Freshproductionidentityandeditorialreviewneededbeforeanywrite. Noimageattachments.'))
