#!/usr/bin/env python3
"""Bounded, read-only Princeton object identity discovery."""
import argparse,importlib.util,json,re
from pathlib import Path
def module(name,file):
 s=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
f=module('f','museum-expansion-princeton-facts-20261007.py');i=module('i','museum-expansion-yale-identity-20261007.py');m=f.m;RUN=f.RUN;IID=f.IID;ref=f.ref;i.RUN=RUN;i.IID=IID
original_terms=i.search_terms
def terms(facts):
 labels=[]
 for label in [facts.get('creator_label'),facts.get('detail_creator_label')]+facts.get('identity_creator_labels',[]):
  if not label or re.search(r'^(?:Unknown|Unidentified|Anonymous|Artist unidentified|Early Byzantine|Byzantine|Late Antiquity|Greek|East Greek|Russian|Italian|French|Chinese|Ethiopian|Roman|Egyptian|Tang|Ming|Japanese|Late Antique)(?:$|,|\s+\(|\s+or\s+)',label,re.I):continue
  labels.append(label)
 return original_terms(dict(creator_label=None,detail_creator_label=None,identity_creator_labels=labels))
i.search_terms=terms
def params_for(rows):
 p=i.params_for(rows);p['native_object_ids']=[];p['princeton_ids']=sorted(r['source_id'] for r in rows);return p
def queries(db,p):
 state=i.queries(db,p)
 native=db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND external_id=ANY(%s) AND scheme ILIKE '%%princeton%%' ORDER BY entity_id,scheme,external_id",(p['princeton_ids'],)).fetchall()
 extra=sorted({v['entity_id'] for v in native}-set(state['artwork_ids']))
 state['artworks']+=db.execute('SELECT '+i.ARTCOLS+' FROM artworks a WHERE a.id=ANY(%s::uuid[]) ORDER BY a.id',(extra,)).fetchall()
 state['links']+=db.execute('SELECT aa.artwork_id::text,aa.artist_id::text,aa.attribution_role,ar.display_name FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=ANY(%s::uuid[]) ORDER BY aa.artwork_id,aa.artist_id',(extra,)).fetchall()
 state['artworks'].sort(key=lambda x:x['id']);state['links'].sort(key=lambda x:(x['artwork_id'],x['artist_id']));state['artwork_ids']=sorted(set(state['artwork_ids'])|set(extra));state['native_scheme_hits']=native;return state
def comparisons(rows,state):
 out=i.comparisons(rows,state)
 for row,cmp in zip(rows,out):cmp['native_scheme_hits']=[v for v in state['native_scheme_hits'] if v['external_id']==row['source_id']]
 return out
def main(suffix):
 candidate=RUN/('native-candidates-'+suffix+'.json.gz');x=m.load(candidate)
 for dep in x['dependencies']:f.checked(dep)
 rows=x['rows'];p=params_for(rows)
 with m.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ');state=queries(db,p);cs=[v['row'] for v in db.execute("SELECT to_jsonb(c) row FROM citations c WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id",(state['artwork_ids'],))]
 dest=RUN/('native-identity-'+suffix+'.json.gz');assert not dest.exists()
 m.save(dest,dict(at=m.now(),candidate_reference=ref(candidate),query_reference=ref(Path(__file__).resolve()),base_query_reference=ref(Path(i.__file__).resolve()),params=p,state=state,comparisons=comparisons(rows,state),read_only=True,policy='Creator/alias, exact-title, inventory, native URL and scheme discovery. Similarity is a lead, not approval. Initial27 pending records included independently of creator/title searches. Preserve qualified labels; no painter authority writes.'))
 m.save(RUN/('identity-citations-'+suffix+'.json.gz'),dict(at=m.now(),identity_reference=ref(dest),selected_ids=state['artwork_ids'],citations=cs,read_only=True));print(json.dumps(dict(counts={k:len(v) for k,v in state.items()},citations=len(cs))),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--suffix',required=True);a=p.parse_args();assert re.fullmatch(r'\d{3}',a.suffix);main(a.suffix)
