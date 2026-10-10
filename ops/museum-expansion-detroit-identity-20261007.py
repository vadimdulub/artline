#!/usr/bin/env python3
"""Read-only Detroit creator, native identifier, accession and subject identity scope."""
import argparse,importlib.util,json,re
from pathlib import Path
def module(name,file):
 s=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
f=module('f','museum-expansion-detroit-facts-20261007.py');i=module('i','museum-expansion-yale-identity-20261007.py');m=f.m;RUN=f.RUN;IID=f.IID;ref=f.ref
original_terms=i.search_terms
def terms(facts):
 if facts.get('creator_label_kind')=='source_cultural_label':return []
 return original_terms(facts)
i.search_terms=terms;i.RUN=RUN;i.IID=IID
SUBJECTS={'163':['%intercession%virgin%','%protection%virgin%','%pokrov%','%intercession%mother%'], '54994':['%new testament%trinity%'], '54996':['%virgin%annunciat%'], '62943':['%creation%world%'], '55894':['%george%dragon%'], '46395':['%mercurius%','%merkourios%','%merkourios%','%mercourios%']}
def params_for(rows):
 p=i.params_for(rows);p['native_object_ids']=[];p['detroit_ids']=sorted(r['source_id'] for r in rows);p['subject_patterns']=sorted({v for r in rows for v in SUBJECTS.get(r['source_id'],[])})
 urls=set(p['source_urls'])
 for url in p['source_urls']:urls.add(url.replace('://dia.org/','://www.dia.org/'))
 p['source_urls']=sorted(urls);return p
def queries(db,p):
 state=i.queries(db,p)
 native=db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND external_id=ANY(%s) AND (scheme ILIKE '%%detroit%%' OR scheme ILIKE '%%dia%%') ORDER BY entity_id,scheme,external_id",(p['detroit_ids'],)).fetchall()
 subjects=db.execute('SELECT id::text FROM artworks WHERE normalized_title LIKE ANY(%s) OR lower(alternate_title) LIKE ANY(%s) ORDER BY id LIMIT 5001',(p['subject_patterns'],p['subject_patterns'])).fetchall();assert len(subjects)<=5000
 extra=sorted(({v['entity_id'] for v in native}|{v['id'] for v in subjects})-set(state['artwork_ids']))
 state['artworks']+=db.execute('SELECT '+i.ARTCOLS+' FROM artworks a WHERE a.id=ANY(%s::uuid[]) ORDER BY a.id',(extra,)).fetchall()
 state['links']+=db.execute('SELECT aa.artwork_id::text,aa.artist_id::text,aa.attribution_role,ar.display_name FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=ANY(%s::uuid[]) ORDER BY aa.artwork_id,aa.artist_id',(extra,)).fetchall()
 state['artworks'].sort(key=lambda v:v['id']);state['links'].sort(key=lambda v:(v['artwork_id'],v['artist_id']));state['artwork_ids']=sorted(set(state['artwork_ids'])|set(extra));state['native_scheme_hits']=native;state['subject_hit_ids']=[v['id'] for v in subjects]
 return state
def comparisons(rows,state):
 out=i.comparisons(rows,state)
 for row,cm in zip(rows,out):
  cm['native_scheme_hits']=[v for v in state['native_scheme_hits'] if v['external_id']==row['source_id']]
  patterns=[re.compile('^'+re.escape(v).replace('%','.*')+'$',re.I) for v in SUBJECTS.get(row['source_id'],[])]
  cm['subject_leads']=[a for a in state['artworks'] if any(rx.search(m.norm(a.get(k) or '')) for rx in patterns for k in ['title','alternate_title'])]
 return out
def main(suffix):
 candidate=RUN/('native-candidates-'+suffix+'.json.gz');x=m.load(candidate);f.checked(x['parser_reference']);rows=x['rows'];p=params_for(rows)
 dest=RUN/('native-identity-'+suffix+'.json.gz');assert not dest.exists()
 with m.connect() as db:state=queries(db,p)
 m.save(dest,dict(at=m.now(),candidate_reference=ref(candidate),query_reference=ref(Path(__file__).resolve()),params=p,state=state,comparisons=comparisons(rows,state),read_only=True,policy='Names, translated subjects and title similarity are leads. Anonymous cultural labels do not trigger collection-wide Russian/Greek creator searches. Native IDs, URL variants, inventories and creator/subject-scoped works are reviewed before any write.'))
 print(json.dumps(dict(counts={k:len(v) for k,v in state.items()},comparisons=[{k:v for k,v in r.items() if k not in ['leads','subject_leads','exact_title_hits','inventory_hits']}|dict(subject_leads=len(r['subject_leads']),exact_title_hits=len(r['exact_title_hits']),inventory_hits=len(r['inventory_hits'])) for r in comparisons(rows,state)])),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--suffix',required=True);a=p.parse_args();assert re.fullmatch(r'\d{3}',a.suffix);main(a.suffix)
