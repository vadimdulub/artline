#!/usr/bin/env python3
"""One bounded Smithsonian public-bulk supplement after exhausted French reserve."""
import csv,fcntl,gzip,importlib.util,inspect,json,re,subprocess,sys
from pathlib import Path
from urllib.parse import urlparse,parse_qs
ROOT=Path(__file__).resolve().parents[1]
def mod(name,file):
 s=importlib.util.spec_from_file_location(name,ROOT/'ops'/file);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
base=mod('base28','continuous-image-batch-000002.py');h=mod('metadata28','india-300-delivery-20261011.py');i=base.i
E=ROOT/'docs/research/continuous-production-20261011/batches/000028';R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000028'
OP='continuous-smithsonian-20261011-b000028';PHASE='saam-supplement';FIELD='continuous_smithsonian_object_evidence_20261011_b000028';MID='259d7efe-d565-56bf-bdc0-b467d3b2f69b';MUSEUM='Smithsonian American Art Museum'
h.OP=OP;h.RUN=E;h.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/OP;h.SCHEMES={'saam':['saam-object']};h.museums=lambda:{MUSEUM:('smithsonian-american-art-museum','https://americanart.si.edu/')}
for p in [E,R,h.BACKUP]:p.mkdir(parents=True,exist_ok=True)
def save(name,value):
 p=E/name
 if p.exists():return h.load(p)
 h.save(p,value);return value
def target(write=False):
 name=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip();assert name=='artline-508319:europe-west1:artline-postgres'
 return dict(base.target(write),connection_name=name,helper='ops/india-300-delivery-20261011.py',local_connections=0)
def values(ft,key,label=None):return [v['content'] for v in ft.get(key,[]) if label is None or v['label']==label]
def one(ft,key,label=None):
 v=values(ft,key,label);assert len(v)==1,(key,label,v);return v[0]
def captured():
 rc=h.load(E/'source-captures/saam-00.receipt.json');raw=gzip.decompress((ROOT/rc['body_path']).read_bytes());assert rc['status']==200 and h.sha(raw)==rc['sha256'];return [json.loads(x) for x in raw.splitlines()],rc
code=inspect.getsource(h.plan).replace('User: go ahead with India, add at least 300 artworks; broad museum coverage first. Minimum counts only new, distinct artwork records.','User-authorized continuous production batch 28; exact Smithsonian accession objects, original maker roles and review state preserved.')
exec(compile(code,__file__,'exec'),h.__dict__)
code=inspect.getsource(h.apply).replace("assert sum(not r['before'] for r in rows)>=300,'Minimum target must count new physical objects, not enrichments'","assert 1<=sum(not r['before'] for r in rows)<=4,'Bounded new physical objects only'").replace('india_minimum_300_museum_coverage_20261011',FIELD)
code=code.replace("  db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE'","  assert not db.execute('SELECT id FROM artworks WHERE current_institution_id=%s AND accession_number=ANY(%s)',(rows[0]['institution_id'],[r['accession_number'] for r in rows])).fetchall(),'Concurrent inventory insert; replan'\n  assert not db.execute(\"SELECT entity_id FROM external_identifiers WHERE entity_type='artwork' AND (scheme ILIKE '%%saam%%' OR scheme ILIKE '%%smithsonian%%') AND external_id=ANY(%s)\",([v for r in rows for v in r['all_source_ids']],)).fetchall(),'Concurrent source identity; replan'\n  assert not db.execute('SELECT id FROM artworks WHERE normalized_title=ANY(%s)',([norm(r['title']) for r in rows],)).fetchall(),'Concurrent same-title identity; replan'\n  db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE'")
exec(compile(code,__file__,'exec'),h.__dict__)
def stage():
 if (E/PHASE/'plan-pin.json').exists():return
 objects,rc=captured();candidates=h.load(E/'candidate-global-title-reconciliation.json')['rows'];chosen={'23984','51026','24673','6626'};rows=[];checks=[]
 with h.connect() as db:
  # Global creator reconciliation is read-only; no artist is created by this workflow.
  names={}
  for a in db.execute("SELECT a.id::text,a.display_name,a.birth_year,a.death_year,a.status,a.display_name name FROM artists a WHERE a.status<>'archived' UNION SELECT a.id::text,a.display_name,a.birth_year,a.death_year,a.status,al.alias name FROM artists a JOIN artist_aliases al ON al.artist_id=a.id WHERE a.status<>'archived'"):
   names.setdefault(h.norm(a['name']),{})[a['id']]=dict(a)
  for c in candidates:
   oid=c['source_id'];o=c['object'];d=o['content']['descriptiveNonRepeating'];ft=o['content']['freetext'];title=d['title']['content']
   if oid not in chosen:
    checks.append(dict(native_id=oid,title=title,decision='deferred',reason='Existing catalogue title/physical-version candidates require separate reconciliation; never duplicate to increase totals',global_title_candidates=c['matches']));continue
   assert not c['matches'];assert o in objects and o['unitCode']==d['unit_code']=='SAAM' and d['data_source']==MUSEUM
   assert d['metadata_usage']['access']=='CC0' and one(ft,'objectRights','Restrictions & Rights')=='CC0'
   assert 'Smithsonian American Art Museum Collection' in values(ft,'setName','See more items in')
   page=d['record_link'];assert urlparse(page).hostname=='americanart.si.edu' and parse_qs(urlparse(page).query)['id']==[oid]
   acc=one(ft,'identifier','Object number');allids=[oid,d['record_ID'],o['id'],o['url'],d['guid']]
   native=[dict(x) for x in db.execute("SELECT entity_id::text,scheme,external_id FROM external_identifiers WHERE entity_type='artwork' AND (scheme ILIKE '%%saam%%' OR scheme ILIKE '%%smithsonian%%') AND external_id=ANY(%s)",(allids,))]
   inventory=[dict(x) for x in db.execute('SELECT id::text,title,current_institution_id::text FROM artworks WHERE accession_number=%s',(acc,))]
   urls=[dict(x) for x in db.execute("SELECT entity_id::text FROM citations WHERE entity_type='artwork' AND source_url=ANY(%s) UNION SELECT entity_id::text FROM external_identifiers WHERE entity_type='artwork' AND canonical_url=ANY(%s)",([page,d['guid']],[page,d['guid']]))]
   assert not native and not urls and all(v['current_institution_id'] not in [None,MID] and h.norm(v['title'])!=h.norm(title) for v in inventory),(oid,native,inventory,urls)
   date=one(ft,'date','Date');match=re.fullmatch(r'(ca\. )?(\d{4})(?:-(\d{4}))?',date);assert match
   lo=int(match[2]);hi=int(match[3] or match[2]);assert 1000<=lo<=hi<=1970
   credit=one(ft,'creditLine');assert not re.search(r'\b(loan|lent|deaccessioned)\b',credit,re.I)
   typ=one(ft,'objectType','Type');source_type={'Painting':'painting','Painting-Miniature':'painting','Photography-Photoprint':'photograph','Graphic Arts-Print':'print'}[typ]
   artist_labels=values(ft,'name','Artist');assert artist_labels;makers=[]
   for label in artist_labels:
    simple=label.split(',')[0];matches=list(names.get(h.norm(simple),{}).values());years=[int(x) for x in re.findall(r'\b\d{4}\b',label)]
    if len(years)==2:matches=[x for x in matches if (x['birth_year'],x['death_year'])==tuple(years)]
    makers.append(dict(source_label=label,source_role='Artist',matches=matches,match_basis='Global existing names/aliases and explicit source life dates when supplied; unidentified creators never fabricated.'))
   linked=makers[0]['matches'][0]['id'] if len(makers)==1 and len(makers[0]['matches'])==1 and not artist_labels[0].startswith('Unidentified') else None
   label='; '.join(artist_labels);medium=one(ft,'physicalDescription','Medium');dim=one(ft,'physicalDescription','Dimensions');ims=d['online_media']['media'];assert len(ims)==1;im=ims[0];assert im['usage']['access']=='CC0' and im['type']=='Images' and parse_qs(urlparse(im['content']).query)['id']==[im['idsId']]
   assert urlparse(im['content']).hostname=='ids.si.edu'
   ep=E/'selected-source-records'/(oid+'.json');h.save(ep,dict(object=o,metadata_capture=rc,creator_reconciliation=makers))
   row=dict(provider='saam',source_id=oid,all_source_ids=allids,source_url=page,museum=MUSEUM,title=title,creator_label=label,creator_link_hold=not bool(linked),verified_artist_id=linked,date_display=date,year_start=lo,year_end=hi,date_decision='eligible',accession_number=acc,source_type=source_type,medium=medium,dimensions=dim,credit=credit,raw=dict(object=o,metadata_capture=rc,creator_reconciliation=makers,source_type=typ,source_roles=ft['name']),evidence_file=str(ep.relative_to(ROOT)),evidence=dict(status=200,retrieved_at=rc['retrieved_at'],sha256=h.sha(ep.read_bytes()),url=page),identity_review='Exact SAAM museum accession, numeric native ID, EDAN identifier, source title, dates, dimensions, credit and source roles. No matching global title, SAAM accession, native identity or source URL. Any unrelated other-museum accession-number collision is preserved in reconciliation and distinguished by its different institution and title. One physical object; original study/medium wording retained. No current-display assertion.',creator_reconciliation=makers)
   rows.append(row);checks.append(dict(native_id=oid,title=title,decision='selected',native_matches=native,global_accession_matches=inventory,global_url_matches=urls,global_title_matches=c['matches'],creator_reconciliation=makers))
 assert len(rows)==4
 save('global-identity-reconciliation.json',dict(at=h.now(),selected=4,considered=10,records=checks,remaining_shard_records='Other records include already illustrated items, archival components, missing dates and unselected media; do not count archival documents as artworks.',resume_cursor=dict(unit='saam',completed_shard='00',next_shard='01',source_sha256=rc['sha256'],metadata_records=56,selected_native_ids=sorted(chosen),deferred_native_ids=sorted({c['source_id'] for c in candidates}-chosen))))
 h.save(E/PHASE/'source-records.json.gz',rows);h.plan(PHASE);p,pin=h.pinned(PHASE);assert len(p['records'])==4 and not p['held'] and not p['new_institutions'] and all(not r['before'] for r in p['records'])
 reg=list(csv.DictReader(open('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv')))
 save('source-register.json',dict(at=h.now(),source=next(x for x in reg if x['source_id']=='smithsonian_open_access'),policy_reference='docs/ARTLINE_IMAGE_USE.md#general-image-use-policy',access_method='Official documented unauthenticated public AWS bulk metadata; one 174005-byte shard. Held si.edu web search not accessed.',access_status='HTTP 200',access_documentation='https://github.com/Smithsonian/OpenAccess#readme',rights_rule='Each selected object, metadata and exact image explicitly CC0; no blanket approval inferred.',coverage='56 metadata records; 10 object candidates reconciled; four selected. Not museum-wide or directory completion.',plan_sha256=pin))
 save('helper-adaptation.json',dict(helper='ops/india-300-delivery-20261011.py',helper_sha256=h.sha((ROOT/'ops/india-300-delivery-20261011.py').read_bytes()),changes=['Bounded four new objects; dedicated operation and source evidence field','Existing SAAM institution and native scheme; no new artists','Shared ingestion lock with native ID, accession and title concurrency checks','Creator roles, unknown attribution and full source rights preserved'],plan_sha256=pin))
def apply():
 p,pin=h.pinned(PHASE);ids=[r['artwork_id'] for r in p['records']]
 with h.connect() as db:
  present=h.snapshot(db,ids);notes=db.execute("SELECT entity_id::text,evidence_note::jsonb->>'plan_sha256' pin FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND field_name=%s",(ids,FIELD)).fetchall()
  if present:
   assert len(present)==len(notes)==len(ids) and all(r['pin']==pin for r in notes) and (h.BACKUP/PHASE/'locked-before.json.gz').exists();print('Own committed plan recovered; verify independently');return
 backup=json.loads(subprocess.check_output(['gcloud','sql','backups','describe','1791735810546','--instance=artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=json'],text=True));assert backup['status']=='SUCCESSFUL';save('cloud-sql-backup.json',backup);save('cloud-backup.json',backup)
 save('production-target-before-metadata-write.json',target(True));h.apply(PHASE)
B='saam-000';i.OP=OP+'-images';i.RUN=E;i.ORIG=Path.home()/'Library/Application Support/Artline/source-images'/i.OP;i.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/i.OP
i.CFG['saam']=dict(mid=MID,scheme='saam-object',name=MUSEUM,rights='cc0',license='CC0 1.0 Universal — Smithsonian Open Access',policy='https://creativecommons.org/publicdomain/zero/1.0/',host='ids.si.edu')
old_uid=i.m.uid;i.m.uid=lambda k:h.uid('source/saam/'+MUSEUM) if k=='source/saam' else old_uid(k)
# Preserve the museum's actual credit line in the delivered asset, beyond full raw evidence.
code=inspect.getsource(i.apply).replace("credits={}","credits={r['artwork_id']:r.get('source_credit','') for r in p['rows']}")
code=code.replace("view_label=cfg['name']+' primary object reproduction'", "view_label=('Smithsonian official combined front and back view — one miniature, accession 1950.4.21' if r['native_id']=='24673' else cfg['name']+' primary object reproduction')")
exec(compile(code,__file__,'exec'),i.__dict__)
def images():
 p,pin=h.pinned(PHASE)
 if not (i.folder(B)/'selection.json.gz').exists():
  rows=[]
  for r in p['records']:
   o=r['raw']['object'];d=o['content']['descriptiveNonRepeating'];im=d['online_media']['media'][0]
   rows.append(dict(artwork_id=r['artwork_id'],native_id=r['source_id'],title=r['title'],creator_label=r['creator_label'],source_credit=r['credit'],source_url=r['source_url'],accession_number=r['accession_number'],first=r['first'],last=r['last'],precision=r['precision'],work_type=h.worktype(r),provider='saam',image=dict(image_url=im['content'],source=o,receipt=r['raw']['metadata_capture']),plan_sha256=pin,plan_path=str(E/PHASE/'plan.json.gz'),rights_basis='Smithsonian official public export explicitly supplies CC0 for metadata, object and exact IDS image. Original artist roles and museum credit line retained. User authorization recorded separately; no independent copyright-holder licence asserted.',manual_visual_required=True))
  h.save(i.folder(B)/'selection.json.gz',dict(provider='saam',batch=B,rows=rows));h.save(i.folder(B)/'pin.json',dict(sha256=h.sha((i.folder(B)/'selection.json.gz').read_bytes())))
 for r in i.selected(B)['rows']:print(r['native_id'],i.prepare_one(r,B)['state'],flush=True)
 (i.ORIG/B).mkdir(parents=True,exist_ok=True);i.audit(B)
 for path in (i.folder(B)/'sheets').glob('*.json'):print('SHEET',h.load(path)['path'],flush=True)
def deliver():
 save('production-target-before-storage-write.json',target(True));i.upload(B)
 save('production-target-before-image-write.json',target(True));i.apply(B)
if __name__=='__main__':
 with (R/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);globals()[sys.argv[1]]()
