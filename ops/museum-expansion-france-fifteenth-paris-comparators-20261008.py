"""Selected existing portrait comparators; verified native descriptions, no images."""
import gzip,hashlib,importlib.util,json,re,time
from pathlib import Path
import requests
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('f',Path(__file__).with_name('museum-expansion-france-fifteenth-facts-20261008.py'));f=importlib.util.module_from_spec(s);s.loader.exec_module(f)
m=f.m;RUN=f.RUN
def main():
 root=RUN/'paris-comparators-001';assert not root.exists();root.mkdir();dest=RUN/'paris-comparators-checked-001.json.gz';assert not dest.exists()
 primary=RUN/'physical-comparison-context-002.json.gz';wanted={'J 791','J 749','J 754','J 726','1996.2','J 755','J 759','J 82','J 11'}
 selected=[r for r in m.load(primary)['rows'] if r['literal_primary_record'].get('Code_Museofile')=='M1107' and r['literal_primary_record'].get('Numero_inventaire') in wanted];assert len(selected)==9;out=[]
 for row in selected:
  p=row['literal_primary_record'];url=p['Lien_site_associe'];name=p['Reference'];rp=root/(name+'.receipt.json');hp=root/(name+'.html.gz');tp=root/(name+'.txt')
  try:
   time.sleep(1)
   with requests.get(url,headers={'User-Agent':'ArtlineMuseumResearch/1.0 (selected existing portrait comparison)'},timeout=(15,45),stream=True) as response:
    raw=b''
    for chunk in response.iter_content(65536):
     raw+=chunk
     if len(raw)>4_000_000:raise ValueError('Bounded response exceeded')
    receipt=dict(url=url,final_url=response.url,status=response.status_code,retrieved_at=m.now(),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest());hp.write_bytes(gzip.compress(raw,mtime=0));m.save(rp,receipt);response.raise_for_status()
   soup=BeautifulSoup(raw,'html.parser')
   for tag in soup(['script','style','noscript']):tag.decompose()
   text=soup.get_text('\n',strip=True);tp.write_text(text);assert text.count('\nInformations détaillées\n')==2
   detail=text.rsplit('\nInformations détaillées\n',1)[1].split('\nIndexation\n')[0]
   assert 'Institution\n:\nMusée Cognacq-Jay, le goût du XVIIIe\n' in detail
   inv=re.search(r'(?:^|\n)Numéro d’inventaire\n:\n([^\n]+)',detail)[1];assert m.norm(inv)==m.norm(p['Numero_inventaire'])
   out.append(dict(existing_artwork_id=row['existing_artwork_id'],source_record_id=name,native_inventory=inv,literal_detail_text=detail,body_reference=f.ref(hp),receipt_reference=f.ref(rp),text_reference=f.ref(tp),source_url=url,final_url=receipt['final_url']));print(json.dumps(dict(inventory=inv,status=200)),flush=True)
  except Exception as error:
   m.save(root/(name+'.error.json'),dict(at=m.now(),url=url,error=repr(error),policy='Stop first error; no retry or bypass.'));raise
 m.save(dest,dict(at=m.now(),rows=out,primary_reference=f.ref(primary),capture_reference=f.ref(Path(__file__).resolve()),database_writes=0,images=0,policy='Exact native institution and inventory verified. Existing catalogue metadata and artist assignments unchanged; native differences are comparison evidence only.'))
if __name__=='__main__':main()
