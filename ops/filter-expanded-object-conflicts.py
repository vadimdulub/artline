#!/usr/bin/env python3
"""Preserve a draft and hold source objects already owned by other catalogue rows."""
import argparse,collections,hashlib,json
from pathlib import Path

def filter_plan(directory):
 audit=json.loads((directory/'existing-object-identity-audit.json').read_text());conflicts={r['rid']:r for r in audit['conflicts']}
 draft=directory/'draft-before-object-audit';draft.mkdir()
 for name in ['plan.json','manifest.json','holds.json']:(directory/name).rename(draft/name)
 plan=json.loads((draft/'plan.json').read_text());manifest=json.loads((draft/'manifest.json').read_text());holds=json.loads((draft/'holds.json').read_text())
 assert conflicts.keys()<=set(r['rid'] for r in plan)
 accepted=[]
 for r in plan:
  if r['rid'] in conflicts:
   holds.append(dict(conflicts[r['rid']],reason='existing_museum_object_identity'));manifest['decisions']['link_'+r['source']]-=1
  else:accepted.append(r)
 manifest['decisions']['existing_museum_object_identity']=len(conflicts)
 save=lambda path,data:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
 save(directory/'plan.json',accepted);save(directory/'holds.json',holds)
 manifest.update(sha256=hashlib.sha256((directory/'plan.json').read_bytes()).hexdigest(),links=len(accepted),new_artist_count=len({r['artist']['slug'] for r in accepted if r['artist']['new']}),existing_artist_count=len({r['artist']['slug'] for r in accepted if not r['artist']['new']}),metadata_enrichments=sum(r['patch'] is not None for r in accepted))
 save(directory/'manifest.json',manifest);print(json.dumps(manifest,indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--dir',type=Path,required=True);filter_plan(p.parse_args().dir)
