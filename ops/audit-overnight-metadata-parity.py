#!/usr/bin/env python3
"""Read-only comparison of campaign metadata, attribution, countries and evidence."""
import argparse,collections,importlib.util,json,time
from pathlib import Path
import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
s=importlib.util.spec_from_file_location('core',Path(__file__).with_name('enrich-artwork-images.py'));core=importlib.util.module_from_spec(s);s.loader.exec_module(core)
START=1789501601
SQL="""WITH requested AS (SELECT * FROM jsonb_to_recordset(%s) AS x(source_key text,scheme text,external_id text))
 SELECT r.source_key,a.id::text,a.slug,a.title,a.accession_number,a.creation_year_start,a.creation_year_end,a.date_precision,a.date_display,a.work_type,
  a.medium_text,a.dimensions_text,a.creation_place_display,a.unlinked_creator_label,a.cultural_context,a.status,a.published_at,a.research_candidate,a.created_at>=to_timestamp(1789501601) created_this_campaign,
  artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision) scope,artline_has_selection_evidence(a.id) selected,
  i.slug institution_slug,coalesce(p.country_code,vc.country_code) holding_country,
  (SELECT jsonb_agg(jsonb_build_object('artist',ar.slug,'role',aa.attribution_role,'note',aa.attribution_note) ORDER BY ar.slug,aa.attribution_role)
   FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=a.id) creators,
  (SELECT jsonb_agg(jsonb_build_object('scheme',x.scheme,'id',x.external_id,'url',x.canonical_url) ORDER BY x.scheme,x.external_id)
   FROM external_identifiers x WHERE x.entity_type='artwork' AND x.entity_id=a.id) identifiers,
  (SELECT count(*) FROM citations c WHERE c.entity_type='artwork' AND c.entity_id=a.id) citations_count,
  (SELECT md5(string_agg(jsonb_build_array(s.slug,c.field_name,c.source_record_id,c.source_url,c.evidence_note)::text,E'\\n' ORDER BY s.slug,c.field_name,c.source_record_id,c.source_url,c.evidence_note))
   FROM citations c JOIN sources s ON s.id=c.source_id WHERE c.entity_type='artwork' AND c.entity_id=a.id) citation_evidence_digest,
  (SELECT jsonb_agg(jsonb_build_object('type',la.claim_type,'institution',li.slug,'context',la.context,'state',la.review_state,'url',la.source_url,'note',la.evidence_note) ORDER BY la.claim_type,li.slug,la.source_url,la.evidence_note)
   FROM artwork_location_assertions la LEFT JOIN institutions li ON li.id=la.institution_id WHERE la.artwork_id=a.id AND la.superseded_by IS NULL) locations
 FROM requested r JOIN external_identifiers e ON e.entity_type='artwork' AND e.scheme=r.scheme AND e.external_id=r.external_id
 JOIN artworks a ON a.id=e.entity_id LEFT JOIN institutions i ON i.id=a.current_institution_id LEFT JOIN places p ON p.id=i.place_id
 LEFT JOIN LATERAL (SELECT min(vp.country_code) country_code FROM institution_venues v JOIN places vp ON vp.id=v.place_id WHERE v.institution_id=i.id HAVING count(DISTINCT vp.country_code)=1 AND bool_and(vp.country_code IS NOT NULL)) vc ON true"""
def main():
 p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();started=time.time();expected={};errors=[];folders=collections.Counter()
 for receipt in sorted(a.run.glob('*/local-metadata-verified.json')):
  run=receipt.parent
  if not (run/'cloud-metadata-verified.json').exists():errors.append({'batch':run.name,'error':'Production metadata receipt absent'});continue
  plan=json.loads((run/'plan.json').read_text());manifest=run/'plan-manifest.json'
  if manifest.exists():assert core.sha((run/'plan.json').read_bytes())==json.loads(manifest.read_text())['sha256'],'Pinned plan changed: '+run.name
  for c in plan['records']:
   scheme=c.get('scheme');oid=c.get('external_id',c.get('object_id'));assert scheme and oid is not None
   key=json.dumps([scheme,str(oid)]);assert key not in expected,'Repeated campaign metadata source identity'
   expected[key]={'source_key':key,'scheme':scheme,'external_id':str(oid),'batch':run.name,'plan':c};folders[run.name]+=1
 fresco=a.run/'met-priority-frescoes'
 if (fresco/'metadata-verified.json').exists():
  receipts=json.loads((fresco/'metadata-verified.json').read_text());assert {x['target'] for x in receipts}=={'local','cloud'} and all(x['verified_records']==2 for x in receipts)
  for c in json.loads((fresco/'plan.json').read_text())['records']:
   assert c['object']['classification']=='Paintings-Fresco' and c['object']['culture']=='Byzantine' and not c['object']['artistDisplayName']
   key=json.dumps([c['scheme'],str(c['external_id'])]);assert key not in expected
   c=dict(c,unlinked_creator_label='Unidentified painter',cultural_context='Byzantine')
   expected[key]={'source_key':key,'scheme':c['scheme'],'external_id':str(c['external_id']),'batch':fresco.name,'plan':c};folders[fresco.name]+=1
 states={};summaries={}
 for target,dsn in [('local','postgres://localhost/artline'),('cloud',core.cloud_dsn())]:
  state={};counts=collections.Counter();types=collections.Counter();scopes=collections.Counter();countries=collections.Counter();requests=[{k:c[k] for k in ('source_key','scheme','external_id')} for c in expected.values()]
  with psycopg.connect(dsn,autocommit=True,row_factory=dict_row,options='-c default_transaction_read_only=on -c statement_timeout=180000') as db:
   for start in range(0,len(requests),500):
    rows=db.execute(SQL,(Jsonb(requests[start:start+500]),)).fetchall()
    for row in rows:
     key=row['source_key'];plan=expected[key]['plan']
     if key in state:errors.append({'target':target,'source_key':key,'error':'Ambiguous native object identity'});continue
     state[key]=row
     try:
      assert row['status']=='review' and row['published_at'] is None and row['research_candidate'] and row['selected'],'Editorial/selection state differs'
      anonymous=plan.get('unlinked_creator_label')=='Unidentified painter' and plan.get('cultural_context')=='Byzantine' and row['unlinked_creator_label']=='Unidentified painter' and row['cultural_context']=='Byzantine' and not row['creators']
      assert row['citations_count']>0 and (row['creators'] or anonymous) and row['locations'],'Source, maker or holding evidence missing'
      if row['created_this_campaign']:assert all(l['type']=='holding' for l in row['locations']),'Unexpected display assertion in metadata selection'
      for field in ('title','creation_year_start','creation_year_end','date_precision','date_display','work_type','unlinked_creator_label','cultural_context'):
       if field in plan:assert row[field]==plan[field],'Pinned source field differs: '+field
      assert row['scope']=='eligible' or plan.get('image_eligibility')=='date_unresolved' and row['scope']=='review' and row['creation_year_start'] is None and row['creation_year_end'] is None and row['date_precision']=='unknown','Unexpected source-date scope'
      counts['verified']+=1;counts['new' if row['created_this_campaign'] else 'existing_enriched']+=1;types[row['work_type']]+=1;scopes[row['scope']]+=1;countries[row['holding_country'] or 'Not mapped']+=1
     except AssertionError as exc:errors.append({'target':target,'source_key':key,'error':str(exc)})
    if (start+500)%5000==0:print(core.now(),target,'metadata compared',min(start+500,len(requests)),flush=True)
  for key in expected.keys()-state.keys():errors.append({'target':target,'source_key':key,'error':'Expected metadata record absent'})
  summaries[target]={'counts':dict(counts),'work_types':dict(types),'scopes':dict(scopes),'holding_country':dict(countries)};states[target]=state
 matched=0
 for key in expected:
  left=states['local'].get(key);right=states['cloud'].get(key)
  if not left or not right:continue
  # IDs can legitimately differ in historical records; native source identity
  # and every selected metadata/attribution/evidence field must agree.
  differences=[field for field in left if field!='id' and left[field]!=right[field]]
  if differences:errors.append({'source_key':key,'error':'Local/production metadata differs','fields':differences})
  else:matched+=1
 artists=[]
 for receipt in sorted(a.run.glob('*/local-artists-verified.json')):
  run=receipt.parent;assert (run/'cloud-artists-verified.json').exists();plan=json.loads((run/'plan.json').read_text());assert core.sha((run/'plan.json').read_bytes())==json.loads((run/'plan-manifest.json').read_text())['sha256'];artists.extend(plan['records'])
 artist_states={}
 for target,dsn in [('local','postgres://localhost/artline'),('cloud',core.cloud_dsn())]:
  with psycopg.connect(dsn,autocommit=True,row_factory=dict_row,options='-c default_transaction_read_only=on') as db:
   rows=db.execute("""SELECT a.slug,a.display_name,a.birth_year,a.death_year,a.birth_display,a.death_display,a.birth_precision,a.death_precision,a.timeline_start_year,a.timeline_end_year,a.timeline_basis,a.status,a.published_at,a.geography_review_state,
    (SELECT jsonb_agg(jsonb_build_object('country',c.country_code,'type',c.relationship_type,'primary',c.is_primary,'note',c.note) ORDER BY c.country_code,c.relationship_type) FROM artist_countries c WHERE c.artist_id=a.id) countries,
    (SELECT md5(string_agg(c.evidence_note,E'\\n' ORDER BY c.evidence_note)) FROM citations c WHERE c.entity_type='artist' AND c.entity_id=a.id) citation_digest
    FROM artists a WHERE a.slug=ANY(%s)""",([c['slug'] for c in artists],)).fetchall()
  index={x['slug']:x for x in rows};artist_states[target]=index
  for c in artists:
   row=index.get(c['slug'])
   if not row or row['status']!='review' or row['published_at'] is not None or row['geography_review_state']!='classified' or sorted(x['country'].strip() for x in row['countries'] or [])!=sorted(c['countries']) or not row['citation_digest']:errors.append({'target':target,'artist':c['slug'],'error':'New artist identity/country/editorial evidence differs'})
 if artist_states['local']!=artist_states['cloud']:errors.append({'error':'New artist metadata differs between databases'})
 report={'at':core.now(),'elapsed_seconds':round(time.time()-started,2),'metadata_records_expected':len(expected),'matching_metadata_records':matched,'batches':dict(folders),'targets':summaries,'new_artists_checked_each_target':len(artists),'new_artist_metadata_matches':artist_states['local']==artist_states['cloud'],'errors':errors,'notes':'Read-only native-identifier-scoped comparison. Actual metadata, artist attribution, source-evidence digests and holding assertions compared; no fixtures or test DB used. Holding country is not painter nationality. New artists have separately verified source country affiliations. Image byte/provenance checks are a separate audit.'}
 core.save_new(a.output,report);print('METADATA AUDIT expected',len(expected),'matching',matched,'artists',len(artists),'errors',len(errors),flush=True)
 if errors:raise SystemExit(1)
if __name__=='__main__':main()
