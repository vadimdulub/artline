#!/usr/bin/env python3
"""Guarded country-round planning, application and read-only verification.

Fresh aliases and museum person IDs prevent duplicate painters. Matching an
artwork by title alone is deliberately held for object-level research.
"""
import argparse,collections,concurrent.futures,importlib.util,json,re
from pathlib import Path
import requests

def module(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
m=module('writer',Path(__file__).with_name('apply-wikimedia-catalogues.py'))
x=module('country',Path(__file__).with_name('research-country-rounds.py'))
f=module('identity',Path(__file__).with_name('reconcile-creators-followup.py'))
image_review=module('image_review',Path(__file__).with_name('prepare-wikimedia-catalogue-images.py'))
BACKUPS=Path('/Users/vadimdulub/Library/Application Support/Artline/backups')/x.SESSION_NAME
SITE='https://artline-web-lpuqqlugnq-ew.a.run.app'

def configure(code,number):
 m.r.RUN=x.BASE/code/f'round-{number:02d}'/'delivery';m.r.BACKUPS=BACKUPS
 m.SOURCE_SLUG='overnight-country-artworks-20260913';m.SOURCE_NAME='Country research — museum-connected artworks and verified painter affiliations'
 m.IMAGE_SOURCE_SLUG='overnight-country-images-20260913';m.VERSION='country-research-v1'
 if x.SESSION_NAME!='overnight-countries-20260913':
  m.SOURCE_SLUG=x.SESSION_NAME+'-artworks';m.IMAGE_SOURCE_SLUG=x.SESSION_NAME+'-images';m.VERSION=x.SESSION_NAME+'-v1'
 m.choose_existing=choose_existing
 if x.SESSION_NAME!='overnight-countries-20260913':
  base={'germany-second-pass':20000,'primary-identity-recovery':30000}.get(x.CAMPAIGN,10000)
  return base+100*list(x.COUNTRIES).index(code)+number
 return {'':0,'greek-historical':200,'france':300,'italy':400,'spain':500,'germany':600,'austria':700,'belgium':900,'finland':1100,'portugal':1300}[x.CAMPAIGN]+{'NL':0,'GR':20,'RU':40,'FR':60,'IT':80,'ES':100,'DE':120,'AT':140,'BE':160,'FI':180,'PT':200}[code]+number

def choose_existing(record,rows):
 accessions={m.accession_key(v) for v in m.r.values(record['entity'],'P217') if isinstance(v,str)}
 if (record.get('primary_museum_review') or record.get('primary_metadata_review',{}).get('override',{}).get('accession')) and record.get('accession'):accessions.add(m.accession_key(record['accession']))
 exact=[r for r in rows if r['accession_number'] and m.accession_key(r['accession_number']) in accessions]
 def same_creator(row):return record['creator_qid'] in row['creator_qids'] or bool({f.names.namekey(n) for n in row['creator_names']} & {f.names.namekey(n) for n in m.r.labels(record['creator_entity'])})
 if len(exact)>1:return None,'ambiguous_existing_accession'
 if exact:
  row=exact[0]
  if row['creator_qids'] and record['creator_qid'] not in row['creator_qids']:return None,'accession_has_conflicting_creator'
  if not same_creator(row):return None,'accession_creator_requires_reconciliation'
  d=record['date']
  if d['first'] is not None and row['creation_year_start'] is not None and (d['last']<row['creation_year_start'] or (row['creation_year_end'] is not None and d['first']>row['creation_year_end'])):return None,'accession_date_conflict'
  return row,None
 if any(same_creator(row) and m.work_titles(record)&{m.r.norm(row['title']),m.r.norm(row['alternate_title'] or '')} for row in rows):return None,'title_creator_match_needs_exact_object_evidence'
 return None,None

def artist_inventory(db):
 return db.execute("""SELECT a.id::text,a.slug,a.display_name,a.birth_year,a.death_year,a.entity_type,a.status,a.geography_review_state,a.revision,
 coalesce((SELECT jsonb_agg(alias) FROM artist_aliases WHERE artist_id=a.id),'[]') aliases,
 coalesce((SELECT jsonb_agg(jsonb_build_object('scheme',scheme,'id',external_id)) FROM external_identifiers WHERE entity_type='artist' AND entity_id=a.id),'[]') authorities,
 coalesce((SELECT jsonb_agg(country_code) FROM artist_countries WHERE artist_id=a.id AND relationship_type='cultural_affiliation'),'[]') countries
 FROM artists a""").fetchall()

def resolve(record,matcher):
 ce=record['creator_entity'];cq=record['creator_qid'];birth=m.r.year(ce,'P569');death=m.r.year(ce,'P570')
 reviewed_dates=record.get('primary_creator_review',{}).get('source',{}).get('artist_dates')
 if reviewed_dates:birth,death=reviewed_dates['birth'],reviewed_dates['death']
 names=m.r.labels(ce);p={'name':record['creator_label'],'wikidata':cq,'birth':birth,'death':death,'role':'artist'}
 if birth is not None and death is not None and not 0<=death-birth<=125:return None,'implausible_source_lifespan'
 direct=set(matcher.ids.get(('wikidata',cq),set()));proof=[]
 for prop,scheme in [('P2252','nga-constituent'),('P2174','moma-person'),('P2741','tate-person')]:
  for value in m.r.values(ce,prop):
   if not isinstance(value,str):continue
   ident=value.rsplit('-',1)[-1] if prop=='P2741' else value
   found=matcher.ids.get((scheme,ident),set());direct.update(found)
   if found:proof.append({'property':prop,'scheme':scheme,'id':ident})
 if direct:
  if len(direct)!=1:return None,'conflicting_existing_authority_ids'
  a=matcher.artists[next(iter(direct))]
  if a['status']=='archived' or a['entity_type']!='person':return None,'existing_artist_not_active_person'
  if any(p[k] is not None and a[k+'_year'] is not None and p[k]!=a[k+'_year'] for k in ('birth','death')):
   decision=record.get('primary_creator_review',{}).get('source',{}).get('existing_identity_decision',{})
   expected=decision.get('existing',{})
   if not (decision.get('kind')=='same_person_biography_conflict_preserved' and expected.get('slug')==a['slug'] and expected.get('wikidata')==cq and [a['birth_year'],a['death_year']]==expected.get('life') and any(e['scheme']==expected.get('museum_scheme') and e['id']==expected.get('museum_id') for e in a['authorities']) and any(e['scheme']=='wikidata' and e['id']==cq for e in a['authorities'])):return None,'authority_biography_conflict'
  old={e['id'] for e in a['authorities'] if e['scheme']=='wikidata'}
  if old and cq not in old:return None,'existing_wikidata_conflict'
  return {'artist':a,'basis':'exact_source_person_or_wikidata_identifier','museum_person_ids':proof},None
 found,reason=matcher.match(p,'wikidata',names)
 if found:return found,None
 collisions=set().union(*(matcher.names.get(f.names.namekey(n),set()) for n in names if n))
 if collisions:
  decision=record.get('primary_creator_review',{}).get('source',{}).get('existing_identity_decision',{})
  excluded=decision.get('excluded',[])
  interval=[birth,death] if birth is not None and death is not None else None
  # A documented activity before another person's birth also excludes that
  # namesake. Keep the medieval artist's unknown lifespan unknown.
  if birth is None and death is None and reviewed_dates and decision.get('primary_activity')==[reviewed_dates['active_start'],reviewed_dates['active_end']]:
   interval=decision['primary_activity']
  if decision.get('kind')=='distinct_named_person' and decision.get('primary_life')==[birth,death] and interval and len(excluded)==len(collisions):
   checked=set()
   for ident in collisions:
    a=matcher.artists[ident]
    if any(e['slug']==a['slug'] and e['life']==[a['birth_year'],a['death_year']] and e['wikidata']!=cq and any(v['scheme']=='wikidata' and v['id']==e['wikidata'] for v in a['authorities']) and a['birth_year'] is not None and a['death_year'] is not None and (a['death_year']<interval[0] or a['birth_year']>interval[1]) for e in excluded):checked.add(ident)
   if checked==collisions:return {'artist':None,'basis':'primary_sources_distinguish_all_colliding_namesakes'},None
  return None,'name_or_alias_collision_without_closed_identity_evidence'
 return {'artist':None,'basis':'new_named_human_no_existing_authority_or_alias_collision'},None

def vetted_object_urls(record,official=None):
 urls={'https://www.wikidata.org/wiki/'+record['qid']}
 if official and official.get('object_url'):urls.add(official['object_url'])
 # An unlinked CSV placeholder may already cite SMK's exact physical object
 # while lacking institution/creator FKs. Lookup these bounded accession URLs
 # before creating another row; conflicting records become a review hold.
 if record.get('collection',{}).get('qid')=='Q671384':
  accessions=[v for v in m.r.values(record['entity'],'P217') if isinstance(v,str)]
  for acc in accessions:
   if re.fullmatch(r'[A-Za-z0-9._/-]{2,80}',acc):
    urls.update({'https://open.smk.dk/artwork/image/'+acc,'https://open.smk.dk/en/artwork/image/'+acc,'https://collection.smk.dk/#/en/detail/'+acc,'https://api.smk.dk/api/v1/art?object_number='+acc,'https://api.smk.dk/api/v1/art/?object_number='+acc})
 return urls

def museum_object_authorities(record):
 # P9834 is the Finnish National Gallery art ID, not a creator identifier.
 return [('fng-object',v) for v in m.r.values(record['entity'],'P9834') if isinstance(v,str) and v.isdigit()]

def reviewed_metadata_override(item,override,run):
 # Preserve source captures and original preparation. Only explicitly reviewed,
 # hash-pinned primary metadata can change the final application plan.
 assert set(override)<= {'date','title','work_type','accession','evidence_file','evidence_sha256','reason'}
 assert override.get('reason') and override.get('evidence_file')
 evidence=(run/override['evidence_file']).resolve()
 assert evidence.is_relative_to(run.resolve()) and evidence.is_file()
 raw=evidence.read_bytes();assert m.core.sha(raw)==override['evidence_sha256']
 source=json.loads(raw);assert source['qid']==item['record']['qid'] and source.get('receipt',{}).get('url','').startswith('https://')
 if 'date' in override:
  d=override['date'];assert set(d)=={'first','last','precision','display','eligible'}
  if d['first'] is None:assert d['last'] is None and d['precision']=='unknown' and d['eligible'] is False
  else:assert isinstance(d['first'],int) and isinstance(d['last'],int) and 0<d['first']<=d['last']<=1970 and d['eligible'] is True and d['precision'] in ('exact','circa','range','circa_range')
  item['record']['date']=d
  if not d['eligible']:item.update(image=None,image_outcome='primary_creation_date_requires_review_metadata_retained')
 if 'title' in override:assert isinstance(override['title'],str) and override['title'].strip();item['record']['title']=override['title']
 if 'accession' in override:
  accession=override['accession'];assert isinstance(accession,str) and accession.strip()
  assert source.get('review')=='primary_object_and_creator_corroborated' and m.accession_key(source.get('object',{}).get('accession'))==m.accession_key(accession)
  item['record']['accession']=accession
 if 'work_type' in override:assert override['work_type'] in ('painting','drawing','fresco','unknown');item['record']['work_type']=override['work_type']
 item['record']['primary_metadata_review']={'override':override,'source':source}

def reviewed_new_artist(record,records,held):
 # Build timelines from the final reviewed dates. The preliminary planner may
 # have used a source lifespan wrongly presented as an artwork date. A dated
 # sibling work can support an activity interval for an undated work by the
 # same creator, without inventing birth/death years.
 ce=record['creator_entity'];cq=record['creator_qid'];birth=m.r.year(ce,'P569');death=m.r.year(ce,'P570')
 reviewed_dates=record.get('primary_creator_review',{}).get('source',{}).get('artist_dates')
 if reviewed_dates:
  birth,death=reviewed_dates['birth'],reviewed_dates['death']
  first,last,basis=reviewed_dates['active_start'],reviewed_dates['active_end'],'activity'
 elif birth is not None and death is not None and 1100<=birth<=death:
  first,last,basis=birth,death,'life'
 else:
  dated=[r['date'] for q,r in records.items() if q not in held and r['creator_qid']==cq and r['date']['eligible'] and r['date']['first'] is not None]
  if not dated:return None
  first=min(d['first'] for d in dated);last=max(d['last'] for d in dated);basis='activity'
  if first<1100:return None
 return {'id':m.uid('artist/'+cq),'qid':cq,'name':record['creator_label'],'birth':birth,'death':death,'first':first,'last':last,'basis':basis,'description':ce.get('descriptions',{}).get('en',{}).get('value',''),'entity':ce}

def validate_primary_creator_review(record,run):
 ev=record.get('primary_creator_review')
 if not ev:return
 path=(run/ev['evidence_file']).resolve()
 assert path.is_relative_to(run.resolve()) and path.is_file()
 raw=path.read_bytes();assert m.core.sha(raw)==ev['evidence_sha256']
 source=json.loads(raw)
 assert source['review']=='primary_object_creator_and_country_individually_reviewed'
 assert source['qid']==record['qid'] and source['creator_qid']==record['creator_qid']==record['creator_entity']['id']
 assert source['country_code']==record['country_code'] and source['receipt']['url'].startswith('https://')
 assert source['receipt'].get('retrieved_at') and source['object']['accession'] and m.accession_key(source['object']['accession'])==m.accession_key(record['accession'])
 original={v.get('id') for v in m.r.values(record['entity'],'P170') if isinstance(v,dict)}
 assert original==set(source['original_creator_qids']) and source['country_evidence'] and source['creator_identity_evidence']
 if source.get('artist_dates'):
  dates=source['artist_dates'];assert set(dates)=={'birth','death','active_start','active_end'}
  assert dates['birth'] is None and dates['death'] is None
  assert isinstance(dates['active_start'],int) and isinstance(dates['active_end'],int) and 1100<=dates['active_start']<=dates['active_end']<=1970
 if source.get('existing_identity_decision'):
  decision=source['existing_identity_decision'];assert decision['kind'] in ('same_person_biography_conflict_preserved','distinct_named_person')
  assert decision['primary_evidence'] and decision['reason']
 ev['source']=source

def prepare(code,number):
 batch=configure(code,number);run=m.r.RUN;manifest=run/'application-manifest.json'
 if manifest.exists():return json.loads(manifest.read_text())
 quality=json.loads((run/'quality-review.json').read_text());images=json.loads((run/'image-preparation.json').read_text())
 assert quality.get('approved') is True,'Actual visual and metadata review must explicitly approve this round'
 assert quality['contact_sheet_sha256']==m.core.sha((run/'contact-sheet.jpg').read_bytes())
 for name,sha in images['ready_hashes'].items():assert m.core.sha((run/'ready'/name).read_bytes())==sha
 if not images['ready']:
  result={'at':m.core.now(),'country':code,'round':number,'batch':batch,'empty':True};m.core.save_new(manifest,result);return result
 inputs=run/'batches'/f'batch-{batch:03d}.inputs.json'
 if not inputs.exists():
  candidates=[json.loads(p.read_text()) for p in sorted((run/'ready').glob('Q*.json'))]
  for item in candidates:
   validate_primary_creator_review(item['record'],run)
   override=quality.get('metadata_overrides',{}).get(item['record']['qid'])
   if override:reviewed_metadata_override(item,override,run)
  m.core.save_new(inputs,candidates)
 m.plan(batch,1000)
 path=run/'batches'/f'batch-{batch:03d}.json';data=json.loads(path.read_text());m.core.save_new(path.with_suffix('.unreviewed.json'),path.read_bytes())
 for item in data['entries']:
  override=quality.get('metadata_overrides',{}).get(item['record']['qid'])
  if override:reviewed_metadata_override(item,override,run)
  if item['record']['qid'] in quality.get('held_images',{}):item.update(image=None,image_outcome='visual_quality_deferred_metadata_retained',image_quality_hold=quality['held_images'][item['record']['qid']])
  im=item.get('image')
  if im:
   page=im['commons_page'];meta=page['imageinfo'][0]['extmetadata'];credit=image_review.image_credit(meta)
   creator_review=item['record'].get('primary_creator_review',{}).get('source',{})
   if creator_review.get('reviewed_image_credit'):
    assert im['rights_status']=='public_domain' and not meta.get('Attribution',{}).get('value')
    credit=creator_review['reviewed_image_credit']
    im['primary_creator_credit_review']=item['record']['primary_creator_review']
   if credit!=im['creator_credit']:
    im.update(creator_credit=credit,attribution_text=im['attribution_text']+' Additional source attribution: '+credit+'. File page: '+im['source_page_url'])
   markup=page.get('revisions',[{}])[0].get('slots',{}).get('main',{}).get('*','')
   try:image_review.check_rights_chronology(item['record'],im['license_label'],markup)
   except ValueError as error:item.update(image=None,image_outcome='source_rights_consistency_deferred_metadata_retained',image_rights_hold=str(error))
 records={i['record']['qid']:i['record'] for i in data['entries']};prepared_images={i['record']['qid']:i.get('image') for i in data['entries']};held=dict(quality.get('held_records',{}));identity={};candidate_keys={};within_holds={}
 official_path=run/'official-object-review.json';official={}
 if any(r['collection']['qid']=='Q190804' and r['accession'] for r in records.values()):
  assert official_path.exists(),'Rijksmuseum candidates require the primary object review before application'
  official={r['qid']:r for r in json.loads(official_path.read_text())['records']}
  for q,rec in records.items():
   if rec['collection']['qid']=='Q190804' and rec['accession']:
    ev=official.get(q)
    if not ev or ev['review']!='official_object_creator_and_accession_corroborated':held[q]='official_museum_object_or_attribution_requires_review'
 # Duplicate catalogue entities can represent a loan or alternate record for
 # the same physical object. Keep them out until collection/object review.
 for q,rec in sorted(records.items(),key=lambda p:int(p[0][1:])):
  keys=[('collection-accession',rec['collection']['qid'],m.accession_key(rec['accession']))] if rec['accession'] else []
  keys += [('source-image',rec['creator_qid'],name) for name in rec['images']]
  old=next((candidate_keys[k] for k in keys if k in candidate_keys),None)
  if old:within_holds[q]='same_source_object_or_reproduction_as_'+old
  else:
   for k in keys:candidate_keys[k]=q
 for target in ('local','production'):
  preimages={}
  with m.r.base.connect(target=='production') as db,db.transaction():
   db.execute('SET TRANSACTION READ ONLY');db.execute("SET LOCAL statement_timeout='120s'")
   matcher=f.Matcher(artist_inventory(db));memo={}
   object_urls={q:vetted_object_urls(rec,official.get(q)) for q,rec in records.items()}
   all_urls=sorted(set().union(*object_urls.values()))
   # The existing citations(entity_type,source_url,entity_id) index supports
   # bounded object URL lookups even when an incomplete record has no current
   # institution yet. Do not create a second object because its holding is blank.
   source_matches=collections.defaultdict(list)
   for found in db.execute("SELECT DISTINCT c.source_url,a.id::text,a.slug FROM citations c JOIN artworks a ON a.id=c.entity_id WHERE c.entity_type='artwork' AND c.source_url=ANY(%s) AND a.status<>'archived'",(all_urls,)).fetchall():source_matches[found['source_url']].append(found)
   object_authorities={q:museum_object_authorities(rec) for q,rec in records.items()};authority_matches=collections.defaultdict(list)
   fng_ids=sorted({value for pairs in object_authorities.values() for scheme,value in pairs if scheme=='fng-object'})
   if fng_ids:
    for found in db.execute("SELECT e.scheme,e.external_id,w.id::text,w.slug FROM external_identifiers e JOIN artworks w ON w.id=e.entity_id WHERE e.entity_type='artwork' AND e.scheme='fng-object' AND e.external_id=ANY(%s) AND w.status<>'archived'",(fng_ids,)).fetchall():authority_matches[(found['scheme'],found['external_id'])].append(found)
   for state in data['targets'][target]:
    q=state['qid'];rec=records[q]
    reason=held.get(q) or within_holds.get(q)
    outside=[found for url in object_urls[q] for found in source_matches[url] if found['id']!=state.get('artwork_id')]
    outside += [found for key in object_authorities[q] for found in authority_matches[key] if found['id']!=state.get('artwork_id')]
    if outside and not reason:
     reason='existing_source_object_identity_requires_reconciliation';state['existing_source_object_matches']=outside
    if reason:state.update(action='deferred',reason=reason);continue
    if state['action']=='deferred':continue
    cq=rec['creator_qid']
    if cq not in memo:memo[cq]=resolve(rec,matcher)
    match,reason=memo[cq]
    if not reason and match['artist']:
     artist=match['artist'];existing=set(artist['countries']);code_country=rec['country_code']
     if existing and code_country not in existing:reason='existing_cultural_affiliation_needs_context'
     else:
      state.update(artist_id=artist['id'],artist_slug=artist['slug'],new_artist=None,artist_identity_basis=match['basis'],artist_identity_signature={'slug':artist['slug'],'name':f.names.namekey(artist['display_name']),'birth':artist['birth_year'],'death':artist['death_year'],'authorities':sorted((i['scheme'],i['id']) for i in artist['authorities'])})
      preimages[artist['id']]=artist
    elif not reason:
     author=reviewed_new_artist(rec,records,{**held,**within_holds})
     if not author:reason='new_artist_timeline_or_identity_requires_review'
     else:
      state.update(new_artist=author,artist_id=author['id'])
      state['artist_identity_basis']=match['basis'];state['artist_slug']='wikimedia-painter-'+cq.lower();state['artist_identity_signature']={'new_wikidata':cq}
    if not reason:
     artist=match['artist'] or state['new_artist'];birth=artist.get('birth_year',artist.get('birth'));death=artist.get('death_year',artist.get('death'));d=rec['date']
     if (d['last'] is not None and birth is not None and d['last']<birth) or (d['first'] is not None and death is not None and d['first']>death):reason='work_date_outside_creator_lifetime'
    if not reason and state['action']=='new' and match['artist'] and rec.get('accession'):
     # Legacy researched works can have an exact inventory and creator but no
     # institution FK. A painter-scoped lookup catches that gap without
     # comparing every museum's accession globally or creating a duplicate.
     incomplete=db.execute("""SELECT w.id::text,w.slug,w.title,w.accession_number
     FROM artwork_artists aa JOIN artworks w ON w.id=aa.artwork_id
     WHERE aa.artist_id=%s AND w.status<>'archived' AND w.current_institution_id IS NULL
     AND upper(regexp_replace(w.accession_number,'\\s','','g'))=%s LIMIT 4""",(match['artist']['id'],m.accession_key(rec['accession']))).fetchall()
     if incomplete:reason='existing_creator_inventory_without_institution_requires_reconciliation';state['incomplete_institution_object_matches']=incomplete
    if not reason and state['action']=='new' and match['artist'] and prepared_images.get(q):
     # Painter-scoped indexed joins, never a global artwork/media CTE. Identical
     # pixels are a research hold, not proof that panels or impressions merge.
     same_image=db.execute("""SELECT DISTINCT w.id::text,w.slug,w.title,w.accession_number
     FROM artwork_artists aa JOIN artworks w ON w.id=aa.artwork_id
     JOIN media_assets im ON im.id=w.primary_media_id
     WHERE aa.artist_id=%s AND w.status<>'archived' AND im.checksum_sha256=%s LIMIT 4""",(match['artist']['id'],prepared_images[q]['sha256'])).fetchall()
     if same_image:
      reason='existing_painter_image_requires_physical_object_review';state['same_image_existing_objects']=same_image
    if reason:state.update(action='deferred',reason=reason)
    else:identity.setdefault(cq,{})[target]={'artist_id':state['artist_id'],'basis':state['artist_identity_basis'],'country_code':rec['country_code']}
  m.core.save_new(BACKUPS/f'batch-{batch:03d}-{target}-artist-preimages.json',preimages)
 # A legacy catalogue may have an additional title/object identity in only
 # one database. Hold that candidate in both; do not create a local duplicate
 # or discard the rest of a researched round because the legacy states differ.
 states_by_target={t:{s['qid']:s for s in rows} for t,rows in data['targets'].items()}
 for q in records:
  pair=[states_by_target[t][q] for t in ('local','production')]
  if any(s['action']=='deferred' for s in pair) and len({(s['action'],s.get('reason')) for s in pair})>1:
   evidence={t:{k:states_by_target[t][q].get(k) for k in ('action','reason','matches','existing_source_object_matches')} for t in ('local','production')}
   reasons=sorted({s.get('reason','identity_needs_review') for s in pair if s['action']=='deferred'})
   for state in pair:state.update(action='deferred',reason='cross_database_identity_review: '+'; '.join(reasons),cross_database_evidence=evidence)
 # Require symmetric decisions and compatible canonical identities before
 # either DB is changed. Target-specific UUIDs remain unchanged.
 def comparable(states):return [(s['qid'],s['action'],s.get('reason'),s.get('artist_identity_signature') if s['action']!='deferred' else None,(s['existing']['slug'] if s.get('existing') else s.get('artwork_id')) if s['action']!='deferred' else None) for s in states]
 assert comparable(data['targets']['local'])==comparable(data['targets']['production']),'Both-target identity decisions differ'
 path.write_text(json.dumps(data,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
 result={'at':m.core.now(),'country':code,'round':number,'batch':batch,'plan_sha256':m.core.sha(path.read_bytes()),'identity_review':identity,'target_counts':{t:dict(collections.Counter(s['action'] for s in v)) for t,v in data['targets'].items()},'holds':[{'qid':s['qid'],'reason':s['reason']} for s in data['targets']['local'] if s['action']=='deferred']}
 m.core.save_new(manifest,result);print(json.dumps({k:v for k,v in result.items() if k!='identity_review'},indent=2),flush=True);return result

def country_evidence(target,data,pin):
 path=m.r.RUN/('country-evidence-'+target+'.json')
 if path.exists():return
 records={i['record']['qid']:i['record'] for i in data['entries']};out=[];seen=set()
 with m.r.base.connect(target=='production') as db:
  for state in data['targets'][target]:
   if state['action']=='deferred' or not state.get('artist_id') or state['artist_id'] in seen:continue
   aid=state['artist_id'];seen.add(aid);rec=records[state['qid']];code=rec['country_code']
   with db.transaction():
    db.execute('SELECT pg_advisory_xact_lock(559220260914)')
    a=db.execute('SELECT id::text,status,geography_review_state FROM artists WHERE id=%s FOR UPDATE',(aid,)).fetchone();assert a and a['status']=='review'
    sid=db.execute('SELECT id FROM sources WHERE slug=%s',(m.SOURCE_SLUG,)).fetchone()['id']
    current={r['country_code'] for r in db.execute("SELECT country_code FROM artist_countries WHERE artist_id=%s AND relationship_type='cultural_affiliation'",(aid,)).fetchall()};assert not current or code in current
    db.execute("INSERT INTO artist_countries(artist_id,country_code,relationship_type,is_primary,note) VALUES(%s,%s,'cultural_affiliation',false,%s) ON CONFLICT DO NOTHING",(aid,code,'Source-supported painter affiliation; country evidence retained in geography citation. Not a museum-location or exclusive citizenship assertion.'))
    exists=db.execute("SELECT 1 FROM citations WHERE entity_type='artist' AND entity_id=%s AND source_id=%s AND field_name='geography'",(aid,sid)).fetchone()
    if not exists:m.r.base.insert(db,'citations',dict(entity_type='artist',entity_id=aid,source_id=sid,field_name='geography',source_record_id=rec['creator_qid'],source_url='https://www.wikidata.org/wiki/'+rec['creator_qid'],retrieved_at=rec['creator_receipt']['retrieved_at'],created_by=m.ACTOR,evidence_note=json.dumps({'country_code':code,'plan_sha256':pin,'country_evidence':rec['country_evidence'],'creator_receipt':rec['creator_receipt'],'publication':'Review retained; geography classification is separate from publication.'},ensure_ascii=False)))
    db.execute("UPDATE artists SET geography_review_state='classified',revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s AND geography_review_state='not_reviewed'",(m.ACTOR,aid))
   out.append({'artist_id':aid,'country_code':code,'status':'review'})
 m.core.save_new(path,{'at':m.core.now(),'plan_sha256':pin,'painters':out})

def apply(code,number,target):
 batch=configure(code,number);manifest=json.loads((m.r.RUN/'application-manifest.json').read_text())
 if manifest.get('empty'):return
 result=m.r.RUN/'batch-results'/f'{batch:03d}-{target}.json'
 if not result.exists():m.apply(batch,target,manifest['plan_sha256'])
 data=json.loads((m.r.RUN/'batches'/f'batch-{batch:03d}.json').read_text());country_evidence(target,data,manifest['plan_sha256'])

def verify(code,number):
 batch=configure(code,number);run=m.r.RUN;manifest=json.loads((run/'application-manifest.json').read_text())
 if (run/'verification.json').exists():return
 if manifest.get('empty'):m.core.save_new(run/'verification.json',{'at':m.core.now(),'empty':True,'metadata_round_completed':True});return
 raw=(run/'batches'/f'batch-{batch:03d}.json').read_bytes();assert m.core.sha(raw)==manifest['plan_sha256'];data=json.loads(raw);items={i['record']['qid']:i for i in data['entries']};report={'at':m.core.now(),'country':code,'round':number,'plan_sha256':manifest['plan_sha256'],'databases':{},'public_images':[]};attached={};public=[]
 for target in ('local','production'):
  states={s['qid']:s for s in data['targets'][target] if s['action']!='deferred'};receipts={p.stem:json.loads(p.read_text()) for p in (run/'applied'/target).glob('Q*.json')};assert states.keys()==receipts.keys()
  counts=collections.Counter()
  with m.r.base.connect(target=='production') as db,db.transaction():
   db.execute('SET TRANSACTION READ ONLY');db.execute("SET LOCAL statement_timeout='120s'")
   for q,state in states.items():
    row=db.execute("""SELECT to_jsonb(a) work,i.slug institution_slug,ma.storage_path,ma.checksum_sha256,ma.byte_size,ma.license_url,
    (SELECT count(*) FROM media_rights_evidence re WHERE re.media_id=ma.id) rights_evidence,
    (SELECT count(*) FROM artwork_location_assertions la WHERE la.artwork_id=a.id AND la.claim_type='display') display_claims,
    artline_has_selection_evidence(a.id) selected FROM artworks a JOIN institutions i ON i.id=a.current_institution_id LEFT JOIN media_assets ma ON ma.id=a.primary_media_id WHERE a.id=%s""",(state['artwork_id'],)).fetchone()
    assert row;w=row['work'];item=items[q];rec=item['record'];receipt=receipts[q]
    assert w['status']=='review' and w['published_at'] is None and row['selected']
    assert db.execute("SELECT 1 FROM external_identifiers WHERE entity_type='artwork' AND entity_id=%s AND scheme='wikidata' AND external_id=%s",(w['id'],q)).fetchone()
    assert db.execute("SELECT 1 FROM citations c JOIN sources s ON s.id=c.source_id WHERE c.entity_type='artwork' AND c.entity_id=%s AND s.slug=%s",(w['id'],m.SOURCE_SLUG)).fetchone()
    if state['action']=='new':
     assert (w['title'],w['creation_year_start'],w['creation_year_end'],w['date_precision'],w['work_type'])==(rec['title'],rec['date']['first'],rec['date']['last'],rec['date']['precision'],rec['work_type'])
     assert w['accession_number']==rec.get('accession'),'Imported inventory must match the reviewed physical object'
     assert row['display_claims']==0 and w['object_form']==rec.get('source_form')
     assert db.execute('SELECT 1 FROM artwork_artists WHERE artwork_id=%s AND artist_id=%s',(w['id'],state['artist_id'])).fetchone()
    assert db.execute("SELECT 1 FROM artists a JOIN artist_countries c ON c.artist_id=a.id WHERE a.id=%s AND a.status='review' AND c.country_code=%s",(state['artist_id'],code)).fetchone()
    if receipt['image_attached']:
     im=item['image'];assert row['storage_path']==im['path'] and row['checksum_sha256']==im['sha256'] and row['byte_size']==im['bytes']<=100000 and row['rights_evidence'] and row['license_url']==im['license_url'];attached[q]=im
    counts[state['action']]+=1;counts['images']+=int(receipt['image_attached']);counts['new_artists']+=int(receipt['new_artist']);counts['unknown_dates']+=int(rec['date']['precision']=='unknown')
    if target=='production':public.append({'id':w['id'],'institution_slug':row['institution_slug']})
  report['databases'][target]=dict(counts)
 assert report['databases']['local']==report['databases']['production']
 def check(pair):
  q,im=pair;raw=(m.r.ROOT/'apps/web/public'/im['path'].lstrip('/')).read_bytes();assert m.core.sha(raw)==im['sha256'];resp=requests.get(SITE+im['path'],timeout=90);resp.raise_for_status();assert resp.headers['Content-Type'].startswith('image/jpeg') and m.core.sha(resp.content)==im['sha256'];return {'qid':q,'url':SITE+im['path'],'sha256':im['sha256'],'status':resp.status_code}
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:report['public_images']=list(pool.map(check,attached.items()))
 report['public_pages']=[]
 for row in public[:3]:
  url=SITE+'/api/backend/v1/museums/'+row['institution_slug']+'/works/'+row['id'];resp=requests.get(url,timeout=120);resp.raise_for_status();assert row['id'] in resp.text;report['public_pages'].append({'url':url,'status':resp.status_code})
 m.core.save_new(run/'verification.json',report);print(code,number,'verified',report['databases'],flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['plan','apply','verify']);p.add_argument('--country',choices=x.COUNTRIES,required=True);p.add_argument('--round',type=int,required=True);p.add_argument('--target',choices=['local','production']);a=p.parse_args();assert 1<=a.round<=20
 {'plan':lambda:prepare(a.country,a.round),'apply':lambda:apply(a.country,a.round,a.target),'verify':lambda:verify(a.country,a.round)}[a.command]()
