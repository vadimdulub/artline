#!/usr/bin/env python3
"""Bounded official Polish collection research; raw captures retained, no DB writes."""
import importlib.util,json,re,sys,collections,concurrent.futures
from pathlib import Path
from urllib.parse import urljoin,urlsplit
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('base',Path(__file__).with_name('research-chinese-art-20261008.py'));b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
b.RUN=b.ROOT/'docs/research/poland-collections-20261008/poland'
Source=b.Source
PDM='https://creativecommons.org/publicdomain/mark/1.0/'
def save(n,v):b.save(n,v)
def load(n):return b.load(n)
def clean(n):
 n=re.sub(r'\s*\([^)]*\)\s*$','',n or '').strip()
 return ' '.join(reversed([p.strip() for p in n.split(',')])) if ',' in n else n

def bounds(d):
 d=(d or '').strip();years=[int(y) for y in re.findall(r'(?<!\d)([12]\d{3})(?!\d)',d)]
 # Single exact/circa date and explicit closed ranges only; no inferred open ends.
 if re.fullmatch(r'(?:ok\.?\s*|około\s*|ca\.?\s*|c\.\s*)?[12]\d{3}(?:\s*r\.?)?\??',d,re.I):return (years[0],years[0]) if '?' not in d else (None,None)
 if re.fullmatch(r'(?:między\s*|ok\.?\s*)?[12]\d{3}\s*[-–—/]\s*[12]\d{3}(?:\s*r\.?)?',d,re.I):return min(years),max(years)
 if re.fullmatch(r'[12]\d{3}\s*[-–]\s*\d{2}',d):return int(d[:4]),int(d[:2]+d[-2:])
 roman={'X':10,'XI':11,'XII':12,'XIII':13,'XIV':14,'XV':15,'XVI':16,'XVII':17,'XVIII':18,'XIX':19,'XX':20}
 m=re.fullmatch(r'(?:(1|2)\.?\s*poł(?:owa|\.)\s*)?([XVI]+)\s*(?:w\.?|wiek)',d)
 if m and m[2] in roman:
  lo=(roman[m[2]]-1)*100+1;hi=lo+99
  if m[1]=='1':hi=lo+49
  if m[1]=='2':lo+=50
  return lo,hi
 return None,None

def row(provider,o,rc,**kw):
 lo,hi=bounds(kw.get('date_display'));return b.candidate(provider,o,rc,year_start=lo,year_end=hi,**kw)

def museum_api(code):
 api,web,museum,cdn={'warsaw':('https://cyfrowe-api.mnw.art.pl','https://cyfrowe.mnw.art.pl/pl/zbiory/','National Museum in Warsaw','https://cyfrowe-cdn.mnw.art.pl'),'krakow':('https://api-zbiory.mnk.pl','https://zbiory.mnk.pl/pl/katalog/','National Museum in Kraków','https://cdn-zbiory.mnk.pl')}[code]
 s=Source();selected={};rejected=[]
 for page in range(1,10):
  d,rc=s.get(api+'/api/search/Object/page/'+str(page),{'filter[masterpieces]':1,'maxPerPage':100});d=d['data']
  assert all(o['masterpieces'] for o in d['items'])
  for o in d['items']:
   types='; '.join(t['name'] for t in o.get('types',[]));route=o.get('routeNode') or ''
   if re.search(r'obraz|malarstwo|rysunek|akwarel|pastel|grafika|rycina|ikona|rzeźba',types+' '+route,re.I):selected[o['id']]=o
  print(code,'masterpiece page',page,'of',d['paginatorDetails']['totalPagesCount'],'selected',len(selected),flush=True)
  if page>=d['paginatorDetails']['totalPagesCount']:break
 out=[]
 for n,(oid,index) in enumerate(selected.items()):
  o,rc=s.get(api+'/api/object/'+str(oid));o=o['data'];assert o['id']==oid
  owner=(o.get('owner') or {}).get('name') or ''
  if owner and not re.search('Muzeum Narodowe w (Warszawie|Krakowie)',owner):rejected.append(dict(id=oid,reason='Different documented owner',owner=owner));continue
  creators=o.get('authors',[]);labels=[]
  for a in creators:
   label=clean(a.get('name'))
   if a.get('comment') or a.get('additionalRoles') or a.get('role') not in ['autor','malarz','twórca','rysownik','wykonawca','rzeźbiarz','rytownik','grafik']:
    label+=' [qualified attribution: '+str(a.get('role') or '')+'; '+str(a.get('comment') or '')+'; '+str(a.get('additionalRoles') or '')+']'
   if re.search(r'nieznan|anonim',label,re.I):label='Anonymous / '+label
   labels.append(label)
  types='; '.join(t['name'] for t in o.get('types',[]));route=o.get('routeNode') or ''
  typ='painting' if re.search('obraz|malarstwo|ikona',types+' '+route,re.I) else 'drawing' if 'rysunek' in types else 'sculpture' if 'rzeźba' in types else 'print' if re.search('grafik|rycin',types+' '+route,re.I) else 'unknown'
  date='; '.join(d['name']+(' ['+d['comment']+']' if d.get('comment') else '') for d in o.get('createDates',[]))
  copyrights=o.get('copyrights',[]);pd=any(x.get('name','').casefold()=='domena publiczna' and not x.get('restricted') for x in copyrights)
  image=o.get('image') or {};imageurl=cdn+'/upload/cache/multimedia_detail/'+image['filePath']+'.'+image['extension'] if image.get('filePath') else None
  factual={k:v for k,v in o.items() if k not in ['publicDescriptions','descriptions','multimedia','bibliographies','exhibitions']}
  for a in factual.get('authors',[]):a.pop('biography',None)
  r=row(code,factual,rc,source_id=str(oid),title=o['title'],museum=museum,source_url=web+str(oid),creator_label='; '.join(labels) or None,date_display=date,medium='; '.join(t['name'] for t in o.get('techniques',[])+o.get('materials',[])),source_type=typ,accession_number=o.get('noEvidence') or index.get('inventoryNumber'),dimensions=o.get('dimensionText'),image_url=imageurl,image_rights_label='; '.join(c['name'] for c in copyrights),image_license_url=PDM if pd else None,credit=owner or None,selection_basis='Official museum masterpiece designation; selected pictorial art and sculpture only',identity_note='Current native object ID, accession and creator; legacy Warsaw IDs are not reused as identity keys.')
  if r['date_decision']=='after_cutoff':rejected.append(dict(id=oid,reason='Created after 1970',date=date));continue
  out.append(r)
  if n%50==0:print(code,'objects',n,'/',len(selected),flush=True)
 save(code+'.json.gz',dict(records=out,held=rejected,bounded=True));print(code,'DONE',len(out),flush=True)

def zacheta():
 s=Source();root='https://zacheta.art.pl';candidates={};excluded=[]
 # At most 40 index pages; no image downloads, only caption eligibility.
 for page in range(40):
  url=root+'/pl/kolekcja/katalog'+('?page='+str(page) if page else '')
  raw,rc=s.get(url,as_json=False);sp=BeautifulSoup(raw,'html.parser');items=sp.select('li.collection-item')
  for item in items:
   a=item.select_one('a.collection-item-link');dt=item.select_one('.date');date=dt.get_text(' ',strip=True) if dt else '';lo,hi=bounds(date)
   u=urljoin(root,a['href'].split('?')[0]);author=item.select_one('.author');title=item.select_one('.title')
   if lo and lo>1970:excluded.append(dict(url=u,date=date));continue
   candidates[u]=dict(title=title.get_text(' ',strip=True),creator=author.get_text(' ',strip=True),date=date)
  print('zacheta index',page,len(candidates),flush=True)
  if not sp.select_one('a[href*="?page='+str(page+1)+'"]'):break
 out=[]
 for n,(u,c) in enumerate(candidates.items()):
  raw,rc=s.get(u,as_json=False);sp=BeautifulSoup(raw,'html.parser');text=sp.get_text(' ',strip=True)
  def field(label,end):
   for b in sp.select('li > b'):
    if b.get_text(' ',strip=True).strip()==label.strip():return b.parent.get_text(' ',strip=True)[len(b.get_text(' ',strip=True)):].strip() or None
   if label!='reprodukcja na licencji:':return None
   m=re.search(re.escape(label)+r'\s*(.*?)(?='+end+')',text);return m[1].strip() if m else None
  dt=field('rok powstania:',r'materiał/technika:|wymiary:|numer inw\.:|reprodukcja na licencji:|Inne prace') or c['date']
  typ=field('typ obiektu:',r'rok powstania:|materiał/technika:|wymiary:|numer inw\.:')
  license=field('reprodukcja na licencji:',r'Inne prace|Audiodeskrypcja|Opis pracy|Group') or 'Unknown'
  r=row('zacheta',dict(caption=c,source_type=typ,rights=license),rc,source_id=u.rsplit('/',1)[-1],title=c['title'],creator_label=c['creator'],museum='Zachęta — National Gallery of Art',source_url=u,date_display=dt,source_type={'malarstwo':'painting','rzeźba':'sculpture','rysunek':'drawing','grafika':'print'}.get(typ,typ),medium=field('materiał/technika:',r'wymiary:|numer inw\.:|reprodukcja na licencji:|Inne prace'),dimensions=field('wymiary:',r'numer inw\.:|reprodukcja na licencji:|Inne prace'),accession_number=field('numer inw.:',r'reprodukcja na licencji:|Inne prace'),image_url=None,image_rights_label=license,image_license_url=None,identity_note='Official permanent-collection catalogue; noncommercial images held. No exhibition-page ownership inference.')
  if r['date_decision']=='after_cutoff':continue
  # Source-qualified roles preserved; missing dates remain explicit review records.
  out.append(r)
  if n%50==0:print('zacheta objects',n,'/',len(candidates),flush=True)
 save('zacheta.json.gz',dict(records=out,after_cutoff=excluded,bounded=True));print('zacheta DONE',len(out),flush=True)
def wroclaw():
 s=Source();root='https://muzeumcyfrowe.mnwr.pl';candidates={};held=[]
 for page in range(1,7):
  d,rc=s.get(root+'/api-front/exhibits',dict(collectionUuid='018a40d1-cd2a-7073-997c-827c03796be0',perPage=60,page=page,order='collectionOrd_desc'))
  for a in BeautifulSoup(d['html'],'html.parser').select('a[data-id="embedded-list-item"]'):
   caption=a.get_text(' ',strip=True);years=re.findall(r'(?<!\d)([12]\d{3})(?!\d)',caption)
   if years and min(map(int,years))>1970:held.append(dict(url=a['href'],reason='Index creation after cutoff',caption=caption));continue
   candidates[urljoin(root,a['href'])]=caption
  if page>=d['maxPages']:break
 out=[]
 for n,(u,caption) in enumerate(candidates.items()):
  raw,rc=s.get(u,as_json=False);sp=BeautifulSoup(raw,'html.parser');text=sp.get_text(' ',strip=True)
  def field(label,end):
   m=re.search(re.escape(label)+r'\s*(.*?)(?='+end+')',text);return m[1].strip() if m else None
  label=field('autor:',r'datowanie:|miejsce powstania:|rodzaj:')
  # Multiple names and attribution markers remain unlinked rather than silently simplified.
  creator=clean(label) if label and len(re.findall(r'\([^)]*\)',label))<=1 else label
  if creator and (len(re.findall(r'\([^)]*\)',label or ''))>1 or re.search(r'krąg|warsztat|szkoła|przypis|według|nieznan|naśladow|\?',creator,re.I)):creator='Qualified attribution: '+creator
  dt=field('datowanie:',r'miejsce powstania:|rodzaj:|materiał:|technika:')
  acc=field('numer inwentarza:',r'prawa autorskie|permalink:')
  typ=field('rodzaj:',r'materiał:|technika:|wymiary:')
  r=row('wroclaw',dict(author_label=label,index_caption=caption,object_rights=field('prawa autorskie do obiektu:',r'permalink:'),reproduction_rights=field('Prawa autorskie do wizerunku:',r'Prawa autorskie|Pobierz')),rc,source_id=u.rsplit('/',1)[-1],title=sp.select_one('h1').get_text(' ',strip=True),creator_label=creator,museum='National Museum in Wrocław',source_url=u,date_display=dt,source_type='painting' if typ in ['obraz','ikona'] else typ,medium='; '.join(x for x in [field('materiał:',r'technika:|wymiary:'),field('technika:',r'wymiary:|sygnatury')] if x),dimensions=field('wymiary:',r'sygnatury|historia|udział w wystawach|bibliografia|pochodzenie:'),accession_number=acc,image_url=None,image_rights_label='Museum photograph rights retained separately from artwork public-domain label',image_license_url=None)
  if r['date_decision']=='after_cutoff':held.append(dict(url=u,reason='Object date after cutoff'));continue
  out.append(r)
  if n%50==0:print('wroclaw',n,'/',len(candidates),flush=True)
 save('wroclaw.json.gz',dict(records=out,held=held,bounded=True));print('wroclaw DONE',len(out),flush=True)

def lodz():
 s=Source();root='https://zasoby.msl.org.pl';queue=[root+'/arts/view/322'];seen=set();out=[];held=[]
 while queue and len(seen)<100:
  u=queue.pop(0)
  if u in seen:continue
  seen.add(u)
  try:raw,rc=s.get(u,as_json=False)
  except Exception as e:
   held.append(dict(url=u,reason=str(e)));continue
  sp=BeautifulSoup(raw,'html.parser');text=sp.get_text(' ',strip=True)
  # A bounded first-hop selection from official collection recommendations.
  if len(seen)<=6:
   queue.extend(urljoin(root,a['href']) for a in sp.select('a[href]') if re.fullmatch(r'/arts/view/\d+',a['href']))
  title=sp.title.get_text(' ',strip=True)
  m=re.search(r'(?:Następny|Powiększ|Poprzedni)\s+([^:]+?)\s+'+re.escape(title)+r'\s+Udostępnij:',text)
  if not m:held.append(dict(url=u,reason='Creator field parsing requires review'));continue
  creator=m[1].replace('Poprzedni','').replace('Następny','').replace('Powiększ','').strip().replace(' / ','; ')
  def field(label,end):
   m=re.search(re.escape(label)+r'\s*(.*?)(?='+end+')',text);return m[1].strip() if m else None
  dt=field('Datowanie:',r'Technika:|Materiały:|Rozmiar:|Numer inwentarzowy:')
  acc=field('Numer inwentarzowy:',r'Opis dzieła|Opis dla osób|Audiodeskrypcja|Wystawy')
  if not acc:held.append(dict(url=u,reason='Missing parsed inventory'));continue
  typ='sculpture' if '/R/' in acc else 'painting' if '/M/' in acc else 'print' if '/G/' in acc else 'unknown'
  r=row('lodz',dict(creator=creator,inventory=acc),rc,source_id=u.rsplit('/',1)[-1],title=title,creator_label=creator,museum='Muzeum Sztuki in Łódź',source_url=u,date_display=dt,source_type=typ,medium='; '.join(v for v in [field('Technika:',r'Materiały:|Rozmiar:|Numer inwentarzowy:'),field('Materiały:',r'Rozmiar:|Numer inwentarzowy:')] if v),dimensions=field('Rozmiar:',r'Numer inwentarzowy:'),accession_number=acc,image_url=None,image_license_url=None,image_rights_label='Reproduction permission not established',identity_note='Collection object, exact inventory. Reconstructed works and multiple creator labels preserved.')
  if r['date_decision']=='after_cutoff':held.append(dict(url=u,reason='Created after cutoff',date=dt));continue
  # Reconstructions are distinct later objects; unknown reconstruction dates are not assumed original.
  if re.search('rekonstrukcj',dt or '',re.I):r['date_decision']='date_review';r['year_start']=r['year_end']=None
  out.append(r);print('lodz',len(seen),title,flush=True)
 save('lodz.json.gz',dict(records=out,held=held,bounded=True));print('lodz DONE',len(out),flush=True)

def royal():
 s=Source();root='https://kolekcja.zamek-krolewski.pl';links={root+'/obiekt-1523-dziewczyna-w-ramie-obrazu'};out=[];held=[]
 for page in range(4):
  raw,rc=s.get(root+'/szukaj-w-kolekcji/dzialy/63'+('?page='+str(page) if page else ''),as_json=False)
  links.update(urljoin(root,a['href']) for a in BeautifulSoup(raw,'html.parser').select('a[href]') if a['href'].startswith('/obiekt-'))
 for u in sorted(links):
  raw,rc=s.get(u,as_json=False);sp=BeautifulSoup(raw,'html.parser')
  def field(name):
   el=sp.select_one('.field--name-'+name)
   if not el:return None
   for label in el.select('.field__label'):label.decompose()
   return el.get_text(' ',strip=True)
  title=field('node-title');label=field('field-tworca-z-rola');date=field('field-datowanie');acc=field('field-id-obk')
  if not all([title,acc]):held.append(dict(url=u,reason='Missing object/title'));continue
  simple=re.sub(r'\s*\((autor|malarz)\)$','',label or '')
  if re.search(r'według|naśladowca|szkoła|warsztat|nieznan|\?|autor wzoru',simple,re.I):creator='Qualified attribution: '+simple
  else:creator=clean(simple)
  fields={k:field(k) for k in ['field-datowanie','field-technika-haslo','field-tworzywo-haslo','field-rodzaj-haslo','field-wlasciciel','field-gabaryty']}
  r=row('royal-warsaw',dict(fields=fields,author_label=label),rc,source_id=re.search(r'obiekt-(\d+)',u)[1],title=title,creator_label=creator,museum='Royal Castle in Warsaw',source_url=u,date_display=date,source_type='painting',medium='; '.join(x for x in [fields['field-technika-haslo'],fields['field-tworzywo-haslo']] if x),dimensions=fields['field-gabaryty'],accession_number=acc,image_url=None,image_license_url=None,image_rights_label='Reproduction permission not established')
  if r['date_decision']!='after_cutoff':out.append(r)
 print('royal DONE',len(out),flush=True);save('royal.json.gz',dict(records=out,held=held,bounded=True))

def highlights():
 s=Source();out=[]
 selections=[
 ('National Museum in Poznań','https://mnp.art.pl/galeria-malarstwa-i-rzezby/monet-powrocil','Plaża w Pourville','Claude Monet','1882','painting',None),
 ('National Museum, Gdańsk, Poland','https://sadostateczny.mng.gda.pl/historia-obrazu','Sąd Ostateczny','Hans Memling',None,'painting','Triptych; source holding/history verified; no inferred creation date'),
 ('National Museum in Lublin','https://zamek-lublin.pl/kaplica-trojcy-swietej/','Polichromia Kaplicy Trójcy Świętej','Master Andrzej and Ruthenian workshop; Kurył (Cyryl); Juszko','1418','mural painting','Documented mural ensemble completed 10 August 1418; not individual-figure or whole-building inflation; historical master label remains unlinked'),
 ]
 for museum,u,title,artist,date,typ,note in selections:
  raw,rc=s.get(u,as_json=False);sp=BeautifulSoup(raw,'html.parser');text=sp.get_text(' ',strip=True)
  assert ('Pourville' in text if 'Pourville' in title else title.split()[0].casefold() in text.casefold()),title
  out.append(row('poland-highlights',dict(editorial_facts=dict(title=title,creator=artist,date=date),identity_note=note),rc,source_id=urlsplit(u).netloc+urlsplit(u).path,title=title,creator_label=artist,museum=museum,source_url=u,date_display=date,source_type=typ,medium=None,accession_number=None,image_url=None,image_license_url=None,image_rights_label='Not cleared',identity_note=note))
 u='https://muzeum.szczecin.pl/zbiory/sztuka-dawna-do-xviii-w/malarstwo-i-rzezba-xvi-xviii-w?format=html';raw,rc=s.get(u,as_json=False);sp=BeautifulSoup(raw,'html.parser')
 for img in sp.select('img[alt]'):
  caption=img['alt']
  if 'fot.' not in caption:continue
  parts=caption.split(', ');creator=parts[0]
  # Multi-comma titles handled explicitly; selected complete paintings, no detail images.
  if any(x in caption for x in ['fragm.','część środkowa','Płyta']):continue
  if len(parts)<5:continue
  date_idx=next((i for i,p in enumerate(parts[2:],2) if re.search(r'\d{4}|XV|XVI',p)),None)
  if date_idx is None:continue
  title=', '.join(parts[1:date_idx]);date=parts[date_idx]
  if re.search(r'Malarz|Artysta nieznany|\?',creator):creator='Qualified attribution: '+creator
  out.append(row('szczecin',dict(caption=caption),rc,source_id=Path(img['src']).stem,title=title,creator_label=creator,museum='National Museum in Szczecin',source_url=u,date_display=date,source_type='painting',medium=', '.join(parts[date_idx+1:-1]),accession_number=None,image_url=None,image_license_url=None,image_rights_label='Named museum photographer; permission not established'))
 save('highlights.json.gz',dict(records=out,bounded=True));print('highlights DONE',len(out),flush=True)

if __name__=='__main__':
 if sys.argv[1] in ['warsaw','krakow']:museum_api(sys.argv[1])
 else:globals()[sys.argv[1]]()
