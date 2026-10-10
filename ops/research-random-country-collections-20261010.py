#!/usr/bin/env python3
"""Bounded primary museum research for the frozen country draw; no DB writes."""
import gzip,hashlib,html,argparse,collections,concurrent.futures,importlib.util,json,re,threading,time
from pathlib import Path
from urllib.parse import urljoin,urlsplit
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('b',Path(__file__).with_name('research-chinese-art-20261008.py'));b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
ROOT=b.ROOT;RUN=ROOT/'docs/research/random-country-collections-20261010';PDM='https://creativecommons.org/publicdomain/mark/1.0/'
def phase(code):b.RUN=RUN/code;b.RUN.mkdir(parents=True,exist_ok=True)
def save(n,v):b.save(n,v)
def page(url,source=None):
 raw,rc=(source or b.Source()).get(url,as_json=False)
 # Some WordPress caches deliver gzip without Content-Encoding; preserve the original receipt.
 payload=gzip.decompress((b.RUN/'captures'/(hashlib.sha256(rc['url'].encode()).hexdigest()+'.body.gz')).read_bytes())
 if payload.lstrip().startswith(b'\x1f\x8b'):raw=gzip.decompress(payload.lstrip()).decode('utf-8')
 return BeautifulSoup(raw,'html.parser'),rc
def nextitem(url,source=None):
 sp,rc=page(url,source);data=json.loads(sp.select_one('#__NEXT_DATA__').string)['props']['pageProps'];return data['data']['item'],rc
def bounds(text):
 text=re.sub(r'(?<=\d)\.(?=\s*[-–])','',(text or '')).strip().rstrip('.');text=text[1:-1] if text.startswith('(') and text.endswith(')') else text;text=re.sub(r'\bprecies\s*','',text,flags=re.I);t=re.sub(r'^(?:circa|ca\.?|c\.?|oko|um|about|around|vers|environ)\s*','',text,flags=re.I)
 t=re.sub(r'(?<=-)\s*(?:circa|ca\.?|c\.?)\s*','',t,flags=re.I)
 t=re.sub(r'(?<=–)\s*(?:circa|ca\.?|c\.?)\s*','',t,flags=re.I)
 t=re.sub(r'^between (\d{3,4}) and (\d{3,4})$',r'\1–\2',t,flags=re.I)
 if re.fullmatch(r'\d{3,4}',t):return int(t),int(t)
 x=re.fullmatch(r'(\d{3,4})\s*[-–—/]\s*(\d{3,4})',t)
 if x:return int(x[1]),int(x[2])
 x=re.fullmatch(r'(\d{4})\s*[-–—/]\s*(\d{2})',t)
 if x:return int(x[1]),int(x[1][:2]+x[2])
 x=re.fullmatch(r'(?:January|February|March|April|May|June|July|August|September|October|November|December|Summer|Winter|Spring|Autumn)\s+(\d{4})',t,re.I)
 if x:return int(x[1]),int(x[1])
 years=re.findall(r'\b[12]\d{3}\b',text)
 if years and min(map(int,years))>1970:return min(map(int,years)),max(map(int,years))
 return None,None
def record(provider,raw,rc,**kw):
 lo,hi=bounds(kw.get('date_display'));return b.candidate(provider,raw,rc,year_start=lo,year_end=hi,image_url=None,image_license_url=None,image_rights_label='Reproduction permission not established',**kw)
def clean_name(x):return re.sub(r'\s*\([^)]*\)\s*$','',x or '').strip()
def accept(r,held):
 if r['date_decision']=='after_cutoff':held.append(dict(key=r['provider']+'/'+r['source_id'],reason='Created after 1970',date=r['date_display']));return False
 if re.search(r'\b(?:on loan|permanent loan|lent by|Leihgabe|Dauerleihgabe|Depositum)\b',r.get('credit') or '',re.I):held.append(dict(key=r['provider']+'/'+r['source_id'],reason='Loan/deposit requires separate holding classification',credit=r['credit']));return False
 assert len(r.get('accession_number') or '')<150
 return True
def vkc():
 phase('BE');src=b.Source();sp,rc=page('https://vlaamsekunstcollectie.be/en/collection',src);tag=sp.find('v-collection');src.session.headers['Authorization']='ApiKey '+tag['search-key'];out=[];held=[];totals={}
 locations=['Royal Museum of Fine Arts Antwerp','Museum of Fine Arts Ghent','Musea Brugge','Mu.ZEE, Art Museum by the Sea']
 for loc in locations:
  for typ,cap in [('schilderij',150),('tekening',30)]:
   types=({'schilderij':['olieverfschilderijen'],'tekening':['potloodtekening','houtskooltekening','inkttekening','pasteltekening']}[typ] if loc=='Museum of Fine Arts Ghent' else ['schilderij','olieverfschildering'] if loc=='Musea Brugge' and typ=='schilderij' else [typ])
   query={'size':cap,'query':{'bool':{'filter':[{'term':{'location_en.keyword':loc}},{'nested':{'path':'sub_types','query':{'terms':{'sub_types.preferred_name_nl.keyword':types}}}}],'must_not':[{'exists':{'field':'unpublished_at'}}]}},'sort':[{'id':'asc'}]}
   raw,rc=src.search_post(tag['host']+'/'+tag['index']+'/_search',query);d=json.loads(raw);totals[loc+'/'+typ]=d['hits']['total']
   for hit in d['hits']['hits']:
    x=hit['_source'];people=x.get('creators',[]);creator='; '.join((p.get('attribution_en') or p.get('attribution_nl') or '')+' '+p['preferred_name'] for p in people).strip() or None
    museum={'Museum of Fine Arts Ghent':'Museum of Fine Arts Ghent (MSK)','Musea Brugge':'Groeningemuseum — Musea Brugge'}.get(loc,loc)
    if loc=='Musea Brugge' and 'GRO' not in x['number']:held.append(dict(key='vkc/'+str(x['id']),reason='Musea Brugge department not securely resolved',number=x['number']));continue
    w=record('vkc',x,rc,source_id=str(x['id']),title=x.get('title_en') or x['title_nl'],alternate_title=x.get('title_nl'),museum=museum,source_url='https://vlaamsekunstcollectie.be/en/collection/'+x['slug'],creator_label=creator,date_display=x.get('dating'),source_type={'schilderij':'painting','tekening':'drawing'}[typ],medium=x.get('display_material_en') or x.get('display_material_nl'),dimensions=x.get('measurements'),accession_number=x['number'],credit=None,selection_basis='Bounded official collection query: first 150 paintings and 30 drawings by stable ID per partner museum; eligible metadata selected before images')
    if len(people)==1:
     p=people[0];w['creator_wikidata']=p.get('wikidata');w['creator_source_url']='https://vlaamsekunstcollectie.be/en/creators/'+p['slug'];w['creator_life_source']=' – '.join(str(p.get(k) or '')[:4] for k in ['birth_date','death_date'])
    if len(people)!=1 or any(p.get('attribution_nl') or p.get('attribution_en') for p in people):w['creator_link_hold']='Multiple or qualified creators; preserve original object label'
    if x.get('copyright') and re.search('public domain|CC0',x['copyright'],re.I) and x.get('image'):
     w.update(image_url=x['image'].rstrip('/')+'/full/!1400,1400/0/default.jpg',image_license_url=PDM,image_rights_label=x['copyright'],image_rights_status='public_domain',image_creator_credit=creator)
    else:w['image_rights_label']=x.get('copyright') or 'Unknown'
    if isinstance(w.get('year_end'),int) and w['year_end']>1970 and w.get('year_start',9999)<=1970:held.append(dict(key='vkc/'+str(x['id']),reason='Creation range crosses 1970',date=w['date_display']));continue
    if accept(w,held):out.append(w)
 print('VKC',len(out),'held',len(held),totals,flush=True);save('vkc-records.json.gz',dict(records=out,held=held,totals=totals))

def typology(medium):
 t=(medium or '').lower()
 if re.search(r'bronze|bronca|plaster|marble|granite|terracotta|wood carving|kamen',t):return 'sculpture'
 if re.search(r'oil|tempera|acrylic|huile|ulje',t):return 'painting'
 if re.search(r'etching|engraving|lithograph|woodcut|linocut|drypoint|bakrorez',t):return 'print'
 if re.search(r'pencil|charcoal|ink|chalk|pastel|watercolour|watercolor|gouache',t):return 'drawing'
 return 'unknown'
def rmfab():
 phase('BE');src=b.Source();sp,rc=page('https://fine-arts-museum.be/fr/la-collection',src);urls=list(dict.fromkeys(urljoin(rc['final_url'],a['href']) for a in sp.select('a[href]') if '/fr/la-collection/' in a['href'] and not re.search('/(?:artist|letter)/',a['href'])))[:20];out=[];held=[]
 for u in urls:
  try:
   sp,rc=page(u,src);author=sp.select_one('span.author');label=author.get_text(' ',strip=True);h=author.parent;title=h.get_text(' ',strip=True)[len(label):].strip();inv=sp.select_one('p.inv').get_text(' ',strip=True);dt,acc=inv.split('Inv.',1);dt=dt.strip(' —–-');acc=acc.strip();main=sp.find(id='content-main') or sp
   text=main.get_text('\n',strip=True);parts=text.split('Description\n',1)[1].split('Artistes',1)[0].strip().splitlines();medium=parts[0];dimensions=next((x.split(':',1)[1].strip() for x in parts if x.startswith('Dimensions')),None);credit=next((x for x in parts if x.startswith('Origine')),None)
   w=record('rmfab',dict(label=text[:2500],inventory=inv),rc,source_id=acc,title=title,museum='Royal Museums of Fine Arts of Belgium, Brussels, Belgium',source_url=u,creator_label=label,date_display=dt or None,source_type=typology(medium),medium=medium,dimensions=dimensions,accession_number=acc,credit=credit,selection_basis='Twenty museum homepage collection recommendations captured in a frozen source response')
   if re.search(r'dépôt|pret|prêt',credit or '',re.I):held.append(dict(url=u,reason='Deposited/loan collection requires ownership reconciliation',credit=credit));continue
   if accept(w,held):out.append(w)
  except Exception as e:held.append(dict(url=u,reason=str(e)))
 save('rmfab-records.json.gz',dict(records=out,held=held));print('RMFAB',len(out),'held',len(held),flush=True)
def lnmm():
 phase('LV');src=b.Source();items=b.load('lnmm-caption-discovery.json.gz');sp,rc=page('https://lnmm.gov.lv/en/collections/collection-of-foreign-art',src)
 urls=list(dict.fromkeys(urljoin(rc['final_url'],a['href']) for a in sp.select('a[href]') if 'art-museum-riga-bourse-collections' in a['href'] and any(t in a['href'] for t in ['painting','graphic','sculpture'])))
 for u in urls:
  sp,rc=page(u,src);caps=[]
  for node in sp.select('div.image'):
   desc=node.select_one('.description');im=node.find('img')
   if desc and im:caps.append(dict(caption=desc.get_text(' ',strip=True),html=str(desc),image=urljoin(u,im['src'])))
  items.append(dict(url=u,evidence=rc,captions=caps))
 save('lnmm-all-caption-discovery.json.gz',items);out={};held=[]
 for item in items:
  u=item['url'];museum='Romans Suta and Aleksandra Beļcova Museum' if '/romans-suta-' in u else 'Art Museum Riga Bourse' if '/art-museum-riga-bourse/' in u else 'Latvian National Museum of Art, Riga, Latvia'
  for pos,c in enumerate(item['captions']):
   text=c['caption'];sp=BeautifulSoup(c['html'],'html.parser');em=sp.find('em');match=re.match(r'^(.+?)\.\s*(.+)$',text)
   if not match:held.append(dict(url=u,caption=text,reason='Caption requires manual parsing'));continue
   creator,rest=match.groups()
   if em and em.get_text(' ',strip=True):
    title=em.get_text(' ',strip=True).strip(' .');prefix=text.find(title);creator=text[:prefix].strip(' .');tail=text[prefix+len(title):].lstrip(' .')
   else:
    split=re.split(r'\.\s*(?=(?:C\.?|Ca\.?|Not later than|Before|After|\d{3,4})\s*\d*)',rest,maxsplit=1)
    if len(split)!=2:held.append(dict(url=u,caption=text,reason='Missing separable title/date'));continue
    title,tail=split;title=title.strip(' .')
   date=re.match(r'^((?:(?:C\.?|Ca\.?|Circa|Not later than|Before|After)\s*)?\d{3,4}(?:\s*[-–/]\s*\d{2,4})?(?:s)?)(?:\.|\s)',tail,re.I)
   if not date:
    date=re.match(r'^(Undated)\.\s*',tail,re.I)
   if not date:held.append(dict(url=u,caption=text,reason='Date caption requires review'));continue
   dt=date[1];remaining=tail[date.end():].strip(' .');medium=remaining.split('.')[0].strip();dims=re.search(r'\b\d+(?:[.,]\d+)?\s*[x×]\s*\d+(?:[.,]\d+)?(?:\s*[x×]\s*\d+(?:[.,]\d+)?)?\s*(?:cm|mm)',remaining)
   if not re.search(r'collection',text,re.I) and '/collections/' not in u and '-collections/' not in u:held.append(dict(url=u,caption=text,reason='Collection ownership not explicit in display caption'));continue
   # Source image name helps retain exact object identity while duplicates in carousel markup collapse.
   stable=re.sub(r'_\d+\.jpg$','',urlsplit(c['image']).path.split('/')[-1]);key=hashlib.sha256((museum+'|'+creator.casefold()+'|'+title.casefold()+'|'+str(bounds(dt))).encode()).hexdigest()[:22]
   w=record('lnmm',c,item['evidence'],source_id=key,title=title,museum=museum,source_url=u+'#artline-caption-'+str(pos),creator_label=creator,date_display=dt,source_type=typology(medium),medium=medium,dimensions=dims[0] if dims else None,accession_number=None,credit=re.search(r'(?:LNMA|LNMM|Museum).*collection',text)[0] if re.search(r'(?:LNMA|LNMM|Museum).*collection',text) else 'Official collection department caption',selection_basis='Official painting, sculpture, graphics and memorial collection highlights with explicit object captions')
   w['reference_image_url']=c['image'];w['native_image_identity']=stable
   if re.search(r'unknown|anonymous|workshop|school|copy|attributed',creator,re.I):w['creator_link_hold']='Qualified or unknown source creator'
   if accept(w,held):out.setdefault(key,w)
 save('lnmm-records.json.gz',dict(records=list(out.values()),held=held));print('LNMM',len(out),'held',len(held),flush=True)
def nmmu():
 phase('HR');src=b.Source();out=[];held=[]
 for n in range(1,4):
  d,rc=src.get('https://nmmu.hr/wp-json/wp/v2/posts',dict(categories=2191,per_page=100,page=n,orderby='id',order='asc',_fields='id,link,title,content'))
  for x in d:
   sp=BeautifulSoup(x['content']['rendered'],'html.parser')
   for el in sp.select('br'):el.replace_with('\n')
   for el in sp.select('p,h1,h2,h3'):el.append('\n')
   lines=[' '.join(v.split()) for v in sp.get_text(' ',strip=False).split('\n') if v.strip()];heading=BeautifulSoup(x['title']['rendered'],'html.parser').get_text(' ',strip=True);top='\n'.join(lines[:12]);acc=re.search(r'\bMG\s*[-–]\s*\d+(?:[-/]\d+)*',top)
   if not acc:held.append(dict(id=x['id'],title=heading,reason='No exact museum inventory in header'));continue
   # Native first-line creator, then title/date; explicit life dates are kept separately.
   if x['id']==7175:lines=lines[1:] # A named curator precedes the native object header.
   creator=clean_name(lines[0]).rstrip(',');start=1
   while start<len(lines) and (re.fullmatch(r'\(?\d{4}\s*[-–]\s*\d{4}\)?',lines[start]) or re.fullmatch(r'\([^)]*\d{4}[^)]*\)',lines[start])):start+=1
   label=lines[start]
   if start+1<len(lines) and re.fullmatch(r',?\s*(?:(?:circa|c\.?|ca\.?|around)\s*)?\d{4}(?:\s*[-–/]\s*\d{2,4})?s?\.?',lines[start+1],re.I):label=label.rstrip(',')+', '+lines[start+1].lstrip(', ');start+=1
   match=re.match(r'^(.+),\s*((?:c\.?|ca\.?|around|circa|early|late)?\s*\d{3,4}(?:\s*[-–/]\s*\d{2,4})?s?)\.?$',label,re.I)
   if not match:match=re.match(r'^(.+),\s*(s\.\s*a\.)$',label,re.I)
   if not match:held.append(dict(id=x['id'],title=heading,header=top,reason='Title/creation header requires manual review'));continue
   title,dt=match.groups();title=title.strip();medium=lines[start+1] if len(lines)>start+1 else None
   if medium and (medium.startswith('series ') or re.match(r'^\d',medium) or medium.startswith('MG-')):medium=next((ln for ln in lines[start+1:start+4] if re.search(r'bronze|oil|wood|plaster|stone|marble|watercol|canvas|gouache|mixed|tempera',ln,re.I) and not ln.startswith('series ')),None)
   dims=re.search(r'\b\d+(?:[.,]\d+)?\s*[x×]\s*\d+(?:[.,]\d+)?(?:\s*[x×]\s*\d+(?:[.,]\d+)?)?\s*(?:cm|mm)',top)
   w=record('nmmu',dict(id=x['id'],heading=heading,header=top),rc,source_id=str(x['id']),title=title,museum='National Museum of Modern Art, Zagreb',source_url=x['link'],creator_label=creator,date_display=dt,source_type=typology(medium),medium=medium,dimensions=dims[0] if dims else None,accession_number=re.sub(r'\s+','',acc[0]).replace('–','-'),credit='National Museum of Modern Art, Zagreb; official collection inventory',selection_basis='First 300 official Discover archive object highlights ordered by native post ID')
   ims=sp.select('img');w['reference_image_url']=ims[0].get('src') if ims else None
   if accept(w,held):out.append(w)
  print('NMMU page',n,'selected',len(out),'held',len(held),flush=True)
 save('nmmu-records.json.gz',dict(records=out,held=held))

def croatia_highlights():
 phase('HR');src=b.Source();out=[];held=[]
 # Official Dubrovnik collection captions: no current-display inference.
 u='https://ugdubrovnik.hr/?file=zbirka';sp,rc=page(u,src)
 for pos,n in enumerate(sp.select('td i')):
  lines=n.get_text('\n',strip=True).splitlines()
  if len(lines)!=3:continue
  creator,td,medium=lines;td=td.rstrip('.');match=re.match(r'^(.+),\s*((?:oko\s*)?\d{4}(?:\.?\s*[-–]\s*\d{4})?)$',td)
  if not match:
   held.append(dict(url=u,caption=lines,reason='Date/title require manual source reconciliation'));continue
  title,dt=match.groups();dt=re.sub(r'(?<=\d)\.(?=\s*-)', '',dt)
  w=record('croatia-highlight',dict(caption=lines),rc,source_id='dubrovnik/'+str(pos),title=title,museum='Museum of Modern Art Dubrovnik',source_url=u+'#artline-caption-'+str(pos),creator_label=creator.title(),date_display=dt,source_type=typology(medium),medium=medium,dimensions=None,accession_number=None,credit='Official museum collection page',selection_basis='Official selected museum collection works')
  if accept(w,held):out.append(w)
 # Split collection departments preserve original qualified labels and exact inventory strings.
 for section in ['zbirka-starih-majstora','zbirka-ikona','zbirka-moderne-umjetnosti']:
  u='https://galum.hr/zbirke/'+section;sp,rc=page(u,src)
  for pos,n in enumerate(sp.select('section.image-data')):
   a=n.select_one('.image-author');t=n.select_one('.image-title');d=n.select_one('.image-description')
   if not(a and t and d):continue
   creator=a.get_text(' ',strip=True);td=t.get_text(' ',strip=True);txt=d.get_text(' ',strip=True);acc=re.search(r'inventarni broj\s*([()\d/.-]+)',txt,re.I)
   if not acc:held.append(dict(url=u,caption=n.get_text(' ',strip=True),reason='Inventory missing'));continue
   match=re.match(r'^(.+),\s*((?:oko\s*)?\d{4}(?:\.?\s*[-–]\s*\d{4})?)\.?$',td);title,dt=match.groups() if match else (td,None)
   creator=re.sub(r'\s*\([^)]*\d[^)]*\)','',creator).strip();medium=txt.split('inventarni broj')[0].strip();dims=re.search(r'\b\d+(?:[.,]\d+)?\s*x\s*\d+(?:[.,]\d+)?(?:\s*x\s*\d+(?:[.,]\d+)?)?\s*cm',medium)
   w=record('croatia-highlight',dict(caption=n.get_text(' ',strip=True)),rc,source_id='split/'+section+'/'+str(pos),title=title,museum='Museum of Fine Arts, Split',source_url=u+'#artline-caption-'+str(pos),creator_label=creator,date_display=dt,source_type='print' if 'bakrorez' in medium else 'sculpture' if 'kamen' in medium else 'painting',medium=medium,dimensions=dims[0] if dims else None,accession_number=acc[1].strip('()'),credit='Official collection department caption',selection_basis='Old Masters, icons and modern art collection department highlights')
   if re.search('pripisano|radionica|nepoznati|krug|škola| po ',creator,re.I):w['creator_link_hold']='Qualified/anonymous Croatian source label preserved'
   if accept(w,held):out.append(w)
 # Duplicate captions collapse; conflicting inventories are all held, not arbitrarily assigned.
 groups=collections.defaultdict(list)
 for w in out:
  if w['museum']=='Museum of Fine Arts, Split':groups[w['accession_number']].append(w)
 bad=set();dupe=set()
 for acc,works in groups.items():
  titles={w['title'] for w in works}
  if len(titles)>1:
   for w in works:bad.add(w['source_id']);held.append(dict(key=w['source_id'],title=w['title'],inventory=acc,reason='Official page reuses inventory for different works'))
  else:
   for w in works[1:]:dupe.add(w['source_id']);held.append(dict(key=w['source_id'],reason='Repeated exact caption'))
 out=[w for w in out if w['source_id'] not in bad|dupe]
 save('croatia-highlights-records.json.gz',dict(records=out,held=held));print('Croatia highlights',len(out),'held',len(held),flush=True)

if __name__=='__main__':
 import sys
 globals()[sys.argv[1]]()
