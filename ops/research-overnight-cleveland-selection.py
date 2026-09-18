#!/usr/bin/env python3
"""Select current museum objects only after exact existing creator/date review."""
import argparse,collections,importlib.util,json,re
from pathlib import Path
s=importlib.util.spec_from_file_location('m',Path(__file__).with_name('overnight-cleveland-selected-images.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);core=m.core
def main():
 p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--reference',type=Path);a=p.parse_args();r=a.run;r.mkdir(parents=True,exist_ok=True);reference=a.reference or r;capture=json.loads((reference/'capture.json').read_text());assert capture['complete']
 with m.ro('postgres://localhost/artline') as db:
  people=db.execute("""SELECT a.id::text,a.slug,a.display_name,a.birth_year,a.death_year,
   ARRAY(SELECT al.alias FROM artist_aliases al WHERE al.artist_id=a.id) aliases,
   (SELECT e.external_id FROM external_identifiers e WHERE e.entity_type='artist' AND e.entity_id=a.id AND e.scheme='wikidata') qid,
   EXISTS(SELECT 1 FROM artist_discovery_selection d WHERE d.artist_id=a.id AND d.is_popular) popular FROM artists a WHERE a.status<>'archived'""").fetchall();existing={x['external_id'] for x in db.execute("SELECT external_id FROM external_identifiers WHERE entity_type='artwork' AND scheme=ANY(%s)",([m.SCHEME,'cleveland-object'],)).fetchall()}
 index=collections.defaultdict(dict)
 for artist in people:
  for name in [artist['display_name']]+artist['aliases']:index[m.norm(name)][artist['id']]=artist
 rows=[];held=[];counts=collections.Counter();seen=set()
 for receipt in capture['pages']:
  raw=(reference/'metadata'/(core.sha(receipt['url'].encode())+'.json')).read_bytes();assert core.sha(raw)==receipt['sha256']
  for o in json.loads(raw)['data']:
   oid=str(o['id'])
   if oid in seen:counts['repeated_page_entries']+=1;continue
   seen.add(oid)
   if oid in capture.get('conflicting_object_ids',[]):held.append({'source_object_id':oid,'reason':'Source object changed between page captures'});continue
   if oid in existing:counts['existing_native_object']+=1;continue
   try:
    maker=m.primary_maker(o);name=m.maker_name(maker);hits=index[m.norm(name)]
    if len(hits)!=1:raise ValueError('Existing creator full name or alias is absent or ambiguous')
    artist=next(iter(hits.values()))
    if not artist['qid']:raise ValueError('Existing creator authority is missing')
    agrees=0
    for field in ['birth_year','death_year']:
     value=maker.get(field) or ''
     if re.fullmatch(r'\d{4}',value) and artist[field] is not None:
      if int(value)!=artist[field]:raise ValueError('Source maker biography conflicts with catalogue identity')
      agrees+=1
    if not agrees:raise ValueError('No museum biography year independently corroborates creator match')
    lo,hi,precision,display=m.date_parts(o);typ={'Painting':'painting','Drawing':'drawing','Print':'print'}.get(o['type'])
    if not typ:raise ValueError('Unselected source object type')
    c={'external_id':oid,'accession_number':o['accession_number'],'title':o['title'],'work_type':typ,'artist':artist['display_name'],'aliases':artist['aliases'],'artist_authority':str(maker['id']),'roles':['primary'],'creation_year_start':lo,'creation_year_end':hi,'date_precision':precision,'date_display':display};m.source_match(c,o)
    rows.append({'source_object_id':oid,'artist':artist,'source_artist_id':str(maker['id']),**{k:c[k] for k in ('title','work_type','accession_number','creation_year_start','creation_year_end','date_precision','date_display')},'object':o,'metadata_capture':receipt})
   except ValueError as e:held.append({'source_object_id':oid,'reason':str(e)})
 rows.sort(key=lambda c:(not c['artist']['popular'],c['work_type']!='painting',c['artist']['display_name'],c['source_object_id']));report={'at':core.now(),'source_records_examined':len(seen),'selected_source_leads':len(rows),'popular':sum(c['artist']['popular'] for c in rows),'types':dict(collections.Counter(c['work_type'] for c in rows)),'held':dict(collections.Counter(c['reason'] for c in held)),**counts,'note':'No image downloads. Exact source accessioned ownership, primary artist name/alias with corroborating life date, 1000–1970 source creation interval, and exact CC0 primary image required. Multipart objects remain held.'};core.save_new(r/'source-leads.json',rows);core.save_new(r/'selection-held.json',held);core.save_new(r/'selection-report.json',report);print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)
if __name__=='__main__':main()
