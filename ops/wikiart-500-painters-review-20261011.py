#!/usr/bin/env python3
"""Research orchestration and read-only quality checks for 500 painters."""
import importlib.util,sys,time,collections,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def module(name,file):
 sp=importlib.util.spec_from_file_location(name,ROOT/file);v=importlib.util.module_from_spec(sp);sp.loader.exec_module(v);return v
d=module('twenty_delivery','ops/wikiart-500-painters-delivery-20261011.py');b=d.b;m=d.m;s=d.s;r=d.r;q=d.q;RUN=d.RUN;BACKUP=d.BACKUP
x=module('previous_helpers','ops/run-random-200-round6-20261007.py')
x.d=d;x.s=s;x.m=m;x.r=r;x.q=q;x.RUN=RUN;x.BACKUP=BACKUP;x.PRIOR_RUNS=[(ROOT/entry['path']).parent for entry in r.load(RUN/'sampling-frame.json.gz')['prior_cohorts']]
v=module('previous_quality','ops/review-random-200-painters-round6-20261007.py');v.x=x;v.r=r;v.RUN=RUN

def pipeline():
 while not (RUN/'indexes-summary.json').exists():time.sleep(10)
 x.index_gaps()
 while not (RUN/'translations-summary.json').exists():time.sleep(10)
 module('index_only_review','ops/wikiart-500-painters-index-only-20261011.py').main()
 previous_selected=-1
 while True:
  finished=(RUN/'pages-summary.json').exists()
  if finished:x.retry_pages()
  s.select()
  selected=len(list((RUN/'selections').glob('*.json.gz')))
  if selected!=previous_selected or finished:
   d.prepare();d.audits();d.sheets();previous_selected=selected
  m.status('pipeline',selected_artists=selected,research_done=finished)
  if finished and selected==500:
   print('All 500 selections and image preparations complete; visual and source-quality review pending.',flush=True);return
  time.sleep(30)

def quality_scan(final=False):
 v.scan(False)
 title_collisions(final)
 result=r.load(RUN/'progress/quality-candidates.json');known={row['artwork_id'] for row in result['title_review_candidates']}
 collision_path=RUN/('supplemental-title-collisions.json' if final else 'progress/title-collisions.json')
 collisions={row['artwork_id']:row for row in r.load(collision_path)['matches']}
 for plan,pin in d.plans():
  for row in plan['rows']:
   if row['action'] not in ['create','existing'] or row['artwork_id'] in known:continue
   title=row['title'];date=row['page'].get('date');reasons=[]
   if re.search(r'\b(19[7-9]\d|20\d\d)\b',title) and not date:reasons.append('Undated work title mentions a potentially post-1970 event or edition')
   if s.normalized(title) in ['main image','image','photo','picture','artwork','acrylic on canvas','oil on canvas']:reasons.append('Generic source title needs object identity review')
   if date and date['creation_year_end']>1970:reasons.append('Creation range crosses the 1970 catalogue cutoff')
   if row['artwork_id'] in collisions:reasons.append('Possible existing object from title normalization or a locale-independent WikiArt source-ID citation; see supplemental collision evidence')
   if reasons:
    result['title_review_candidates'].append(dict(artist=plan['artist']['display_name'],artist_id=plan['artist']['id'],artwork_id=row['artwork_id'],title=title,action=row['action'],source_url=row['source_url'],date=date,source_fields=row['page']['fields'],flags=reasons));known.add(row['artwork_id'])
 if final:
  assert result['painters']==len(m.cohort())
  r.save(RUN/'quality-final-candidates.json',result)
 else:m.status('quality-candidates',**{k:value for k,value in result.items() if k not in ['at','phase']})
 print('Additional source-title/date screening:',len(result['title_review_candidates']),'total title candidates',flush=True)
def quality():quality_scan(True)
def quality_progress():quality_scan(False)
def components():
 rows=[]
 for plan,pin in d.plans():
  for row in plan['rows']:
   if row['action'] in ['create','existing'] and (re.search(r'\b(wing|wings|panel|panels|triptych|diptych|polyptych|altarpiece|shrine|reliquary|closed|left side|right side|central section|central part|rear|reverse|recto|verso|predella|detail|fragment)\b',row['title'],re.I) or re.search(r'\b(triptych|diptych|polyptych|altarpiece|altar|shrine|reliquary)\b',row['page']['fields'].get('Series',''),re.I)):
    rows.append(dict(artist=plan['artist']['display_name'],artwork_id=row['artwork_id'],title=row['title'],source_url=row['source_url'],action=row['action'],source_fields=row['page']['fields']))
 m.status('component-candidates',painters=len(list(d.plans())),rows=rows)
 print('Component/view title candidates:',len(rows),flush=True)
def article_title_key(value):
 value=s.normalized(value)
 return re.sub(r'^(?:the|a|an|le|la|les|l|un|une|el|los|las|il|lo|gli|der|die|das|ein|eine|het)\s+','',value)
def title_collisions(final=False):
 plans=list(d.plans());matches=[]
 for data,pin in plans:
  baseline=r.load(RUN/'catalogue-works'/(data['artist']['id']+'.json.gz'));lookup=collections.defaultdict(dict);cited_ids=collections.defaultdict(dict)
  for old in baseline:
   for citation in old['citations']:
    source_id=citation.get('source_record_id') or ''
    if (citation.get('source_url') or '').startswith('https://www.wikiart.org/') and re.fullmatch('[0-9a-f]{24}',source_id):cited_ids[source_id][old['id']]=old
   for value in [old['title'],old.get('alternate_title')]:
    key=article_title_key(value)
    if key:lookup[key][old['id']]=old
  for row in data['rows']:
   if row['action']!='create':continue
   names=row['page'].get('identity_titles',[])+[row['title']]
   candidates={old['id']:old for name in names for old in lookup.get(article_title_key(name),{}).values() if s.indistinct_dates(row['work'],old)}
   exact=cited_ids.get(row['source_id'],{});candidates.update(exact)
   if candidates:matches.append(dict(artist=data['artist']['display_name'],artwork_id=row['artwork_id'],title=row['title'],source_url=row['source_url'],date=row['page'].get('date'),exact_cited_source_id_matches=sorted(exact),candidate_records=[{k:old.get(k) for k in ['id','title','alternate_title','date_display','work_type','medium_text','dimensions_text','existing_image_source']}for old in candidates.values()]))
 result=dict(at=r.now(),painters=len(plans),matches=matches,held_artwork_ids={row['artwork_id']:'An existing artist-scoped record has a compatible article-normalized title or cites this exact WikiArt source ID in another language. Preserve the possible object/version collision without creating a duplicate.' for row in matches},scope='Supplemental read-only article-insensitive title and locale-independent source-ID citation comparison against each artist’s saved production baseline. Holds are not asserted duplicate mergers.')
 if final:
  assert len(plans)==len(m.cohort());r.save(RUN/'supplemental-title-collisions.json',result)
 else:m.status('title-collisions',**{k:value for k,value in result.items()if k!='at'})
 print('Article-insensitive title collisions:',len(matches),'candidate holds',flush=True)
def title_collisions_final():title_collisions(True)
def gaps():x.index_gaps()
def retries():x.retry_pages()
def cross():
 # Two excluded low-count cohorts delivered metadata only, with no image plans.
 metadata_only={'low-count-200-painters-20261008','low-count-200-painters-round2-20261009'}
 original=x.PRIOR_RUNS
 for folder in original:
  if folder.name in metadata_only:
   assert 'no new images were uploaded or attached' in (folder/'README.md').read_text().lower() or 'no catalogue images were uploaded or attached' in (folder/'README.md').read_text().lower()
 x.PRIOR_RUNS=[folder for folder in original if folder.name not in metadata_only]
 x.cross_creator_audit()
 r.save(RUN/'cross-creator-comparison-scope.json',{'at':r.now(),'prior_cohorts_excluded_from_artist_sample':len(original),'prior_image_cohorts_compared':[str(p.relative_to(ROOT)) for p in x.PRIOR_RUNS],'metadata_only_cohorts_without_delivered_images':sorted(metadata_only)})
def preflight():module('round2_checks','ops/wikiart-500-painters-checks-20261011.py').preflight()
if __name__=='__main__':globals()[sys.argv[1]]()
