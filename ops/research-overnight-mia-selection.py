#!/usr/bin/env python3
"""Choose new Mia metadata records before images, using existing painter identities."""
import argparse,collections,importlib.util,json,re
from pathlib import Path
s=importlib.util.spec_from_file_location('mia',Path(__file__).with_name('overnight-mia-images.py'));mia=importlib.util.module_from_spec(s);s.loader.exec_module(mia);core=mia.core

def main():
 p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);a=p.parse_args();r=a.run
 assert not (r/'source-leads.json').exists(),'Pinned source selection already exists'
 with mia.ro('postgres://localhost/artline') as db:
  people=db.execute("""SELECT a.id::text,a.slug,a.display_name,a.birth_year,a.death_year,
   (SELECT e.external_id FROM external_identifiers e WHERE e.entity_type='artist' AND e.entity_id=a.id AND e.scheme='wikidata') qid,
   ARRAY(SELECT al.alias FROM artist_aliases al WHERE al.artist_id=a.id) aliases,
   EXISTS(SELECT 1 FROM artist_discovery_selection d WHERE d.artist_id=a.id AND d.is_popular) popular FROM artists a WHERE a.status<>'archived'""").fetchall()
  existing={x['external_id'] for x in db.execute("SELECT external_id FROM external_identifiers WHERE entity_type='artwork' AND scheme='mia-object'").fetchall()}
 index=collections.defaultdict(dict)
 for artist in people:
  for name in [artist['display_name']]+artist['aliases']:index[mia.norm(name)][artist['id']]=artist
 seen=set();selected=[];held=[];counts=collections.Counter()
 for typ in ['Paintings','Drawings','Prints']:
  report=json.loads((r/(typ.lower()+'-metadata.json')).read_text());assert report['images_requested']==0
  for row in report['records']:
   o=row['object'];oid=str(o['id'])
   if oid in seen:continue
   seen.add(oid)
   if oid in existing:counts['existing_native_object']+=1;continue
   try:
    work_type={'Paintings':'painting','Drawings':'drawing','Prints':'print'}.get(o.get('classification','').strip())
    if not work_type:raise ValueError('Mixed or unsupported authoritative classification')
    hits=index[mia.norm(mia.creator_name(o.get('artist'),work_type))]
    if len(hits)!=1:raise ValueError('Creator not uniquely matched to an existing painter; retained for review')
    artist=next(iter(hits.values()))
    if not artist['qid']:raise ValueError('Existing painter has no canonical authority')
    life=re.search(r'\b(\d{4})\s*[-–—]\s*(\d{4})\b',o.get('life_date') or '')
    if life and any(actual is not None and actual!=int(source) for actual,source in zip((artist['birth_year'],artist['death_year']),(life[1],life[2]))):raise ValueError('Source creator biography conflicts with existing identity')
    lo,hi,precision=mia.helpers.date_parts(o.get('dated') or '')
    if lo!=hi and (lo,hi)==(artist['birth_year'],artist['death_year']):raise ValueError('Creation interval repeats creator lifespan')
    c={'external_id':oid,'title':o['title'],'work_type':work_type,'accession_number':o.get('accession_number'),'date_display':o['dated'],'creation_year_start':lo,'creation_year_end':hi,'date_precision':precision,'artist':artist['display_name'],'aliases':artist['aliases'],'roles':['primary']}
    mia.source_match(c,o)
    selected.append({'source_object_id':oid,**{k:c[k] for k in ('title','work_type','accession_number','date_display','creation_year_start','creation_year_end','date_precision')},'artist':artist,'object':o,'metadata_capture':row['metadata_capture']})
   except ValueError as e:held.append({'source_object_id':oid,'reason':str(e)})
 selected.sort(key=lambda c:(not c['artist']['popular'],c['work_type']!='painting',c['artist']['display_name'],c['source_object_id']))
 core.save_new(r/'source-leads.json',selected);core.save_new(r/'selection-held.json',held)
 report={'at':core.now(),'source_objects_examined':len(seen),'selected_metadata_leads':len(selected),'popular':sum(c['artist']['popular'] for c in selected),'by_type':dict(collections.Counter(c['work_type'] for c in selected)),'held':dict(collections.Counter(c['reason'] for c in held)),**counts,'policy':'Current museum metadata precedes images. Known unique creator names/aliases, non-conflicting biographies, bounded creation dates, exact PDM source media. Mixed classifications and qualified or unmapped creators retained for review. This bounded source search does not claim the full museum catalogue.'}
 core.save_new(r/'source-lead-report.json',report);print(json.dumps(report,indent=2),flush=True)
if __name__=='__main__':main()
