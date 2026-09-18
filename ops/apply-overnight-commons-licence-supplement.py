#!/usr/bin/env python3
"""Add already-verified exact Commons PDM URI evidence to existing production media."""
import pathlib,importlib.util,json,psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
ROOT=pathlib.Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('cm',ROOT/'ops/overnight-commons-images.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);run=ROOT/'docs/research/overnight-images-20260915/commons';backup=pathlib.Path.home()/'Library/Application Support/Artline/backups/overnight-images-20260915/commons-explicit-pdm-before'
def main():
 audit=json.loads((run/'explicit-pdm-audit.json').read_text());updates=[]
 assert not any(x['error'] for x in audit['results'])
 for x in audit['results']:
  p=run/'images/night-commons'/(x['artwork_id']+'.json')
  if not p.exists():continue
  im=json.loads(p.read_text());e=x['evidence'];assert im['rendered_licence_evidence']==e
  m.rights_and_identity(im,im['raw']['wikidata'],im['raw']['commons'],im['raw']['structured_data'],e);updates.append((im,e))
 with psycopg.connect(m.core.cloud_dsn(),autocommit=True,row_factory=dict_row) as db:
  with db.transaction():
   old=db.execute('SELECT media_id::text,source_checksum,policy_url,evidence_json FROM media_rights_evidence WHERE media_id=ANY(%s::uuid[])',([im['media_id'] for im,e in updates],)).fetchall();byid={x['media_id']:x for x in old}
   bp=backup/'cloud-supplement-before.json'
   if not bp.exists():m.core.save_new(bp,old)
   count=0
   with db.pipeline():
    for im,e in updates:
     if im['media_id'] not in byid:continue
     row=byid[im['media_id']];assert row['policy_url']==m.PDM and row['source_checksum']==m.core.sha(m.core.encode(im['raw']))
     db.execute('UPDATE media_rights_evidence SET evidence_json=evidence_json || %s WHERE media_id=%s',(Jsonb({'rendered_licence_evidence':e}),im['media_id']));count+=1
  verified=db.execute("SELECT count(*) n FROM media_rights_evidence WHERE media_id=ANY(%s::uuid[]) AND evidence_json->'rendered_licence_evidence'->>'uri'=%s",(list(byid),m.PDM)).fetchone()['n'];assert verified==count
  p=run/'explicit-pdm-cloud-applied.json'
  if not p.exists():m.core.save_new(p,{'at':m.core.now(),'updated_and_verified':count,'original_audit_records':len(audit['results']),'raw_source_checksums_unchanged':True})
  print('Production Commons licence supplement verified',count,flush=True)
if __name__=='__main__':main()
