#!/usr/bin/env python3
"""One bounded source-backed icon supplement; no scheduler or local DB connection."""
import csv,fcntl,gzip,importlib.util,inspect,json,re,subprocess,sys
from pathlib import Path
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
def mod(name,file):
 s=importlib.util.spec_from_file_location(name,ROOT/'ops'/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
h=mod('h','india-300-delivery-20261011.py');base=mod('base','continuous-image-batch-000002.py')
E=ROOT/'docs/research/continuous-production-20261011/batches/000030';R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000030';PHASE='nationalmuseum-icons';FIELD='continuous_nationalmuseum_object_evidence_20261011_b000030'
h.OP='continuous-nationalmuseum-20261011-b000030';h.RUN=E;h.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/h.OP;h.SCHEMES={'nationalmuseum':['nationalmuseum-object','museum-native-nationalmuseum-object','nationalmuseum-sweden-object']}
h.museums=lambda:{'Nationalmuseum':('nationalmuseum-stockholm','https://www.nationalmuseum.se/')}
code=inspect.getsource(h.apply).replace("assert sum(not r['before'] for r in rows)>=300,'Minimum target must count new physical objects, not enrichments'","assert 1 <= len(rows) <= 50 and all(not r['before'] for r in rows), 'New bounded source objects only'").replace('india_minimum_300_museum_coverage_20261011',FIELD)
needle="  db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE'"
replacement="  inventory=db.execute('SELECT id::text,accession_number FROM artworks WHERE current_institution_id=%s AND accession_number=ANY(%s)',(rows[0]['institution_id'],[r['accession_number'] for r in rows])).fetchall();assert not inventory,'Concurrent object insert; replan'\n  db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE'"
assert needle in code;code=code.replace(needle,replacement);exec(compile(code,'established-helper-bounded-nationalmuseum','exec'),h.__dict__)
code=inspect.getsource(h.plan).replace('User: go ahead with India, add at least 300 artworks; broad museum coverage first. Minimum counts only new, distinct artwork records.','User authorized bounded source-backed production inserts; batch 30 Nationalmuseum icon supplement; new artworks stay review.')
exec(compile(code,'established-nationalmuseum-planner-authorization','exec'),h.__dict__)
# Keep creation bounds as supplied by the native museum, including ±2-year circa bounds.
def save(name,v):
 p=E/name
 if p.exists():return h.load(p)
 h.save(p,v);return v
HELD={'26419':'Dated 1820 field conflicts with catalogue ca.1820 and inscription of purchase/barter in 1820; individual physical creation-date/attribution review required.','26497':'Header late 17th century conflicts with catalogue late 17th–early 18th; creator school label and native bounds need editorial reconciliation.','26376':'Separate accession, but member of NMI 57–59 Deesis ensemble; reconcile whole/part identities before inserting component.'}
def stage():
 if (E/PHASE/'plan-pin.json').exists():
  base.target();h.pinned(PHASE);print('Pinned batch exists; resume verification/delivery from checkpoint');return
 save('production-target-reconciliation.json',base.target())
 files=['AGENTS.md','docs/ARTLINE_IMAGE_USE.md','docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md','docs/LOCAL_DATA_LOCATIONS.md','docs/research/continuous-production-20261011/CHECKPOINT.json','docs/research/continuous-production-20261011/source-queue.json']
 save('required-inputs.json',dict(at=h.now(),files=[dict(path=x,sha256=h.sha((ROOT/x).read_bytes())) for x in files],instruction_precedence='Current bounded worker instruction; production authorization; local real catalogue read-only. Supervisor unchanged.'))
 registry=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv');reg=list(csv.DictReader(registry.open()));assert len(reg)==111
 save('source-register.json',dict(at=h.now(),registry_records=111,original_registry_path=str(registry),registry_sha256=h.sha(registry.read_bytes()),route=[x for x in reg if x['source_id']=='nationalmuseum_sweden'],policy='docs/ARTLINE_IMAGE_USE.md#general-image-use-policy',access_status='Official collection metadata HTTP 200; historical direct-image HTTP 403 hold preserved. New documented public media portal landing HTTP 200; item-level route not yet verified.',supplementary_json_not_substituted=True))
 holdpath=ROOT/'docs/research/images-followup-20260916/nationalmuseum-direct-source-pause.json'
 inherited=h.load(E.parent/'000029/source-access-holds.json')
 save('source-access-holds.json',dict(at=h.now(),nationalmuseum_direct_image_hold=dict(path=str(holdpath.relative_to(ROOT)),sha256=h.sha(holdpath.read_bytes()),record=h.load(holdpath)),inherited=inherited,request_rule='No requests to held direct image resources; metadata is explicitly unaffected. Other held providers not retried.'))
 prev=h.load(E.parent/'000029/batch-verification-receipt.json');ids=prev['production_ids']
 with h.connect() as db:
  rs=[dict(x) for x in db.execute('SELECT a.id::text,a.primary_media_id::text,m.adapter_version,m.evidence_json FROM artworks a JOIN media_rights_evidence m ON m.media_id=a.primary_media_id WHERE a.id=ANY(%s::uuid[])',(ids,))];assert len(rs)==19
  for x in rs:
   ev=x['evidence_json'];ev=json.loads(ev) if isinstance(ev,str) else ev
   assert x['adapter_version']=='continuous-primary-images-20261011-b000029' and ev['selection_sha256']==prev['selection_sha256'] and ev['batch_visual_review_sha256']==prev['visual_review_sha256']
  existing=list(db.execute('SELECT entity_id::text FROM citations WHERE field_name=%s',(FIELD,)));assert not existing,'Interrupted writes exist; reconcile before replanning'
 save('prior-batch-live-reconciliation.json',dict(at=h.now(),prior_batch=29,rows=rs,verified_prior_images=19,current_batch_prior_citations=0,no_prior_deliveries_counted=True))
 selected=[];checks=[]
 candidates=h.load(E/'discovery-global-reconciliation.json')['records']
 with h.connect() as db:
  for lead in candidates:
   oid=lead['source_id'];o=h.load(E/'objects'/(oid+'.json'));u='https://collection.nationalmuseum.se/en/collection/item/'+oid+'/';rc=h.load(E/'source-captures'/('icon-'+oid+'.receipt.json'));raw=gzip.decompress((E/'source-captures'/('icon-'+oid+'.body.gz')).read_bytes());assert rc['status']==200 and h.sha(raw)==rc['sha256']
   actual=json.loads(BeautifulSoup(raw,'html.parser').select_one('#__NEXT_DATA__').string)['props']['pageProps']['data']['item'];assert actual==o
   qids=re.findall(r'Q\d+',o.get('ObjExternalIDTxt',''));titles=[o['ObjTitleMainTxt'],o['ObjTitleMainTxt_sv']]
   # Bounded exact indexed-title and source identifier reconciliation, globally.
   titlescope=[dict(x) for x in db.execute('SELECT id::text,title,accession_number,current_institution_id::text FROM artworks WHERE normalized_title=ANY(%s) AND status<>%s',([h.norm(t) for t in titles],'archived'))]
   other=[dict(x) for x in db.execute("SELECT scheme,entity_id::text,external_id FROM external_identifiers WHERE entity_type='artwork' AND external_id=ANY(%s)",(qids,))] if qids else []
   conflict=[x for x in titlescope if x['current_institution_id']=='3dd937e8-ac85-4b50-8b55-c45034c1a18e' or (x['accession_number'] or '').replace(' ','')==o['ObjInventoryNumberTxt'].replace(' ','')]
   reason=HELD.get(oid)
   if lead['matches'] or other or conflict:reason='Global identifier/title-accession match needs review'
   lo,hi=int(o['ObjFromYearTxt']),int(o['ObjToYearTxt']);assert lo<=hi<=1970
   assert o['ObjCollectionSearchTxt']['LabelTxt']=='Icons' and o['ObjInventoryNumberTxt'].startswith('NMI ')
   checks.append(dict(source_id=oid,reason=reason or 'selected',global_title_candidates=titlescope,wikidata_candidates=other,native_accession_matches=lead['matches'],source_date=o['ObjDateMainTxt'],native_bounds=[lo,hi]))
   if reason:continue
   assert o['ObjPersonRefTxt']=='Unknown';makers=o['ObjPersonRef']['Items'];assert len(makers)==1 and makers[0]['LinkLabelTxt']=='Unknown'
   p=E/'objects'/(oid+'.json')
   selected.append(dict(provider='nationalmuseum',source_id=oid,source_url=u,museum='Nationalmuseum',title=o['ObjTitleMainTxt'],creator_label='Unknown',creator_link_hold=True,culture=None,date_display=o['ObjDateMainTxt'],year_start=lo,year_end=hi,date_decision='eligible',accession_number=o['ObjInventoryNumberTxt'],source_type='painting',medium=o.get('ObjMaterialTechniqueTxt') or None,dimensions=o.get('ObjDimensionGroupTxt') or None,credit=o.get('ObjDonationTxt') or None,raw=dict(o,original_title=o['ObjTitleMainTxt_sv']),evidence_file=str(p.relative_to(ROOT)),evidence=dict(status=200,retrieved_at=rc.get('retrieved_at') or rc['at'],sha256=h.sha(p.read_bytes()),source_capture_sha256=rc['sha256'],url=u),source_notes='Native date bounds retained, including circa expansion. Original Swedish title/creator and full catalogue text captured. Unknown maker remains label. One physical accession per record; quadripartite composition is one artwork. Historical repainting/metal covers are retained in source evidence. No current-display claim.'))
 save('global-identity-reconciliation.json',dict(at=h.now(),records=checks,selected=len(selected),held=len(checks)-len(selected),no_new_painters=True))
 h.save(E/PHASE/'source-records.json.gz',selected);h.plan(PHASE)
 p,pin=h.pinned(PHASE);assert len(p['records'])==len(selected) and all(not r['before'] for r in p['records'])
 save('helper-adaptation.json',dict(at=h.now(),helper='ops/india-300-delivery-20261011.py',helper_sha256=h.sha((ROOT/'ops/india-300-delivery-20261011.py').read_bytes()),changes=['Separate OP/RUN/BACKUP and Nationalmuseum identifier aliases','Bounded 1–50 new objects replaces India-specific 300 minimum','Programme-specific checksum-bound citation field','Accession recheck under shared ingestion transaction lock'],plan_sha256=pin,authorization='User expressly authorized source-backed production inserts; new records remain review.'))
 print('READY',len(selected),flush=True)
def apply():
 plan,pin=h.pinned(PHASE);ids=[r['artwork_id'] for r in plan['records']]
 with h.connect() as db:
  present=h.snapshot(db,ids);notes=db.execute("SELECT entity_id::text,evidence_note::jsonb->>'plan_sha256' pin FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND field_name=%s",(ids,FIELD)).fetchall()
  if present:
   assert len(present)==len(notes)==len(ids) and all(r['pin']==pin for r in notes),'Existing rows not attributable to this plan; manual reconciliation required'
   locked=h.load(h.BACKUP/PHASE/'locked-before.json.gz');assert locked['artworks']=={} and locked['plan_sha256']==pin
   print('Own committed metadata recovered; no replay. Reconcile final image receipt and current rows.');return
 save('production-target-before-write.json',base.target(True))
 backup=json.loads(subprocess.check_output(['gcloud','sql','backups','describe','1791718979252','--instance=artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=json'],text=True));assert backup['status']=='SUCCESSFUL';save('cloud-sql-backup.json',backup)
 assert (E/'independent-source-verification.json').exists()
 base.target(True);h.apply(PHASE)
if __name__=='__main__':
 with (R/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);globals()[sys.argv[1]]()
