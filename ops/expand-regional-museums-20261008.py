#!/usr/bin/env python3
"""Selected Cyprus/Malta/Lebanon catalogue additions, with source-backed holdings."""
import importlib.util,json,sys
from pathlib import Path
from psycopg.types.json import Jsonb
s=importlib.util.spec_from_file_location('review',Path(__file__).with_name('review-catalogue-20261008.py'));op=importlib.util.module_from_spec(s);s.loader.exec_module(op)
m,RUN,BACKUP,uid=op.m,op.RUN,op.BACKUP,op.uid
SOURCE={
 'pedoulas':('Pedoulas Community Council — Byzantine Museum','https://www.pedoulas.org.cy/index.php/en/culture-en/museums-en/byzantine-museum-of-pedoulas','collection_page'),
 'saints':('Cyprus Tourism Organisation — Cyprus, Island of Saints','https://www.visitcyprus.com/wp-content/uploads/files/cultural_routes/Cyprus_island_of_saints_EN.pdf','book'),
 'sursock':('Sursock Museum — Collection','https://sursock.museum/collections','collection_page'),
 'malta':('Heritage Malta — National Collection','https://emuseum.heritagemalta.mt/','collection_page')}
MUSEUMS=[('sursock-museum','Sursock Museum','Beirut','LB','https://sursock.museum/content/plan-your-visit','sursock'),('muza-valletta','MUŻA — The National Community Art Museum','Valletta','MT','https://heritagemalta.mt/mt/explore/muza/','malta')]
def sourcekey(w):return 'pedoulas' if w['museum'].startswith('pedoulas') else 'saints' if w['museum'].startswith('koilani') else 'malta' if w['museum']=='muza-valletta' else 'sursock'
def prepare():
 selection=m.load(RUN/'regional-selection.json');rows={t:[] for t in ['countries','places','sources','institutions','institution_venues','source_institutions','artworks','artwork_artists','citations','external_identifiers','artwork_location_assertions']};stamp=m.now();sourceids={};museumids={};baseline={};creator_matches={};decisions=[]
 with m.connect('production') as db:
  if not db.execute("SELECT 1 FROM countries WHERE code='MT'").fetchone():rows['countries'].append(dict(code='MT',name='Malta',region_code='southern-europe',historical_note='Geographic grouping follows the catalogue UN M49 convention.'))
  for key,(name,url,typ) in SOURCE.items():
   slug='regional-review-'+key+'-20261008';found=db.execute('SELECT id FROM sources WHERE slug=%s',(slug,)).fetchone();assert not found,'Already prepared/applied source'
   sourceids[key]=uid('source:'+key);rows['sources'].append(dict(id=sourceids[key],slug=slug,name=name,source_type=typ,base_url=url))
  for slug,name,city,country,url,key in MUSEUMS:
   assert not db.execute('SELECT 1 FROM institutions WHERE slug=%s OR lower(name)=lower(%s)',(slug,name)).fetchone(),'Museum already present'
   place=db.execute('SELECT id FROM places WHERE name=%s AND country_code=%s',(city,country)).fetchone();pid=str(place['id']) if place else uid('place:'+city)
   if not place:rows['places'].append(dict(id=pid,name=city,normalized_name=m.normal(city),country_code=country))
   iid=uid('museum:'+slug);museumids[slug]=iid
   rows['institutions'].append(dict(id=iid,slug=slug,name=name,normalized_name=m.normal(name),place_id=pid,website_url=url,status='review',kind='museum',description=''))
   rows['institution_venues'].append(dict(id=uid('venue:'+slug),institution_id=iid,slug=slug+'-main',name=name,place_id=pid,visit_url=url,source_url=url,checked_at=stamp,status='review'))
   rows['citations'].append(dict(id=uid('museum-citation:'+slug),entity_type='institution',entity_id=iid,field_name='identity_and_geography',source_id=sourceids[key],source_url=url,evidence_note='Official museum visitor page identifies the museum, city and country. Collection holdings do not establish current display.',retrieved_at=stamp,created_by=m.ACTOR))
  for slug in ['pedoulas-byzantine-museum','koilani-ecclesiastical-museum']:
   found=db.execute('SELECT to_jsonb(i) row FROM institutions i WHERE slug=%s',(slug,)).fetchone()['row'];museumids[slug]=found['id'];baseline[slug]=found
   assert not db.execute('SELECT 1 FROM artworks WHERE current_institution_id=%s',(found['id'],)).fetchone(),'Existing scoped works need deduplication'
  for w in selection['selected']:
   key=sourcekey(w);iid=museumids[w['museum']];aid=uid('artwork:'+w['museum']+':'+w['key']);slug='regional-'+w['museum']+'-'+w['key']
   assert not db.execute('SELECT 1 FROM artworks WHERE id=%s OR slug=%s',(aid,slug)).fetchone()
   assert not db.execute('SELECT 1 FROM external_identifiers WHERE canonical_url=%s AND entity_type=\'artwork\'',(w['url'],)).fetchone() if key=='malta' else True
   artist=None
   if w['creator'] and not w['creator'].startswith('Attributed'):
    artists=db.execute('SELECT id,display_name FROM artists WHERE lower(display_name)=lower(%s) AND status<>\'archived\'',(w['creator'],)).fetchall();assert len(artists)<=1
    if artists:artist=str(artists[0]['id']);creator_matches[w['creator']]=artist
   # Institution scopes, native object URLs and existing creator oeuvre were reviewed before this selected pass.
   evidence=dict(operation='catalogue-review-expansion-20261008',source=SOURCE[key][0],url=w['url'],locator=w['locator'],supplied_creator=w['creator'],source_date=w['date_display'],source_dimensions=w['dimensions'],museum_assignment_confidence=0.99,confidence_basis='Named object caption in official museum/community collection; Heritage Malta object Museum field explicitly identifies MUŻA.',uncertainty='Editorial confidence, not calibrated probability. No current display claim. Anonymous creators and unspecified dates remain unknown.',selection='Museum-supported collection object; no personal must-see or museum masterpiece designation inferred.')
   if key=='saints':evidence['limitation']='Historical official guide; records documented holding, not a fresh display check.'
   if key=='sursock' and w['key']=='aa-01344':evidence['identity_review']='Distinct from the existing WikiArt Untitled (1965): museum object is a 120 x 90 cm upright 1966 canvas panel, versus landscape 1024 x 667 full-composition reproduction for the 1965 work. Generic title alone is not a match. Source caption records museum purchase in 1966.'
   if w['key']=='1199':evidence['version']='Single recto/verso sheet, not the separate Seville painting or Valletta ceiling.'
   if w['key']=='3674':evidence['version']='Terracotta model at MUŻA, not the final marble sculpture in Rome.'
   if w['key']=='3661':evidence['date_bounds']='Broad decade bounds preserve late/early qualifiers without inventing exact dates.'
   rows['artworks'].append(dict(id=aid,slug=slug,title=w['title'],normalized_title=m.normal(w['title']),date_display=w['date_display'],creation_year_start=w['start'],creation_year_end=w['end'],date_precision=w['precision'],work_type=w['work_type'],medium_text=w['medium'],dimensions_text=w['dimensions'],current_institution_id=iid,current_location_text=next((x[1] for x in MUSEUMS if x[0]==w['museum']),baseline.get(w['museum'],{}).get('name')),location_checked_at=stamp,accession_number=w.get('accession'),status='review',research_candidate=True,unlinked_creator_label=w['creator'] if not artist else None,object_form=w.get('object_form'),created_by=m.ACTOR,updated_by=m.ACTOR))
   if artist:rows['artwork_artists'].append(dict(artwork_id=aid,artist_id=artist,attribution_role='primary',attribution_note='Creator explicitly named by the cited object record.'))
   rows['citations'].append(dict(id=uid('citation:'+aid),entity_type='artwork',entity_id=aid,field_name='catalogue_metadata_and_holding',source_id=sourceids[key],source_record_id=w.get('accession',w['key']),source_url=w['url'],page_or_locator=w['locator'],evidence_note=json.dumps(evidence,ensure_ascii=False),retrieved_at=stamp,created_by=m.ACTOR))
   rows['external_identifiers'].append(dict(id=uid('external:'+aid),entity_type='artwork',entity_id=aid,scheme='regional-reviewed-object',external_id=w['museum']+':'+w['key'],canonical_url=w['url'],source_id=sourceids[key],retrieved_at=stamp))
   rows['artwork_location_assertions'].append(dict(id=uid('holding:'+aid),artwork_id=aid,claim_type='holding',institution_id=iid,context='collection',source_id=sourceids[key],source_url=w['url'],evidence_note=json.dumps(evidence,ensure_ascii=False),checked_at=stamp,review_state='accepted'))
  rows['source_institutions']=[dict(source_id=sourceids[k],institution_id=museumids[slug]) for k,slug in [('pedoulas','pedoulas-byzantine-museum'),('saints','koilani-ecclesiastical-museum'),('sursock','sursock-museum'),('malta','muza-valletta')]]
 plan=dict(at=stamp,inserts=rows,existing_institutions=baseline,creator_matches=creator_matches,selection=selection,selection_sha256=m.digest(RUN/'regional-selection.json'),publication_changes=0,image_downloads=0)
 m.save(BACKUP/'regional-plan.json.gz',plan);m.save(RUN/'regional-plan-pin.json',dict(sha256=m.digest(BACKUP/'regional-plan.json.gz'),counts={t:len(v) for t,v in rows.items()}));print({t:len(v) for t,v in rows.items()})
def apply():
 path=BACKUP/'regional-plan.json.gz';plan=m.load(path);assert m.digest(path)==m.load(RUN/'regional-plan-pin.json')['sha256'];assert m.digest(RUN/'regional-selection.json')==plan['selection_sha256'];assert m.load(RUN/'cloud-backup.json')['status']=='SUCCESSFUL';assert not (RUN/'regional-applied.json').exists()
 with m.connect('production',False) as db:
  db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
  for slug,r in plan['existing_institutions'].items():assert m.select_rows(db,'institutions','id',[r['id']])==[r],'Museum changed'
  for r in plan['inserts']['artworks']:assert not db.execute('SELECT 1 FROM artworks WHERE slug=%s OR id=%s',(r['slug'],r['id'])).fetchone()
  # Inserts use database defaults for unspecified values, rather than turning them into nulls.
  from psycopg import sql
  for t in ['countries','places','sources','institutions','institution_venues','source_institutions','artworks','artwork_artists','citations','external_identifiers','artwork_location_assertions']:
   for r in plan['inserts'][t]:
    keys=list(r);db.execute(sql.SQL('INSERT INTO {} ({}) VALUES ({})').format(sql.Identifier(t),sql.SQL(',').join(map(sql.Identifier,keys)),sql.SQL(',').join(sql.Placeholder() for k in keys)),[r[k] for k in keys])
  for t,kind in [('artworks','artwork'),('institutions','institution')]:
   for r in plan['inserts'][t]:db.execute("INSERT INTO audit_log(actor_user_id,action,entity_type,entity_id,request_id,after_json) VALUES (%s,'regional_catalogue_added',%s,%s,%s,%s)",(m.ACTOR,kind,r['id'],'catalogue-review-expansion-20261008',Jsonb({'record':r,'plan_sha256':m.digest(path)})))
  actual=m.select_rows(db,'artworks','id',[r['id'] for r in plan['inserts']['artworks']]);assert len(actual)==20 and all(r['status']=='review' and r['published_at'] is None and r['primary_media_id'] is None for r in actual)
  assert len(m.select_rows(db,'artwork_location_assertions','artwork_id',[r['id'] for r in actual]))==20
  m.save(BACKUP/'regional-in-transaction.json.gz',dict(artworks=actual,holdings=m.select_rows(db,'artwork_location_assertions','artwork_id',[r['id'] for r in actual])))
 m.save(RUN/'regional-applied.json',dict(at=m.now(),counts={t:len(v) for t,v in plan['inserts'].items()},backup_id='1791461266671',publication_changes=0,display_claims=0,local_writes=0));print('Committed regional additions')
if __name__=='__main__':{'prepare':prepare,'apply':apply}[sys.argv[1]]()
