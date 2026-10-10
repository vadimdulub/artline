"""Reparse already captured museum-supplied MDS metadata for 118 selected works."""
import collections,gzip,hashlib,importlib.util,json,re
from pathlib import Path
z=importlib.util.spec_from_file_location('p',Path(__file__).with_name('museum-expansion-britain-five-native-20261009.py'));p=importlib.util.module_from_spec(z);z.loader.exec_module(p);m=p.m;n=p.n;RUN=p.RUN;ref=p.ref
def parsed(raw,inventory):
 soup=n.BeautifulSoup(raw,'html.parser');out=[]
 for node in soup.select('details.object-overview'):
  fields={}
  for dt in node.select('dt'):
   dd=dt.find_next_sibling('dd')
   if dd is None:continue
   key=dt.get_text(' ',strip=True).rstrip(':').strip();value=dd.get_text(' ',strip=True)
   if value not in fields.setdefault(key,[]):fields[key].append(value)
  if fields.get('Collection')!=['Culture Perth & Kinross'] or inventory not in fields.get('Object number',[]):continue
  urls={a['href'] for a in node.select('a[href]') if re.fullmatch(r'https://museumdata\.uk/objects/[0-9a-f-]+',a['href'])};assert len(urls)==1
  url=next(iter(urls));text=node.get_text(' ',strip=True);licence=re.search(r'Use licence for this record:\s*(.*?)\s*Attribution for this record:',text)
  out.append(dict(fields=fields,url=url,licence=licence[1] if licence else None,attribution=url+', Culture Perth & Kinross'+(', '+licence[1] if licence else '')))
 return out
def main():
 dest=RUN/'perth-retained-native-001.json.gz';assert not dest.exists();root=m.ROOT/'docs/research/artwork-locations-20261004/mds-selected-objects-20261005c';out=[];refs={};bodies={}
 for row in m.load(RUN/'candidate-facts-001.json.gz')['rows']:
  if row['institution_id']!='8ee64e58-9eb2-5c26-82ae-fe6688fa6928':continue
  path=root/(row['existing_artwork_id']+'.json.gz');old=m.load(path);cap=old['source_receipt'];assert cap['status']==200;body=m.ROOT/cap['body_path'];raw=gzip.decompress(body.read_bytes());assert hashlib.sha256(raw).hexdigest()==cap['sha256'];objects=parsed(raw,row['facts']['inventory']);assert objects==old['objects'];refs[str(path)]=ref(path);bodies[str(body)]=ref(body)
  out.append(dict(number=row['number'],artwork_id=row['existing_artwork_id'],inventory=row['facts']['inventory'],objects=objects,source_receipt=cap,body_reference=ref(body),retained_reference=ref(path),state='exact_inventory_objects' if objects else 'no_exact_inventory_object'))
 assert len(out)==118;m.save(dest,dict(at=m.now(),rows=out,body_references=list(bodies.values()),retained_references=list(refs.values()),script_reference=ref(Path(__file__).resolve()),network_context_reference=ref(RUN/'perth-network-context-001.json.gz'),policy='Only saved selected inventory searches reparsed and hash-verified. No new requests. MDS is museum-supplied primary network evidence; branch inference requires separate specific object statements and official gallery continuity. Repeated source fields and frame dimensions retained. No images,metadata or status writes.'))
 print(json.dumps(dict(selected=len(out),objects=dict(collections.Counter(len(v['objects']) for v in out)),bodies=len(bodies))),flush=True)
if __name__=='__main__':main()
