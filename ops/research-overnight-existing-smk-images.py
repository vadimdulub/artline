#!/usr/bin/env python3
"""Select image gaps in existing SMK works against current museum evidence."""
import argparse,collections,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('selection',Path(__file__).with_name('import-overnight-smk-selection.py'));selection=importlib.util.module_from_spec(s);s.loader.exec_module(selection);smk=selection.smk;core=smk.core

def main():
 p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--reference',type=Path,required=True);a=p.parse_args();r=a.run;r.mkdir(parents=True,exist_ok=True);assert not (r/'candidates.json').exists()
 cap=json.loads((a.reference/'capture.json').read_text());assert cap['complete'];queued=set()
 for path in r.parent.glob('*/candidates.json'):
  events=core.latest_events(path.parent)
  for c in json.loads(path.read_text()).get('candidates',[]):
   # A prior API result lacking image evidence is not evidence that the
   # current explicit museum record lacks it. Revalidate those old holds.
   if events.get(c['artwork_id'],{}).get('outcome') not in ('no_explicit_open_image','failed','manual_review'):queued.add(c['artwork_id'])
 with smk.ro('postgres://localhost/artline') as db:
  rows=db.execute(smk.QUERY+" AND a.primary_media_id IS NULL AND artline_has_selection_evidence(a.id) ORDER BY popular DESC,a.id").fetchall()
  artists=db.execute("""SELECT a.id::text,a.slug,a.display_name,a.birth_year,a.death_year,e.external_id,
   (SELECT q.external_id FROM external_identifiers q WHERE q.entity_type='artist' AND q.entity_id=a.id AND q.scheme='wikidata') qid
   FROM artists a JOIN external_identifiers e ON e.entity_type='artist' AND e.entity_id=a.id WHERE e.scheme='smk-person' AND a.status<>'archived'""").fetchall()
  iid=db.execute('SELECT id::text FROM institutions WHERE slug=%s',(smk.SLUG,)).fetchone()['id']
 people=collections.defaultdict(list)
 for x in artists:people[x['external_id']].append(x)
 gaps=collections.defaultdict(list)
 for row in rows:
  if row['artwork_id'] not in queued:gaps[row['external_id']].append(row)
 selected=[];held=[];seen=set()
 for receipt in cap['pages']:
  raw=(a.reference/'metadata'/(core.sha(receipt['url'].encode())+'.json')).read_bytes();assert core.sha(raw)==receipt['sha256']
  for o in json.loads(raw)['items']:
   oid=o['object_number']
   if oid not in gaps:continue
   seen.add(oid)
   try:
    if oid in cap['duplicate_accession_numbers'] or len(gaps[oid])!=1:raise ValueError('Ambiguous native object identity')
    row=gaps[oid][0];maker=smk.primary_maker(o);hits=people[maker['creator_lref']]
    if len(hits)!=1 or row['artist_slugs']!=[hits[0]['slug']] or row['roles']!=['primary']:raise ValueError('Exact current museum creator authority is not linked')
    artist=dict(hits[0],popular=row['popular'])
    for source_key,db_key in [('creator_date_of_birth','birth_year'),('creator_date_of_death','death_year')]:
     value=maker.get(source_key,'')
     if value[:4].isdigit() and artist[db_key] is not None and int(value[:4])!=artist[db_key]:raise ValueError('Current creator life dates conflict')
    if row['current_institution_id']!=iid:raise ValueError('Current holding requires review')
    lead={k:row[k] for k in ('title','work_type','accession_number','creation_year_start','creation_year_end','date_precision','date_display')}
    lead.update(source_object_id=oid,source_api_id=o['id'],artist=artist,object=o,metadata_capture=receipt)
    c=selection.candidate(lead,a.reference)
    c.update(artwork_id=row['artwork_id'],slug=row['slug'],target_ids={'local':row['artwork_id']},institution_ids={'local':iid},source_id=row['source_id'])
    smk.source_match(c,o);selected.append(c)
   except ValueError as exc:held.append({'source_object_id':oid,'reason':str(exc)})
 selected.sort(key=lambda c:(not c['popular'],c['work_type']!='painting',c['artist'],c['external_id']))
 backup=Path.home()/'Library/Application Support/Artline/backups/overnight-images-20260915'/r.name
 core.save_new(backup/'local-selected-before.json',{'at':core.now(),'rows':[x for x in rows if x['artwork_id'] in {c['artwork_id'] for c in selected}]})
 for c in selected:core.save_new(r/'selected/night-smk'/(c['artwork_id']+'.json'),c)
 core.save_new(r/'candidates.json',{'created_at':core.now(),'candidates':selected})
 core.save_new(r/'held.json',held)
 report={'at':core.now(),'existing_unqueued_gaps':len(gaps),'present_in_current_open_image_capture':len(seen),'selected':len(selected),'popular':sum(c['popular'] for c in selected),'by_type':dict(collections.Counter(c['work_type'] for c in selected)),'held':dict(collections.Counter(c['reason'] for c in held)),'policy':'Images only for exact existing native identities, current primary creator authorities, matching source title/type/date, explicit image PDM and holding evidence. No artwork metadata changed and no new work created.'}
 core.save_new(r/'selection-report.json',report);print(json.dumps(report,indent=2),flush=True)
if __name__=='__main__':main()
