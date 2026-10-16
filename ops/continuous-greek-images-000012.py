import importlib.util,json,gzip,sys,fcntl,csv
from pathlib import Path
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('base',ROOT/'ops/continuous-image-batch-000002.py');base=importlib.util.module_from_spec(s);s.loader.exec_module(base)
i=base.i;h=base.h;connect=base.connect;target=base.target;load=base.load;save=base.save
E=ROOT/'docs/research/continuous-production-20261011/batches/000012';RUNTIME=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000012';B='athens-000'
i.OP='continuous-primary-images-20261011-b000012';i.RUN=E;i.ORIG=Path.home()/'Library/Application Support/Artline/source-images'/i.OP;i.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/i.OP
MID='052007aa-11f7-4d57-90e6-d3b62bb0bf4b';SCHEME='continuous-athens-object'
i.CFG['athens']=dict(mid=MID,scheme=SCHEME,name='National Gallery - Alexandros Soutsos Museum',rights='restricted',license='Museum reproduction; no independent copyright-holder licence asserted',policy='https://www.nationalgallery.gr/en/terms-of-use/',host='www.nationalgallery.gr')
for p in [E,RUNTIME,i.ORIG,i.BACKUP]:p.mkdir(parents=True,exist_ok=True)
import uuid
source_id=str(uuid.uuid5(uuid.NAMESPACE_URL,'continuous-greek-20261011-b000009/source/athens/National Gallery - Alexandros Soutsos Museum'))
old_uid=i.m.uid;i.m.uid=lambda k:source_id if k=='source/athens' else old_uid(k)
def capture(url,name):
 p=E/'source-captures'/(name+'.body.gz');p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():return gzip.decompress(p.read_bytes()),load(p.with_name(name+'.receipt.json'))
 i.provider_slot('www.nationalgallery.gr');r=i.session().get(url,timeout=(15,40));p.write_bytes(gzip.compress(r.content,mtime=0));rc=dict(at=h.now(),url=url,status=r.status_code,sha256=h.sha(r.content),body_path=str(p.relative_to(ROOT)));save(p.with_name(name+'.receipt.json'),rc);return r.content,rc

def prepare():
 if (i.folder(B)/'selection.json.gz').exists():return finish()
 save(E/'production-target-reconciliation.json',target())
 registry=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv');rs=list(csv.DictReader(registry.open()));assert len(rs)==111
 save(E/'source-register.json',dict(at=h.now(),registry_sha256=h.sha(registry.read_bytes()),registry_records=111,source=next(r for r in rs if r['source_id']=='national_gallery_athens'),policy='docs/ARTLINE_IMAGE_USE.md#nationwide-greek-museum-delivery--8-october-2026',retained_holds=['docs/research/continuous-production-20261011/batches/000003/source-access-holds.json','docs/research/museum-expansion-20261006/athens-followup-holds.json','docs/research/russian-icon-images-20260921/commons-search-hold.json']))
 raw,rc=capture('https://www.nationalgallery.gr/en/artwork/portrait-of-count-schulenburg/','schulenburg');assert rc['status']==200
 soup=BeautifulSoup(raw,'html.parser');head=soup.select_one('h1.artwork');dated=head.find('span').get_text(strip=True);head.find('span').extract();title=head.get_text(strip=True).rstrip(',').strip();acc=soup.select_one('.artwork-no').get_text(' ',strip=True).replace('Inv. Number','').strip();image=soup.select_one('img')['src'];assert dated=='1725' and '94653' in image
 aid='f7041588-861c-5efe-ab37-a00476831ed7'
 with connect() as db:
  a=db.execute('SELECT id::text,title,accession_number,creation_year_start,creation_year_end,date_precision,primary_media_id FROM artworks WHERE id=%s',(aid,)).fetchone();assert a['primary_media_id'] is None and (a['title'],a['accession_number'],a['creation_year_start'],a['creation_year_end'])==(title,acc,1725,1725)
  creators=db.execute('SELECT ar.id::text,ar.display_name FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=%s',(aid,)).fetchall();assert len(creators)==1 and 'Panagiotis' in creators[0]['display_name']
 row=dict(artwork_id=aid,native_id='portrait-of-count-schulenburg',title=title,creator_label=creators[0]['display_name'],source_url=rc['url'],accession_number=acc,first=1725,last=1725,precision=a['date_precision'],work_type='painting',provider='athens',image=dict(image_url=image,source=dict(title=title,accession=acc,date=dated,creator=creators[0]['display_name'],image_url=image),receipt=rc),plan_sha256=h.sha(raw),plan_path=str(E/rc['body_path'].split('000012/')[1]),rights_basis='Selected authentic Greek museum reproduction dated 1725 under Greek source extension. Actual restricted museum rights retained; user approval is not a copyright-holder licence.')
 save(i.folder(B)/'selection.json.gz',dict(provider='athens',batch=B,rows=[row]));save(i.folder(B)/'pin.json',dict(sha256=h.sha((i.folder(B)/'selection.json.gz').read_bytes())))
 save(E/'gap-reconciliation.json',dict(at=h.now(),selected=1,resume_after_artwork_id=aid,rejected_prior='Building social-preview image from batch 9 not reused',metadata_changes=0))
 finish()
def finish():
 for row in i.selected(B)['rows']:print(i.prepare_one(row,B)['state'])
 if not (E/'cloud-backup.json').exists():save(E/'cloud-backup.json',load(base.OLD/'cloud-backup.json'))
 i.audit(B);print(load(i.folder(B)/'sheets/000.json')['path'])
def deliver():
 checked=target(True)
 if not (E/'production-target-before-write.json').exists():save(E/'production-target-before-write.json',checked)
 i.upload(B);target(True);i.apply(B)
if __name__=='__main__':
 with (RUNTIME/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);globals()[sys.argv[1]]()
