#!/usr/bin/env python3
"""Fresh post-priority Detroit research scope and bounded follow-up identities."""
import argparse,importlib.util,json,re
from pathlib import Path
def module(name,file):
 s=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
f=module('f','museum-expansion-detroit-facts-v3-20261007.py');ext=module('ext','museum-expansion-detroit-identity-v2-20261007.py');i=ext.v;m=f.m;ref=f.ref;IID=f.IID;RUN=m.RUN/'native/detroit-followup';i.RUN=RUN;i.i.RUN=RUN
ALIASES={'44986':['Joachim Patinier','Joachim Patinir','Lambert Lombard'],'45287':['Vincenzo Foppa','Maestro dei Garofani'],'45292':['Francesco Salviati','Andrea del Sarto'],'45716':['Claude Lorrain'],'45727':['Claude Lorrain'],'45841':['Lorenzo Costa'],'44441':['Alexander Lawrie'],'45289':['Peter Paul Rubens'],'45747':['Johannes Vermeer']}
def parse(path):
 row=f.parse(path);facts=row['facts'];life=next((s['value'] for s in facts['source_fields'] if s['label']=='Life Dates'),'');years=[int(y) for y in re.findall(r'(?<!\d)\d{3,4}(?!\d)',life)]
 if 2<=len(years)<=4 and max(years)-min(years)>=10 and (facts['first'],facts['last'])==(min(years),max(years)):
  row['review_flags']=sorted(set(row['review_flags'])|{'creation_range_matches_creator_activity' if re.search(r'\bactive\b',life,re.I) else 'creation_range_matches_creator_lifespan'})
 aliases=ALIASES.get(row['source_id'],[]);facts['identity_creator_labels']=sorted(set(facts['identity_creator_labels']+aliases));row['identity_alias_basis']='Former attributions or alternate creator names are discovery labels only. Read the retained native published references and follow-up notes; do not rewrite the current source creator.' if aliases else None
 row['parser_extension_reference']=ref(Path(__file__).resolve());return row
def scope():
 sc=module('sc','museum-expansion-ago-discovery-20261007.py');sc.scope('detroit-followup',IID)
 assert m.load(RUN/'initial-scope-001.json.gz')['counts']==dict(linked=6,eligible=6)
def facts(suffix):
 checkpoint=m.RUN/'native/detroit-priority/delivery-checkpoint-001.json';assert ref(checkpoint)['sha256']=='1bb84ef12601ee2a933bd9724ebdece28bfb8108c25d9835f6cb8da106c817ae'
 plan=m.load(m.RUN/'native/detroit-priority/detroit-priority-reviewed-additions-001-plan.json.gz');added={v['facts']['source_id'] for v in plan['records']};assert len(added)==5
 paths=sorted((f.RUN/'objects-001').glob('*.json.gz'));rows=[parse(p) for p in paths];excluded=[r for r in rows if r['source_id'] in added];rows=[r for r in rows if r['source_id'] not in added];assert len(excluded)==5
 dest=RUN/('native-candidates-'+suffix+'.json.gz');assert not dest.exists()
 m.save(dest,dict(at=m.now(),rows=rows,already_added_excluded=[dict(source_id=r['source_id'],source_reference=r['source_reference']) for r in excluded],complete_capture_count=len(paths),parser_reference=ref(Path(__file__).resolve()),base_parser_reference=ref(Path(f.__file__).resolve()),baseline_checkpoint_reference=ref(checkpoint),queue_reference=ref(f.c.QUEUE),capture_incomplete=len(paths)<117,policy='New post-five-addition research snapshot only. Museum scope contains six accepted holdings. Source creation ranges matching life or activity fields require editorial validation; original values are retained. Historical creators and aliases expand duplicate checks only. No additions or publication approval.'))
 print(json.dumps(dict(captured=len(paths),already_added=5,followup_rows=len(rows),flags=[dict(number=r['number'],source_id=r['source_id'],title=r['facts']['title'],flags=r['review_flags']) for r in rows if r['review_flags']])),flush=True)
def identity(suffix):
 candidate=RUN/('native-candidates-'+suffix+'.json.gz');x=m.load(candidate);f.checked(x['parser_reference']);f.checked(x['base_parser_reference']);rows=x['rows'];p=i.params_for(rows);dest=RUN/('native-identity-'+suffix+'.json.gz');assert not dest.exists()
 with m.connect() as db:
  state=i.queries(db,p);citations=[r['row'] for r in db.execute("SELECT to_jsonb(c) row FROM citations c WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id",(state['artwork_ids'],))]
 m.save(dest,dict(at=m.now(),candidate_reference=ref(candidate),query_reference=ref(Path(__file__).resolve()),identity_base_references=[ref(Path(ext.__file__).resolve()),ref(Path(i.__file__).resolve())],params=p,state=state,comparisons=i.comparisons(rows,state),read_only=True))
 m.save(RUN/('identity-citations-'+suffix+'.json.gz'),dict(at=m.now(),selected_ids=state['artwork_ids'],citations=citations,identity_reference=ref(dest),read_only=True));print(json.dumps(dict(counts={k:len(v) for k,v in state.items()},citations=len(citations))),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['scope','facts','identity']);p.add_argument('--suffix',default='001');v=p.parse_args();assert re.fullmatch(r'\d{3}',v.suffix);scope() if v.command=='scope' else globals()[v.command](v.suffix)
