"""Select a bounded, date-screened five-museum ArCo research batch."""
import collections,csv,hashlib,importlib.util,json
from pathlib import Path
def module(name,file):
 s=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
prior=module('prior','museum-expansion-france-seventeenth-apply-v2-20261008.py');arco=module('arco','museum-expansion-arco-20261006.py');m=prior.m
RUN=m.RUN/'native/italy-second-minimum-20261008';ref=prior.reference;checked=prior.checked
SLUGS=['arco-museum-0d8a32ec2ffcf4b95397','galleria-estense','arco-museum-1409403273605054eecf','musei-civici-pavia','pinacoteca-accademia-albertina']
def targets():
 rows=m.load(prior.RUN/'next-museum-pass-001.json')['italian_museums']
 found=[v for v in rows if v['slug'] in SLUGS or v['name'].startswith("Pinacoteca dell'Accademia Albertina")]
 assert len(found)==5;return found
def main():
 dest=RUN/'five-museum-discovery-001.json.gz';assert not dest.exists();cont=m.load(RUN/'continuation-001.json');assert cont['previous_goal_turn']=='progress' and cont['verified_new']==125;checked(cont['previous_checkpoint'])
 ts=targets();by={v['slug']:v for v in ts};iids=sorted(v['institution_id'] for v in ts);prior.r.identity.base.IIDS=iids
 source=m.RUN/'arco/source-candidates-after-wave-07.csv'
 with source.open(newline='') as fp:rows=[v for v in csv.DictReader(fp) if v['museum_slug'] in by]
 ids=sorted({v['source_record_id'] for v in rows}|{v['source_record_id'].split('/')[-1] for v in rows});urls=sorted({v['source_url'] for v in rows}|{v['source_url'].replace('https:','http:') for v in rows}|{'https://w3id.org/arco/resource/'+v['source_record_id'] for v in rows})
 with m.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ');assert db.execute('SHOW transaction_read_only').fetchone()['transaction_read_only']=='on'
  institutions=[v['row'] for v in db.execute('SELECT to_jsonb(i) row FROM institutions i WHERE id=ANY(%s::uuid[]) ORDER BY id',(iids,))]
  scoped_ids=[v['id'] for v in db.execute('SELECT id::text FROM artworks WHERE current_institution_id=ANY(%s::uuid[]) UNION SELECT artwork_id::text FROM artwork_location_assertions WHERE institution_id=ANY(%s::uuid[]) ORDER BY id',(iids,iids))]
  snapshot=prior.snapshot(db,scoped_ids);counts=prior.counts(db)
  ex=db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND (external_id=ANY(%s) OR canonical_url=ANY(%s)) ORDER BY entity_id,scheme,external_id",(ids,urls)).fetchall()
  ci=db.execute("SELECT entity_id::text,field_name,source_record_id,source_url FROM citations WHERE entity_type='artwork' AND (source_record_id=ANY(%s) OR source_url=ANY(%s)) ORDER BY entity_id,source_record_id,source_url,field_name",(ids,urls)).fetchall()
 m.save(RUN/'initial-scope-001.json.gz',dict(at=m.now(),scoped_ids=scoped_ids,snapshot=snapshot,counts=counts,institutions=institutions,read_only=True))
 known=set()
 for v in ex+ci:
  for key in ['external_id','source_record_id','canonical_url','source_url']:
   value=(v.get(key) or '').rstrip('/')
   if value:known.add(value)
 selected=[];held=[];summary=[]
 for slug,t in by.items():
  cs=counts[t['institution_id']];eligible=[];source_known=[]
  for row in rows:
   if row['museum_slug']!=slug:continue
   rid=row['source_record_id'];variants={rid,rid.split('/')[-1],row['source_url'],row['source_url'].replace('https:','http:'),'https://w3id.org/arco/resource/'+rid}
   if variants&known:source_known.append(row);continue
   if not arco.numeric_date(row['source_creation_range']):held.append(dict(row,reason='cached_date_needs_review'));continue
   eligible.append(row)
  # Enough headroom for identity/physical-unit holds while keeping this pass bounded.
  limit=min(220,max(100,200-cs['eligible']+60));chosen=sorted(eligible,key=lambda v:(v['source_type']!='dipinto',not bool(v['source_title']),v['source_record_id']))[:limit]
  for row in chosen:selected.append(dict(number=len(selected)+1,institution_id=t['institution_id'],museum={k:t[k] for k in ['institution_id','name','slug']},index_record=row,authority_candidates=t['authorities'],state='selected_for_source_research_only'))
  summary.append(dict(name=t['name'],slug=slug,institution_id=t['institution_id'],linked=cs['linked'],eligible=cs['eligible'],cached_rows=sum(v['museum_slug']==slug for v in rows),known_source_rows=len(source_known),date_screened_unknown_source_rows=len(eligible),selected=len(chosen),selection_limit=limit))
 m.save(dest,dict(at=m.now(),targets=ts,summary=summary,rows=selected,cached_date_holds=held,known_identifiers=ex,known_citations=ci,source_reference=ref(source),priority_reference=ref(prior.RUN/'next-museum-pass-001.json'),selector_reference=ref(Path(__file__).resolve()),initial_reference=ref(RUN/'initial-scope-001.json.gz'),read_only=True,policy='Selected metadata research only, not approved additions. Check each current object page and custody graph, author roles, date, version and existing physical identity. Institute URI AND catalogue city scope; no images or display claims.'))
 print(json.dumps(dict(selected=len(selected),initial_records=len(scoped_ids),museums=summary),ensure_ascii=False),flush=True)
if __name__=='__main__':main()
