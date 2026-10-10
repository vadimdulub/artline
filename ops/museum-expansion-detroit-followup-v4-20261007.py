#!/usr/bin/env python3
"""Complete selected Detroit capture: literal facts and expanded identity discovery."""
import argparse, importlib.util, json, re, types
from pathlib import Path
s=importlib.util.spec_from_file_location('previous',Path(__file__).with_name('museum-expansion-detroit-followup-v3-20261007.py'));previous=importlib.util.module_from_spec(s);s.loader.exec_module(previous)
f=previous.f;i=previous.i;m=previous.m;RUN=previous.RUN;IID=previous.IID;ref=previous.ref
previous.previous.ALIASES.update({
 '46064':['Urban Görtschacher'],
 '51090':['Jan van Goyen'],
 '50300':['Morros'],
 '50434':['Antonio Amorosi','Antonio Amarosi','Diego Velazquez','Willem Drost','Bernhard Keil','Bernardo Keilhau','Monsu Bernardo'],
 '49563':['Jaume Baco','Jaime Bacho'],
 '52008':['Mathieu Le Nain','Maitre des Jeux'],
 '52011':['Jean-Honore Fragonard'],
 '51476':['Joseph Marie Vien'],
 '51436':['Thomas Gainsborough'],
 '52180':['Gabriel Metsu'],
 '52205':['Andrea del Verrocchio'],
 '52211':['Carlo Saraceni','Adam Elsheimer'],
 '52895':['Giovanni da Bologna','Marco di Paolo'],
 '53773':['Matteo di Giovanni'],
 '53774':['Matteo di Giovanni'],
 '53612':['Segna di Buonaventura','Ugolino da Siena','Master of San Quirico d Orcia'],
 '53613':['Hugo van der Goes','Jan de Vos','Master of Frankfort'],
})
previous.TITLE_ALIASES.update({'44441':['New York Interior'],'45712':['Personnage Biblique','Samson','Portrait of an Actor'],'45839':['Portrait of an Old Man','Portrait of Man in Profile'],'51090':['River Scene'],'51436':['Mrs. John Gainsborough'],'52180':['The Love Letter','The Billet Doux'],'51641':['La Sculpture'],'53478':['Madonna of Humility']})
def parse(path):
 row=previous.parse(path);row['followup_v4_reference']=ref(Path(__file__).resolve());return row
def dependencies():
 paths=set();seen=set()
 def visit(mod):
  if id(mod) in seen:return
  seen.add(id(mod));file=getattr(mod,'__file__',None)
  if not file or Path(file).resolve().parent!=m.ROOT/'ops':return
  paths.add(Path(file).resolve())
  for value in vars(mod).values():
   if isinstance(value,types.ModuleType):visit(value)
 visit(previous);paths.add(Path(__file__).resolve());return [ref(p) for p in sorted(paths)]
def facts(suffix):
 checkpoint=m.RUN/'native/detroit-priority/delivery-checkpoint-001.json';assert ref(checkpoint)['sha256']=='1bb84ef12601ee2a933bd9724ebdece28bfb8108c25d9835f6cb8da106c817ae'
 plan=m.load(m.RUN/'native/detroit-priority/detroit-priority-reviewed-additions-001-plan.json.gz');added={v['facts']['source_id'] for v in plan['records']};assert len(added)==5
 paths=sorted((f.RUN/'objects-001').glob('*.json.gz'));assert len(paths)==117,'Wait for the frozen selected capture to finish'
 rows=[parse(p) for p in paths];excluded=[r for r in rows if r['source_id'] in added];rows=[r for r in rows if r['source_id'] not in added];assert len(excluded)==5 and len(rows)==112
 dest=RUN/('native-candidates-'+suffix+'.json.gz');assert not dest.exists()
 m.save(dest,dict(at=m.now(),rows=rows,already_added_excluded=[dict(source_id=r['source_id'],source_reference=r['source_reference']) for r in excluded],complete_capture_count=len(paths),parser_reference=ref(Path(__file__).resolve()),dependencies=dependencies(),baseline_checkpoint_reference=ref(checkpoint),queue_reference=ref(f.c.QUEUE),capture_incomplete=False,uncaptured=[dict(number=5,source_id='54995',reason='Retained transport timeout; not retried.')],policy='Literal source facts, with former attribution and translated subject aliases for duplicate discovery only. No publication or additions approval. Existing six accepted holdings are outside this selection.'))
 print(json.dumps(dict(captured=len(paths),followup=len(rows),flags=[dict(number=r['number'],flags=r['review_flags']) for r in rows if r['review_flags']])),flush=True)
def identity(suffix):
 candidate=RUN/('native-candidates-'+suffix+'.json.gz');x=m.load(candidate)
 for dep in x['dependencies']:f.checked(dep)
 rows=x['rows'];p=i.params_for(rows);dest=RUN/('native-identity-'+suffix+'.json.gz');assert not dest.exists()
 with m.connect() as db:
  state=i.queries(db,p);citations=[r['row'] for r in db.execute("SELECT to_jsonb(c) row FROM citations c WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id",(state['artwork_ids'],))]
 m.save(dest,dict(at=m.now(),candidate_reference=ref(candidate),query_reference=ref(Path(__file__).resolve()),dependencies=dependencies(),params=p,state=state,comparisons=i.comparisons(rows,state),read_only=True))
 m.save(RUN/('identity-citations-'+suffix+'.json.gz'),dict(at=m.now(),selected_ids=state['artwork_ids'],citations=citations,identity_reference=ref(dest),read_only=True));print(json.dumps(dict(counts={k:len(v) for k,v in state.items()},citations=len(citations))),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['facts','identity']);p.add_argument('--suffix',default='002');v=p.parse_args();assert re.fullmatch(r'\d{3}',v.suffix);globals()[v.command](v.suffix)
