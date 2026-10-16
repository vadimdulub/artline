#!/usr/bin/env python3
"""Reviewed physical-object selection: Hans Holbein the Elder, 10 October 2026."""
import copy, importlib.util, json, re
from pathlib import Path
sp=importlib.util.spec_from_file_location('campaign',Path(__file__).with_name('creators-deep-4h-20261010.py'))
x=importlib.util.module_from_spec(sp);sp.loader.exec_module(x);x.configure('hans-holbein-the-elder')
plan=x.r.load(x.RUN/'research-selection.json.gz');allrows=plan['rows']
STUTTGART='0f4482c4-028c-538d-bb28-580e139c4695'
MUNICH='8bfd5cfe-59b4-4f9b-a621-6c995a804c42'
AUGSBURG='06104102-3941-4edb-ae63-5f4b64faefe1'
BERLIN='7f338394-6c07-5b37-9d63-7b85e66e9007'
grey={9:'ecce-homo',10:'grablegung-christi',11:'auferstehung-christi',12:'dornenkroenung-christi',13:'christus-pilatus',14:None,15:'christus-ruhe',16:'kreuzabnahme-christi',17:'christus-am-oelberg',18:'gefangennahme-christi',19:'christus-dem-hohenpriester',20:'geisselung-christi'}
native={i:'https://www.staatsgalerie.de/de/sammlung-digital/graue-passion-'+v if v else 'https://www.staatsgalerie.de/de/node/49581' for i,v in grey.items()}
native.update({29:'https://www.sammlung.pinakothek.de/en/artwork/01G13YvxkE/hans-holbein-d-ae-1465/priorin-veronika-welser-ehemals-teil-der-basilika-san-paolo-fuori-le-mura-waf-377',34:'https://artsandculture.google.com/asset/ambrosius-and-hans-the-sons-of-the-artist-0102/CgEJxcllxGC6fA',35:'https://www.sammlung.pinakothek.de/en/artwork/RQ4XXMp410/hans-holbein-d-ae-1465/katharinenaltar-martyrium-der-hl-katharina-5297',37:'https://www.sammlung.pinakothek.de/en/artwork/Dj4maPM45A/hans-holbein-d-ae-1465/katharinenaltar-die-hll-ulrich-und-conrad-5296',42:'https://www.sammlung.pinakothek.de/en/artwork/wE4K6QrGZ5',43:'https://www.sammlung.pinakothek.de/en/artwork/Y0GR9bXLRX',44:'https://www.sammlung.pinakothek.de/de/artwork/ApL8B9M4N2/hans-holbein-d-ae/sebastiansaltar-martyrium-des-hl-sebastian'})
notes={
29:'The native catalogue identifies this as the separately surviving portrait fragment WAF 377, formerly part of the Basilica San Paolo panel. It is not a detail crop of an intact new object. Paired image matches the nun, crossed hands, beads, banderole and irregular panel edge. Keep the native circa 1504 qualification. The holding is Augsburg, not Munich.',
34:'Exact paired image match to Berlin Kupferstichkabinett KdZ 2507: two three-quarter heads with identifying inscriptions, 1511. The title-only candidate Portrait of the Artist\'s Sons (row 39) is a visibly different sheet with profile heads and a townscape; it is deferred, not falsely marked duplicate. The source header includes the younger son as a depicted person, while the structured Creator field names the Elder. Link the existing Staatliche Museen umbrella institution and preserve the specific Kupferstichkabinett collection in the citation.',
35:'Exact paired image match to Augsburg 5297, Catherine kneeling beside the wheel and executioner, 1512. Separate inventory and composition from 5296. No composite altarpiece record is added.',
37:'Exact paired image match to Augsburg 5296, Ulrich and Conrad seated at a table under ornament, 1512. Separate inventory and composition from 5297. No composite altarpiece record is added.',
42:'WikiArt image shows Saint Barbara, the front of left wing 669. The native title explicitly identifies Saint Barbara on the front and the Annunciation Angel on the back, while its served photograph shows the back. The paired images therefore represent opposite faces, not an exact face match. The full triptych reference (row 45) visibly includes the identical Barbara panel. One physical wing only is selected.',
43:'WikiArt labels this Maria Der Verkündigung, but the reproduction visibly shows Saint Elisabeth distributing charity, identical to the right wing in the full triptych reference (row 45). Native inventory 668 explicitly identifies Saint Elisabeth on the front and the Annunciation Virgin on the back. Its served image is the back. Correct the new title to the pictured front, retain the WikiArt wording as an alternate source label, and describe both faces in the evidence. Do not create a second object for the reverse. The undated monochrome reproductive print-like source row 53 is held separately; its date and physical identity are not inferred from this panel.',
44:'Exact paired image match to Munich 5352, the 1516 centre panel with Sebastian and bowmen. WikiArt row 45 is a complete triptych view containing this panel and both selected wings; exclude the composite from separate artwork creation.'}
rows=[]
for i in sorted(native):
 row=copy.deepcopy(allrows[i-1]);u=native[i];v=x.r.load(x.RUN/'native-objects'/(x.r.sha(u.encode())+'.json'));t=v['text'];w=row['work']
 row['selection_index']=i;row['confidence']=.97 if i in [42,43] else .99
 if i in grey:
  acc=re.search(r'Inventarnummer (.*?) Medium',t)[1]
  dims=re.search(r'Maße Typ Höhe ([0-9,]+) Einheit cm Typ Breite ([0-9,]+) Einheit cm',t)
  dimensions=dims[1].replace(',','.')+' × '+dims[2].replace(',','.')+' cm'
  title=re.search(r'Metadaten Titel (.*?) Inventarnummer',t)[1]
  credit=re.search(r'Hinweis (.*?) Literatur',t)[1]
  medium='oil-containing mixed technique on spruce wood';iid=STUTTGART;publisher='Staatsgalerie Stuttgart: digital collection'
  note='Exact individual panel image matched against the native collection reproduction. Title, composition, 1494–1500 date range and unique inventory identify this physical panel. Keep the German native title and source wording distinct from the WikiArt translation. Exclude the two full Grey Passion composite entries. '
  if i==10:note+='The native title is Entombment of Christ (Grablegung), while WikiArt uses Lamentation; the depicted group placing Christ in the tomb is identical. '
  if i in [13,14]:note+='The native credit explicitly records a loan: '+credit+'. This is a holding/custody link, not an assertion that the museum owns the panel. '
  note+='No current-display claim is imported.'
  facts=dict(title=title,date='between 1494 and 1500',medium=medium,dimensions=dimensions,accession=acc,collection_credit=credit,actual_native_rights_label='gemeinfrei')
 elif i==34:
  acc='KdZ 2507';dimensions='10.3 × 15.5 cm';medium='silverpoint on white prepared paper; revisions in pen and ink';iid=BERLIN;publisher='Kupferstichkabinett, Staatliche Museen zu Berlin via Google Arts & Culture';note=notes[i]
  facts=dict(title='Ambrosius and Hans, the sons of the artist',creator='Hans Holbein the Elder',date='1511',medium=medium,dimensions=dimensions,accession=acc,collection='Kupferstichkabinett, Staatliche Museen zu Berlin',actual_native_image_credit='Photo © bpk / Kupferstichkabinett, Staatliche Museen zu Berlin – Preußischer Kulturbesitz / Jörg P. Anders; text © Staatliche Museen zu Berlin / Hans Mielke')
 else:
  acc=re.search(r'(?:Inventory number|Inventarnummer) (.*?) (?:Acquisition|Erwerb)',t)[1]
  dimensions=re.search(r'(?:Dimensions of the object|Maße des Objekts) (.*?) (?:Displayed|Ausgestellt)',t)[1].replace(',','.').replace(' x ',' × ')
  support=re.search(r'(?:Material / Technology / Carrier|Material / Technik / Bildträger) (.*?) (?:Dimensions of the object|Maße des Objekts)',t)[1]
  medium=('painting on fir wood (Abies sp.)' if i==29 else 'painting on conifer wood' if i in [35,37] else 'painting on lime wood (Tilia sp.)')
  iid=AUGSBURG if i in [29,35,37] else MUNICH;publisher='Bayerische Staatsgemäldesammlungen: collection catalogue';note=notes[i]
  facts=dict(title=v['title'].removeprefix('Sammlung | '),date='circa 1504' if i==29 else '1512' if i in [35,37] else '1516',support=support,dimensions=dimensions,accession=acc,collection='Staatsgalerie in der Katharinenkirche Augsburg' if iid==AUGSBURG else 'Alte Pinakothek München',actual_native_image_label='CC BY-SA 4.0')
  if i==29:w.update(date_display='c. 1504',date_precision='circa')
  if i==43:
   w['alternate_title']=w['title'];w['title']='Saint Elisabeth (Saint Sebastian Altarpiece, right wing)';w['normalized_title']=x.q.norm(w['title'])
 row['editorial_review']=note;row['identity_basis']+=' '+note
 row['image_identity_review']='Selected original WikiArt reproduction visually inspected with the native object reference on saved comparison sheets. '+note
 w.update(medium_text=medium,dimensions_text=dimensions,work_type='drawing' if i==34 else 'painting')
 row['native_sources']=[dict(url=u,publisher=publisher,receipt=v['receipt'],record_id=acc,facts=facts,review=note,confidence=row['confidence'])]
 row['museum_research']=dict(institution_id=iid,accession_number=acc,native_source_index=0,confidence=row['confidence'],basis=note+' Collection attribution is separate from the approved WikiArt image source and its actual rights label.')
 rows.append(row)
excluded={40:'Exact visual match to existing Unterlinden Portrait de femme 8023f578-208c-4d54-96bf-fdac9d402989, despite untranslated creator and title. Native page has internally inconsistent 1510–1512 prose and circa 1515 date field; preserve existing record.',45:'Composite triptych image contains the three selected physical panels 668, 669 and 5352. No additional physical object.',49:'Existing exact WikiArt object.',50:'Existing exact WikiArt object.',51:'Existing exact WikiArt object.',52:'Existing exact WikiArt object.',53:'Undated monochrome reproductive print-like image with a surrounding printed border. Cannot assume the painting date or physical identity of panel 668.'}
plan['rows']=rows
plan['held'] += [dict(title=v['work']['title'],source_url=v['source_url'],reason=excluded.get(i,'Outside this bounded personal study selection. No image delivery or production creation. Further object/version/attribution research remains.')) for i,v in enumerate(allrows,1) if i not in native]
plan['reviewed_at']=x.r.now();plan['reviewer']='Codex editorial and paired visual research'
plan['additional_identity_inventory']=dict(path=str((x.RUN/'expanded-existing-records.json.gz').relative_to(x.ROOT)),sha256=x.r.sha((x.RUN/'expanded-existing-records.json.gz').read_bytes()),records=20)
plan['research_limitations']=['19 selected physical objects out of 53 direct source candidates; artist coverage remains incomplete.','No generated images, reconstructed dates, modern display claims or wholesale biography changes.','Native photographs for the two Sebastian wings show their backs; the selected WikiArt images show the fronts. Title correction and physical face relation are explicit.','After-the-Elder engravings in the comparison inventory are different physical works, not silently merged with paintings. The possible Fillian/Cromwell source attribution error remains untouched.','Grey Passion images vary in age and colour reproduction; all exact physical compositions were checked.']
# Check museum identities independently of creator labels and WikiArt identifiers.
with x.r.connect('production') as db,db.transaction():
 db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
 collisions=[]
 for row in rows:
  h=row['museum_research'];iids=[h['institution_id']]
  if h['institution_id']==MUNICH:iids+=['f8c6649e-7d37-5cb2-b1e1-ba134ac75258']
  found=db.execute('SELECT id::text,title,accession_number,current_institution_id::text FROM artworks WHERE current_institution_id=ANY(%s::uuid[]) AND accession_number=%s',(iids,h['accession_number'])).fetchall()
  collisions.extend(found)
 urls=list(native.values());collisions+=db.execute("SELECT entity_id::text,source_url FROM citations WHERE entity_type='artwork' AND source_url=ANY(%s)",(urls,)).fetchall()
 assert not collisions,collisions
x.r.save(x.RUN/'native-identity-collision-check.json',dict(at=x.r.now(),bounded_by='Selected institution IDs and accession numbers; exact native object citation URLs',collisions=collisions,local_database_connected=False))
x.c.validate(plan)
x.r.save_gz(x.RUN/'reviewed-plan.json.gz',plan);x.r.save_gz(x.RUN/'image-selection.json.gz',plan)
x.r.save(x.RECOVERY/x.SLUG/'cloud-backup.json',x.r.load(x.RECOVERY/'cloud-backup.json'))
print(json.dumps(dict(new=len(rows),native_citations=len(rows),holding_links=len(rows),source_bodies=x.c.validate(plan))))
