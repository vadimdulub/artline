#!/usr/bin/env python3
"""Selected Buchet objects with canvas faces, primary evidence and unknowns explicit."""
import copy, importlib.util, json
from pathlib import Path
sp=importlib.util.spec_from_file_location('campaign',Path(__file__).with_name('creators-deep-4h-20261010.py'))
x=importlib.util.module_from_spec(sp);sp.loader.exec_module(x);x.configure('gustave-buchet')
plan=x.r.load(x.RUN/'research-selection.json.gz');allrows=plan['rows']
selected=[1,2,3,7,8,9,10,11,12,13,14,15,16,17,18]
notes={
1:'Exact portrait matched to MCBA annual report 2018, printed p. 37 image and p. 25 accession 2018-031. The second WikiArt portrait URL is held for duplicate reconciliation and is not another addition.',
2:'Distinct 1918 still life with vase. Exact WikiArt object page, creator identity, date, stable IDs and reproduction reconciled. No independent object record established; medium, dimensions and holdings remain unknown.',
3:'Exact glass and carafe composition matched to MCBA annual report 2013, printed pp. 42–43 image and p. 35 accession 2013-043. The adjacent 1926 Composition avec pinceaux et bouteille is a different object.',
7:'Exact curved-rib and cone composition matches Karl & Faber 2023 lot 438, SIK-ISEA 98033. This is the 1927 front of a canvas with a different seated nude dated 1940 on its reverse. One physical object is added, with this selected face explicit. The reported 73 × 59 cm is image-opening size and is not imported as canvas dimensions. The reverse is not the 1930 back-view nude in row 12.',
8:'Exact vertical landscape and buildings matched to the Sothebys 2020 Swiss Made Unlocked object. Use 91.5 × 73 cm unframed, not 96.9 × 78.1 cm framed. Private collection provenance does not establish museum ownership. Different composition from the 1927 Village corse on the reverse of selected books still life.',
9:'Exact nude and abstract arrangement matched to Germann item 1891. The primary source says circa 1929; preserve this qualification. Its H 775 × W 1085 mm measurements are explicitly framed, so painting dimensions remain unknown.',
10:'Exact yellow-grey seated torso with blue breast matched to Christies lot 5678751. The pale figure holding a white cloth in the separate WikiArt Frauenakt 1930-1 is visibly a different composition despite the identical generic title and date.',
11:'The pale seated nude with white cloth is visibly different from Christies lot 5678751 and from selected row 10. Reject that attempted auction match. Direct WikiArt creator/object identity and full reproduction are consistent; do not borrow the other paintings material, dimensions or provenance.',
12:'Direct WikiArt 1930 back-view nude is distinct from the 1940 seated figure on the reverse of Karl & Faber lot 438. Secondary Sothebys 2011 lot 95 lead remains unverified against a primary lot record; no auction measurements or provenance imported.',
13:'Three Women is a distinct full composition documented by the direct WikiArt page in 1930. Secondary Sothebys 2009 lot 63 lead remains unverified against a primary lot record. Preserve unknown material, dimensions and holdings.',
14:'Exact books still life matches the illustrated reverse of Karl & Faber 2021 lot 534: front Village corse 1927, reverse Nature morte, les livres 1941, SIK-ISEA 92202 and 85307. One physical canvas is added under its selected reverse face; the front is not separately imported. Do not confuse it with the different abstract Composition 1926. Approximate 92 × 60 cm describes the canvas, not a frame.',
15:'Distinct steamer and harbour scene dated 1951 by direct WikiArt. Secondary Sothebys 2008 lot 115 lead remains unverified against primary catalogue evidence. No inferred museum holding or material.',
16:'Exact still life with newspaper matched to Christies lot 5596773, 1952, oil on canvas 54 × 73 cm. Galerie Paul Vallotton and Swiss private collection provenance are not museum holdings.',
17:'Distinct Torse composition dated 1953 by direct WikiArt. Secondary Christies 2007 lot 147 lead remains unverified against a primary object record; preserve unknown dimensions, material and holding.',
18:'Exact harbour-city composition matched to Christies lot 5678752, dated 1955. The source explicitly says oil on cardboard, 54.5 × 38 cm, and European private collection. No museum holding inferred.'}
pdfs={1:('mcba-2018','Musée cantonal des Beaux-Arts, Lausanne: annual report 2018','Printed pp. 25 and 37; PDF pages 26 and 38','2018-031','oil on cardboard mounted on chipboard','80 × 67.5 cm'),3:('mcba-2013','Musée cantonal des Beaux-Arts, Lausanne: annual report 2013','Printed pp. 35 and 42–43; PDF pages 19 and 23','2013-043','oil on canvas','81 × 62 cm'),7:('karl-faber-2023','Karl & Faber, modern art auction catalogue 321, 2023','Lot 438, printed pp. 118–119; PDF page 61','438','oil on canvas',None),14:('karl-faber-2021','Karl & Faber, modern art auction catalogue 303, 2021','Lot 534, printed pp. 98–99; PDF page 51','534','oil on canvas','approximately 92 × 60 cm')}
web={8:('https://www.sothebys.com/en/buy/auction/2020/swiss-made-unlocked/gustave-buchet-landschaft-mit-haeusern-1928','Sothebys, Swiss Made Unlocked, 2020','oil on canvas','91.5 × 73 cm'),9:('https://www.germannauktionen.ch/de/items/1891','Germann Auktionen, object 1891','oil on cardboard',None),10:('https://www.christies.com/en/lot/lot-5678751','Christies, lot 5678751','oil on canvas','73 × 60 cm'),16:('https://www.christies.com/en/lot/lot-5596773','Christies, lot 5596773','oil on canvas','54 × 73 cm'),18:('https://www.christies.com/en/lot/lot-5678752','Christies, lot 5678752','oil on cardboard','54.5 × 38 cm')}
rows=[]
for i in selected:
 row=copy.deepcopy(allrows[i-1]);w=row['work'];note=notes[i]
 row.update(selection_index=i,confidence=.99 if i in pdfs or i in web else .96,editorial_review=note,image_identity_review='Full selected WikiArt reproduction visually inspected on saved reference sheets; exact native images compared where specified. '+note,native_sources=[])
 row['identity_basis']+=' '+note
 if i in (7,14):
  old=w['title'];w['title']=old+(' (recto, 1927)' if i==7 else ' (verso, 1941)');w['alternate_title']=old;w['normalized_title']=x.q.norm(w['title'])
 if i==9:w.update(date_display='c. 1929',date_precision='circa')
 if i in pdfs:
  key,publisher,locator,record,medium,dims=pdfs[i];rc=x.r.load(x.RUN/(key+'-receipt.json'))
  src=dict(url=rc['url'],publisher=publisher,receipt=rc,locator=locator,record_id=record,facts=dict(title=w['title'],date=w['date_display'],medium=medium,dimensions=dims,accession_number=record if i in (1,3) else None,physical_object_note=note),review=note,confidence=.99)
  row['native_sources'].append(src);w.update(work_type='painting',medium_text=medium,dimensions_text=dims)
  if i in (1,3):row['museum_research']=dict(institution_id='93dd39c6-502b-5f86-8582-80a106159187',accession_number=record,native_source_index=0,confidence=.99,basis=note+' Explicit acquisition and collection inventory; no current display claim.')
 if i in web:
  u,publisher,medium,dims=web[i];native=x.r.load(x.RUN/'native-objects'/(x.r.sha(u.encode())+'.json'))
  row['native_sources'].append(dict(url=u,publisher=publisher,receipt=native['receipt'],record_id=u.rsplit('/',1)[-1],facts=dict(title=w['title'],date=w['date_display'],medium=medium,dimensions=dims,holding='No museum ownership established'),review=note,confidence=.99));w.update(work_type='painting',medium_text=medium,dimensions_text=dims)
 rows.append(row)
excluded={4:'Existing linked Composition with a Vase from Vieux-Strasbourg, 1921.',5:'Existing linked Composition avec 7 tubes, 1925.',6:'Held pending primary confirmation of the reported second painted face and physical-object identity. Not the MCBA Composition avec pinceaux et bouteille, and not the 1927 Village corse canvas.',19:'Not selected for this bounded through-1955 image pass; remains eligible for future pre-1971 catalogue research.',20:'Not selected for this bounded through-1955 image pass; remains eligible for future pre-1971 catalogue research.',21:'Not selected for this bounded through-1955 image pass; remains eligible for future pre-1971 catalogue research.',22:'Not selected for this bounded through-1955 image pass; remains eligible for future pre-1971 catalogue research.',23:'Unknown creation date; object-specific dating not established.',24:'Unknown creation date; object-specific dating not established.',25:'Unknown creation date; object-specific dating not established.'}
plan['rows']=rows;plan['held'] += [dict(title=r['work']['title'],source_url=r['source_url'],reason=excluded[i]) for i,r in enumerate(allrows,1) if i not in selected]
plan.update(reviewed_at=x.r.now(),reviewer='Codex object and rendered primary-source visual review',research_limitations=['Nine of fifteen selections have exact primary object corroboration. Six rely on the user-approved WikiArt object source with uncertain fields left unknown.','Two double-sided canvases represented once each, with selected face explicit; reverse-side dates do not silently rewrite the selected face date.','Two same-title Frauenakt images are different compositions. Rejected comparison retained.','Only two MCBA holdings accepted; private auction histories and a museums exhibition of an artists work do not imply ownership.','All additions remain in review. Actual WikiArt image rights labels preserved separately from user source approval.'])
x.c.validate(plan);x.r.save_gz(x.RUN/'reviewed-plan.json.gz',plan);x.r.save_gz(x.RUN/'image-selection.json.gz',plan)
x.r.save(x.RECOVERY/x.SLUG/'cloud-backup.json',x.r.load(x.RECOVERY/'cloud-backup.json'))
print(json.dumps(dict(new=len(rows),native_citations=sum(len(v['native_sources']) for v in rows),holdings=2,source_bodies=x.c.validate(plan))))
