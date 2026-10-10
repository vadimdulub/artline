"""Verify selected native page bytes, literal detail text, institution and inventory."""
import gzip,hashlib,importlib.util,json,re
from pathlib import Path
from urllib.parse import urlparse
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('f',Path(__file__).with_name('museum-expansion-france-fifteenth-facts-20261008.py'));f=importlib.util.module_from_spec(s);s.loader.exec_module(f)
m=f.m;RUN=f.RUN
def main():
 dest=RUN/'paris-object-context-checked-001.json.gz';assert not dest.exists()
 candidates=RUN/'native-candidates-001.json.gz';rows=m.load(candidates)['rows'][360:510]
 complete=RUN/'paris-object-context-361-510-complete.json';done=m.load(complete)
 assert done['candidate_reference']==f.ref(candidates) and len(done['receipts'])==150;f.checked(done['capture_script'])
 deps={candidates,complete,Path(__file__).resolve(),f.checked(done['capture_script'])};contexts=[]
 for r in rows:
  stem=RUN/'paris-object-context-001'/f"{r['number']:03d}-{r['source_id']}";rp=Path(str(stem)+'.receipt.json');hp=Path(str(stem)+'.html.gz');tp=Path(str(stem)+'.txt')
  receipt=m.load(rp);assert f.ref(rp) in done['receipts'] and receipt['status']==200 and receipt['number']==r['number'] and receipt['source_id']==r['source_id']
  assert receipt['url']==r['facts']['source_fields']['Lien_site_associe'].strip() and urlparse(receipt['final_url']).hostname=='www.parismuseescollections.paris.fr'
  raw=gzip.decompress(hp.read_bytes());assert len(raw)==receipt['bytes'] and hashlib.sha256(raw).hexdigest()==receipt['sha256']
  soup=BeautifulSoup(raw,'html.parser')
  for tag in soup(['script','style','noscript']):tag.decompose()
  text=soup.get_text('\n',strip=True);assert text==tp.read_text() and text.count('\nInformations détaillées\n')==2
  detail=text.rsplit('\nInformations détaillées\n',1)[1].split('\nIndexation\n')[0]
  assert 'Institution\n:\nMusée Cognacq-Jay, le goût du XVIIIe\n' in detail
  match=re.search(r'(?:^|\n)Numéro d’inventaire\n:\n([^\n]+)',detail);assert match
  native_inventory=match[1];equal=m.norm(native_inventory)==m.norm(r['facts']['inventory'])
  contexts.append(dict(number=r['number'],source_id=r['source_id'],source_url=receipt['url'],final_url=receipt['final_url'],literal_detail_text=detail,native_inventory=native_inventory,national_inventory=r['facts']['inventory'],inventory_equal=equal,receipt_reference=f.ref(rp),body_reference=f.ref(hp),text_reference=f.ref(tp)))
  deps.update([rp,hp,tp])
 m.save(dest,dict(at=m.now(),rows=contexts,dependencies=[f.ref(p) for p in sorted(deps)],policy='150 selected native object pages with byte hashes, regenerated literal text and Cognacq-Jay institutional identity checked. Inventory differences, if any, remain for individual reconciliation. No object approved by this mechanical check; no images fetched or display claims.'))
 print(json.dumps(dict(pages=len(contexts),inventory_differences=[dict(number=r['number'],national=r['national_inventory'],native=r['native_inventory']) for r in contexts if not r['inventory_equal']],database_writes=0)),flush=True)
if __name__=='__main__':main()
