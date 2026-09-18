#!/usr/bin/env python3
"""Twenty primary FNG checks scoped to already selected Finnish museum objects.

The museum's anonymous public metadata download is indexed locally. No images
are downloaded here. Accession, creator and title checks precede enrichment.
"""
import collections, importlib.util, json
from pathlib import Path
s=importlib.util.spec_from_file_location('m',Path(__file__).with_name('apply-country-round.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
CORE=m.m.core;BASE=m.x.ROOT/'docs/research/overnight-countries-20260913';RUN=BASE/'finland/primary-followup'
def namekey(v):return tuple(sorted(m.f.names.namekey(v or '').split()))
def research():
 p=BASE/'finland/primary-api/objects.json';receipt=json.loads(p.with_name('objects.receipt.json').read_text());assert CORE.sha(p.read_bytes())==receipt['sha256']
 data=json.loads(p.read_text());byid={r['objectId']:r for r in data};byacc=collections.defaultdict(list)
 for r in data:
  if r.get('inventoryNumber'):byacc[m.m.accession_key(r['inventoryNumber'])].append(r)
 for n in range(1,21):
  dest=RUN/f'round-{n:02d}'/'research.json'
  if dest.exists():continue
  reviewed=[]
  for path in sorted((BASE/'finland/FI'/f'round-{n:02d}'/'delivery/ready').glob('Q*.json')):
   r=json.loads(path.read_text())['record'];q=r['qid'];ids=[int(v) for v in m.m.r.values(r['entity'],'P9834') if str(v).isdigit()];choices=[byid[i] for i in ids if i in byid] if ids else byacc.get(m.m.accession_key(r['accession']),[])
   e=dict(qid=q,ready_sha256=CORE.sha(path.read_bytes()),candidate_title=r['title'],candidate_accession=r['accession'],creator_qid=r['creator_qid'],decision='held')
   if len(choices)!=1:e['reason']='no_unique_current_primary_object';reviewed.append(e);continue
   obj=choices[0];e.update(primary_object=obj,primary_receipt=receipt,object_url='https://kokoelma.kansallisgalleria.fi/en/object/'+str(obj['objectId']))
   if m.m.accession_key(obj.get('inventoryNumber'))!=m.m.accession_key(r['accession']):e['reason']='current_primary_accession_differs';reviewed.append(e);continue
   people=[v for v in obj['people'] if v.get('role',{}).get('en')=='Artist'];names={namekey(v) for v in m.m.r.labels(r['creator_entity'])}
   if len(people)!=1 or people[0].get('attribution') or namekey(people[0].get('firstName','')+' '+people[0].get('familyName','')) not in names:e['reason']='primary_creator_or_attribution_needs_review';reviewed.append(e);continue
   person=people[0]
   if any(person.get(k+'Year') is not None and m.m.r.year(r['creator_entity'],prop) is not None and person[k+'Year']!=m.m.r.year(r['creator_entity'],prop) for k,prop in [('birth','P569'),('death','P570')]):e['reason']='primary_person_life_conflict';reviewed.append(e);continue
   titles={m.m.r.norm(v) for v in obj.get('title',{}).values() if v};candidate={m.m.r.norm(v) for v in r['titles']}
   if not titles&candidate:e['reason']='primary_title_crosswalk_needs_review';reviewed.append(e);continue
   first=obj.get('yearFrom');last=obj.get('yearTo',first);prefix=obj.get('datePrefix',{});d=r['date'];e['primary_date']=dict(first=first,last=last,prefix=prefix)
   if first is not None and (not isinstance(first,int) or not isinstance(last,int) or first>last or last>1970):e['reason']='primary_creation_outside_cutoff_or_invalid';reviewed.append(e);continue
   if first is not None and d['first'] is not None and (last<d['first'] or first>d['last']):e['reason']='primary_creation_conflicts_with_candidate';reviewed.append(e);continue
   e.update(decision='primary_identity_corroborated',identity_basis='Unique exact museum inventory and current object ID; source-language title plus single unqualified museum creator name matched to Wikidata aliases, with nonconflicting available life years. Museum country is not treated as painter affiliation.',copy_context=obj.get('collection',{}).get('en')=='State Copy Collection' or any('copy' in t for t in titles))
   reviewed.append(e)
  CORE.save_new(dest,dict(at=CORE.now(),round=n,reviewed=reviewed,counts=dict(collections.Counter(r['decision'] for r in reviewed)),holds=dict(collections.Counter(r.get('reason') for r in reviewed if r['decision']=='held'))));print('FNG primary round',n,dict(collections.Counter(r['decision'] for r in reviewed)),flush=True)
if __name__=='__main__':research()
