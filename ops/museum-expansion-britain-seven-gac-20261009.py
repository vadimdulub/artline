"""Bounded Guildhall partner metadata discovery; only publicly supplied cards and links."""
import importlib.util,json,re
from pathlib import Path
z=importlib.util.spec_from_file_location('p',Path(__file__).with_name('museum-expansion-britain-seven-native-20261009.py'));p=importlib.util.module_from_spec(z);z.loader.exec_module(p);m=p.m;RUN=p.RUN;BASE='https://artsandculture.google.com';p.n.SITES['guildhall_gac']=BASE
def cards(raw):
 soup=p.n.BeautifulSoup(raw,'html.parser');rows={}
 def walk(v):
  if not isinstance(v,list):return
  if v and v[0]=='gac.oi' and isinstance(v[4],str) and v[4].startswith('/asset/'):
   sid=v[4].rstrip('/').rsplit('/',1)[-1];r=dict(source_id=sid,title=v[1],creator=v[2],url=BASE+v[4]);assert sid not in rows or rows[sid]==r;rows[sid]=r
  else:
   for child in v:walk(child)
 for script in soup.select('script'):
  text=script.get_text()
  if not text.startswith('window.INIT_data'):continue
  for match in re.finditer(r"window\.INIT_data\['[^']+'\]\s*=\s*",text):walk(json.JSONDecoder().raw_decode(text[match.end():])[0])
 return list(rows.values())
def main():
 dest=RUN/'guildhall-gac-probe-001.json';assert not dest.exists();url=BASE+'/partner/guildhall-art-gallery';discovery=m.load(RUN/'native-probes-001.json');page=next(v for v in discovery['rows'] if v['provider']=='guildhall');assert any(v['href']==url for v in page['parsed']['links']);raw,cap=p.n.capture('guildhall_gac',url);data=p.parsed(raw);rs=cards(raw);assert len(rs)<=104;m.save(dest,dict(at=m.now(),url=url,capture=cap,parsed=data,rows=rs,discovery_reference=p.ref(RUN/'native-probes-001.json'),script_reference=p.ref(Path(__file__).resolve()),policy='Museum-linked publisher partner page. Short metadata leads only; select exact objects before details. No images or denied-platform requests.'))
 print(json.dumps(dict(rows=rs,links=[v for v in data['links'] if any(s in v['href'] for s in ['/asset/','/explore/collections/'])])),flush=True)
if __name__=='__main__':main()
