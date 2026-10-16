#!/usr/bin/env python3
"""Selected Soviet painting portfolios, with repeat auction listings reconciled."""
import collections,concurrent.futures,importlib.util,re,sys
from bs4 import BeautifulSoup
from urllib.parse import urljoin,urlsplit
from pathlib import Path
sp=importlib.util.spec_from_file_location('soviet',Path(__file__).with_name('soviet-realism-20261011.py'));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
BASE='https://sovcom.ru';CATEGORY=BASE+'/chastnye_prodazhi/sovetskaya-zhivopis/'

def field(card,label):
 el=next((e for e in card.select('strong') if m.norm(e.get_text(' ',strip=True)).startswith(label)),None)
 if not el:return None
 text=[]
 for sibling in el.next_siblings:
  if getattr(sibling,'name',None) in ['br','strong']:break
  text.append(sibling.get_text(' ',strip=True) if hasattr(sibling,'get_text') else str(sibling))
 return ' '.join(text).strip(' –-\t\n') or None

def parse(card,rc,artist=None):
 link=card.select_one('.lot-title a, .cart-item-title h3 a');im=card.select_one('img');cl=card.select_one('a[href*="/avtory/"]')
 if not link or not im:return None
 title=link.get_text(' ',strip=True);url=urljoin(BASE,link['href']);date_display=field(card,'год');date=m.date_tail(date_display or '')
 title=re.sub(r'^\(λ\)\s*','',title).rstrip('.').strip();medium=field(card,'техника');dims=field(card,'размер')
 creator_label=(cl.get_text(' ',strip=True) if cl else artist['full_name'] if artist else None)
 creator_url=urljoin(BASE,cl['href']) if cl else artist['url'] if artist else None
 if not creator_label or not creator_url:return None
 hold=None
 if not date:hold='Unresolved creation date'
 elif not 1917<=date['creation_year_start']<=date['creation_year_end']<=1970:hold='Outside Soviet through-1970 creation scope'
 elif re.search(r'\b(?:копия|по мотивам|репродукци|приписыва|подражани|неизвестн|круг|школа)\w*',creator_label+' '+title,re.I):hold='Qualified attribution or copy/version requires separate review'
 elif not medium or not re.search('масло|темпера|гуашь|акварель|карандаш|пастель|тушь',medium,re.I):hold='Material is outside selected painting/drawing scope'
 row=dict(provider='sovcom',source_id=m.sha(url.encode())[:24],source_url=url,source_title=title,title=title,
  creator_label=creator_label,creator_source_label=creator_label,creator_url=creator_url,date=date,source_date_display=date_display,
  dimensions_text=dims,medium_text=medium,category='soviet-painting',categories=['soviet-painting'],
  receipt=rc,source_image_url=urljoin(BASE,im['src']),source_rights_label='© 2000–2026 СОВКОМ. Все права защищены',rights_status='restricted',
  description_source=field(card,'описание'),hold=hold,outcome='captured',work_type='watercolor' if 'акварель' in (medium or '').casefold() else 'drawing' if re.search('карандаш|пастель|тушь',medium or '',re.I) else 'painting')
 return row

def category():
 def one(page):
  url=CATEGORY+('?PAGEN_1='+str(page) if page>1 else '')
  raw,rc=m.capture(url,'sovcom-captures');s=BeautifulSoup(raw,'html.parser');rows=[parse(c,rc) for c in s.select('tr.cart-item')];rows=[r for r in rows if r]
  m.save(m.RUN/'sovcom-category'/f'{page:03d}.json.gz',dict(receipt=rc,rows=rows));return rows
 rows={}
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
  for rr in pool.map(one,range(1,22)):
   for r in rr:rows[r['source_url']]=r
 m.save(m.RUN/'sovcom-category-records.json.gz',list(rows.values()))
 print('SOVCOM category',len(rows),'records;',sum(not r['hold'] for r in rows.values()),'dated leads',flush=True)

def artists():
 rows=m.load(m.RUN/'sovcom-category-records.json.gz');urls=collections.Counter(r['creator_url'] for r in rows if not r['hold'])
 # Bounded portfolios selected from dated works in the source's Soviet painting category.
 selected=sorted(urls,key=lambda u:(-urls[u],u))[:140]
 m.save(m.RUN/'sovcom-selected-portfolios.json',dict(urls=selected,selection='Native Soviet painting category contains an explicitly eligible work; portfolios ordered by number of such works, URL tie break; max 140. The source explicitly describes this category as Soviet painting / Socialist Realism. Individual later, unknown, abstract and duplicate works remain excluded.'))
 def one(url):
  dest=m.RUN/'sovcom-portfolios'/(m.sha(url.encode())+'.json.gz')
  if dest.exists():return m.load(dest)
  raw,rc=m.capture(url,'sovcom-captures');s=BeautifulSoup(raw,'html.parser');h=s.select_one('h1');name=h.get_text(' ',strip=True) if h else ''
  bio=[]
  for e in h.next_siblings if h else []:
   if getattr(e,'name',None) in ['div','table','h1','h2']:break
   if hasattr(e,'get_text'):bio.append(e.get_text(' ',strip=True))
  text=' '.join(bio);life=re.search(r'(?:Родил\w*[^.]{0,120}?)(18\d{2}|19\d{2})',text,re.I)
  profile=dict(url=url,full_name=name,label=name,source_label=name,birth_year=int(life[1]) if life else None,title=name,biography_source_text=text,receipt=rc,outcome='captured',provider='sovcom')
  rows=[parse(c,rc,profile) for c in s.select('tr.cart-item')];rows=[r for r in rows if r]
  result=dict(profile=profile,rows=rows);m.save(dest,result);m.save(m.RUN/'artists'/(m.sha(url.encode())+'.json.gz'),profile)
  return result
 counts=collections.Counter()
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
  for n,result in enumerate(pool.map(one,selected),1):
   counts['rows']+=len(result['rows']);counts['eligible']+=sum(not r['hold'] for r in result['rows'])
   if n%10==0:print('SOVCOM portfolios',n,'/',len(selected),dict(counts),flush=True)
 print('SOVCOM portfolios',dict(counts),flush=True)

def reconcile():
 rows=[]
 for p in (m.RUN/'sovcom-portfolios').glob('*.json.gz'):rows+=m.load(p)['rows']
 byurl={};held=[]
 for row in rows:
  if row['hold']:held.append(row);continue
  byurl.setdefault(row['source_url'],row)
 byimage=collections.defaultdict(list)
 for r in byurl.values():byimage[r['source_image_url']].append(r)
 selected=[];repeats=[]
 for image,group in byimage.items():
  identities={(m.norm(x['creator_label']),x['date']['creation_year_start'],x['date']['creation_year_end'],m.norm(x['dimensions_text'])) for x in group}
  # Full creator names are stable across the portfolio's historical lot list.
  if len(identities)>1:
   held.extend(dict(x,hold='Same source reproduction has conflicting creator/date/dimensions') for x in group);continue
  r=sorted(group,key=lambda x:(not '/chastnye_prodazhi/' in x['source_url'],x['source_url']))[0]
  r=dict(r,repeated_source_records=[dict(source_url=x['source_url'],source_title=x['title'],receipt=x['receipt']) for x in group if x['source_url']!=r['source_url']])
  selected.append(r);repeats.extend(r['repeated_source_records'])
 # Same artist/title/date/dimensions is a potential reoffered object even with a new image filename.
 bykey=collections.defaultdict(list)
 for r in selected:bykey[(r['creator_url'],m.norm(r['title']),r['date']['creation_year_start'],r['date']['creation_year_end'],m.norm(r['dimensions_text']))].append(r)
 final=[]
 for group in bykey.values():
  if len(group)>1:
   # Retain one candidate; record other auction listings for image comparison.
   group.sort(key=lambda r:r['source_url']);r=dict(group[0],possible_repeat_records=group[1:]);final.append(r)
   repeats.extend(dict(source_url=x['source_url'],reason='Same creator/title/date/dimensions; not counted separately') for x in group[1:])
  else:final+=group
 m.save(m.RUN/'sovcom-records.json.gz',dict(rows=final,held=held,repeated_listings=repeats))
 print('SOVCOM reconciled',len(final),'candidate objects;',len(held),'held;',len(repeats),'repeat listings not counted',flush=True)

if __name__=='__main__':globals()[sys.argv[1]]()
