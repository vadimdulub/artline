#!/usr/bin/env python3
"""Selected South African museum catalogue evidence and production publication."""
import argparse,collections,datetime,gzip,html,importlib.util,json,re,time,uuid
from pathlib import Path
from urllib.parse import urljoin,urlsplit

spec=importlib.util.spec_from_file_location('core',Path(__file__).with_name('catalogue-expansion-20261008.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
ROOT=m.ROOT;RUN=ROOT/'docs/research/south-africa-20261008'
BACKUP=Path.home()/'Library/Application Support/Artline/backups/south-africa-20261008'
m.RUN=RUN;m.BACKUP=BACKUP
norm=m.norm;save=m.save;load=m.load;connect=m.connect
def capture(url,params=None):
 for attempt in range(3):
  try:return m.capture(url,params=params)
  except (m.requests.exceptions.ConnectionError,m.requests.exceptions.Timeout) as error:
   if attempt==2:raise
   print('Transient transport retry',urlsplit(url).netloc,type(error).__name__,flush=True)
   time.sleep(2*(attempt+1))
def uid(value):return str(uuid.uuid5(uuid.NAMESPACE_URL,'artline/south-africa-20261008/'+value))

def snapshot():
 with connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY')
  institutions=db.execute("SELECT to_jsonb(i) r,p.name city,p.country_code FROM institutions i LEFT JOIN places p ON p.id=i.place_id WHERE p.country_code='ZA' OR i.name ILIKE ANY(%s) ORDER BY i.id",(['%South Africa%','%Iziko%','%Johannesburg%','%Pretoria%','%Durban%','%Humphreys%','%Oliewenhuis%','%Rupert%','%Norval%','%Sanlam%','%Stellenbosch%','%Wits Art%','%Michaelis%','%William Fehr%','%Mandela Metropolitan%','%Tatham%'],)).fetchall()
  ids=[i['r']['id'] for i in institutions]
  works=[x['r'] for x in db.execute('SELECT to_jsonb(a) r FROM artworks a WHERE current_institution_id=ANY(%s::uuid[])',(ids,))]
  wids=[w['id'] for w in works];relations={}
  for table,col in [('artwork_artists','artwork_id'),('artwork_media','artwork_id'),('artwork_location_assertions','artwork_id'),('citations','entity_id'),('external_identifiers','entity_id')]:
   relations[table]=[x['r'] for x in db.execute(f'SELECT to_jsonb(t) r FROM {table} t WHERE {col}=ANY(%s::uuid[])',(wids,))]
  artists=list(db.execute('SELECT id::text,slug,display_name,sort_name,normalized_name,entity_type,birth_year,death_year,status FROM artists'))
  aliases=list(db.execute('SELECT artist_id::text,alias,normalized_alias FROM artist_aliases'))
  artist_external=list(db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artist'"))
  sources=[x['r'] for x in db.execute('SELECT to_jsonb(s) r FROM sources s')]
  places=[x['r'] for x in db.execute("SELECT to_jsonb(p) r FROM places p WHERE country_code='ZA'")]
 result=dict(at=m.now(),institutions=institutions,artworks=works,relations=relations,artists=artists,artist_aliases=aliases,artist_external=artist_external,sources=sources,places=places)
 save(RUN/'production-baseline.json.gz',result);BACKUP.mkdir(parents=True,exist_ok=True);BACKUP.chmod(0o700);save(BACKUP/'production-baseline.json.gz',result)
 counts=collections.Counter(w['current_institution_id'] for w in works)
 for i in institutions:print(i['r']['id'],i['r']['slug'],i['r']['name'],i['city'],counts[i['r']['id']],flush=True)
 print('Snapshot',len(institutions),'institutions',len(works),'artworks',len(artists),'artists',flush=True)

PAGES={
 'whag':'https://whag.co.za/collections',
 'rupert':'https://rupertmuseum.org/collections/',
 'mandela':'https://www.artmuseum.co.za/SearchCollection.aspx?pageID=5',
 'sanlam':'https://www.sanlamartcollection.co.za/',
 'oliewenhuis':'https://nationalmuseum.co.za/oliewenhuis-collections/',
 'iziko-gac':'https://artsandculture.google.com/partner/south-african-national-gallery?hl=en',
 'jag-gac':'https://artsandculture.google.com/partner/johannesburg-art-gallery?hl=en',
 'pretoria-up':'https://www.up.ac.za/museums-collections/art-collection',
 'tatham':'https://www.tatham.org.za/',
}
def discover():
 for key,url in PAGES.items():
  try:raw,rc=capture(url)
  except Exception as e:print(key,'STOPPED',type(e).__name__,str(e)[:150],flush=True);continue
  if rc['status']!=200:print(key,'HTTP',rc['status'],flush=True);continue
  soup=m.BeautifulSoup(raw,'html.parser')
  links=[dict(text=a.get_text(' ',strip=True),url=urljoin(rc['final_url'],a['href'])) for a in soup.select('a[href]')]
  scripts=[urljoin(rc['final_url'],s['src']) for s in soup.select('script[src]')]
  for tag in soup(['script','style','header','footer','nav']):tag.decompose()
  text=soup.get_text('\n',strip=True)
  save(RUN/(key+'-index.json'),dict(receipt=rc,text=text,links=links,scripts=scripts))
  print(key,'bytes',len(raw),'text',len(text),'links',len(links),'scripts',len(scripts),flush=True)

def dates(value):
 s=(value or '').strip().replace('–','-').replace('—','-');match=re.fullmatch(r'(?:(c\.?|ca\.?|circa|about)\s*)?(1\d{3})(?:\s*[-/]\s*(1\d{3}|\d{2}))?(\?)?',s,re.I)
 if not match:return None
 first=int(match[2]);last=int(match[3]) if match[3] and len(match[3])==4 else first//100*100+int(match[3]) if match[3] else first
 if not first<=last<=1970 or last==1970 and (match[1] or match[4]):return None
 return dict(first=first,last=last,date_display=value.strip(),date_precision=('circa' if first==last else 'circa_range') if match[1] or match[4] else ('exact' if first==last else 'range'))

def kind(medium):
 s=norm(medium)
 if re.search(r'\b(?:oil|olie|olieverf|huile|acrylic|akriel|tempera|gouache)\b',s):return 'painting'
 if re.search(r'watercolou?r|waterverf|aquarel',s):return 'watercolor'
 if re.search(r'\b(?:etching|ets|lithograph|lithografie|lithografiee|litho|lino|linocut|linosnee|houtdruk|woodcut|wood engraving|engraving|gravure|serigraph|serigrafie|silkscreen|screenprint|aquatint|mezzotint|drypoint|droenaald|engraving)\b',s):return 'print'
 if re.search(r'\b(?:pencil|potlood|pastel|charcoal|houtskool|ink|inkwash|kryt|pen|conte|crayon)\b',s):return 'drawing'
 if re.search(r'\b(?:bronze|brons|marble|marmer|plaster|gips|terracotta|soapstone|beeld)\b',s):return 'sculpture'
 if re.search(r'\b(?:tapestry|tapisserie|tapisseriee|textile|borduurwerk)\b',s):return 'textile'
 if re.search(r'\b(?:ceramic|ceramics|porcelain|porselein|stoneware|earthenware|pottery)\b',s):return 'ceramic'
 return None

HISTORIC_ARTISTS=['Pierneef','Stern','Sekoto','Pemba','Laubser','Battiss','Preller','Skotnes','Clarke','Kumalo','Legae','Villa','Van Wouw','Volschenk','Oerder','Wenning','Coetzee','Sumner','Boonzaier','Mancoba','Sithole','Bhengu','Page','Lock','Higgs','Seneque','Methven','Trotter','Timlin','Everard','Naude','Welz','Jentsch','Van Essche','Amshewitz','Cilliers','Mgudlandlu','Baines','Kay','Hodgins','Buckland','Roworth','Verster','Du Plessis','Mayer','Alexander','Portway','Kottler','Caldecott','Peffer']
def labelled_fields(block):
 fields={}
 for label in block.select('b'):
  key=label.get_text(' ',strip=True).rstrip(':').strip();parts=[]
  for el in label.next_siblings:
   if getattr(el,'name',None)=='br':break
   parts.append(el.get_text(' ',strip=True) if hasattr(el,'get_text') else str(el))
  fields[key]=' '.join(' '.join(parts).split())
 return fields

def gac_cards(raw):
 out={};text=raw.decode('utf-8')
 def walk(v):
  if not isinstance(v,list):return
  if len(v)>4 and v[0]=='gac.oi' and isinstance(v[4],str) and v[4].startswith('/asset/'):
   sid=v[4].rstrip('/').rsplit('/',1)[-1];out[sid]=dict(source_id=sid,title=v[1],creator_label=v[2],source_url='https://artsandculture.google.com'+v[4])
  else:
   for child in v:walk(child)
 for hit in re.finditer(r"window\.INIT_data\['[^']+'\]\s*=\s*",text):
  value=json.JSONDecoder().raw_decode(text[hit.end():])[0];walk(value)
 return list(out.values())

def gac():
 allrows={};index_refs=[]
 for key,partner,path in [('iziko','south-african-national-gallery','iziko-gac-index.json'),('jag','johannesburg-art-gallery','jag-gac-index.json'),('up','university-of-pretoria-museums','up-gac-page.json')]:
  d=load(RUN/path);raw=gzip.decompress((ROOT/d['receipt']['body_path']).read_bytes());soup=m.BeautifulSoup(raw,'html.parser');urls=[]
  for link in soup.select('a[href]'):
   label=re.sub(r'\s+\d+$','',link.get_text(' ',strip=True));url=urljoin(d['receipt']['final_url'],link['href'])
   if '/explore/collections/'+partner in url and any(name in label for name in ['Drawing','Paper','Painting','Oil paint','Canvas','Wood','Ceramic','Gold','Metal','Jacobus','Maggie','Walter Battiss','Kollwitz','Liebermann','Cappiello','Grosz','Champaigne','Thomas Baines','Rembrandt','Rossetti','Boudin']):urls.append((label,url))
  for r in gac_cards(raw):r.update(institution_key=key,index_receipt=d['receipt']);allrows[r['source_id']]=r
  for label,url in list(dict.fromkeys(urls))[:16]:
   raw,rc=capture(url);assert rc['status']==200
   for r in gac_cards(raw):
    if r['source_id'] not in allrows:r.update(institution_key=key,index_receipt=rc);allrows[r['source_id']]=r
   index_refs.append(dict(institution_key=key,label=label,receipt=rc));print('GAC index',key,label,'distinct',len(allrows),flush=True)
 save(RUN/'gac-index-selection.json.gz',dict(rows=list(allrows.values()),indexes=index_refs))
 out=[];held=[]
 for n,r in enumerate(list(allrows.values())[:360],1):
  raw,rc=capture(r['source_url']);assert rc['status']==200;soup=m.BeautifulSoup(raw,'html.parser');fields={}
  for li in soup.select('li.XD0Pkb'):
   label=li.select_one('.PUhAff')
   if label:fields[label.get_text(' ',strip=True).rstrip(':')]=li.get_text(' ',strip=True)[len(label.get_text(' ',strip=True)):].strip()
  heading=soup.select_one('h3.To7WBf');provider=heading.get_text(' ',strip=True) if heading else None
  date=dates(fields.get('Date Created'));typ=kind(fields.get('Medium'))
  if not typ:typ={'Painting':'painting','Drawing':'drawing','Sculpture':'sculpture','Ceramic':'ceramic','Ceramics':'ceramic','Metalwork':'metalwork','Textile':'textile','Print':'print'}.get(fields.get('Type'))
  reason=None
  expected={'iziko':'Iziko','jag':'Johannesburg','up':'Pretoria'}[r['institution_key']]
  if not provider or expected.lower() not in provider.lower():reason='Object provider does not confirm selected institution'
  elif not date:reason='Unknown or ineligible creation date'
  elif not typ:reason='Object type requires further research'
  elif r['institution_key']=='jag' and typ in ['print','photograph']:reason='JAG print/photograph edition and impression dates unresolved; provider also contains demonstrated date errors'
  elif not fields.get('Title') or norm(fields['Title'])!=norm(r['title']):reason='Index/object title conflict'
  if reason:held.append(dict(source_id=r['source_id'],reason=reason,fields=fields,provider=provider,receipt=rc));continue
  r.update(date);r.update(title=fields['Title'],creator_label=fields.get('Creator'),medium=fields.get('Medium'),dimensions=fields.get('Physical Dimensions'),accession=fields.get('Accession Number') or fields.get('Inventory Number'),key='gac/'+r['source_id'],source_kind='gac',work_type=typ,receipt=rc,raw_fields=fields,provider=provider,identity_basis='Individual museum-authored Google Arts & Culture object record confirms native object identity and provider. Exact source creation field retained; no current display inferred.')
  out.append(r)
  if n%25==0:print('GAC objects',n,'/',min(360,len(allrows)),'accepted',len(out),flush=True)
 save(RUN/'gac-selected.json.gz',out);save(RUN/'gac-held.json.gz',held);print('GAC selected',len(out),dict(collections.Counter(r['institution_key'] for r in out)),flush=True)

def mandela():
 selected={};held=[]
 for artist in HISTORIC_ARTISTS:
  raw,rc=capture('https://www.artmuseum.co.za/searchResults.aspx',{'artist':artist});assert rc['status']==200
  soup=m.BeautifulSoup(raw,'html.parser');n=0
  for link in soup.select('a[href*="cmd=collection&id="]'):
   fields=labelled_fields(link.find_parent('td'));sid=re.search(r'[?&]id=(\d+)',link['href'])[1];date=dates(fields.get('Date'));typ=kind(fields.get('Medium'));n+=1
   if sid in selected:continue
   if not date or not typ or not fields.get('Accession number'):
    held.append(dict(source_id=sid,reason='Unknown/outside-scope creation date, medium or inventory',fields=fields,index_receipt=rc));continue
   if n>35 or len(selected)>=600:held.append(dict(source_id=sid,reason='Bounded artist/object selection'));continue
   selected[sid]=dict(source_id=sid,source_url=urljoin(rc['final_url'],link['href']),title=link.get_text(' ',strip=True),creator_label=fields.get('Name of Artist'),medium=fields['Medium'],dimensions=None,accession=fields['Accession number'],index_fields=fields,index_receipt=rc,work_type=typ,**date)
  print('Mandela',artist,'index objects',n,'selected',len(selected),flush=True)
 save(RUN/'mandela-index-selection.json.gz',dict(selected=list(selected.values()),held=held))
 out=[]
 for n,r in enumerate(selected.values(),1):
  raw,rc=capture(r['source_url']);assert rc['status']==200;soup=m.BeautifulSoup(raw,'html.parser');link=soup.find('b',string=re.compile('Name of Artist'));assert link
  fields=labelled_fields(link.find_parent('table'))
  if norm(fields.get('Title of artwork'))!=norm(r['title']) or fields.get('Date')!=r['date_display'] or fields.get('Accession number')!=r['accession']:
   held.append(dict(source_id=r['source_id'],reason='Object and index title/date/inventory mismatch',index=r,object_fields=fields,receipt=rc));continue
  r['title']=fields['Title of artwork']
  r.update(creator_label=fields['Name of Artist'],key='mandela/'+r['source_id'],source_kind='mandela',institution_key='mandela',receipt=rc,raw_fields=fields,identity_basis='Official municipal museum individual object page confirms native ID, title, creator, creation-date field, medium and accession. No current display assertion.')
  out.append(r)
  if n%25==0:print('Mandela individual objects',n,'/',len(selected),flush=True)
 save(RUN/'mandela-selected.json.gz',out);save(RUN/'mandela-held.json.gz',held);print('Mandela final',len(out),flush=True)

def rupert():
 indexed=[];held=[];per_artist=collections.Counter();selected=[];seen=set()
 # Public read-only search action and parameters used by the site's own form.
 # Pretty /page/N/ routes repeat page one; their earlier captures are superseded.
 for collection_type in ['rupert-art-foundation','rembrandt-van-rijn-art-foundation']:
  for page in range(1,31):
   raw,rc=capture('https://rupertmuseum.org/wp-admin/admin-ajax.php',{'action':'rm_collections_search_ajax','colsearch[page]':page,'colsearch[collection_type]':collection_type,'colsearch[collection]':'','colsearch[artist]':''})
   assert rc['status']==200;data=json.loads(raw);assert int(data['page'])==page
   new_count=0
   for obj in data['collections']:
    sid=str(obj['ID']);fields=obj['metadata']
    if sid in seen:continue
    seen.add(sid);new_count+=1
    r=dict(source_id=sid,title=fields['itemtitle'],creator_label=fields['displayname'],date_display=fields.get('generaldate'),medium=fields.get('generalmedium'),dimensions=fields.get('measurements') or None,accession=fields['logosflow_id'],source_url=obj['guid'],index_receipt=rc,index_metadata=fields)
    indexed.append(r);date=dates(r['date_display']);typ=kind(r['medium'])
    if not date or not typ:held.append(dict(source_id=sid,reason='No eligible explicit creation date or supported medium',date=r['date_display'],medium=r['medium']));continue
    if per_artist[r['creator_label']]>=30 or len(selected)>=500:held.append(dict(source_id=sid,reason='Bounded selection: 30 works per creator, 500 objects total'));continue
    r.update(date);r['work_type']=typ;selected.append(r);per_artist[r['creator_label']]+=1
   print('Rupert',collection_type,'page',page,'distinct indexed',len(indexed),'selected',len(selected),flush=True)
   assert new_count>0 or len(data['collections'])==0,'Repeated source page'
   if page>=int(data['pages']) or not data['collections']:break
 save(RUN/'rupert-index-selection-v2.json.gz',dict(indexed=indexed,selected=selected,held=held))
 out=[]
 for n,r in enumerate(selected,1):
  raw,rc=capture(r['source_url']);assert rc['status']==200;soup=m.BeautifulSoup(raw,'html.parser');section=soup.select_one('.collection-left-sub');assert section
  lines=section.get_text('\n',strip=True).splitlines()
  if norm(lines[0])!=norm(r['title']) or lines[1]!=r['date_display'] or lines[-1]!=r['accession'] or 'Medium: '+r['medium'] not in lines:
   held.append(dict(source_id=r['source_id'],reason='Individual object/index conflict',index=r,lines=lines,receipt=rc));continue
  owner=lines[-2]
  if owner not in ['Rupert Art Foundation','Rembrandt van Rijn Art Foundation']:
   held.append(dict(source_id=r['source_id'],reason='Managed collection owner outside selected foundations',owner=owner));continue
  artist_el=soup.select_one('.collection-left a[href*="/artist/"]') or soup.select_one('a[href*="/artist/"]')
  if artist_el and norm(artist_el.get_text(' ',strip=True))!=norm(r['creator_label']):held.append(dict(source_id=r['source_id'],reason='Creator conflict',index=r));continue
  r.update(key='rupert/'+r['source_id'],source_kind='rupert',institution_key='rupert-foundation' if owner=='Rupert Art Foundation' else 'rembrandt-foundation',collection_owner=owner,receipt=rc,raw_fields=dict(lines=lines,creator_label=r['creator_label'],source_post_id=r['source_id']),identity_basis='Individual museum catalogue confirms inventory, creation date, medium and named foundation collection. Retain the foundation as holding institution; managed by Rupert Museum, without a current building/display assignment.')
  out.append(r)
  if n%25==0:print('Rupert individual objects',n,'/',len(selected),'accepted',len(out),flush=True)
 save(RUN/'rupert-selected-v2.json.gz',out);save(RUN/'rupert-held-v2.json.gz',held)
 print('Rupert final',len(out),dict(collections.Counter(r['collection_owner'] for r in out)),flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['snapshot','discover','rupert','mandela','gac']);args=p.parse_args();globals()[args.action]()
