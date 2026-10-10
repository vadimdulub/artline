"""Verify comparator source captures and inspect selected official sculpture frames."""
import gzip
import hashlib
import importlib.util
import io
import json
from pathlib import Path
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from PIL import Image,ImageOps,ImageDraw

spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-chania-common-20261010.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
m,RUN=c.m,c.RUN
PROOF=Path.home()/'Library/Application Support/Artline/research-proofs/chania-delivery-20261010'

def main():
    assert not(RUN/'focused-source-review-001.json.gz').exists()
    identity=m.load(RUN/'production-identity-001.json.gz');state=identity['state'];cites=m.load(RUN/'production-identity-citations-001.json.gz')['citations'];ids=state['artwork_ids']
    existing=m.load(RUN/'focused-comparators-001.json.gz');assert existing['ids']==ids and existing['identity_reference']==c.ref(RUN/'production-identity-001.json.gz')
    m.save(RUN/'focused-source-resume-001.json',dict(at=m.now(),reason='Skip unrelated plain-text citations when parsing the eight known JSON sculpture records. Reuse successful captures; original writer and comparator snapshot preserved.',prior_snapshot=c.ref(RUN/'focused-comparators-001.json.gz'),database_writes=0))
    pins=[];frames=[];verified=[]
    for cite in cites:
        if not cite['evidence_note'].lstrip().startswith('{'):continue
        data=json.loads(cite['evidence_note'])
        if 'acropolis-more' in cite['evidence_note']:
            facts=data['source_record']['facts'];rc=facts['source_fields']['receipt']
        elif cite['entity_id'] in ['a682334d-8577-5e67-98be-da7eb6094035','b438c714-d06c-59ff-a9f4-cdc0be026eb2']:
            facts=data['facts'];rc=facts['receipt']
        elif cite['entity_id']=='ab2c601a-0f1a-5a17-95b9-5e68a511ddf5':
            facts=data['decision'];rc=facts['receipt']
        else:continue
        body=m.ROOT/rc['body_path'];raw=gzip.decompress(body.read_bytes());assert hashlib.sha256(raw).hexdigest()==rc['sha256'] and len(raw)==rc['bytes']
        pins.append(c.ref(body));verified.append(dict(artwork_id=cite['entity_id'],source_url=cite['source_url'],receipt=rc,raw_source_verified=True,facts=facts))
        if 'acropolis-more' not in cite['evidence_note']:continue
        soup=BeautifulSoup(raw,'html.parser');images=[v['src'] for v in soup.select('img[src]') if '/sites/default/files/exhibits_images/' in v['src']];assert images
        url=urljoin(rc['url'],images[0]);saved=RUN/'focused-image-receipts'/(cite['entity_id']+'.json')
        if saved.exists():
            old=m.load(saved);assert old['url']==url and old['status']==200 and hashlib.sha256(Path(old['path']).read_bytes()).hexdigest()==old['sha256'];frames.append(old);continue
        response=requests.get(url,timeout=(15,40))
        receipt=dict(at=m.now(),artwork_id=cite['entity_id'],url=url,final_url=response.url,status=response.status_code,source_capture=c.ref(body))
        if response.status_code in [403,429]:m.save(RUN/'focused-image-access-hold-001.json',receipt);break
        response.raise_for_status();im=Image.open(io.BytesIO(response.content));im.load();path=PROOF/'comparison-images'/(cite['entity_id']+'.jpg');path.parent.mkdir(parents=True,exist_ok=True);assert not path.exists();path.write_bytes(response.content)
        receipt.update(path=str(path),sha256=hashlib.sha256(response.content).hexdigest(),bytes=len(response.content),width=im.width,height=im.height)
        m.save(RUN/'focused-image-receipts'/(cite['entity_id']+'.json'),receipt);frames.append(receipt)
    prepared={v['number']:v for v in m.load(c.RESEARCH/'image-delivery-prepared-001.json')['rows']}
    selected=[dict(path=prepared[n]['prepared_path'],label='Chania '+str(n)+' '+prepared[n]['inventory_literal']) for n in [45,69,80,81]]
    selected.extend(dict(path=x['path'],label='Existing '+x['artwork_id'][:8]) for x in frames)
    sheet=Image.new('RGB',(1200,560*((len(selected)+2)//3)),'#eeeeee');draw=ImageDraw.Draw(sheet)
    for i,item in enumerate(selected):
        with Image.open(item['path']) as im:tile=ImageOps.contain(im.convert('RGB'),(380,520))
        x=(i%3)*400;y=(i//3)*560;sheet.paste(tile,(x+(400-tile.width)//2,y+30));draw.text((x+10,y+8),item['label'],fill='black')
    path=PROOF/'focused-comparison-contact.jpg';assert not path.exists();sheet.save(path,quality=92)
    m.save(RUN/'focused-source-review-001.json.gz',dict(at=m.now(),verified_sources=verified,dependencies=list({x['path']:x for x in pins}.values()),frames=frames,contact=dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest()),scope='Eight same-title ancient sculpture comparators. Captured authoritative source bodies verified offline; five healthy-source official frames requested for comparison only. No Chania or ArtIC retries after fresh403 observations.'))
    print(json.dumps(dict(source_records_verified=len(verified),frames=len(frames),contact=str(path),protected_records=len(ids))),flush=True)

if __name__=='__main__':main()
