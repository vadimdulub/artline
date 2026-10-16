#!/usr/bin/env python3
"""Bounded MoMA month-specific drawings; existing supervisor and local catalogue untouched."""
import collections,csv,fcntl,gzip,importlib.util,inspect,json,re,subprocess,sys
from pathlib import Path
import requests
ROOT=Path(__file__).resolve().parents[1]
def mod(n,f):
 s=importlib.util.spec_from_file_location(n,ROOT/'ops'/f);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
h=mod('h','india-300-delivery-20261011.py');base=mod('base','continuous-image-batch-000002.py');mo=mod('mo','million-moma-20261011.py')
E=ROOT/'docs/research/continuous-production-20261011/batches/000039';R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000039';D=Path.home()/'Library/Application Support/Artline/source-metadata/continuous-production-20261011/000039'
PHASE='moma-drawings';FIELD='continuous_moma_object_evidence_20261011_b000039';h.OP='continuous-moma-20261011-b000039';h.RUN=E;h.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/h.OP
h.SCHEMES={'moma':['moma-object','museum-native-moma-object']};h.museums=lambda:{'Museum of Modern Art':('wikimedia-museum-q188740','https://www.moma.org/')}
code=inspect.getsource(h.apply).replace("assert sum(not r['before'] for r in rows)>=300,'Minimum target must count new physical objects, not enrichments'","assert 1 <= len(rows) <= 50 and all(not r['before'] for r in rows), 'Bounded new objects only'").replace('india_minimum_300_museum_coverage_20261011',FIELD)
needle="  db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE'"
replacement="  inventory=db.execute('SELECT id::text,accession_number FROM artworks WHERE current_institution_id=%s AND accession_number=ANY(%s)',(rows[0]['institution_id'],[r['accession_number'] for r in rows])).fetchall();assert not inventory,'Concurrent accession insert; replan'\n  db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE'"
assert needle in code;code=code.replace(needle,replacement)
oldkeys="WHERE entity_type='artwork' AND scheme=ANY(%s)\",(list({r['scheme'] for r in rows}),)"
newkeys="WHERE entity_type='artwork' AND scheme=ANY(%s) AND external_id=ANY(%s)\",(list({r['scheme'] for r in rows}),[r['source_id'] for r in rows])"
assert oldkeys in code;code=code.replace(oldkeys,newkeys)
exec(compile(code,'established-helper-bounded-moma','exec'),h.__dict__)
code=inspect.getsource(h.plan).replace('User: go ahead with India, add at least 300 artworks; broad museum coverage first. Minimum counts only new, distinct artwork records.','User authorized bounded source-backed production inserts; batch 39 MoMA month-specific drawings; new artworks stay review.')
old="'SELECT to_jsonb(a) v FROM artworks a WHERE current_institution_id=ANY(%s::uuid[])',([i['id'] for i in instmap.values()],)"
new="'SELECT to_jsonb(a) v FROM artworks a WHERE current_institution_id=ANY(%s::uuid[]) AND (accession_number=ANY(%s) OR normalized_title=ANY(%s))',([i['id'] for i in instmap.values()],[r['accession_number'] for r in rows],[norm(r['title']) for r in rows])"
assert old in code;code=code.replace(old,new);exec(compile(code,'established-bounded-moma-planner','exec'),h.__dict__)
def save(name,v):
 p=E/name
 if p.exists():return h.load(p)
 h.save(p,v);return v

def stage():
 if (E/PHASE/'plan-pin.json').exists():h.pinned(PHASE);base.target();print('Pinned plan preserved');return
 base.target();D.mkdir(parents=True,exist_ok=True)
 registry=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv');reg=list(csv.DictReader(registry.open()));assert len(reg)==111
 save('source-register.json',dict(at=h.now(),original_registry_path=str(registry),registry_sha256=h.sha(registry.read_bytes()),registry_records=111,routes=[r for r in reg if r['source_id'] in ['moma','national_gallery_prague','national_gallery_athens']],supplementary_json_not_substituted=True,policy='MoMA released metadata CC0; images explicitly excluded; source image URLs retained only as evidence.',access_status='Pinned official repository metadata already captured today; source webpage access hold preserved; no MoMA artwork page or image requests.'))
 source_receipts={}
 for name in ['Artworks.csv','Artists-full.csv','README.md']:
  rc=h.load(mo.m.RUN/'sources/moma'/(name+'.receipt.json'));path=Path(rc['path']);assert h.sha(path.read_bytes())==rc['sha256'];source_receipts[name]=rc
 save('source-dataset-verification.json',dict(at=h.now(),receipts=source_receipts,repository_pin=h.load(mo.RUN/'repository-pin.json'),all_hashes_verified=True))
 # Independent public official metadata endpoint only; do not retry held MoMA website.
 url=source_receipts['README.md']['url'];p=D/'README.md';rp=E/'repository-policy-live-verification.json'
 if not rp.exists():
  rr=requests.get(url,timeout=(10,40));p.write_bytes(rr.content);h.save(rp,dict(at=h.now(),url=url,status=rr.status_code,sha256=h.sha(rr.content),path=str(p)));assert rr.status_code==200
 rc=h.load(rp);assert rc['status']==200 and h.sha(p.read_bytes())==rc['sha256']==source_receipts['README.md']['sha256']
 save('source-access-holds.json',dict(at=h.now(),inherited_ledger='docs/research/continuous-production-20261011/batches/000038/source-access-holds.json',inherited_queue='source-queue-before.json',moma_website_hold='docs/research/creators-deep-continuation-20261011/README.md',moma_images='Registry: never; official repository explicitly excludes image rights',request_rule='No held provider retried; pinned official CSV reuse; only public GitHub README requested.',incidental_research='Prague icon discovery returned collection on long-term loan from Czech Academy; no object identity or ownership established. National Gallery Athens Tzafouris search gave no exact official object. Both remain discovery gaps, no import or image selection.'))
 leads=h.load(E/'moma-date-specific-leads.json')['records'];counts=collections.Counter();candidates=[];pending=[]
 for r in leads:
  if r['Classification']!='Drawing' or counts[r['Artist']]>=2:pending.append(dict(native_id=r['ObjectID'],reason='Next metadata batch; drawings prioritized with maximum two per creator'));continue
  counts[r['Artist']]+=1;candidates.append(r)
 with (mo.m.DATA/'moma/Artists-full.csv').open(encoding='utf-8-sig') as f:authorities={r['ConstituentID']:r for r in csv.DictReader(f)}
 selected=[];checks=[]
 with h.connect() as db:
  prev=h.load(E.parent/'000038/batch-verification-receipt.json');ids=prev['production_ids']
  prior=[dict(x) for x in db.execute('SELECT a.id::text,a.primary_media_id::text,m.adapter_version,m.evidence_json FROM artworks a JOIN media_rights_evidence m ON m.media_id=a.primary_media_id WHERE a.id=ANY(%s::uuid[])',(ids,))];assert len(prior)==20
  for x in prior:
   ev=x['evidence_json'];ev=json.loads(ev) if isinstance(ev,str) else ev;assert x['adapter_version']=='continuous-primary-images-20261011-b000038' and ev['selection_sha256']==prev['selection_sha256']
  own=list(db.execute('SELECT entity_id::text FROM citations WHERE field_name=%s',(FIELD,)));assert not own,'Interrupted own writes found; reconcile pinned plan'
  save('prior-batch-live-reconciliation.json',dict(at=h.now(),previous_batch=38,verified_prior_images=20,current_batch_prior_citations=0,prior_images=prior,no_previous_counts_reused=True))
  # Compare globally by native IDs and URLs, then by indexed exact titles plus creator, accession and date.
  for r in candidates:
   oid=r['ObjectID'];url='https://www.moma.org/collection/works/'+oid;y=int(r['Date'].strip().strip('()')[-4:]);assert y<=1970
   native=[dict(x) for x in db.execute("SELECT entity_id::text,scheme,external_id FROM external_identifiers WHERE entity_type='artwork' AND ((scheme LIKE '%%moma%%' AND external_id=%s) OR canonical_url=%s)",(oid,url))]
   citations=[dict(x) for x in db.execute("SELECT entity_id::text FROM citations WHERE entity_type='artwork' AND source_url=%s",(url,))]
   inv=[dict(x) for x in db.execute('SELECT id::text,title FROM artworks WHERE current_institution_id=%s AND accession_number=%s',(mo.MID,r['AccessionNumber']))]
   people,err=mo.creators(r,authorities);assert not err and len(people)==1 and not people[0]['prefix'];person=people[0];pid=person['constituentid'];qid=person['wikidataid']
   artistmatches=[dict(x) for x in db.execute("SELECT a.id::text,a.display_name,a.birth_year,a.death_year,e.scheme,e.external_id FROM external_identifiers e JOIN artists a ON a.id=e.entity_id WHERE e.entity_type='artist' AND ((e.scheme IN ('moma-person','moma-artist') AND e.external_id=%s) OR (e.scheme='wikidata' AND e.external_id=%s))",(pid,qid or 'NO_QID'))]
   names=[dict(x) for x in db.execute("SELECT a.id::text,a.display_name,a.birth_year,a.death_year FROM artists a WHERE normalized_name=%s UNION SELECT a.id::text,a.display_name,a.birth_year,a.death_year FROM artist_aliases al JOIN artists a ON a.id=al.artist_id WHERE lower(al.alias)=lower(%s)",(h.norm(r['Artist']),r['Artist']))]
   artistids={x['id'] for x in artistmatches+names};artistid=next(iter(artistids)) if len(artistids)==1 else None
   titles=[dict(x) for x in db.execute("SELECT a.id::text,a.title,a.accession_number,a.current_institution_id::text,a.creation_year_start,a.creation_year_end,a.dimensions_text,a.unlinked_creator_label,ARRAY(SELECT aa.artist_id::text FROM artwork_artists aa WHERE aa.artwork_id=a.id) artist_ids FROM artworks a WHERE a.normalized_title=%s AND a.status<>'archived'",(h.norm(r['Title']),))]
   possible=[x for x in titles if x['current_institution_id']==mo.MID or x['accession_number']==r['AccessionNumber'] or (x['creation_year_start']==y and (artistid in x['artist_ids'] or h.norm(x['unlinked_creator_label'])==h.norm(r['Artist'])))]
   reason='existing_or_ambiguous_object' if native or citations or inv or possible else None
   if len(artistids)>1:reason='artist_identity_conflict'
   # Exact date belongs to drawing itself; title references to paintings or earlier sculpture do not replace source Date.
   check=dict(native_id=oid,native=native,citations=citations,accession=inv,global_title_candidates=titles,possible_duplicates=possible,creator_authority=person,artist_matches=artistmatches,name_matches=names,artist_id=artistid,decision=reason or 'selected',source_year=y)
   checks.append(check)
   if reason:continue
   object_path=D/'objects'/(oid+'.json');h.save(object_path,r)
   selected.append(dict(provider='moma',source_id=oid,source_url=url,museum='Museum of Modern Art',title=r['Title'],creator_label=r['Artist'],verified_artist_id=artistid,creator_link_hold=not artistid,culture=None,date_display=r['Date'],year_start=y,year_end=y,date_decision='eligible',accession_number=r['AccessionNumber'],source_type='drawing',medium=r['Medium'] or None,dimensions=r['Dimensions'] or None,credit=r['CreditLine'] or None,raw=r,evidence_file=str(object_path),evidence=dict(status=200,retrieved_at=source_receipts['Artworks.csv']['retrieved_at'],sha256=h.sha(object_path.read_bytes()),dataset_sha256=source_receipts['Artworks.csv']['sha256'],artist_dataset_sha256=source_receipts['Artists-full.csv']['sha256'],url=source_receipts['Artworks.csv']['url']),creator_authority=person,source_notes='Explicit single month/day/year transcribed in full; numeric year is only a search bound. One standalone accession and Drawing source class; studies kept distinct from referenced paintings/sculptures. Metadata licence is CC0 and excludes images. Cataloged and OnView fields are source evidence only, not publication or fresh display claims.'))
 save('global-identity-reconciliation.json',dict(at=h.now(),records=checks,selected=len(selected),held=len(checks)-len(selected),pending=pending,distinct_creators=len({r['creator_label'] for r in selected})))
 h.save(E/PHASE/'source-records.json.gz',selected);h.plan(PHASE);plan,pin=h.pinned(PHASE);assert len(plan['records'])==len(selected) and all(not r['before'] for r in plan['records'])
 save('helper-adaptation.json',dict(at=h.now(),helper='ops/india-300-delivery-20261011.py',helper_sha256=h.sha((ROOT/'ops/india-300-delivery-20261011.py').read_bytes()),changes=['Separate campaign identity and checksum-bound citation','Bounded new records replaces India minimum','Museum scope further bounded by candidate accession/title','Shared ingestion lock and within-lock accession recheck'],plan_sha256=pin))
 print('STAGED',len(selected),'held',len(checks)-len(selected),flush=True)

def apply():
 plan,pin=h.pinned(PHASE);ids=[r['artwork_id'] for r in plan['records']];base.target()
 with h.connect() as db:
  present=h.snapshot(db,ids);notes=db.execute("SELECT entity_id::text,evidence_note::jsonb->>'plan_sha256' pin FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND field_name=%s",(ids,FIELD)).fetchall()
  if present:
   assert len(present)==len(notes)==len(ids) and all(x['pin']==pin for x in notes)
   locked=h.load(h.BACKUP/PHASE/'locked-before.json.gz');assert locked['artworks']=={} and locked['plan_sha256']==pin
   print('Own committed plan recovered; no write replay',flush=True);return
 assert h.load(E/'independent-source-verification.json')['plan_sha256']==pin
 backup=json.loads(subprocess.check_output(['gcloud','sql','backups','describe','1791718979252','--instance=artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=json'],text=True));assert backup['status']=='SUCCESSFUL';save('cloud-sql-backup.json',backup);h.save(h.BACKUP/'cloud-sql-backup.json',backup)
 save('production-target-before-write.json',base.target(True));base.target(True);h.apply(PHASE)
if __name__=='__main__':
 R.mkdir(parents=True,exist_ok=True)
 with (R/'worker.lock').open('a+') as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);globals()[sys.argv[1]]()
