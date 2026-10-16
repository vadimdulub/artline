import importlib.util,csv,json,gzip,fcntl
from pathlib import Path
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('b','ops/continuous-norway-images-000092.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h;i=b.i;E=b.E.parent
lock=(b.RUNTIME/'worker.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
paths=['AGENTS.md','docs/ARTLINE_IMAGE_USE.md','docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md','docs/LOCAL_DATA_LOCATIONS.md','docs/research/continuous-production-20261011/CHECKPOINT.json','docs/research/continuous-production-20261011/source-queue.json']
reg=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv');rows=list(csv.DictReader(reg.open()));assert len(rows)==111
b.save(E/'required-input-reconciliation.json',dict(at=h.now(),files=[dict(path=p,sha256=h.sha((b.ROOT/p).read_bytes())) for p in paths],registry_path=str(reg),registry_sha256=h.sha(reg.read_bytes()),complete_registry=rows,precedence='Current one-batch instruction; production authorized, real local DB read-only, no supervisor changes.'))
b.save(E/'source-queue-before.json',b.load(E.parents[1]/'source-queue.json'))
stop=b.ROOT/'docs/research/illustrated-300k-20261011/workers-stopped.json';b.save(E/'completed-campaign-stop-preservation.json',dict(path=str(stop.relative_to(b.ROOT)),sha256=h.sha(stop.read_bytes()),separate_campaign=i.OP,restarted=False))
p=E.parent/'000091/source-access-holds-final.json'
b.save(E/'source-access-holds.json',dict(at=h.now(),inherited_ledger=str(p.relative_to(b.ROOT)),inherited_sha256=h.sha(p.read_bytes()),inherited=b.load(p),native_qagoma_requests=0,wikiart_store_requests=0,hold_policy='No requests to held providers; Norway has no recorded access hold.'))
b.save(E/'production-target-reconciliation.json',b.target())
with b.connect() as db:
 own=[dict(x) for x in db.execute('SELECT media_id::text,evidence_json FROM media_rights_evidence WHERE adapter_version=%s',(i.OP,))];assert not own or (i.folder(b.B)/'selection.json.gz').exists()
 previous=b.load(E.parent/'000091/moma/independent-production-verification.json')
 b.save(E/'prior-verification-reference.json',dict(path=str((E.parent/'000091/moma/independent-production-verification.json').relative_to(b.ROOT)),sha256=h.sha((E.parent/'000091/moma/independent-production-verification.json').read_bytes()),keys=list(previous),previous_increments_counted=0))
 b.save(E/'own-write-reconciliation.json',dict(at=h.now(),existing_own_media=own,prior_campaign_increments_counted=0))
profiles=[('28eca636-cb1a-5973-80d0-75eedee64f41','albert-henry-fullwood'),('3f30cf6c-8397-5bed-acc4-33971aa5a422','isaac-walter-jenner'),('bd4acf6f-a743-58e1-807c-c072f2472673','jesse-jewhurst-hilder')]
results=[];data=Path.home()/'Library/Application Support/Artline/source-metadata/continuous-production-20261011/000092/wikiart';data.mkdir(parents=True,exist_ok=True)
for aid,slug in profiles:
 dest=E/'qagoma-profile-captures'/(slug+'.json')
 if dest.exists():results.append(b.load(dest));continue
 url='https://www.wikiart.org/en/'+slug+'/all-works/text-list';i.provider_slot('www.wikiart.org');r=i.session().get(url,timeout=(15,45),allow_redirects=False)
 raw=r.content;path=data/(slug+'.body.gz');path.write_bytes(gzip.compress(raw,mtime=0))
 sp=BeautifulSoup(raw,'html.parser');links=[dict(title=a.get_text(' ',strip=True),url=a.get('href')) for a in sp.select('a[href]') if '/en/'+slug+'/' in a.get('href','') and '/all-works/' not in a['href']]
 rc=dict(artwork_id=aid,url=url,status=r.status_code,retrieved_at=h.now(),sha256=h.sha(raw),body_path=str(path),links=links,retry_after=r.headers.get('Retry-After'))
 b.save(dest,rc);results.append(rc)
 print(slug,r.status_code,len(links))
 if r.status_code in [401,403,429]:b.save(E/'access-holds/www.wikiart.org.json',rc);break
b.save(E/'qagoma-discovery.json',dict(at=h.now(),rows=results,indexed_search=dict(queries=['site:wikiart.org Fullwood "Nocturne"','site:wikiart.org "Isaac Walter Jenner"','site:wikiart.org "Jesse Jewhurst Hilder" "Launch"'],outcome='Returned unrelated indexed works; no exact candidate URL discovered. Search is not proof of absence.'),image_requests=0,native_qagoma_requests=0))
print('preflight saved')
