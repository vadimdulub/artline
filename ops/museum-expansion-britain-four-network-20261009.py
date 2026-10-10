"""Preserve NMNI network evidence and capture public collection-structure context."""
import gzip,hashlib,importlib.util,json,subprocess
from pathlib import Path
z=importlib.util.spec_from_file_location('p',Path(__file__).with_name('museum-expansion-britain-four-native-20261009.py'));p=importlib.util.module_from_spec(z);z.loader.exec_module(p);s=p.s;m=p.m;RUN=p.RUN;ref=p.ref;n=p.n
IID=s.NETWORK
def current(db):return dict(institution=db.execute('SELECT to_jsonb(i) row FROM institutions i WHERE id=%s',(IID,)).fetchone()['row'],counts=s.BASE.counts(db,IID))
def main():
 dest=RUN/'ulster-network-context-001.json.gz';assert not dest.exists();initial=m.load(RUN/'initial-scope-001.json.gz');arts=[v for v in initial['snapshot']['artworks'] if v['current_institution_id']==IID];assert len(arts)==53;ids={v['id'] for v in arts};hs=[v for v in initial['snapshot']['assertions'] if v['artwork_id'] in ids and v['institution_id']==IID and v['review_state']=='accepted' and not v['superseded_by']];assert len(hs)==53;refs={};rows=[]
 for h in hs:
  e=json.loads(h['evidence_note']);path=m.ROOT/e['evidence_path'];raw=gzip.decompress(path.read_bytes());assert hashlib.sha256(raw).hexdigest()==e['source_response_sha256'];refs[str(path)]=ref(path);rows.append(dict(artwork_id=h['artwork_id'],assertion_id=h['id'],source_url=h['source_url'],evidence=e,body_reference=refs[str(path)]))
 with m.connect() as db:state=current(db);assert state['counts']['linked']==53;assert s.snapshot(db,initial['scoped_ids'])==initial['snapshot']
 n.SITES.update(nmni='https://www.nationalmuseumsni.org',nmni_cms='https://cms.nationalmuseumsni.org');context=[]
 for provider,url in [('nmni','https://www.nationalmuseumsni.org/art-curators'),('nmni_cms','https://cms.nationalmuseumsni.org/sites/default/files/2025-01/National%20Museums%20NI%20Collections%20Development%20Policy_updated%202025.pdf')]:
  raw,cap=n.capture(provider,url)
  text=subprocess.run(['pdftotext','-','-'],input=raw,capture_output=True,check=True).stdout.decode() if raw.startswith(b'%PDF') else n.BeautifulSoup(raw,'html.parser').get_text(' ',strip=True)
  context.append(dict(url=url,capture=cap,text=text))
 normalized=' '.join(context[1]['text'].split());assert '2.2 Ulster Museum' in normalized and 'Fine Art collection' in normalized
 m.save(dest,dict(at=m.now(),network_state=state,rows=rows,body_references=list(refs.values()),collection_context=context,script_reference=ref(Path(__file__).resolve()),policy='53 pre-existing accepted NMNI holdings are distinct from unlinked works. Collection policy places Fine Art in the Ulster Museum section; native object department and referenced exact branch claims still require individual review. General policy alone is not object-level proof. Preserve old network assertions and their evidence in audit history if a reviewed branch refinement supersedes them. No institution merge, ownership or display claim.'))
 print(json.dumps(dict(network_records=len(arts),counts=state['counts'],native_bodies=len(refs),collection_context=len(context))),flush=True)
if __name__=='__main__':main()
