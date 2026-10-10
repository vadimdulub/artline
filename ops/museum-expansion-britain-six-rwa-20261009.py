"""Bounded primary-source searches for the 79 selected existing RWA creators."""
import collections,importlib.util,json,re
from pathlib import Path
from urllib.parse import urlencode,urljoin,urlsplit,urlunsplit
z=importlib.util.spec_from_file_location('p',Path(__file__).with_name('museum-expansion-britain-six-native-20261009.py'));p=importlib.util.module_from_spec(z);z.loader.exec_module(p);m=p.m;n=p.n;RUN=p.RUN;ref=p.ref
def parsed(raw):
 soup=n.BeautifulSoup(raw,'html.parser')
 for el in soup.select('script,style,header,footer,nav'):el.decompose()
 return dict(headings=[v.get_text(' ',strip=True) for v in soup.select('h1,h2,h3')],text=soup.get_text(' ',strip=True),image_labels=[{k:v.get(k) for k in ['alt','title']} for v in soup.select('img') if v.get('alt') or v.get('title')])
def main():
 dest=RUN/'rwa-native-001.json.gz';assert not dest.exists();rs=[r for r in m.load(RUN/'candidate-facts-001.json.gz')['rows'] if r['facts']['museum_qid']=='Q7375007'];groups=collections.defaultdict(list)
 for r in rs:groups[r['facts']['creator_label']].append(r['number'])
 assert len(rs)==147 and len(groups)==79;selection=RUN/'rwa-native-selection-001.json';assert not selection.exists();m.save(selection,dict(at=m.now(),creators=dict(groups),source_reference=ref(RUN/'candidate-facts-001.json.gz'),policy='Public search for existing selected creator labels only. Follow at most3 observed artist-biography links matching that creator surname. First bounded result page only. No ArtUK requests,images,checkout or authentication. Biography does not itself prove any artwork holding/date.'))
 out=[];failures=0;stopped=False
 for k,(name,numbers) in enumerate(sorted(groups.items()),1):
  row=dict(creator=name,numbers=numbers,objects=[]);destrow=RUN/'rwa-selected-001'/('%03d.json'%k);assert not destrow.exists();url=n.SITES['rwa']+'/search?'+urlencode({'q':name})
  try:
   raw,cap=n.capture('rwa',url);data=p.parsed(raw);links={urlunsplit(urlsplit(urljoin(url,a['href']))._replace(query='',fragment='')) for a in data['links'] if '/blogs/artists/' in a['href'] and m.norm(name).split()[-1] in m.norm(a['text']).split()};row.update(search_capture=cap,search_text=data['text'],observed_links=sorted(links));assert len(links)<=3,'More than3 matching biography links; inspect first'
   for link in sorted(links):
    raw,cap=n.capture('rwa',link);row['objects'].append(dict(url=link,capture=cap,parsed=parsed(raw)))
   row['state']='biographies_captured' if links else 'no_matching_biography';failures=0
  except Exception as err:
   failures+=1;row.update(state='capture_error',error=type(err).__name__+': '+str(err));stopped=failures>=3 or any(v in str(err) for v in ['403','429','Forbidden'])
  m.save(destrow,row);out.append(dict(creator=name,state=row['state'],reference=ref(destrow)));print(json.dumps(dict(creator=name,state=row['state'],completed=len(out),selected=len(groups))),flush=True)
  if stopped:break
 m.save(dest,dict(at=m.now(),rows=out,selection_reference=ref(selection),script_reference=ref(Path(__file__).resolve()),requests_stopped=stopped,consecutive_failures=failures,unprocessed_creators=[v for v in groups if v not in {r['creator'] for r in out}],policy='Primary biography and image-caption text retained. Only a work-specific collection caption can corroborate a selected object; artist membership or general collection statements do not. Do not infer artwork creation from life/election/acquisition dates.'))
if __name__=='__main__':main()
