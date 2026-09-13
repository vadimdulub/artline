#!/usr/bin/env python3
"""Bounded read-only before/after verification of the pinned round-two plan."""
import argparse,collections,hashlib,importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
s=importlib.util.spec_from_file_location('writer',ROOT/'ops/apply-expanded-round2.py');writer=importlib.util.module_from_spec(s);s.loader.exec_module(writer)
common=writer.common;q=writer.q

def audit(directory,label,before):
 manifest,plan=writer.load(directory);by_rid={r['rid']:r for r in plan};data=[]
 for start in range(0,len(plan),250):
  keys=[{'rid':r['rid'],'work':r['slug'],'artist':r['artist']['slug']} for r in plan[start:start+250]]
  ledger="0" if before else "(SELECT count(*) FROM research_artwork_enrichments e WHERE e.plan_sha256="+q(manifest['sha256'])+" AND e.research_record_id=p.k->>'rid' AND e.artwork_id=w.id AND e.artist_id=a.id)"
  sql="""WITH p AS MATERIALIZED(SELECT value k FROM jsonb_array_elements("""+q(json.dumps(keys))+"""::jsonb))
  SELECT jsonb_build_object('rid',p.k->>'rid','work',w.slug,'artist',a.slug,
   'status',w.status,'candidate',w.research_candidate,'label',w.unlinked_creator_label,
   'metadata',jsonb_build_object('type',w.work_type,'date_display',w.date_display,'first',w.creation_year_start,'last',w.creation_year_end,'precision',w.date_precision,'medium',w.medium_text,'dimensions',w.dimensions_text,'accession',w.accession_number),
   'stable_work_hash',md5((to_jsonb(w)-ARRAY['id','updated_at','created_at','updated_by','revision','primary_media_id','unlinked_creator_label','work_type','date_display','creation_year_start','creation_year_end','date_precision','medium_text','dimensions_text','accession_number'])::text),
   'artist_hash',md5((to_jsonb(a)-ARRAY['id','created_at','updated_at','revision','portrait_media_id'])::text),
   'artist_metadata',CASE WHEN a.id IS NULL THEN NULL ELSE jsonb_build_object('birth',a.birth_year,'death',a.death_year,'status',a.status,'basis',a.timeline_basis,'start',a.timeline_start_year,'end',a.timeline_end_year) END,
   'links',coalesce((SELECT jsonb_agg(jsonb_build_object('artist',x.slug,'role',aa.attribution_role) ORDER BY x.slug) FROM artwork_artists aa JOIN artists x ON x.id=aa.artist_id WHERE aa.artwork_id=w.id),'[]'::jsonb),
   'citations',(SELECT count(*) FROM citations c WHERE c.entity_type='artwork' AND c.entity_id=w.id AND c.field_name='round2_museum_research' AND c.source_record_id=p.k->>'rid'),
   'ledger',"""+ledger+""",
   'scope',artline_creation_scope(w.creation_year_start,w.creation_year_end,w.date_precision))
   FROM p JOIN artworks w ON w.slug=p.k->>'work' LEFT JOIN artists a ON a.slug=p.k->>'artist' ORDER BY p.k->>'rid'"""
  part=common.query(sql);assert len(part)==len(keys),'Missing audit records';data.extend(part)
 data.sort(key=lambda r:r['rid'])
 previous={} if before else {r['rid']:r for r in json.loads((directory/(label+'-before-rows.json')).read_text())}
 for row in data:
  r=by_rid[row['rid']];a=r['artist'];patch=r['patch']
  assert row['status']=='review' and row['candidate'],('visibility changed',r['rid'])
  assert row['scope']!='excluded',('cutoff',r['rid'])
  if before:
   assert row['links']==[] and row['label']==r['label'] and row['citations']==0,r['rid']
   assert (row['artist'] is None)==a['new'],('artist precondition',r['rid'])
  else:
   old=previous[row['rid']]
   assert row['label'] is None and row['links']==[{'artist':a['slug'],'role':'primary'}],('attribution',r['rid'])
   assert row['citations']==row['ledger']==1,('provenance',r['rid'])
   assert row['stable_work_hash']==old['stable_work_hash'],('unrelated artwork metadata',r['rid'])
   expected=old['metadata'] if patch is None else {'type':patch['type'],'date_display':patch['date']['display'],'first':patch['date']['first'],'last':patch['date']['last'],'precision':patch['date']['precision'],'medium':patch['medium'] or None,'dimensions':patch['dimensions'] or None,'accession':patch['accession'] or None}
   assert row['metadata']==expected,('artwork metadata',r['rid'],row['metadata'],expected)
   if a['new']:
    assert row['artist_metadata']=={'birth':a['birth_year'],'death':a['death_year'],'status':'review','basis':'life','start':a['birth_year'],'end':a['death_year']},('new artist',r['rid'])
   else:assert row['artist_hash']==old['artist_hash'],('existing artist changed',r['rid'])
 global_counts=common.query("SELECT json_build_object('artworks', (SELECT count(*) FROM artworks),'artists',(SELECT count(*) FROM artists),'research_records',(SELECT count(*) FROM research_records),'unlinked_candidates',(SELECT count(*) FROM artworks w WHERE w.research_candidate AND w.status='review' AND NOT EXISTS(SELECT 1 FROM artwork_artists aa WHERE aa.artwork_id=w.id)))")[0]
 if not before:
  old=json.loads((directory/(label+'-before.json')).read_text())['global_counts']
  assert global_counts['artworks']==old['artworks'] and global_counts['research_records']==old['research_records'],'Unexpected objects/research changes'
  assert global_counts['artists']==old['artists']+manifest['new_artist_count'],'Unexpected painter count'
  assert global_counts['unlinked_candidates']==old['unlinked_candidates']-len(plan)
 summary={'plan_sha256':manifest['sha256'],'works':len(data),'new_painters':manifest['new_artist_count'],'existing_painters':manifest['existing_artist_count'],'metadata_enrichments':manifest['metadata_enrichments'],'global_counts':global_counts,'source_counts':dict(collections.Counter(r['source'] for r in plan)),'date_scopes':dict(collections.Counter(r['scope'] for r in data)),'unknown_types':sum(r['metadata']['type']=='unknown' for r in data),'rows_sha256':hashlib.sha256(json.dumps(data,sort_keys=True,ensure_ascii=False).encode()).hexdigest(),'integrity_passed':True}
 suffix='before' if before else 'verification'
 common.save(directory/(label+'-'+suffix+'-rows.json'),data);common.save(directory/(label+'-'+suffix+'.json'),summary)
 print(json.dumps(summary),flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--dir',type=Path,required=True);p.add_argument('--label',required=True);p.add_argument('--before',action='store_true');a=p.parse_args();audit(a.dir,a.label,a.before)
