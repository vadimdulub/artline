#!/usr/bin/env python3
"""Next bounded Walters image selection, excluding the prior reviewed records."""
import argparse,importlib.util,json,re
from pathlib import Path

s=importlib.util.spec_from_file_location('walters',Path(__file__).with_name('recover-local-walters-native-images-20261006.py'))
w=importlib.util.module_from_spec(s);s.loader.exec_module(w)
PREVIOUS=w.RUN
EXCLUDE_RUNS=[PREVIOUS]
RUN=w.core.ROOT/'docs/research/local-walters-followup-images-20261006'
w.RUN=RUN;w.base.RUN=RUN

def query_candidates(limit,exclude_runs):
 excluded=list({c['artwork_id'] for previous in exclude_runs for c in json.loads((previous/'candidates.json').read_bytes())['candidates']})
 with w.base.connect() as db:
  rows=db.execute('''SELECT a.id::text artwork_id,a.slug,a.title,a.alternate_title,a.creation_year_start,a.creation_year_end,a.date_display,a.date_precision,a.work_type,a.object_form,a.unlinked_creator_label,a.accession_number,to_jsonb(a) before_record,i.slug institution_slug,i.name museum,i.id::text institution_id,e.scheme,e.external_id,e.source_id::text,e.canonical_url page,
   ARRAY(SELECT aa.attribution_role FROM artwork_artists aa WHERE aa.artwork_id=a.id ORDER BY aa.artist_id) roles,
   COALESCE((SELECT jsonb_agg(jsonb_build_object('name',ar.display_name,'birth',ar.birth_year,'death',ar.death_year) ORDER BY ar.id) FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=a.id),'[]') creators,
   COALESCE((SELECT jsonb_agg(to_jsonb(aa) ORDER BY aa.artist_id) FROM artwork_artists aa WHERE aa.artwork_id=a.id),'[]') creator_links,
   (SELECT jsonb_agg(to_jsonb(ei) ORDER BY ei.id) FROM external_identifiers ei WHERE ei.entity_type='artwork' AND ei.entity_id=a.id) identifiers
   FROM artworks a JOIN institutions i ON i.id=a.current_institution_id JOIN external_identifiers e ON e.entity_type='artwork' AND e.entity_id=a.id AND e.scheme='walters-object'
   WHERE a.current_institution_id=%s AND a.primary_media_id IS NULL AND a.status='review' AND e.source_id IS NOT NULL
   AND NOT(a.id=ANY(%s::uuid[])) AND a.work_type IN ('painting','watercolor','fresco')
   AND artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision)='eligible' AND artline_has_selection_evidence(a.id)
   AND a.creation_year_end-a.creation_year_start<=20
   ORDER BY a.creation_year_start,a.id LIMIT %s''',(w.IID,excluded,limit)).fetchall()
  baseline=db.execute('SELECT count(*) total,count(*) FILTER(WHERE primary_media_id IS NULL) missing FROM artworks').fetchone()
 for c in rows:c.update(provider=w.PROVIDER,artist='; '.join(x['name'] for x in c['creators']) or c['unlinked_creator_label'],target_ids={'local':c['artwork_id']})
 return dict(at=w.core.now(),baseline=baseline,excluded_previous_runs=[str(previous.relative_to(w.core.ROOT)) for previous in exclude_runs],candidates=rows)

def select(limit):
 if (RUN/'candidates.json').exists():return
 result=query_candidates(limit,EXCLUDE_RUNS);w.core.save_new(RUN/'candidates.json',result);print('Selected',len(result['candidates']),'existing missing-image records',flush=True)
w.select=select

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['research','prepare','apply','verify']);p.add_argument('--limit',type=int,default=30)
 p.add_argument('--run-name',default=RUN.name);p.add_argument('--exclude-run',type=Path,action='append',default=[]);a=p.parse_args()
 if not re.fullmatch(r'local-walters-[a-z0-9-]+-20261006',a.run_name):raise ValueError('Invalid operation directory')
 RUN=w.core.ROOT/'docs/research'/a.run_name;w.RUN=RUN;w.base.RUN=RUN
 EXCLUDE_RUNS.extend(path.resolve() for path in a.exclude_run)
 if a.phase=='research':w.research(a.limit)
 elif a.phase=='prepare':
  for path in (RUN/'selected'/w.PROVIDER).glob('*.json'):w.verify_image(json.loads(path.read_bytes()))
  w.base.prepare(w.PROVIDER)
 elif a.phase=='apply':w.base.apply()
 else:
  for im in w.base.prepared():w.verify_image(im)
  w.base.verify()
  w.verify_rights_and_holds()
