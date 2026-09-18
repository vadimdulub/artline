#!/usr/bin/env python3
"""Establish museum-identified painters from documented work activity, not lifespans."""
import argparse,collections,hashlib,importlib.util,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
s=importlib.util.spec_from_file_location('planner',ROOT/'ops/plan-expanded-round2.py');p=importlib.util.module_from_spec(s);s.loader.exec_module(p)

def merged_matches(last_round=8):
 matches=collections.defaultdict(dict);paths=[]
 for number in range(2,last_round+1):
  path=ROOT/f'docs/research/expanded-round{number}-20260913/new-source-matches.json'
  if path.exists():
   paths.append(str(path.relative_to(ROOT)))
   for rid,values in json.loads(path.read_text()).items():matches[rid].update(values)
 return matches,paths

def source_entry(r,matches):
 if r['source']:
  f=r['facts'];person=f['painter'];reason=p.previous.blocked({'painter':person,'context':f.get('object_context',{}),'state':r['state'],'review':r['review'],'note':r['note'],'first':r['first'],'last':r['last'],'precision':r['precision'],'type':r['type']})
  if reason:return None,reason
  evidence={'source':r['source'],'object_id':f['object_id'],'object_url':f['object_url'],'painter':person,'evidence':f['evidence'],'original_facts_sha':r['source_sha'],'original_state':r['state'],'original_note':r['note'],'original_review':r['review']};patch=None;source=r['source']
 else:
  possible=matches.get(r['rid'],{})
  if len(possible)!=1:return None,'no_unique_official_object'
  evidence=next(iter(possible.values()));person=evidence['painter'];source=evidence['source'];patch={k:evidence[k] for k in ['date','type','medium','dimensions','accession']}
  if r['type']!='unknown':return None,'existing_metadata_review'
 if not person.get('source_id'):return None,'no_stable_creator_authority'
 if p.previous.QUALIFIED.search(person['name']) or re.search(r'\?|\bu[0-9a-f]{4}\b|\b(master|mestari|mästaren)\b|monogram',person['name'],re.I):return None,'qualified_creator'
 if person.get('birth') is not None and person.get('death') is not None:return None,'closed_biography_requires_existing_review'
 d=patch['date'] if patch else r
 first,last=d['first'],d['last']
 if d['precision'] not in ('exact','circa','range','circa_range') or first is None or last is None or not 1000<=first<=last<=1970 or last-first>125:return None,'no_eligible_dated_activity'
 if person.get('birth') is not None and last<person['birth'] or person.get('death') is not None and first>person['death']:return None,'activity_biography_conflict'
 return {'rid':r['rid'],'slug':r['slug'],'entry_sha':r['entry_sha'],'label':r['label'],'cells':r['cells'],'source':source,'painter':person,'evidence':evidence,'patch':patch,'before':{k:r[k] for k in ['title','type','first','last','precision']}},None

def main(number):
 out=ROOT/f'docs/research/expanded-round{number}-20260913';assert not (out/'plan.json').exists();rows=json.loads((out/'unlinked.json').read_text());artists=json.loads((out/'artists.json').read_text());matches,paths=merged_matches(number-1);names={p.namekey(n) for a in artists for n in [a['display_name'],a['sort_name'],*a['aliases']] if n};tokens=[set(n.split()) for n in names];identifiers={(x['scheme'],x['id']) for a in artists for x in a['identifiers']};groups=collections.defaultdict(list);counts=collections.Counter();holds=[]
 closed_authorities=set()
 for values in matches.values():
  for f in values.values():
   person=f['painter']
   if person.get('source_id') and person.get('birth') is not None and person.get('death') is not None:closed_authorities.add((f['source'],person['source_id']))
 for r in rows:
  if r['source']:
   person=r['facts']['painter']
   if person.get('source_id') and person.get('birth') is not None and person.get('death') is not None:closed_authorities.add((r['source'],person['source_id']))
 for r in rows:
  item,reason=source_entry(r,matches)
  if reason:counts[reason]+=1;continue
  person=item['painter'];key=p.namekey(person['name']);token=set(key.split())
  if key in names or p.namekey(person.get('sort_name')) in names:counts['existing_name_requires_identity_review']+=1;continue
  if any(len(t)>1 and len(token)>1 and (t<=token or token<=t) for t in tokens):counts['possible_shortened_existing_name']+=1;continue
  source=item['source'];id=person['source_id']
  if (source,id) in closed_authorities:counts['complete_authority_biography_requires_resolution']+=1;continue
  if ('wikidata',person.get('wikidata')) in identifiers or any(source in s.split('-') and s.endswith(('person','artist')) and value==id for s,value in identifiers):counts['existing_authority_requires_reconciliation']+=1;continue
  groups[(source,id)].append(item)
 # Hold separate authority IDs which claim the same complete name, rather than
 # creating duplicate painter rows from unresolved museum authority duplicates.
 names_to_ids=collections.defaultdict(set)
 for key,items in groups.items():
  for r in items:names_to_ids[p.namekey(r['painter']['name'])].add(key)
 plan=[]
 for key,items in groups.items():
  if any(len(names_to_ids[p.namekey(r['painter']['name'])])>1 for r in items):counts['duplicate_authority_name_review']+=len(items);continue
  bios={(r['painter'].get('birth'),r['painter'].get('death')) for r in items}
  if len(bios)!=1:counts['authority_biography_conflict']+=len(items);continue
  items.sort(key=lambda r:((r['patch']['date'] if r['patch'] else r['before'])['last']-(r['patch']['date'] if r['patch'] else r['before'])['first'],r['rid']))
  r=items[0];person=r['painter'];d=r['patch']['date'] if r['patch'] else r['before'];identity=':'.join(key);slug=(re.sub('[^a-z0-9]+','-',p.norm(person['name'])).strip('-')[:70].rstrip('-') or 'museum-painter')+'-activity-'+hashlib.sha256(identity.encode()).hexdigest()[:12]
  r['artist']={'slug':slug,'display_name':person['name'],'sort_name':person.get('sort_name') or person['name'],'birth_year':person.get('birth'),'death_year':person.get('death'),'entity_type':'person','status':'review','new':True,'basis':'museum_person_id_and_documented_work_activity','timeline_basis':'activity','active_start_year':d['first'],'active_end_year':d['last']}
  r['evidence']['activity_basis']={'source_person_id':person['source_id'],'object_id':r['evidence']['object_id'],'first':d['first'],'last':d['last'],'precision':d['precision'],'meaning':'Documented creation period of this work; not a lifespan'}
  plan.append(r);counts['link_'+r['source']]+=1;counts['deferred_until_authority_established']+=len(items)-1
  holds.extend({'rid':x['rid'],'reason':'deferred_until_authority_established','authority':identity} for x in items[1:])
 counts_obj=collections.Counter((r['source'],r['evidence']['object_id']) for r in plan);plan=[r for r in plan if counts_obj[(r['source'],r['evidence']['object_id'])]==1]
 plan.sort(key=lambda r:r['rid']);p.previous.save(out/'plan.json',plan);p.previous.save(out/'holds.json',holds);p.previous.save(out/'new-source-matches.json',{r['rid']:matches[r['rid']] for r in rows if r['rid'] in matches});p.previous.save(out/'source-audit.json',{'counts':dict(counts),'strategy':'One eligible dated artwork establishes each new museum person authority, with activity explicitly distinguished from lifespan.'});p.previous.save(out/'source-paths.json',paths+['ops/plan-expanded-activity.py','ops/apply-expanded-activity.py','ops/verify-expanded-activity.py'])
 manifest={'version':3,'activity_mode':True,'audited':len(rows),'sha256':hashlib.sha256((out/'plan.json').read_bytes()).hexdigest(),'links':len(plan),'new_artist_count':len(plan),'existing_artist_count':0,'metadata_enrichments':sum(r['patch'] is not None for r in plan),'decisions':dict(counts)};p.previous.save(out/'manifest.json',manifest);print(json.dumps(manifest,indent=2),flush=True)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--round',type=int,required=True);main(a.parse_args().round)
