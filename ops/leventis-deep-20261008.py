#!/usr/bin/env python3
"""Selected Leventis object research and production delivery with pinned evidence."""
import base64,collections,concurrent.futures,hashlib,importlib.util,io,json,re,subprocess,sys,unicodedata,uuid
from pathlib import Path
from urllib.parse import quote
import requests,pymupdf
from PIL import Image,ImageOps,ImageDraw
from psycopg import sql
from psycopg.types.json import Jsonb
spec=importlib.util.spec_from_file_location('alignment',Path(__file__).with_name('align-catalogues-20261008.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
OP='leventis-deep-20261008';RUN=m.ROOT/'docs/research'/OP;BACKUP=Path.home()/'Library/Application Support/Artline/backups'/OP;TEMP=Path('/tmp/artline-leventis-deep-20261008');ORIGINALS=Path.home()/'Library/Application Support/Artline/source-images'/OP
NS=uuid.uuid5(uuid.NAMESPACE_URL,'https://artlines.org/research/'+OP)
def uid(x):return str(uuid.uuid5(NS,x))
def norm(x):return re.sub(r'[^a-z0-9]+',' ',unicodedata.normalize('NFKD',x or '').encode('ascii','ignore').decode().lower()).strip()
def code(x):return re.sub(r'[^A-Z0-9.]','',str(x).upper().replace('AGLG',''))
def insert(db,t,row):
 keys=list(row);db.execute(sql.SQL('INSERT INTO {} ({}) VALUES ({})').format(sql.Identifier(t),sql.SQL(',').join(map(sql.Identifier,keys)),sql.SQL(',').join(sql.Placeholder() for _ in keys)),[row[k] for k in keys])
def data():return m.load(RUN/('selection-reviewed.json' if (RUN/'selection-reviewed.json').exists() else 'selection.json'))
def select():
 facts=m.load(RUN/'web-facts.json');out=[];held=[]
 # Duplicate museum pages, malformed date fields, grouped objects and colliding native inventory codes are reviewed explicitly.
 skip={4765:'Duplicate AGLG 315; 1950 typo conflicts with the native 1650 record 6625.',4760:'Duplicate AGLG 454: use complete object record 6602.',4758:'Duplicate AGLG 276: use complete object record 6598.',6706:'Creator field incorrectly says Othon Friesz while signed Miró. Missing inventory/date/medium; retained as a research lead.',6610:'Both 6609 and 6610 claim AGLG 557 for different compositions. Resolve accession collision before adding.',6609:'Both 6609 and 6610 claim AGLG 557 for different compositions. Resolve accession collision before adding.',6644:'One web entry combines three objects AGLG 302/303/304; preserve existing aggregate and hold image/splitting pending inventory-to-composition mapping.',6655:'Two distinct sheets AGLG 309/310 on one web entry; preserve aggregate, do not attach a misleading single-sheet image.',4771:'Malformed date fields include 1900 and testing text; coins outside selected painting/drawing/print expansion.',6822:'Coin outside this selected fine-art pass.',4774:'Coin outside this selected fine-art pass.',4769:'Coin outside this selected fine-art pass.',4768:'Medal without creation date outside this selected fine-art pass.',4767:'BCE coin date field loses era; outside selected fine-art pass.'}
 for f in facts:
  n=f['wp_id'];h=f['headings']
  if n in skip:held.append(dict(key='wp:'+str(n),title=f['title'],reason=skip[n]));continue
  medium=next((x.split(':',1)[1].strip() for x in h if x.startswith('Medium:')),'').replace('Οil','Oil').replace('Εtching','Etching')
  dim=next((x.split(':',1)[1].strip() for x in h if x.startswith('Dimensions:')),None)
  acc=next((x.split(':',1)[1].strip() for x in h if x.startswith('Code:')),None)
  ds=h[h.index('Year:')+1:] if 'Year:'in h else [];ds=[x for x in ds if not x.startswith('Code:')];raw=' '.join(ds);yr=[int(x) for x in ds if re.fullmatch(r'\d{3,4}',x)];yr+=[int(x[2:]) for x in ds if re.fullmatch(r'- \d{3,4}',x)]
  start=end=None;precision='unknown';display='Creation date unknown';reason='No reliable creation date supplied; preserve unknown.'
  if yr and len(yr)<=2 and all(1<=x<=2026 for x in yr):
   start=min(yr);end=max(yr);precision='exact' if start==end else 'range';display=str(start) if start==end else f'{start}–{end}';reason='Native object Year field, checked against accompanying entry; publication/acquisition dates excluded.'
  if '1950s' in raw:start,end,precision,display,reason=1950,1959,'decade','1950s'+('?' if '?'in raw else ''),'Qualified decade from native object field; image not approved under by-1955 source extension.'
  # Specific signed dates and authored catalogue statements outrank demonstrably erroneous form fields.
  if n==6654:start=end=1783;display='1783';precision='exact';reason='Signed and dated J. B. hüet 1783 in bilingual object entry; reject form field 1782.'
  if n==4746:start=end=1955;display='1955';precision='exact';reason='Authored object note explicitly says Trellises and Shadows, of 1955; retain conflicting form-field 1954 in evidence.'
  if n==4744:start=end=1893;display='1893';precision='exact';reason='Museum-authored Smartify entry AGLG 223 explicitly gives 1893, 55 x 55 cm; native 1983 typo conflicts with creator chronology and text referencing 1894 competition.';dim='55 x 55 cm'
  if n==6629:start=end=None;display='Creation date unknown';precision='unknown';reason='Form-field 1611–1657 reproduces one proposed sitter lifespan; not a creation date.'
  if n==6606:reason='Native range 1954–1963 is consistent with the entry’s period for the recurring lovers theme; retain as uncertain dating, not exact year.';precision='circa_range';display='c. 1954–1963'
  if n==4734:dim=None;held.append(dict(key='wp:'+str(n),title=f['title'],reason='1971 creation outside <=1970 additions; existing record retained and documented date can be corrected. Malformed dimensions testing ignored.'))
  creators=f['creator'];creator='; '.join(creators) or None
  if n==6772:creator='Camille Pissarro' # C. Pissarro 1901 signature plus Pissarro catalogue raisonné no.1394.
  if n==6669:creator='Louis-Auguste le Clerc or Jacques-Sébastien le Clerc' # Alternative authorship in catalogue discussion, not flattened form label.
  typ='painting' if medium.lower().startswith('oil') else 'print' if any(x in medium.lower() for x in ['etching','aquatint','engraving']) else 'watercolor' if any(x in medium.lower() for x in ['watercolour','bodycolour','gouache']) else 'drawing'
  out.append(dict(key='wp:'+str(n),wp_id=n,title=f['title'],creator=creator,accession=acc,medium=medium or None,dimensions=dim,start=start,end=end,precision=precision,date_display=display,work_type=typ,url=f['url'],locator='Native object page, metadata panel and catalogue entry',source_kind='web',image_url=f['image_url'],source_sha256=f['sha256'],date_evidence=reason,raw_date=raw,content_evidence=f['content'],html_path=f['html_path'],image_eligible=end is not None and end<=1955 and n!=4734))
 def pdf(y,page,acc,title,creator,medium,dimensions,start=None,end=None,precision=None,xref=None,note=None):
  end=start if end is None else end
  display='Creation date unknown' if start is None else str(start) if start==end else f'{start}–{end}'
  if precision=='century':display=f'{(start-1)//100+1}th century'
  if precision=='circa':display='c. '+display
  if precision=='circa_range':display='c. '+display
  path=BACKUP/'publications'/f'{y}.pdf';url='https://www.leventisgallery.org/assets/uploads/'+('Annual_Report_' if y==2017 else 'Annual-Report_')+str(y)+'.pdf'
  out.append(dict(key='pdf:'+code(acc),title=title,creator=creator,accession='AGLG '+acc,medium=medium,dimensions=dimensions,start=start,end=end,precision=precision or ('unknown' if start is None else 'exact' if start==end else 'range'),date_display=display,work_type='print' if any(x in medium.lower()for x in ['etching','print','engraving','lithograph','mezzotint']) else 'painting' if medium.startswith('Oil') else 'watercolor' if any(x in medium.lower()for x in ['watercolour','tempera']) else 'drawing',url=url,locator=f'Report {y}, PDF page {page}, accession AGLG {acc}; acquisition/donation caption',source_kind='pdf',pdf_year=y,pdf_page=page,xref=xref,source_sha256=m.digest(path),date_evidence=note or ('Date explicitly transcribed from object caption; report/acquisition year is not a creation date.' if start else 'Caption omits creation date. Artist life dates and acquisition year are not substituted.'),image_eligible=end is not None and end<=1955 and xref is not None))
 pdf(2017,55,'765','Nude / Venus, frontispiece for Stéphane Mallarmé’s Pages','Pierre-Auguste Renoir','Etching',None,1890,1891,xref=601)
 pdf(2017,55,'766','Caterina Cornaro','Copy after Titian','Oil painting',None,note='Report calls this a copy of the Uffizi painting; copy maker and date unknown. Medium not specified; corrected to unknown in editorial pass.')
 out[-1]['medium']=None;out[-1]['work_type']='painting'
 pdf(2018,50,'775','Office of N. I. Saripolos','Athena N. Saripolou','Watercolour','41 x 32 cm')
 pdf(2018,50,'779','Still Life with Watermelon','Agenor Asteriadis','Tempera on paper','22 x 26 cm')
 pdf(2018,50,'780','Figure','Yannis Gaitis','Ink on paper','35 x 25 cm')
 pdf(2018,51,'784','Still Life (No Title)','Christoforos Savva','Oil on canvas','60 x 73 cm',1957)
 pdf(2019,60,'912','Saint Paul’s Column, Paphos','Tristram Ellis','Watercolour on paper','25.8 x 17.5 cm',1879,xref=522)
 pdf(2019,60,'913','Famagusta Harbour','John Thomson','Oil on canvas','30 x 51 cm',1879,xref=517,note='1879 explicitly in caption; named John Thomson is not linked to existing namesake who died 1840.')
 for acc,title,dim,yr,xref,page in [('1004','Ground-floor Corridor','43.8 x 31 cm',1882,519,60),('1005','Piano Room','39.5 x 30.5 cm',1882,520,60),('1006','The Bedroom of My Sister, Penelope','30.5 x 38.8 cm',None,None,60),('1007','The N. I. Saripolou Family Gathering with Music','36.5 x 30.2 cm',None,None,60),('1008','My Father’s and Mother’s Bedroom','30 x 30.5 cm',None,None,61),('1009','Bedroom','35.2 x 30.7 cm',None,None,61),('1010','Entrance to the Stairs','34.6 x 30.7 cm',None,None,61),('1011','The Living Room of My Father’s House','33 x 30.7 cm',None,None,61),('1012','Bedroom with Blue Curtains','30.3 x 38.2 cm',None,None,61)]:pdf(2019,page,acc,title,'Athina N. Saripolou','Print',dim,yr,xref=xref)
 pdf(2019,61,'1023','Boats on the Scheldt River','Pericles Pantazis','Oil on canvas','41.5 x 56 cm')
 pdf(2019,62,'1024','Self-portrait of the Artist','Pericles Pantazis','Oil on canvas','46 x 37 cm')
 pdf(2019,66,'943','Constantinople: The Sultan Going to the Mosque','Samuel Davenport','Steel engraving with hand-colouring','20.5 x 27.5 cm',1843,xref=636)
 pdf(2019,66,'944','State Prison of the Seven Towers, Looking over the Sea of Marmora','William Henry Capone','Steel engraving with hand-colouring','20.5 x 27.5 cm')
 pdf(2019,67,'948','Views in Constantinople','Edward J. Whymper','Wood engraving with hand-colouring','26 x 18.5 cm',1876,precision='circa',xref=654)
 pdf(2019,67,'949A','View of Pera, Constantinople','Augustin François Lemaître','Steel engraving with hand-colouring','12.5 x 17.2 cm',1838,xref=656)
 pdf(2019,67,'949B','Constantinople from Pera','Edward Finden','Steel engraving with hand-colouring','13.3 x 15.3 cm',1856,xref=666)
 pdf(2019,68,'950','Alexander the Great','John Chapman','Copperplate engraving','16.3 x 11 cm')
 pdf(2019,68,'951','Victoria, Aug. 10th 1835','John Cochran','Engraving with hand-colouring','17 x 12 cm',1836,xref=684)
 pdf(2019,68,'952','Her Most Gracious Majesty Queen Victoria','William Holl the Younger','Engraving with hand-colouring','17 x 12 cm',1838,1844,precision='circa_range',xref=686)
 pdf(2019,68,'953','Her Majesty the Queen','Charles Edward Wagstaff','Mezzotint with hand-colouring','17 x 12 cm',1838,xref=678)
 pdf(2019,68,'954','Queen Victoria','John Henry Robinson','Engraving with hand-colouring','22 x 16 cm',1847,xref=680)
 pdf(2019,68,'955','Queen Victoria, Golden Jubilee Portrait',None,'Coloured print on wood','36.4 x 30 cm',1887,xref=676)
 pdf(2019,69,'957','Franz Joseph I, Emperor of Austria','Pierre Guillaume Metzmacher','Steel engraving with hand-colouring','24 x 18 cm',1867,xref=697)
 pdf(2019,69,'958','His Majesty King George III Returning from Hunting','Matthew Dubourg','Coloured lithograph','33 x 46.5 cm',1820,xref=699)
 pdf(2019,69,'959','Campaign Poster of Theodore Roosevelt',None,'Print','50 x 40 cm',1912,xref=691)
 pdf(2019,69,'960','Alexander the Great Framed by War Scenes and Portraits of His Generals','François Müller','Engraving','45 x 29 cm')
 for i,dim in enumerate(['25.4 x 35.5','25.1 x 35.3','25 x 35.3','35.4 x 25.4','26 x 37','25.5 x 35.5']):pdf(2020,53,str(1099+i),'Untitled','Loukia Nikolaides-Vasiliou',('Watercolour and pencil on paper' if i<2 else 'Watercolour on paper'),dim+' cm')
 dims=['35.5 x 25.5','25.5 x 35.5','22 x 30','35.5 x 25.4','25.5 x 35.5','25.3 x 35.5','25.5 x 35.5','25.4 x 35.5','38.5 x 28.4','35.5 x 25.5','29 x 39.5','25.5 x 35.5']
 for i,dim in enumerate(dims,1):pdf(2020,54 if i<=6 else 55,'1105.'+str(i),'Untitled watercolour sketch','Loukia Nikolaides-Vasiliou','Watercolour on paper' if i in [5,6] else 'Watercolour and pencil on paper',dim+' cm',note='One individually accessioned sheet from a selection of 16 sketches; only 12 individually captioned sheets are selected. Date unknown.')
 pdf(2021,38,'1115','Young Drinker','Pericles Pantazis','Oil on wood','34 x 22.5 cm',1871,xref=187)
 pdf(2021,38,'1116','Resting by a Haystack','Theodore Ralli','Oil on canvas','28.5 x 39.5 cm',1801,1900,precision='century',xref=188)
 pdf(2021,38,'1117','The Queen of Cyprus, Caterina Cornaro, and Her Sister Cornelia','Venetian School','Oil on canvas','116 x 137 cm',1501,1600,precision='century',xref=189)
 pdf(2022,52,'1133','Vase with Flowers and Apples','Pericles Pantazis','Oil on canvas','41 x 55 cm')
 result=dict(at=m.now(),selected=out,held=held,source_scope='Selected official catalogue objects and accessioned fine-art acquisitions from Reports 2017–2022. No temporary exhibition loans imported as ownership.');m.save(RUN/'selection.json',result);print('SELECTED',len(out),'web',sum(x['source_kind']=='web' for x in out),'PDF',sum(x['source_kind']=='pdf' for x in out),'image eligible',sum(x['image_eligible'] for x in out))

def prepare():
 selection=data();decisions=m.load(RUN/'creator-decisions-reviewed.json');stamp=m.now();sources={'web':dict(id=uid('source:web'),slug=OP+'-objects',name='A. G. Leventis Gallery — official collection object catalogue',source_type='collection_page',base_url='https://leventisgallery.org/artworks/')}
 for y in sorted({x['pdf_year']for x in selection['selected'] if x['source_kind']=='pdf'}):sources[str(y)]=dict(id=uid('source:'+str(y)),slug=OP+'-report-'+str(y),name=f'A. G. Leventis Gallery — Report {y}',source_type='book',base_url=next(x['url']for x in selection['selected']if x.get('pdf_year')==y))
 plan=dict(at=stamp,sources=list(sources.values()),records=[],held=selection['held'],selection_sha256=m.digest(RUN/'selection-reviewed.json'),artist_decisions_sha256=m.digest(RUN/'creator-decisions-reviewed.json'))
 with m.connect('production')as db:
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
  inst=db.execute("SELECT to_jsonb(i) r FROM institutions i WHERE slug='leventis-gallery'").fetchone()['r'];iid=inst['id'];plan['institution']=inst
  old=db.execute("SELECT to_jsonb(a) r FROM artworks a WHERE current_institution_id=%s ORDER BY a.id",(iid,)).fetchall();ids=[x['r']['id']for x in old];links=m.select_rows(db,'artwork_artists','artwork_id',ids);locations=m.select_rows(db,'artwork_location_assertions','artwork_id',ids);ext=m.select_rows(db,'external_identifiers','entity_id',ids)
  codes=collections.defaultdict(list)
  for x in old:codes[code(x['r']['accession_number'])].append(x['r'])
  plan['duplicate_existing_accessions']={k:v for k,v in codes.items()if len(v)>1};plan['scoped_before']=dict(artworks=old,creators=links,locations=locations,external=ext)
  for f in selection['selected']:
   matches=codes[code(f['accession'])];before=next((x for x in matches if x['primary_media_id']),matches[0]if matches else None)
   if before is None and f['end'] is not None and f['end']>1970:plan['held'].append(dict(key=f['key'],reason='Creation after 1970; not imported.'));continue
   aid=before['id']if before else uid('artwork:'+f['key']);artist=decisions[f['creator']or'Unknown']['artist_id'];existing_links=[x for x in links if str(x['artwork_id'])==aid]
   if existing_links:artist=None # Preserve the exact established creator attribution.
   patch={}
   if before:
    if before['creation_year_start']is None and before['creation_year_end']is None and f['start']is not None:patch.update(creation_year_start=f['start'],creation_year_end=f['end'],date_display=f['date_display'],date_precision=f['precision'])
    for field,value in [('medium_text',f['medium']),('dimensions_text',f['dimensions']),('current_location_text',inst['name'])]:
     if value and not before[field]:patch[field]=value
    if not existing_links and not artist and f['creator'] and not before['unlinked_creator_label']:patch['unlinked_creator_label']=f['creator']
    if f.get('wp_id')==6669:patch['unlinked_creator_label']=f['creator']
    if artist and before['unlinked_creator_label']:patch['unlinked_creator_label']=None
    artwork=None
   else:
    artwork=dict(id=aid,slug=OP+'-'+code(f['accession']).lower().replace('.','-'),title=f['title'],normalized_title=norm(f['title']),date_display=f['date_display'],creation_year_start=f['start'],creation_year_end=f['end'],date_precision=f['precision'],work_type=f['work_type'],medium_text=f['medium'],dimensions_text=f['dimensions'],current_institution_id=iid,current_location_text=inst['name'],location_checked_at=stamp,accession_number=f['accession'],status='review',research_candidate=True,unlinked_creator_label=None if artist else f['creator'],created_by=m.ACTOR,updated_by=m.ACTOR)
   sk=str(f['pdf_year'])if f['source_kind']=='pdf'else'web';sid=sources[sk]['id'];image_ok=f['image_eligible']and not(before and before['primary_media_id'])
   plan['records'].append(dict(artwork_id=aid,before=before,insert=artwork,patch=patch,artist_id=artist,existing_links=existing_links,add_holding=not any(str(x['artwork_id'])==aid and x['claim_type']=='holding'and str(x['institution_id'])==iid and x['review_state']=='accepted' for x in locations),source_id=sid,fact=f,image_selected=image_ok))
  # Check exact URLs and exact scoped title/artist identities for newly selected objects.
  new=[x for x in plan['records']if x['insert']];urls=[x['fact']['url']for x in new if x['fact']['source_kind']=='web'];dups=db.execute("SELECT entity_id::text,canonical_url FROM external_identifiers WHERE entity_type='artwork'AND canonical_url=ANY(%s)",(urls,)).fetchall();assert not dups,dups
  for x in new:assert not db.execute('SELECT 1 FROM artworks WHERE id=%s OR slug=%s',(x['artwork_id'],x['insert']['slug'])).fetchone()
  plan['global_duplicate_review']=m.load(RUN/'global-identity-leads.json');assert not plan['global_duplicate_review']
  m.save(BACKUP/'delivery-plan.json.gz',plan)
 m.save(RUN/'plan-pin.json',dict(at=stamp,sha256=m.digest(BACKUP/'delivery-plan.json.gz'),new_artworks=sum(x['before']is None for x in plan['records']),existing_reviewed=sum(x['before']is not None for x in plan['records']),metadata_updates=sum(bool(x['patch'])for x in plan['records']),artist_links=sum(bool(x['artist_id'])for x in plan['records']),image_candidates=sum(x['image_selected']for x in plan['records']),publication_changes=0,local_writes=0));print(json.dumps(m.load(RUN/'plan-pin.json'),indent=2))
def images():
 p=m.load(BACKUP/'delivery-plan.json.gz');assert m.digest(BACKUP/'delivery-plan.json.gz')==m.load(RUN/'plan-pin.json')['sha256'];matches=m.load(RUN/'image-source-matches.json') if (RUN/'image-source-matches.json').exists() else {};ORIGINALS.mkdir(parents=True,exist_ok=True);dest=m.ROOT/'apps/web/public/assets/artworks/imported'/OP;dest.mkdir(parents=True,exist_ok=True)
 def one(x):
  f=dict(x['fact']);aid=x['artwork_id'];match=matches.get(f['key']);f['image_url']=match['image_url'] if match else f.get('image_url');tag='-native' if match else '';original=ORIGINALS/(aid+tag+'.bin');receipt=ORIGINALS/(aid+tag+'.json')
  if original.exists():raw=original.read_bytes();rc=m.load(receipt);assert rc['url']==(f.get('image_url') or f['url']+'#page='+str(f['pdf_page']))
  elif f['source_kind']=='web':
   r=requests.get(f['image_url'],timeout=(15,60));r.raise_for_status();raw=r.content;rc=dict(url=f['image_url'],retrieved_at=m.now(),sha256=hashlib.sha256(raw).hexdigest(),content_type=r.headers.get('Content-Type'),source_page=f['url']);original.write_bytes(raw);m.save(receipt,rc)
  else:
   doc=pymupdf.open(BACKUP/'publications'/f"{f['pdf_year']}.pdf");page=doc[f['pdf_page']-1];assert f['xref']in[x['xref']for x in page.get_image_info(xrefs=True)];im=doc.extract_image(f['xref']);raw=im['image'];rc=dict(url=f['url']+'#page='+str(f['pdf_page']),retrieved_at=m.now(),sha256=hashlib.sha256(raw).hexdigest(),pdf_sha256=f['source_sha256'],pdf_page=f['pdf_page'],image_xref=f['xref'],format=im['ext'],extraction='Native embedded image, complete composition; no scan crop, reconstruction or upscaling.');original.write_bytes(raw);m.save(receipt,rc)
  src=ImageOps.exif_transpose(Image.open(io.BytesIO(raw))).convert('RGB');original_size=src.size;src.thumbnail((1500,1500));quality=88
  while True:
   buf=io.BytesIO();src.save(buf,'JPEG',quality=quality,optimize=True);compressed=buf.getvalue()
   if len(compressed)<=100000:break
   if quality>60:quality-=4
   else:src.thumbnail((max(1,int(src.width*.9)),max(1,int(src.height*.9))))
  path=dest/(aid+'.jpg');path.write_bytes(compressed)
  return dict(artwork_id=aid,media_id=uid('media:'+aid),key=f['key'],title=f['title'],creator=f['creator'],path='/assets/artworks/imported/'+OP+'/'+path.name,visual_path=str(path),sha256=hashlib.sha256(compressed).hexdigest(),bytes=len(compressed),width=src.width,height=src.height,original_size=original_size,source_url=f['url'],image_url=f.get('image_url')or rc['url'],source_id=x['source_id'],source_record_id=f['accession'],source_checksum=f['source_sha256'],receipt=rc,date_evidence=f['date_evidence'],museum_media_match=match,rights_status='restricted'if f['source_kind']=='pdf'else'unknown',rights_label='© A. G. Leventis Gallery'if f['source_kind']=='pdf'else'No item-specific reuse licence stated on museum object page',user_authorization='User-approved Cyprus museum image workflow (20 September 2026), selected works by 1955; direct upload preference 7 October; explicit Leventis research and gallery-book request 8 October. Not an independently obtained copyright-holder licence.')
 with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:ims=list(pool.map(one,[x for x in p['records']if x['image_selected'] and (not matches or x['fact']['key'] in matches or 'logo' not in (x['fact'].get('image_url') or '').lower())]))
 m.save(RUN/('prepared-images-reviewed.json' if matches else 'prepared-images.json'),ims)
 for k in range(0,len(ims),20):
  subset=ims[k:k+20];sheet=Image.new('RGB',(1200,300*((len(subset)+4)//5)),'#eee');draw=ImageDraw.Draw(sheet)
  for j,im in enumerate(subset):
   img=Image.open(im['visual_path']);img.thumbnail((220,245));xx=(j%5)*240;yy=(j//5)*300;sheet.paste(img,(xx+(240-img.width)//2,yy));draw.text((xx+5,yy+248),str(k+j+1)+' '+im['key'],fill='black');draw.text((xx+5,yy+265),im['title'][:30],fill='black')
  sheet.save(TEMP/f'contact-{k//20+1}.jpg')
 print('PREPARED',len(ims),'images; sheets',(len(ims)+19)//20)

def pinned():
 p=m.load(BACKUP/'delivery-plan.json.gz');digest=m.digest(BACKUP/'delivery-plan.json.gz');assert digest==m.load(RUN/'plan-pin.json')['sha256'];assert p['selection_sha256']==m.digest(RUN/'selection-reviewed.json');assert p['artist_decisions_sha256']==m.digest(RUN/'creator-decisions-reviewed.json');return p,digest
def upload():
 p,digest=pinned();ims=m.load(RUN/'prepared-images-reviewed.json');review=m.load(RUN/'visual-review.json');assert review['images_manifest_sha256']==m.digest(RUN/'prepared-images-reviewed.json')and review['approved_ids']==[x['artwork_id']for x in ims]
 assert len({x['sha256']for x in ims})==len(ims),'Duplicate/logo image protection';assert all('logo'not in x['image_url'].lower()for x in ims)
 token=subprocess.check_output(['gcloud','auth','print-access-token','--account=vadim@alingva.com'],text=True).strip();session=requests.Session();session.headers['Authorization']='Bearer '+token;checks=[];bucket='artline-508319-images'
 for im in ims:
  dest=RUN/'storage'/(im['artwork_id']+'.json');raw=Path(im['visual_path']).read_bytes();assert len(raw)==im['bytes']<=100000 and hashlib.sha256(raw).hexdigest()==im['sha256']
  if dest.exists():checks.append(m.load(dest));continue
  name=im['path'].lstrip('/');u='https://storage.googleapis.com/storage/v1/b/'+bucket+'/o/'+quote(name,safe='');r=session.get(u,timeout=(15,30));created=False
  if r.status_code==404:r=session.post('https://storage.googleapis.com/upload/storage/v1/b/'+bucket+'/o',params=dict(uploadType='media',name=name,ifGenerationMatch=0),data=raw,headers={'Content-Type':'image/jpeg'},timeout=(15,45));created=True
  r.raise_for_status();o=r.json();assert int(o['size'])==len(raw)and o['md5Hash']==base64.b64encode(hashlib.md5(raw).digest()).decode();check=dict(artwork_id=im['artwork_id'],path=im['path'],sha256=im['sha256'],generation=o['generation'],created=created);m.save(dest,check);checks.append(check)
  if len(checks)%10==0:print('STORAGE VERIFIED',len(checks),'/',len(ims),flush=True)
 m.save(RUN/'storage-verified.json',dict(at=m.now(),plan_sha256=digest,images_sha256=m.digest(RUN/'prepared-images-reviewed.json'),checks=checks));print('UPLOADED',len(checks))
def apply():
 p,digest=pinned();assert m.load(RUN/'cloud-backup.json')['status']=='SUCCESSFUL';storage=m.load(RUN/'storage-verified.json');assert storage['images_sha256']==m.digest(RUN/'prepared-images-reviewed.json');ims={x['artwork_id']:x for x in m.load(RUN/'prepared-images-reviewed.json')};assert len(storage['checks'])==len(ims);assert not(RUN/'applied.json').exists();after=[];stamp=m.now()
 with m.connect('production',False)as db:
  db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
  ids=[x['artwork_id']for x in p['records']if x['before']];locked={r['r']['id']:r['r']for r in db.execute('SELECT to_jsonb(a) r FROM artworks a WHERE id=ANY(%s::uuid[]) ORDER BY a.id FOR UPDATE',(ids,)).fetchall()}
  assert all(locked[x['artwork_id']]==x['before']for x in p['records']if x['before']),'Preimage drift; re-review required'
  current_links=m.select_rows(db,'artwork_artists','artwork_id',ids)
  assert sorted(current_links,key=lambda x:json.dumps(x,sort_keys=True))==sorted([x for x in p['scoped_before']['creators']if str(x['artwork_id'])in ids],key=lambda x:json.dumps(x,sort_keys=True)),'Creator links changed'
  for s in p['sources']:insert(db,'sources',s);insert(db,'source_institutions',dict(source_id=s['id'],institution_id=p['institution']['id']))
  for index,x in enumerate(p['records'],1):
   f=x['fact'];aid=x['artwork_id'];sid=x['source_id'];before=x['before'];im=ims.get(aid)
   evidence=dict(operation=OP,plan_sha256=digest,source_url=f['url'],source_record_id=f['accession'],locator=f['locator'],source_sha256=f['source_sha256'],creator_label=f['creator'],date=f['date_display'],date_evidence=f['date_evidence'],raw_web_date=f.get('raw_date'),museum_assignment_confidence=.99,confidence_basis='Exact institution accession in official object page or acquisition/donation caption; confidence is editorial, not a calibrated probability.',uncertainty='Unknowns and qualified authorship retained. Museum holding is not a fresh current-display claim.',corroborating_source=f.get('corroborating_source'))
   if x['insert']:insert(db,'artworks',x['insert'])
   if x['artist_id']:insert(db,'artwork_artists',dict(artwork_id=aid,artist_id=x['artist_id'],attribution_role='primary',attribution_note='Explicit creator in museum object/caption; supplied label: '+f['creator']+'. Reviewed identity match; see '+OP+' evidence.'))
   if x['add_holding']:insert(db,'artwork_location_assertions',dict(id=uid('holding:'+aid),artwork_id=aid,claim_type='holding',institution_id=p['institution']['id'],context='collection',source_id=sid,source_url=f['url'],evidence_note=json.dumps(evidence,ensure_ascii=False),checked_at=stamp,review_state='accepted'))
   insert(db,'citations',dict(id=uid('citation:'+aid),entity_type='artwork',entity_id=aid,field_name='verified_catalogue_metadata_and_holding',source_id=sid,source_record_id=f['accession'],source_url=f['url'],page_or_locator=f['locator'],evidence_note=json.dumps(evidence,ensure_ascii=False),retrieved_at=stamp,created_by=m.ACTOR))
   insert(db,'external_identifiers',dict(id=uid('external:'+aid),entity_type='artwork',entity_id=aid,scheme='leventis-reviewed-object-20261008',external_id=f['accession'],canonical_url=f['url'],source_id=sid,retrieved_at=stamp))
   patch=dict(x['patch'])
   if im:
    assert not before or before['primary_media_id']is None
    media=dict(id=im['media_id'],storage_kind='local',storage_path=im['path'],source_page_url=im['source_url'],provider_name='A. G. Leventis Gallery',mime_type='image/jpeg',width=im['width'],height=im['height'],byte_size=im['bytes'],checksum_sha256=im['sha256'],alt_text=im['title']+(' — '+im['creator']if im['creator']else''),rights_status=im['rights_status'],license_label=im['rights_label'],license_url=im['source_url'],creator_credit='A. G. Leventis Gallery; artwork: '+(im['creator']or'creator unrecorded'),attribution_text='Image source: A. G. Leventis Gallery. '+im['rights_label'],retrieved_at=im['receipt']['retrieved_at'])
    insert(db,'media_assets',media);insert(db,'media_rights_evidence',dict(media_id=im['media_id'],source_id=sid,source_record_id=f['accession'],source_checksum=im['source_checksum'],source_image_url=im['image_url'],policy_url=im['source_url'],rights_basis=im['user_authorization'],adapter_version=OP,checked_at=stamp,evidence_json=Jsonb(im)))
    view=(im.get('museum_media_match')or{}).get('view_label','Complete supplied source image; report reproductions retain their original resolution and margins')
    insert(db,'artwork_media',dict(artwork_id=aid,media_id=im['media_id'],sort_order=0,view_label=view));patch['primary_media_id']=im['media_id']
    db.execute("INSERT INTO audit_log(actor_user_id,action,entity_type,entity_id,request_id,after_json)VALUES(%s,'leventis_image_added','media_asset',%s,%s,%s)",(m.ACTOR,im['media_id'],OP,Jsonb(media)))
   if patch:
    keys=list(patch);db.execute(sql.SQL('UPDATE artworks SET {},revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s').format(sql.SQL(',').join(sql.SQL('{}=%s').format(sql.Identifier(k))for k in keys)),[patch[k]for k in keys]+[m.ACTOR,aid])
   current=db.execute('SELECT to_jsonb(a) r FROM artworks a WHERE id=%s',(aid,)).fetchone()['r']
   assert current['status']=='review'and current['published_at']is None
   if before:
    allowed=set(patch)|{'revision','updated_at','updated_by'};assert all(current[k]==before[k]for k in before if k not in allowed)
   db.execute("INSERT INTO audit_log(actor_user_id,action,entity_type,entity_id,request_id,before_json,after_json)VALUES(%s,%s,'artwork',%s,%s,%s,%s)",(m.ACTOR,'leventis_artwork_enriched'if before else'leventis_artwork_added',aid,OP,Jsonb(before)if before else None,Jsonb(current)));after.append(current)
   if index%20==0:print('APPLIED IN TRANSACTION',index,'/',len(p['records']),flush=True)
  assert len({x['id']for x in after})==len(after)
  m.save(BACKUP/'transaction-after.json.gz',dict(at=stamp,plan_sha256=digest,artworks=after))
 m.save(RUN/'applied.json',dict(at=m.now(),plan_sha256=digest,new_artworks=sum(x['before']is None for x in p['records']),enriched=sum(x['before']is not None for x in p['records']),images=len(ims),artist_links=sum(bool(x['artist_id'])for x in p['records']),holding_assertions=sum(x['add_holding']for x in p['records']),backup_id='1791473692262',publication_changes=0,local_writes=0));print('COMMITTED',m.load(RUN/'applied.json'))

def verify():
 p,digest=pinned();applied=m.load(RUN/'applied.json');expected={x['id']:x for x in m.load(BACKUP/'transaction-after.json.gz')['artworks']};ims={x['artwork_id']:x for x in m.load(RUN/'prepared-images-reviewed.json')};ids=list(expected)
 with m.connect('production')as db:
  rows=m.select_rows(db,'artworks','id',ids);assert {x['id']:x for x in rows}==expected,'Post-apply artwork drift'
  links=m.select_rows(db,'artwork_artists','artwork_id',ids);locations=m.select_rows(db,'artwork_location_assertions','artwork_id',ids);citations=m.select_rows(db,'citations','entity_id',ids)
  media=m.select_rows(db,'media_assets','id',[x['media_id']for x in ims.values()]);evidence=m.select_rows(db,'media_rights_evidence','media_id',[x['media_id']for x in ims.values()]);by_media={x['id']:x for x in media};by_evidence={x['media_id']:x for x in evidence}
  audits=db.execute("SELECT entity_id::text,after_json FROM audit_log WHERE request_id=%s AND entity_type='artwork'",(OP,)).fetchall();assert len(audits)==len(rows)and all(expected[x['entity_id']]==x['after_json']for x in audits)
  for x in p['records']:
   aid=x['artwork_id'];r=expected[aid];assert r['status']=='review'and r['published_at']is None and r['current_institution_id']==p['institution']['id']
   assert any(c['id']==uid('citation:'+aid)for c in citations)
   assert any(str(v['artwork_id'])==aid and v['claim_type']=='holding'and v['review_state']=='accepted'for v in locations)
   if x['artist_id']:assert any(str(z['artwork_id'])==aid and str(z['artist_id'])==x['artist_id']for z in links)
   if aid in ims:
    im=ims[aid];assert r['primary_media_id']==im['media_id'];ma=by_media[im['media_id']];assert ma['checksum_sha256']==im['sha256']and ma['byte_size']==im['bytes']<=100000;assert by_evidence[im['media_id']]['evidence_json']==im
  # Original image selections, statuses and all non-targeted museum records survive unchanged.
  all_now=db.execute('SELECT to_jsonb(a) r FROM artworks a WHERE current_institution_id=%s',(p['institution']['id'],)).fetchall();allmap={x['r']['id']:x['r']for x in all_now}
  for x in p['scoped_before']['artworks']:
   old=x['r'];new=allmap[old['id']];assert(old['status'],old['published_at'])==(new['status'],new['published_at'])
   if old['primary_media_id']:assert old['primary_media_id']==new['primary_media_id']
   if old['id']not in expected:assert old==new
  assert sum(v['claim_type']=='display'for v in locations)==sum(v['claim_type']=='display'and str(v['artwork_id'])in ids for v in p['scoped_before']['locations'])
  totals=dict(artworks=len(all_now),with_images=sum(bool(x['r']['primary_media_id'])for x in all_now),known_dates=sum(x['r']['creation_year_start']is not None or x['r']['creation_year_end']is not None for x in all_now),in_review=sum(x['r']['status']=='review'for x in all_now))
 def get(url):
  for attempt in range(3):
   r=requests.get(url,timeout=(15,55))
   if r.status_code in[500,502,503,504]and attempt<2:continue
   r.raise_for_status();return r
 def check_image(im):
  url='https://artlines.org'+im['path'];r=get(url);assert hashlib.sha256(r.content).hexdigest()==im['sha256'];return dict(artwork_id=im['artwork_id'],url=url,status=r.status_code,sha256=im['sha256'])
 with concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool:imagechecks=list(pool.map(check_image,ims.values()))
 samplekeys=['wp:6772','wp:6718','wp:4744','wp:6668','pdf:765','pdf:1115','pdf:1116','pdf:1117','pdf:1099','pdf:1133'];samples=[x for x in p['records']if x['fact']['key']in samplekeys];apichecks=[]
 for x in samples:
  url='https://artlines.org/api/backend/v1/museums/leventis-gallery/works/'+x['artwork_id'];r=get(url);body=r.json();assert body['id']==x['artwork_id']and body['status']=='review'
  if x['artwork_id']in ims:assert body['media_url']==ims[x['artwork_id']]['path']
  apichecks.append(dict(artwork_id=x['artwork_id'],key=x['fact']['key'],status=r.status_code))
 directory=get('https://artlines.org/api/backend/v1/museums/leventis-gallery/works?limit=12').json();m.save(BACKUP/'live-gallery-page.json',directory)
 result=dict(at=m.now(),target='production',new_artworks=applied['new_artworks'],existing_enriched=applied['enriched'],images_added=len(ims),artist_links=applied['artist_links'],museum_totals=totals,verified_artwork_audits=len(audits),api_checks=apichecks,image_checks=imagechecks,existing_images_preserved=True,publication_changes=0,local_database_writes=0,errors=[])
 m.save(RUN/'verification.json',result);print('VERIFIED',json.dumps({k:v for k,v in result.items()if k not in['api_checks','image_checks']},indent=2))
if __name__=='__main__':globals()[sys.argv[1]]()
