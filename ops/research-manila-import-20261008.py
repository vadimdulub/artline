#!/usr/bin/env python3
"""Bounded primary-source Manila/Metro Manila museum catalogue selection."""
import argparse,collections,concurrent.futures,hashlib,importlib.util,json,re
from pathlib import Path
from urllib.parse import urljoin,quote
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('r',Path(__file__).with_name('research-chinese-art-20261008.py'));r=importlib.util.module_from_spec(s);s.loader.exec_module(r);r.RUN=r.ROOT/'docs/research/asian-collections-import-20261008/manila'
def kind(medium):
 text=(medium or '').lower()
 if any(x in text for x in ['woodcut','lithograph','etching','engraving','print']):return 'print'
 if 'watercolor' in text or 'watercolour' in text:return 'watercolor'
 if any(x in text for x in ['pencil','charcoal','graphite','pen and ink']):return 'drawing'
 if any(x in text for x in ['oil','acrylic','tempera','painting']):return 'painting'
 if any(x in text for x in ['bronze','sculpture','plaster relief','narra']):return 'sculpture'
 return 'unknown'
def item(provider,identifier,title,creator,date,museum,url,rc,raw,medium=None,dimensions=None,image=None,source_type=None):
 lo=hi=None;decision='date_review';display=date
 if date:
  match=re.fullmatch(r'(?:[Cc](?:a)?\.?\s*)?(\d{4})(?:\s*[-–]\s*(\d{4}))?',date.strip())
  if match:
   lo=int(match[1]);hi=int(match[2]or match[1]);decision='within_cutoff_source_bounds' if hi<=1970 else 'after_cutoff' if lo>1970 else 'date_review'
  elif re.search(r'(?:18\d\ds|19th century|19 th century)',date,re.I):decision='within_cutoff_source_period'
  elif re.fullmatch(r'(?:[Cc]irca\s+)?(?:18|19|20)\d0s',date.strip()):
   lo=int(re.search(r'\d{4}',date)[0]);hi=lo+9;decision='within_cutoff_source_bounds' if hi<=1970 else 'after_cutoff' if lo>1970 else 'date_review'
 if provider=='lopez' and date=='2026':
  lo=hi=None;decision='date_review';display='Date unknown (museum page displays 2026)';raw['date_uncertainty']='Unlabelled header shows the current year even for historical makers. Do not accept as artwork creation; preserve for source correction.'
 out=r.candidate(provider,raw,rc,source_id=identifier,title=title,museum=museum,accession_number=None,source_url=url,creator_label=creator,date_display=display,year_start=lo,year_end=hi,source_type=source_type or kind(medium),medium=medium,dimensions=dimensions,culture=None,image_url=image,image_license_url=None,image_rights_label='No general image reuse license established',credit=museum);out['date_decision']=decision;return out
def lopez():
 src=r.Source();base='https://lml.org.ph';h,rc=src.get(base+'/collections/artworks',as_json=False)
 artists=re.findall(r"artist:\s*'([^']+)',\s*artistId:\s*'(\d+)'",h);assert 10<=len(artists)<=60;rows=[]
 for name,aid in artists:
  url=base+'/collections/artworks-artist?artist='+aid;h,rc=src.get(url,as_json=False);soup=BeautifulSoup(h,'html.parser')
  for article in soup.select('article'):
   header=article.find('header');footer=article.find('footer')
   if not header or not footer or not header.find('h2'):continue
   title=header.find('h2').get_text(' ',strip=True);date=header.find('p').get_text(' ',strip=True) if header.find('p') else None
   fields={t.get_text(' ',strip=True):t.find_next_sibling('p').get_text(' ',strip=True) for t in footer.select('h3') if t.find_next_sibling('p')}
   creator=fields.get('Artist');assert creator==name
   ident=aid+'/'+hashlib.sha256(title.encode()).hexdigest()[:16]
   rows.append(item('lopez',ident,title,creator,date,'Lopez Museum and Library',url,rc,dict(fields=fields,source_date=date,caption=article.get_text(' ',strip=True)),fields.get('Medium')))
  print('Lopez',name,'total',len(rows),flush=True)
 r.save('lopez.json.gz',dict(records=rows))
def ayala():
 src=r.Source();base='https://www.ayalamuseum.org';urls=[];pages=[]
 for group in ['Fine Arts','Amorsolo Landscapes','Contemporaries of Fernando Amorsolo']:
  url=base+'/collection/search?group='+quote(group)
  h,rc=src.get(url,as_json=False);soup=BeautifulSoup(h,'html.parser');pageurls=[url]+list(dict.fromkeys(urljoin(base,a['href']) for a in soup.select('a[href*="page="]') if a.get_text(' ',strip=True).isdigit()))
  assert len(pageurls)<=10
  for page in pageurls:
   h,rc=src.get(page,as_json=False);soup=BeautifulSoup(h,'html.parser');pages.append(rc)
   for a in soup.select('a.card[href]'):
    if '/collection/' in a['href']:urls.append(urljoin(base,a['href']))
 urls=list(dict.fromkeys(urls));assert len(urls)<=200
 rows=[];held=[]
 for n,url in enumerate(urls,1):
  h,rc=src.get(url,as_json=False);soup=BeautifulSoup(h,'html.parser');box=soup.select_one('.collection-show .object-details')
  if box is None:held.append(dict(url=url,reason='No public object metadata; access membership content only with authorization'));continue
  title=box.select_one('h2.title').get_text(' ',strip=True);by=box.select_one('h4.artist');creator=by.find('a').get_text(' ',strip=True) if by and by.find('a') else None
  spans=by.find_all('span') if by else [];date=spans[-1].get_text(' ',strip=True) if spans else None
  fields={x.get_text(' ',strip=True):x.find_next_sibling().get_text(' ',strip=True) for x in box.select('.specs h4') if x.find_next_sibling()}
  credit=fields.get('Acknowledgement') or ''
  if re.search(r'loan|courtesy|private collection',credit,re.I):held.append(dict(url=url,title=title,reason='Source specifies borrowed/private ownership',fields=fields));continue
  pic=soup.select_one('.collection-show .object-image img');image=urljoin(base,pic['src']) if pic and pic.get('src') else None
  row=item('ayala',url.rsplit('/',1)[-1],title,creator,date,'Ayala Museum',url,rc,dict(fields=fields,public_object_caption=box.get_text(' ',strip=True)),fields.get('Medium'),fields.get('Dimensions'),image);row['credit']=credit or 'Ayala Museum';rows.append(row)
  if n%20==0:print('Ayala',n,'/',len(urls),flush=True)
 r.save('ayala.json.gz',dict(records=rows,held=held,index_pages=pages))
def national_posts():
 src=r.Source();url='https://www.nationalmuseum.gov.ph/wp-json/wp/v2/posts?search=ArtStrollSunday&per_page=100&_fields=id,link,title,content,date';data,rc=src.get(url)
 defs={23474:('Genesis: Leggenda Filippina','Cenon Rivera','1963','Oil on canvas'),20933:('Portrait of an Old Woman','Araceli Limcaco-Dans','1947','Oil on canvas'),18604:('Serenata','Ramón Estella','1949','Oil on canvas'),18069:('Holy Family','Federico Estrada','1953','Narra wood sculpture'),18008:('Rural Scene (Pampanga)','Cesar Buenaventura','1949','Oil painting'),17889:('Dalagang Bukid','Fernando Amorsolo y Cueto','1928','Oil painting'),17850:('La Inmaculada Concepción',None,'Late 19th century','Painting'),17755:('Madonna with Angels','Francesco Ricardo Monti','ca. 1946','Plaster relief'),17507:('Pasig River','Miguel Galvez','1948','Oil painting'),17352:('Woman Reading Newspaper','Zosimo Flores Dimaano','1939','Oil painting'),17170:('Philippine Charity Sweepstakes','Pablo Amorsolo y Cueto','1938','Painting')}
 rows=[]
 for w in data:
  if w['id'] not in defs:continue
  title,creator,date,medium=defs[w['id']];soup=BeautifulSoup(w['content']['rendered'],'html.parser');text=soup.get_text(' ',strip=True);assert title.casefold() in text.casefold()
  if creator:assert creator.casefold().replace(' y cueto','') in text.casefold() or creator in ['Fernando Amorsolo y Cueto','Pablo Amorsolo y Cueto']
  rows.append(item('national-philippines',str(w['id']),title,creator,date,'National Museum of Fine Arts, Manila',w['link'],rc,dict(source_post_id=w['id'],content=text,post_date_not_artwork_creation=w['date']),medium))
 r.save('national.json.gz',dict(records=rows,excluded_post_ids=[w['id'] for w in data if w['id'] not in defs]))
def national_highlights():
 src=r.Source();museum='National Museum of Fine Arts, Manila';hall='https://www.nationalmuseum.gov.ph/exhibitions/fine-arts/gallery-spoliarium-hall/';h,rc=src.get(hall,as_json=False);text=BeautifulSoup(h,'html.parser').get_text(' ',strip=True)
 dateurl='https://www.nationalmuseum.gov.ph/2021/12/18/140th-birth-anniversary-of-filipino-sculptor-graciano-nepomuceno/';h,dc=src.get(dateurl,as_json=False);dt=BeautifulSoup(h,'html.parser').get_text(' ',strip=True)
 rows=[item('manila-highlights','national-spoliarium','Spoliarium','Juan Luna y Novicio','1884',museum,hall,rc,dict(holding_caption=text,date_evidence=dc,date_source_url=dateurl,date_source_text=dt,version='Original monumental painting; not the circa 1930–1940 wood relief after it.'),'Painting'),item('manila-highlights','national-bustamante','El Asesinato del Gobernador Bustamante','Felix Resurrección Hidalgo',None,museum,hall,rc,dict(holding_caption=text,version='Monumental National Museum version, distinct from the Lopez Museum study/version. Artwork date left unknown; creator lifespan is not used.'),'Painting'),item('manila-highlights','national-spoliarium-nepomuceno','Spoliarium by Luna','Graciano Nepomuceno','ca. 1930-1940',museum,dateurl,dc,dict(caption=dt,version='Wood relief after Juan Luna; a distinct artwork and creator.'),'Wood relief sculpture')]
 r.save('national-highlights.json.gz',dict(records=rows))
def ncca():
 url='https://talapamana.ncca.gov.ph/index.php/component/content/article/works-of-national-artists-visual-arts?Itemid=101&catid=13';h,rc=r.Source().get(url,as_json=False);so=BeautifulSoup(h,'html.parser');selected={};held=[]
 for idx,tr in enumerate(so.select('table tr')[1:],1):
  c=[t.get_text(' ',strip=True) for t in tr.find_all(['th','td'],recursive=False)]
  if len(c)!=11:continue
  museum=None;basis=None
  if 'Tanaw:' in c[7] and 'Bangko Sentral ng Pilipinas Painting Collection' in c[7]:museum='Bangko Sentral ng Pilipinas Art Collection';basis='NCCA inventory explicitly cites the BSP collection catalogue for this artwork.'
  elif c[10]=='Ayala Museum Collection':museum='Ayala Museum'
  elif c[10] in ['Eugenio Lopez Memorial Museum']:museum='Lopez Museum and Library'
  elif c[10] in ['National Museum Collection','National Museum','National Museum of The Philippines']:museum='National Museum of Fine Arts, Manila'
  elif 'Varg' in c[10]:museum='Jorge B. Vargas Museum and Filipiniana Research Center'
  elif c[9]=='Collection of the Ateneo Art Gallery' and c[1]=='City':
   museum='Ateneo Art Gallery';c=c.copy();c[6]=c[5];c[5]='';basis='Explicit collection ownership in remarks. Source date column is shifted; creation date unknown, not the exhibition date.'
  if not museum:continue
  if re.search(r'loan|private collection', ' '.join(c[8:]),re.I):held.append(dict(row=idx,columns=c,reason='Loan/private owner'));continue
  if not c[6] or re.search(r'\b(?:19|20)\d{2}\b',c[6]):held.append(dict(row=idx,columns=c,reason='Shifted creator/date columns'));continue
  # Lopez nude/model alternate titles cannot establish a second distinct object.
  key=(museum,c[1].casefold(),c[6].casefold());identifier=hashlib.sha256('|'.join(key).encode()).hexdigest()[:20]
  if key in selected:
   selected[key]['raw'].setdefault('duplicate_inventory_rows',[]).append(dict(row=idx,columns=c));continue
  medium=None if c[3].lower() in ['undated',''] else c[3]
  row=item('ncca',identifier,c[1],c[6],c[5] or None,museum,url,rc,dict(row_number=idx,columns=c,holding_basis=basis or 'NCCA national inventory explicitly names the owning collection.',source_provider='National Commission for Culture and the Arts',source_caveat='Historical collection evidence; no current display claim.'),medium,c[4] or None,source_type=c[2] or None)
  row['source_provider_name']='National Commission for Culture and the Arts — TALAPAMANA inventory'
  if c[1]=='Burial' and '1948' in c[9]:row.update(year_start=None,year_end=None,date_display='Date uncertain: source lists 1951; remarks cite 1948',date_decision='date_review');row['raw']['field_uncertainty']='Conflicting creation dates and measurements retained in source; no preferred date invented.';row['dimensions']=None
  selected[key]=row
 r.save('ncca.json.gz',dict(records=list(selected.values()),held=held));print('NCCA explicit collections',len(selected),flush=True)
def ust():
 rows=[];museum='University of Santo Tomas Museum'
 defs=[('https://ustmuseum.ust.edu.ph/activities-and-exhibits/2016','brown-madonna','Brown Madonna','Galo Ocampo','1938','Oil on canvas'),('https://ustmuseum.ust.edu.ph/activities-and-exhibits/2016','ivory-crucified-christ','Crucified Christ',None,'Late 16th to 17th century','Ivory sculpture'),('https://ustmuseum.ust.edu.ph/news/2021/blessed-fr-buenaventura-garcia-paredes-o-p','puruganan-paredes','Portrait of Blessed Fr. Buenaventura Garcia Paredes, O.P.','Ricarte Puruganan',None,'Painting')]
 for url,ident,title,creator,date,medium in defs:
  h,rc=r.Source().get(url,as_json=False);text=BeautifulSoup(h,'html.parser').get_text(' ',strip=True);assert title.removeprefix('Portrait of ') in text or title=='Brown Madonna'
  row=item('manila-highlights','ust-'+ident,title,creator,date,museum,url,rc,dict(caption=text,holding_basis='Museum identifies its own collection work; Singapore loan is historical, not a change of owner.'),medium)
  if ident=='ivory-crucified-christ':row['date_decision']='within_cutoff_source_period'
  rows.append(row)
 r.save('ust.json.gz',dict(records=rows))
def assemble():
 rows=[]
 for name in ['lopez','ayala','national','national-highlights','ncca','ust']:
  p=r.RUN/(name+'.json.gz')
  if p.exists():rows+=r.load(p.name)['records']
 # Keep decorative jewellery in source research; this pass selects pictorial and sculptural arts.
 scope_held=[x for x in rows if x['provider']=='ayala' and any(w in x['title'].lower() for w in ['pendant','necklace'])]
 rows=[x for x in rows if x not in scope_held]
 for x in rows:
  if x['provider']=='ayala' and x.get('medium')=='Digital art':x['raw']['field_uncertainty']='Digital-art medium label conflicts with 1969/1970 date context; medium held as unknown.';x['medium']=None
 r.save('scope-held.json.gz',scope_held)
 excluded=[x for x in rows if x['date_decision']=='after_cutoff'];selected=[x for x in rows if x['date_decision']!='after_cutoff'];r.save('source-records.json.gz',selected);r.save('excluded.json.gz',excluded);r.save('research-summary.json',dict(at=r.now(),selected=len(selected),excluded_post1970=len(excluded),by_museum=dict(collections.Counter(x['museum'] for x in selected)),scope='Manila and Metro Manila: museum-owned works; no current-display claims.'))
 print('Manila selected',len(selected),'later excluded',len(excluded),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase');a=p.parse_args();globals()[a.phase]()
