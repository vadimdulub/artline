"""Further selected Acropolis sculptures and deferred heads; no image downloads."""
import importlib.util,json
from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup
z=importlib.util.spec_from_file_location('s',Path(__file__).with_name('museum-expansion-acropolis-more-source-20261009.py'));s=importlib.util.module_from_spec(z);z.loader.exec_module(s);m=s.m;RUN=s.RUN;SITE='https://www.theacropolismuseum.gr';OLD=m.RUN/'native/acropolis-20261009'
def main():
 prior=m.load(OLD/'native-selection-001.json');nextrows=m.load(OLD/'next-source-discovery-001.json.gz')['rows'];base=m.load(RUN/'production-initial-scope-001.json.gz');known={v['source_url'].rstrip('/'):v['entity_id']for v in base['snapshot']['citations']if(v.get('source_url')or'').startswith(SITE+'/')}
 selected=[v for v in prior['deferred']if 'head'in v['index_text'].split(' Category ')[0].lower()]+[dict(v,number=n)for n,v in enumerate(nextrows,180)];assert len(selected)==84;already=[dict(v,existing_artwork_id=known[v['url'].rstrip('/')])for v in selected if v['url'].rstrip('/')in known];selected=[v for v in selected if v['url'].rstrip('/')not in known]
 m.save(RUN/'native-selection-001.json',dict(at=m.now(),selected=selected,already=already,deferred=[v for v in prior['deferred']if 'head'not in v['index_text'].split(' Category ')[0].lower()],source_references=[s.s.ref(OLD/'native-selection-001.json'),s.s.ref(OLD/'next-source-discovery-001.json.gz')],policy='76follow-up index leads and8deferred heads; physical object,cast,parent and creator review required. No images.'))
 out=[];narratives=[]
 for item in selected:
  n=item['number'];raw,rc=s.src.capture('native-object-'+str(n)+'-001',item['url']);h=BeautifulSoup(raw,'html.parser');fields={}
  for label in h.select('.popular_exhibitions_inside_container_paddings .col-lg-5'):
   value=label.find_next_sibling('div');fields[label.get_text(' ',strip=True)]=value.get_text(' ',strip=True)
  title=h.select_one('h2.title').get_text(' ',strip=True);assert fields.get('Inventory number')and fields.get('Category')=='Sculpture';canonical=h.select_one('link[rel=canonical]');main=h.find('main')or h;links=[dict(text=a.get_text(' ',strip=True),url=urljoin(SITE,a['href']))for a in main.select('a[href]')if a['href'].startswith('/en/')]
  text=main.get_text(' ',strip=True).split('Register to the Acropolis Museum Newsletter')[0];row=dict(number=n,title=title,source_url=item['url'],canonical_url=canonical['href']if canonical else rc['final_url'],fields=fields,text=text,links=links,receipt=rc,index_text=item['index_text']);out.append(row)
  desc=h.select_one('#menu1');alternate=h.select_one('link[hreflang=el]');nr=dict(number=n,source_url=item['url'],inventory=fields['Inventory number'],description=desc.get_text(' ',strip=True)if desc else'',greek_url=urljoin(SITE,alternate['href'])if alternate else None)
  if 'Translation from Greek text under progress'in nr['description']:
   assert nr['greek_url'];gr,grc=s.src.capture('native-greek-'+str(n)+'-001',nr['greek_url']);gh=BeautifulSoup(gr,'html.parser');gd=gh.select_one('#menu1');assert gd;nr.update(greek_description=gd.get_text(' ',strip=True),greek_receipt=grc)
  narratives.append(nr);print(json.dumps(dict(number=n,progress=len(out),title=title,inventory=fields['Inventory number'],date=fields.get('Date')),ensure_ascii=False),flush=True)
 m.save(RUN/'native-details-001.json.gz',dict(at=m.now(),rows=out,selection_reference=s.s.ref(RUN/'native-selection-001.json'),script_reference=s.s.ref(Path(__file__).resolve()),policy='Selected official physical-object fields; literal dates and attributions retained. Holding not display.'))
 m.save(RUN/'native-narratives-001.json.gz',dict(at=m.now(),rows=narratives,source_reference=s.s.ref(RUN/'native-details-001.json.gz'),script_reference=s.s.ref(Path(__file__).resolve())))
 print(json.dumps(dict(details=len(out),known=len(already),greek=sum('greek_description'in v for v in narratives))),flush=True)
if __name__=='__main__':main()
