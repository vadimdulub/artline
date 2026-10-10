"""Retain original CPK museum-supplied objects and official gallery-structure context."""
import collections,gzip,hashlib,importlib.util,io,json,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
z=importlib.util.spec_from_file_location('s',Path(__file__).with_name('museum-expansion-britain-five-source-20261009.py'));s=importlib.util.module_from_spec(z);z.loader.exec_module(s);m=s.m;RUN=s.RUN;ref=s.ref
z=importlib.util.spec_from_file_location('p',Path(__file__).with_name('museum-expansion-britain-five-native-20261009.py'));p=importlib.util.module_from_spec(z);z.loader.exec_module(p);n=p.n
def current(db):return dict(institution=db.execute('SELECT to_jsonb(i) row FROM institutions i WHERE id=%s',(s.NETWORK,)).fetchone()['row'],counts=s.BASE.counts(db,s.NETWORK))
def main():
 dest=RUN/'perth-network-context-001.json.gz';assert not dest.exists();initial=m.load(RUN/'initial-scope-001.json.gz');src={v['artwork']['id']:v for v in m.load(RUN/'source-context-001.json.gz')['rows']};hs=[v for v in initial['snapshot']['assertions'] if v['institution_id']==s.NETWORK];refs={};rows=[]
 for h in hs:
  e=json.loads(h['evidence_note']);path=m.ROOT/e['evidence_path'];raw=gzip.decompress(path.read_bytes());assert hashlib.sha256(raw).hexdigest()==e['source_response_sha256'];refs[str(path)]=ref(path);text=n.BeautifulSoup(raw,'html.parser').get_text(' ',strip=True);assert src[h['artwork_id']]['artwork']['accession_number'] in text;rows.append(dict(number=src[h['artwork_id']]['number'],assertion=h,evidence=e,body_reference=ref(path),text=text))
 with m.connect() as db:state=current(db);assert state['counts']['linked']==34;assert s.snapshot(db,initial['scoped_ids'])==initial['snapshot']
 n.SITES['perth_cdn']='https://cdn.culturepk.org.uk';context=[]
 for provider,url in [('perth','https://www.culturepk.org.uk/museum/perth-art-gallery/'),('perth','https://www.culturepk.org.uk/news/new-year-new-gallery-much-loved-perth-institution-to-have-a-refresh/'),('perth_cdn','https://cdn.culturepk.org.uk/2025/09/collections-management-framework-v12.docx')]:
  raw,cap=n.capture(provider,url)
  if url.endswith('.docx'):
   with zipfile.ZipFile(io.BytesIO(raw)) as z:tree=ET.fromstring(z.read('word/document.xml'));text='\n'.join(''.join(v.itertext()) for v in tree.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'))
  else:text=n.BeautifulSoup(raw,'html.parser').get_text(' ',strip=True)
  context.append(dict(url=url,capture=cap,text=text))
 m.save(dest,dict(at=m.now(),network_state=state,rows=rows,body_references=list(refs.values()),collection_context=context,script_reference=ref(Path(__file__).resolve()),policy='Original MDS records identify Culture Perth and Kinross,not an automatic gallery alias. Official2022 announcement separates the new history museum from the continuing art gallery and relocating Fergusson collection. Current gallery page and linked2025 management framework supply collection context,not automatic object-level branch or display proof. Review each exact inventory,creator,date,collection/version and specific referenced gallery claim before any refinement.'))
 print(json.dumps(dict(rows=len(rows),states=dict(collections.Counter(v['assertion']['review_state'] for v in rows)),bodies=len(refs),counts=state['counts'],context=len(context))),flush=True)
if __name__=='__main__':main()
