#!/usr/bin/env python3
"""Bounded Getty Byzantine whole-object supplement; no supervisor changes."""
import csv,fcntl,gzip,importlib.util,inspect,json,re,subprocess,sys
from pathlib import Path
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
def mod(name,file):
 s=importlib.util.spec_from_file_location(name,ROOT/'ops'/file);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
base=mod('base27','continuous-image-batch-000002.py');h=mod('metadata27','india-300-delivery-20261011.py');i=base.i
E=ROOT/'docs/research/continuous-production-20261011/batches/000027';R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000027'
OP='continuous-getty-20261011-b000027';PHASE='getty-byzantine';FIELD='continuous_getty_object_evidence_20261011_b000027';MID='62fb1e52-07ff-50bd-8eeb-95ea5bf4af1c';MUSEUM='J. Paul Getty Museum'
h.OP=OP;h.RUN=E;h.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/OP
h.SCHEMES={'getty':['getty-object']};h.museums=lambda:{MUSEUM:('spain-research-museum-q731126','https://www.getty.edu/')}
API='https://data.getty.edu/museum/collection/';SITE='https://www.getty.edu/art/collection';LOCAL='https://data.getty.edu/local/thesaurus/';AAT='http://vocab.getty.edu/aat/';OWNER=API+'group/c496a7b4-6087-4deb-a1ac-0f21bd3fd87b'
for p in [E,R,h.BACKUP]:p.mkdir(parents=True,exist_ok=True)
def save(name,value):
 p=E/name
 if p.exists():return h.load(p)
 h.save(p,value);return value
def target(write=False):
 name=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip();assert name=='artline-508319:europe-west1:artline-postgres'
 return dict(base.target(write),connection_name=name,helper='ops/india-300-delivery-20261011.py',local_connections=0)
def capture(name):
 p=E/'source-captures'/(name+'.receipt.json');rc=h.load(p);bp=p.with_name(name+'.body.gz');raw=gzip.decompress(bp.read_bytes());assert rc['status']==200 and h.sha(raw)==rc['sha256'];return raw,dict(rc,body_path=str(bp.relative_to(ROOT)))
def contents(rows,typ):return list(dict.fromkeys(v['content'] for v in rows if any(t.get('id')==typ for t in v.get('classified_as',[])) and v.get('content')))
def object_data(slug):
 raw,rc=capture(slug+'-api');o=json.loads(raw);raw,nrc=capture(slug+'-native');soup=BeautifulSoup(raw,'html.parser');n=json.loads(soup.select_one('script[type="application/ld+json"]').get_text());identity=json.loads(soup.select_one('script#local_id_manager').get_text());return o,n,identity,rc,nrc
code=inspect.getsource(h.plan).replace('User: go ahead with India, add at least 300 artworks; broad museum coverage first. Minimum counts only new, distinct artwork records.','User authorized continuous production enrichment; bounded batch 27 Getty Byzantine whole inventory objects; retain anonymous illuminators and separate author roles.')
exec(compile(code,__file__,'exec'),h.__dict__)
code=inspect.getsource(h.apply).replace("assert sum(not r['before'] for r in rows)>=300,'Minimum target must count new physical objects, not enrichments'","assert 1<=sum(not r['before'] for r in rows)<=6, 'Bounded new physical objects only'").replace('india_minimum_300_museum_coverage_20261011',FIELD)
code=code.replace("  db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE'","  assert not db.execute('SELECT id FROM artworks WHERE current_institution_id=%s AND accession_number=ANY(%s)',(rows[0]['institution_id'],[r['accession_number'] for r in rows])).fetchall(),'Concurrent inventory insert; replan'\n  assert not db.execute(\"SELECT entity_id FROM external_identifiers WHERE entity_type='artwork' AND scheme LIKE '%%getty%%' AND external_id=ANY(%s)\",([v for r in rows for v in r['all_source_ids']],)).fetchall(),'Concurrent native insert; replan'\n  db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE'")
exec(compile(code,__file__,'exec'),h.__dict__)
def stage():
 if (E/PHASE/'plan-pin.json').exists():return
 save('production-target-reconciliation.json',target())
 registry=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv');reg=list(csv.DictReader(registry.open()));assert len(reg)==111
 paths=['AGENTS.md','docs/ARTLINE_IMAGE_USE.md','docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md','docs/LOCAL_DATA_LOCATIONS.md','docs/research/continuous-production-20261011/CHECKPOINT.json','docs/research/continuous-production-20261011/source-queue.json']
 save('required-input-reconciliation.json',dict(at=h.now(),files=[dict(path=p,sha256=h.sha((ROOT/p).read_bytes())) for p in paths],registry_path=str(registry),registry_sha256=h.sha(registry.read_bytes()),registry_records=111,registry=reg,precedence='New production authorization; local catalogue read-only; original full registry retained; external supervisor unchanged.'))
 q=h.load(E.parents[1]/'source-queue.json');save('source-queue-before.json',q)
 save('source-access-holds.json',dict(at=h.now(),inherited=[r for r in q['sources'] if 'hold' in r['status'] or '403' in r['status']],getty_existing_hold_found=False,checked_ledgers=['docs/research/*202610*/source-access-holds.json','docs/research/continuous-production-20261011/batches/*/*hold*.json'],new_holds=[],initial_search_parameter_issue='query= ignored by API, zero results not exhaustion; documented q= parameter succeeds; both responses retained.'))
 # Verify the prior image batch from its persisted selection and locked preimages.
 prev=E.parent/'000026';receipt=h.load(prev/'batch-verification-receipt.json');ids=receipt['production_ids'];pin=receipt['selection_sha256']
 with h.connect() as db:
  live=[dict(r) for r in db.execute("SELECT a.id::text,a.primary_media_id::text,e.adapter_version,e.evidence_json FROM artworks a JOIN media_rights_evidence e ON e.media_id=a.primary_media_id WHERE a.id=ANY(%s::uuid[])",(ids,))]
 assert len(live)==5 and all((json.loads(x['evidence_json']) if isinstance(x['evidence_json'],str) else x['evidence_json'])['selection_sha256']==pin for x in live)
 save('prior-batch-live-reconciliation.json',dict(at=h.now(),batch=26,live=live,prior_selection_sha256=pin,increment_for_this_batch=0))
 data,src=capture('search-q');pool=json.loads(data)['data'];checks=[];selected=[];chosen={'108C7J','108NT3','103RTS','103RVW','103TMY','10657E'}
 with h.connect() as db:
  for x in pool:
   slug=x['id_manager_slug'];reason=None
   if slug not in chosen:
    reason='Component or ensemble deferred; do not count folios separately' if not x.get('is_standalone') or x.get('is_parent') else 'Outside selected Byzantine/Cretan whole-object subset'
    checks.append(dict(slug=slug,source_id=x['id'],accession=x['accession_number'],outcome=reason));continue
   o,n,identity,rc,nrc=object_data(slug);assert identity==dict(slug=slug,indexedId=x['id']);assert o['id']==API+x['id'] and n['url']==SITE+x['slug_with_path']
   assert {t['id'] for t in o['current_owner']}=={OWNER};assert LOCAL+'object-record-structure-whole' in {t['id'] for t in o['classified_as']} and not o.get('part_of')
   assert x['primary_name']==n['name']==contents(o['identified_by'],LOCAL+'object-title-primary')[0];acc=contents(o['identified_by'],AAT+'300312355');assert acc==[x['accession_number']] and acc[0] in n['identifier']
   assert n['temporal']==x['date_created'];span=o['produced_by']['timespan'];assert contents(span['identified_by'],AAT+'300458798')==[n['temporal']]
   lo=int(span['begin_of_the_begin'][:4]);hi=int(span['end_of_the_end'][:4]);assert 100<=lo<=hi<=1970
   expected={'108C7J':(1275,1299),'108NT3':(1325,1345),'103RTS':(1200,1299),'103RVW':(1510,1520),'103TMY':(900,999),'10657E':(474,474)};assert (lo,hi)==expected[slug]
   allids=list(dict.fromkeys([x['id'],slug,x['id'].split('/')[-1]]+[v['content'] for v in o['identified_by'] if v['type']=='Identifier']))
   native=[dict(r) for r in db.execute("SELECT entity_id::text,scheme,external_id FROM external_identifiers WHERE entity_type='artwork' AND scheme LIKE '%%getty%%' AND external_id=ANY(%s)",(allids,))]
   accessions=[dict(r) for r in db.execute("SELECT id::text,title,accession_number,current_institution_id::text FROM artworks WHERE accession_number=ANY(%s) OR (current_institution_id=%s AND accession_number LIKE %s)",(n['identifier'],MID,acc[0]+'.%'))]
   urls=[dict(r) for r in db.execute("SELECT entity_id::text FROM citations WHERE entity_type='artwork' AND source_url=ANY(%s) UNION SELECT entity_id::text FROM external_identifiers WHERE entity_type='artwork' AND canonical_url=ANY(%s)",([n['url'],o['id']],[n['url'],o['id']]))]
   if native or accessions or urls:reason='Existing global object/component identity; excluded'
   checks.append(dict(slug=slug,source_id=x['id'],accession=acc[0],outcome=reason or 'selected',native=native,accessions=accessions,urls=urls))
   if reason:continue
   roles=[]
   for production in [o['produced_by']]+o['produced_by'].get('part',[]):
    for maker in production.get('carried_out_by',[]):roles.append(dict(id=maker['id'],name=maker['_label'],roles=[v['content'] for v in maker.get('referred_to_by',[]) if 'content' in v]))
   artmakers=[v for v in roles if any(role in ['Illuminator','Artist'] for role in v['roles'])];assert len(artmakers)==1 and artmakers[0]['name']=='Unknown'
   medium=n.get('material');dim=n.get('size');assert medium in contents(o.get('referred_to_by',[]),AAT+'300435429') and dim in contents(o.get('referred_to_by',[]),AAT+'300435430')
   source=dict(index=x,api=o,native=n,roles=roles,api_receipt=rc,native_receipt=nrc,index_receipt=src);ep=E/'selected-source-records'/(slug+'.json');h.save(ep,source)
   selected.append(dict(provider='getty',source_id=x['id'],all_source_ids=allids,slug_id=slug,source_url=n['url'],museum=MUSEUM,title=n['name'],creator_label='Unknown',creator_link_hold=True,culture='; '.join(x.get('culture',[])) or None,date_display=n['temporal'],year_start=lo,year_end=hi,date_decision='eligible',accession_number=acc[0],source_type='manuscript_illumination' if 'Manuscripts' in [v['_label'] for v in o['classified_as']] else 'ceramic' if slug=='103TMY' else 'unknown',medium=medium,dimensions=dim,credit=MUSEUM+'; documented current owner and curatorial keeper in native Linked Art record',raw=source,evidence_file=str(ep.relative_to(ROOT)),evidence=dict(status=200,retrieved_at=rc['retrieved_at'],sha256=h.sha(ep.read_bytes()),url=n['url']),creator_reconciliation='Museum explicitly attributes visual production to Unknown. Named textual authors preserved in source roles; no painter invented or author linked as illuminator.',identity_review='One complete museum inventory object. Detached leaf kept distinct; manuscript child folios not imported. Full index/API/native identifiers, provenance, dimensions and original cultural labels preserved. No current-display claim.'))
 save('global-identity-reconciliation.json',dict(at=h.now(),checked=len(checks),selected=len(selected),records=checks,source_search_sha256=src['sha256'],resume=dict(query='Byzantine',next_offset=50,size=50,search_total=581,processed_slugs=[x['slug'] for x in checks],selected_slugs=[x['slug_id'] for x in selected])))
 assert selected;h.save(E/PHASE/'source-records.json.gz',selected);h.plan(PHASE)
 p,pin=h.pinned(PHASE);assert not p['new_institutions'] and not p['artists'] and all(not r['before'] for r in p['records'])
 save('source-register.json',dict(at=h.now(),source=next(r for r in reg if r['source_id']=='getty_museum'),policy_reference='docs/ARTLINE_IMAGE_USE.md#general-image-use-policy',actual_access='Native pages, search API and Linked Art object API HTTP 200',image_rule='Per-object native CC0 required; no provider-wide approval inferred',coverage='50 source leads classified; six whole-object candidates; museum-wide and directory coverage incomplete',plan_sha256=pin))
 save('helper-adaptation.json',dict(helper='ops/india-300-delivery-20261011.py',helper_sha256=h.sha((ROOT/'ops/india-300-delivery-20261011.py').read_bytes()),changes=['Bounded 1–6 new objects instead of India 300','Dedicated operation, evidence field and recovery path','Existing Getty institution and identifier','Under shared lock recheck exact native identities and inventory'],plan_sha256=pin))
def apply():
 p,pin=h.pinned(PHASE);ids=[r['artwork_id'] for r in p['records']]
 with h.connect() as db:
  present=h.snapshot(db,ids);notes=db.execute("SELECT entity_id::text,evidence_note::jsonb->>'plan_sha256' pin FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND field_name=%s",(ids,FIELD)).fetchall()
  if present:
   assert len(present)==len(notes)==len(ids) and all(r['pin']==pin for r in notes) and (h.BACKUP/PHASE/'locked-before.json.gz').exists();print('Own committed plan recovered; verify independently');return
 backup=json.loads(subprocess.check_output(['gcloud','sql','backups','describe','1791735810546','--instance=artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=json'],text=True));assert backup['status']=='SUCCESSFUL';save('cloud-sql-backup.json',backup);save('cloud-backup.json',backup)
 save('production-target-before-metadata-write.json',target(True));h.apply(PHASE)
B='getty-000';i.OP=OP+'-images';i.RUN=E;i.ORIG=Path.home()/'Library/Application Support/Artline/source-images'/i.OP;i.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/i.OP
i.CFG['getty']=dict(mid=MID,scheme='getty-object',name=MUSEUM,rights='cc0',license='CC0 1.0 Universal — Getty Open Content',policy='https://creativecommons.org/publicdomain/zero/1.0/',host='media.getty.edu')
old_uid=i.m.uid;i.m.uid=lambda k:h.uid('source/getty/'+MUSEUM) if k=='source/getty' else old_uid(k)
def images():
 if (i.folder(B)/'selection.json.gz').exists():return
 p,pin=h.pinned(PHASE);rows=[];holds=[]
 for r in p['records']:
  if r['slug_id'] not in ['108NT3','103TMY','10657E']:
   holds.append(dict(artwork_id=r['artwork_id'],reason='Whole manuscript: page/cover representation requires separate view review; no component-image substitution.'));continue
  n=r['raw']['native'];assert n['license']=='http://creativecommons.org/publicdomain/zero/1.0/'
  thumb=n['thumbnailUrl'];assert thumb==r['raw']['index']['manifest']['thumb'] and r['raw']['index']['manifest']['license']==n['license']
  url=thumb.replace('/full/!300,300/','/full/!1200,1200/');assert url!=thumb
  rows.append(dict(artwork_id=r['artwork_id'],native_id=r['source_id'],title=r['title'],creator_label=r['creator_label'],source_url=r['source_url'],accession_number=r['accession_number'],first=r['first'],last=r['last'],precision=r['precision'],work_type=h.worktype(r),provider='getty',image=dict(image_url=url,source=n,receipt=r['raw']['native_receipt']),plan_sha256=pin,plan_path=str(E/PHASE/'plan.json.gz'),rights_basis='Exact object native JSON-LD and index IIIF both explicitly label this reproduction CC0. Getty source rights and credit retained. Full supplied composition, no current display claim.',manual_visual_required=True))
 save('image-representation-holds.json',dict(at=h.now(),holds=holds))
 h.save(i.folder(B)/'selection.json.gz',dict(provider='getty',batch=B,rows=rows));h.save(i.folder(B)/'pin.json',dict(sha256=h.sha((i.folder(B)/'selection.json.gz').read_bytes())))
 for r in rows:print(r['title'],i.prepare_one(r,B)['state'],flush=True)
 (i.ORIG/B).mkdir(parents=True,exist_ok=True);i.audit(B)
 print('Images prepared',[(r['artwork_id'],str(i.folder(B)/'prepared'/(r['artwork_id']+'.json'))) for r in rows])
def deliver():
 save('production-target-before-storage-write.json',target(True));i.upload(B)
 save('production-target-before-image-write.json',target(True));i.apply(B)
if __name__=='__main__':
 with (R/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);globals()[sys.argv[1]]()
