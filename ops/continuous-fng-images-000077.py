#!/usr/bin/env python3
"""Batch 77 fallback to the saved Sinebrychoff primary-image cursor."""
import importlib.util,fcntl,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('fng77base',ROOT/'ops/continuous-fng-images-000070.py');old=importlib.util.module_from_spec(s);s.loader.exec_module(old)
b=old.b;i=old.i;h=old.h;load=old.load;save=old.save;connect=old.connect;target=old.target
P=ROOT/'docs/research/continuous-production-20261011/batches/000077';E=P/'fng'
RUNTIME=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000077';B='fng-000'
for m in [old,old.base,old.b]:m.E=E;m.RUNTIME=RUNTIME;m.B=B
# Each helper uses the new operation, never the completed parent campaign.
i.OP='continuous-primary-images-20261011-b000077-fng';i.RUN=E
i.ORIG=Path.home()/'Library/Application Support/Artline/source-images'/i.OP
i.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/i.OP
for d in [E,RUNTIME,i.ORIG,i.BACKUP]:d.mkdir(parents=True,exist_ok=True)
previous_locked_identities=i.locked_identities
def locked_identities(db,ids,rows):
 initial=load(E/'preparation-production-snapshot.json.gz')['before'];live=h.snapshot(db,ids)
 for aid in ids:
  assert live[aid]==initial[aid], 'Selected artwork or relationships changed before locked attachment'
 return previous_locked_identities(db,ids,rows)
i.locked_identities=locked_identities
def reconcile():
 for name in ['required-input-reconciliation.json','source-queue-before.json','completed-campaign-stop-preservation.json']:
  val=load(P/name)
  if name=='completed-campaign-stop-preservation.json':val['separate_campaign']=i.OP
  save(E/name,val)
 save(E/'production-target-reconciliation.json',target())
 holds=load(P/'source-access-holds.json');relevant=[]
 for r in holds['ledgers']:
  p=ROOT/r['path'];d=load(p)
  if 'kansallisgalleria.fi' in json.dumps(d):relevant.append(dict(path=r['path'],data=d))
 assert not relevant,'Review FNG provider hold before any requests'
 save(E/'source-access-holds.json',dict(at=h.now(),scanned_ledger=str(P/'source-access-holds.json'),relevant=relevant,policy='Saved anonymous official metadata export and photograph-specific CC0 primary media; no key-required API request.'))
 with connect() as db:
  own=[dict(x) for x in db.execute('SELECT media_id::text,evidence_json FROM media_rights_evidence WHERE adapter_version=%s',(i.OP,))]
  assert not own or (i.folder(B)/'selection.json.gz').exists(),'Uncertain prior own write requires reconciliation'
 save(E/'prior-own-write-reconciliation.json',dict(at=h.now(),rows=own))
 old.sinebrychoff()
 cap=load(ROOT/'docs/research/source-index-delivery-20261010/datasets/fng-export-receipt.json')
 save(E/'metadata-and-mime-reuse-verification.json',dict(at=h.now(),source_export=cap,export_checksum_verified=True,unselected_images_downloaded=0,metadata_refresh_due='2026-11-08',mime_correction_origin='docs/research/continuous-production-20261011/batches/000038/mime-retry-amendment.json',correction='Exact FNG jpg URLs may use application/octet-stream; JPEG magic and complete decoding required.'))
def prepare():old.prepare()
def deliver():
 assert load(E/'prewrite-source-verification.json')['records_verified']==len(i.accepted(B)[0])
 old.deliver()
if __name__=='__main__':
 with (RUNTIME/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);globals()[sys.argv[1]]()
