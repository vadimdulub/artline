"""Selected primary pages and exact previously captured comparator objects."""
import gzip,hashlib,importlib.util,json
from pathlib import Path
import requests
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('i',Path(__file__).with_name('museum-expansion-france-sixteenth-identity-20261008.py'));i=importlib.util.module_from_spec(s);s.loader.exec_module(i);m=i.m;RUN=i.RUN;ref=i.ref
SOURCES=[
 ('louvre-oa428',586,'https://collections.louvre.fr/ark:/53355/cl010097193'),
 ('louvre-mi1067',[398,490],'https://collections.louvre.fr/ark:/53355/cl010055588'),
 ('louvre-inv20410',[398,490],'https://collections.louvre.fr/ark:/53355/cl010062565'),
 ('paris-j42',[398,490],'https://www.parismuseescollections.paris.fr/node/185333'),
 ('wikiart-pompadour',439,'https://www.wikiart.org/en/maurice-quentin-de-la-tour/portrait-of-madame-de-pompadour'),
 ('met-watteau-fan',510,'https://www.metmuseum.org/art/collection/search/339838'),
]
OLD=[
 (470,'a4656ff8-f4cb-4b8c-811a-bb9eae6268b0','docs/research/artwork-locations-20261004/vam-20261005b/5b75b17e720a1e435e30e0e1849a046f529f827ad76a85a648289dba42ed75ea.body.gz','d88fcdaff107a70fbde97753decf483c5f43a2a78aad4cb1d9c57d14524c6f64','https://api.vam.ac.uk/v2/museumobject/O84952'),
 (488,'98f9ff47-e0ea-4047-9b99-df512acd501c','docs/research/artwork-locations-20261004/primary/a98b6e5752d411697b88dd460e95263b2c2f73aaac4816da3f0e781a8b2d49db.body.gz','409ee2863cec6e6cfd38cc34d41776c7ad600caa00aba0c68f4a89aa34d2cb5c','https://kokoelma.kansallisgalleria.fi/api/v1/objects'),
]
def main():
    root=RUN/'targeted-context-001';assert not root.exists();root.mkdir();out=[];old=[]
    for number,aid,path,digest,url in OLD:
        p=m.ROOT/path;raw=gzip.decompress(p.read_bytes());assert hashlib.sha256(raw).hexdigest()==digest;data=json.loads(raw)
        if number==470:record=data['record'];assert record['systemNumber']=='O84952' and record['accessionNumber']=='DYCE.76'
        else:
            found=[x for x in data if x.get('objectId')==390567];assert len(found)==1;record=found[0];assert record['inventoryNumber']=='A I 548'
        old.append(dict(number=number,existing_artwork_id=aid,body_reference=ref(p),uncompressed_sha256=digest,source_url=url,literal_primary_record=record,policy='Exact object extracted from the original response; citation response hash checked. All source qualifications and measurement roles retained.'))
    m.save(RUN/'existing-targeted-context-001.json.gz',dict(at=m.now(),rows=old,citation_reference=ref(i.OLD/'identity-citations-002.json.gz'),extractor_reference=ref(Path(__file__).resolve()),database_writes=0))
    for name,number,url in SOURCES:
        try:
            with requests.get(url,headers={'User-Agent':'ArtlineMuseumResearch/1.0 (selected object identity evidence)'},timeout=(15,45),stream=True) as response:
                raw=b''
                for chunk in response.iter_content(65536):
                    raw+=chunk
                    if len(raw)>4_000_000:raise ValueError('Bounded response exceeded')
                receipt=dict(url=url,final_url=response.url,status=response.status_code,retrieved_at=m.now(),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest());body=root/(name+'.html.gz');rp=root/(name+'.receipt.json');body.write_bytes(gzip.compress(raw,mtime=0));m.save(rp,receipt);response.raise_for_status()
            soup=BeautifulSoup(raw,'html.parser')
            for tag in soup(['script','style','noscript']):tag.decompose()
            text=soup.get_text('\n',strip=True);tp=root/(name+'.txt');tp.write_text(text)
            out.append(dict(number=number,name=name,body_reference=ref(body),receipt_reference=ref(rp),text_reference=ref(tp),literal_text=text,**receipt));print(json.dumps(dict(name=name,status=receipt['status'])),flush=True)
        except Exception as error:
            ep=root/(name+'.error.json');m.save(ep,dict(at=m.now(),url=url,error=repr(error),policy='No retry or access bypass. Independent selected requests may continue.'));out.append(dict(number=number,name=name,error_reference=ref(ep)));print(json.dumps(dict(name=name,error=repr(error))),flush=True)
    m.save(RUN/'targeted-context-001.json.gz',dict(at=m.now(),rows=out,capture_reference=ref(Path(__file__).resolve()),database_writes=0,images=0))
if __name__=='__main__':main()
