"""Selected Acropolis sculptures with complete literal page fields and no images."""
import importlib.util,json,re
from pathlib import Path
from urllib.parse import urljoin,urlsplit
from bs4 import BeautifulSoup
z=importlib.util.spec_from_file_location('s',Path(__file__).with_name('museum-expansion-acropolis-source-20261009.py'));s=importlib.util.module_from_spec(z);z.loader.exec_module(s);m=s.m;RUN=s.RUN;SITE='https://www.theacropolismuseum.gr'
def main():
 discovery=m.load(RUN/'native-discovery-001.json.gz');base=m.load(RUN/'production-initial-scope-001.json.gz');known={v['source_url'].rstrip('/'):v['entity_id']for v in base['snapshot']['citations']if(v.get('source_url')or'').startswith(SITE+'/')};first=[];heads=[];deferred=[];existing=[]
 for n,r in enumerate(discovery['rows'],1):
  t=r['index_text'].split(' Category ')[0][6:];v=dict(r,number=n)
  if r['url'].rstrip('/')in known:existing.append(dict(v,existing_artwork_id=known[r['url'].rstrip('/')],state='already_catalogued_exact_native_url'));continue
  if re.match(r'(?:Part |Arm |Animal snout|Athena’s arm|Dionysos.*hand|Eye$|Feet |Foot |Fragment |Garment |Hand |Hoof|Hooves|Kore’s feet|Right hand)',t):deferred.append(v)
  elif'head'in t.lower():heads.append(v)
  else:first.append(v)
 selected=first+heads[:max(0,120-len(first))];selected.sort(key=lambda v:v['number']);chosen={v['number']for v in selected};deferred+= [v for v in heads if v['number']not in chosen];assert len(selected)==120
 selection=dict(selected=selected,already=existing,deferred=deferred,source_reference=s.s.ref(RUN/'native-discovery-001.json.gz'),policy='Prioritize independent reliefs,statues,busts and selected inventoried heads.120detailsmaximum. Existing exact native URLs skipped. Small body fragments deferred for parent reconciliation. No image download.')
 dest=RUN/'native-selection-001.json';m.save(dest,selection);out=[]
 for item in selected:
  key='native-object-'+str(item['number'])+'-001';raw,rc=s.src.capture(key,item['url']);h=BeautifulSoup(raw,'html.parser');fields={}
  for label in h.select('.popular_exhibitions_inside_container_paddings .col-lg-5'):
   value=label.find_next_sibling('div');fields[label.get_text(' ',strip=True)]=value.get_text(' ',strip=True)
  title=h.select_one('h2.title').get_text(' ',strip=True);assert fields.get('Inventory number')and fields.get('Category')=='Sculpture';canonical=h.select_one('link[rel=canonical]');links=[dict(text=a.get_text(' ',strip=True),url=urljoin(SITE,a['href']))for a in (h.find('main')or h).select('a[href]')if a['href'].startswith('/en/')]
  text=(h.find('main')or h).get_text(' ',strip=True);text=text.split('Register to the Acropolis Museum Newsletter')[0]
  v=dict(number=item['number'],title=title,source_url=item['url'],canonical_url=canonical['href']if canonical else rc['final_url'],fields=fields,text=text,links=links,receipt=rc,index_text=item['index_text']);out.append(v);print(json.dumps(dict(number=v['number'],progress=len(out),title=title,inventory=fields['Inventory number'],date=fields.get('Date')),ensure_ascii=False),flush=True)
 m.save(RUN/'native-details-001.json.gz',dict(at=m.now(),rows=out,selection_reference=s.s.ref(dest),script_reference=s.s.ref(Path(__file__).resolve()),policy='120selected official object pages; literal dates,qualifications,materials,inventory and narrative retained. Holdings not current display. No images downloaded.'))
if __name__=='__main__':main()
