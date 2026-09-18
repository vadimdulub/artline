#!/usr/bin/env python3
"""Select missing source-supported SMK objects, preserving date/identity holds."""
import argparse,collections,importlib.util,json,re
from pathlib import Path
s=importlib.util.spec_from_file_location('smk',Path(__file__).with_name('overnight-smk-selected-images.py'));smk=importlib.util.module_from_spec(s);s.loader.exec_module(smk);core=smk.core

def main():
 p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--reference',type=Path);p.add_argument('--allow-native-authority',action='store_true');p.add_argument('--new-artist-plan',type=Path);a=p.parse_args();r=a.run;r.mkdir(parents=True,exist_ok=True);reference=a.reference or r;capture=json.loads((reference/'capture.json').read_text());assert capture['complete'] and capture['images_requested']==0
 allowed={w['source_object_id'] for c in json.loads(a.new_artist_plan.read_text())['records'] for w in c['selected_source_objects']} if a.new_artist_plan else None
 with smk.ro('postgres://localhost/artline') as db:
  people=db.execute("""SELECT a.id::text,a.slug,a.display_name,a.birth_year,a.death_year,e.external_id,
   (SELECT q.external_id FROM external_identifiers q WHERE q.entity_type='artist' AND q.entity_id=a.id AND q.scheme='wikidata') qid,
   EXISTS(SELECT 1 FROM artist_discovery_selection d WHERE d.artist_id=a.id AND d.is_popular) popular
   FROM artists a JOIN external_identifiers e ON e.entity_type='artist' AND e.entity_id=a.id AND e.scheme='smk-person' WHERE a.status<>'archived'""").fetchall()
  existing={x['external_id'] for x in db.execute("SELECT external_id FROM external_identifiers WHERE entity_type='artwork' AND scheme=ANY(%s)",([smk.SCHEME,'smk-object'],)).fetchall()}
 index=collections.defaultdict(list)
 for artist in people:index[artist['external_id']].append(artist)
 rows=[];held=[];counts=collections.Counter();seen=set()
 for receipt in capture['pages']:
  path=reference/'metadata'/(core.sha(receipt['url'].encode())+'.json');raw=path.read_bytes();assert core.sha(raw)==receipt['sha256'];batch=json.loads(raw)
  for o in batch['items']:
   oid=o['object_number'];source_id=o['id'];assert source_id not in seen;seen.add(source_id)
   if allowed is not None and oid not in allowed:counts['outside_selected_new_artist_objects']+=1;continue
   if oid in existing:counts['existing_native_object']+=1;continue
   try:
    if oid in capture['duplicate_accession_numbers']:raise ValueError('Accession shared by distinct source object IDs; physical-object review needed')
    if re.search(r'\b(verso|recto)\b',oid,re.I):raise ValueError('Multipart/side identity needs relationship review')
    typ=smk.work_type(o);maker=smk.primary_maker(o);hits=index[maker['creator_lref']]
    if len(hits)!=1:raise ValueError('Source maker authority is not uniquely linked to an existing painter')
    artist=hits[0]
    if not artist['qid'] and not a.allow_native_authority:raise ValueError('Existing painter has no canonical Wikidata authority')
    for source_key,db_key in [('creator_date_of_birth','birth_year'),('creator_date_of_death','death_year')]:
     value=maker.get(source_key,'')
     if re.match(r'^\d{4}-',value) and artist[db_key] is not None and int(value[:4])!=artist[db_key]:raise ValueError('Source maker biography conflicts with existing identity')
    lo,hi,precision,display=smk.date_parts(o)
    titles=o.get('titles',[])
    chosen=next((t['title'] for t in titles if t.get('language') in ('engelsk','English','en') and t.get('title')),None) or next((t['title'] for t in titles if t.get('title')),None)
    if not chosen:raise ValueError('Source title is absent')
    c={'external_id':oid,'source_api_id':source_id,'accession_number':oid,'title':chosen,'work_type':typ,'roles':['primary'],'artist_authority':artist['external_id'],'creation_year_start':lo,'creation_year_end':hi,'date_precision':precision,'date_display':display}
    smk.source_match(c,o)
    rows.append({'source_object_id':oid,**{k:c[k] for k in ('source_api_id','title','work_type','accession_number','creation_year_start','creation_year_end','date_precision','date_display')},'artist':artist,'object':o,'metadata_capture':receipt})
   except ValueError as e:held.append({'source_object_id':oid,'source_api_id':source_id,'reason':str(e)})
 rows.sort(key=lambda c:(not c['artist']['popular'],c['work_type']!='painting',c['artist']['display_name'],c['source_object_id']))
 report={'at':core.now(),'source_objects_examined':len(seen),'selected_source_leads':len(rows),'popular':sum(x['artist']['popular'] for x in rows),'types':dict(collections.Counter(x['work_type'] for x in rows)),'held':dict(collections.Counter(x['reason'] for x in held)),**counts,'note':'No images downloaded. Exact existing native maker IDs and source biographies checked; activity-derived and undated creation ranges held; repeated accessions and side identities held. Physical works remain distinct.'}
 core.save_new(r/'source-leads.json',rows);core.save_new(r/'selection-held.json',held);core.save_new(r/'selection-report.json',report);print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)
if __name__=='__main__':main()
