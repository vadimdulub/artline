#!/usr/bin/env python3
"""Apply26 Fitzwilliam additions and4 exact existing holdings; preserve all prior metadata."""
import argparse,copy,gzip,hashlib,importlib.util,json
from pathlib import Path
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('prior',Path(__file__).with_name('museum-expansion-fitzwilliam-apply-20261007.py'));prior=importlib.util.module_from_spec(s);s.loader.exec_module(prior);i=prior.i;e=prior.e;f=prior.f;m=prior.m;RUN=prior.RUN;IID=prior.IID
KEY='fitzwilliam-target-200-001';SID=m.uid('source/'+KEY);SLUG='museum-expansion-20261006-'+KEY;COUNT=26;HCOUNT=4;PLAN=RUN/(KEY+'-plan.json.gz');REVIEW=RUN/'native-editorial-002.json.gz';CANDIDATES=RUN/'native-candidates-003.json.gz';IDENTITY=RUN/'native-identity-003.json.gz';COMPARISONS=RUN/'native-comparisons-003.json.gz'
reference=prior.reference;checked_reference=prior.checked_reference
HOLDINGS={
 '3637':dict(artwork_id='e260039d-8805-54e0-9d05-72ba613fa77f',scheme='wikiart-artwork',external_id='5772769dedc2cb3880d1fda0',creator='John Everett Millais',native_creator='Millais, John Everett',url='https://www.wikiart.org/en/john-everett-millais/the-bridesmaid',artist_external='john-everett-millais',basis='Exact WikiArt identity, title, creator,1851 creation, oil/panel medium, Fitzwilliam holding label and20.3×27.9cm dimensions agree with native accession499*. Dimensions appear in reverse order, with explicit height/width retained from the museum.'),
 '3956':dict(artwork_id='668813c2-830c-506c-b6c9-cfe04fc16827',scheme='wikiart-artwork',external_id='57727d4fedc2cb3880e73dac',creator='Philip Wilson Steer',native_creator='Steer, Philip Wilson',url='https://www.wikiart.org/en/philip-wilson-steer/hydrangeas-1901',artist_external='philip-wilson-steer',basis='Exact WikiArt identity, title, creator,1901 creation, oil/canvas medium and Fitzwilliam holding label agree with native accession PD.185-1975. Native note distinguishes the related Cape Town portrait and V&A drawings; none is substituted.'),
 '4008':dict(artwork_id='72e7f1e0-921d-5541-b218-f4af03e26f24',scheme='wikidata',external_id='Q50820390',creator='Elijah Walton',native_creator='Walton, Elijah',url='https://www.wikidata.org/wiki/Special:EntityData/Q50820390.json',artist_external='Q16063414',basis='Existing exact Wikidata object identifies Fitzwilliam native4008, accession456*, creator Elijah Walton and1865. Asterisk is part of the source inventory and is not collapsed into different accession456.'),
 '4028':dict(artwork_id='c6f3d739-80d5-521f-bffe-9ee39b69f854',scheme='wikidata',external_id='Q50821640',creator='James Wills',native_creator='Wills, James',url='https://www.wikidata.org/wiki/Special:EntityData/Q50821640.json',artist_external='Q21457932',basis='Existing exact Wikidata object identifies Fitzwilliam native4028, accession657, creator James Wills and1749. Museum dimensions110.5×145cm agree; portrait title refers to the same Andrews family object.')}

def checked_extra(row):
 cap=row['capture'];rc=cap['receipt'];raw=gzip.decompress((m.ROOT/cap['body_path']).read_bytes());assert rc['status']==200 and rc['url']==rc['final_url']==row['url'] and hashlib.sha256(raw).hexdigest()==rc['sha256']
 if row['kind']=='wikidata':assert json.loads(raw)==row['parsed']
 else:
  soup=BeautifulSoup(raw,'html.parser');parsed=dict(full_text=soup.get_text(' ',strip=True),h1=[a.get_text(' ',strip=True) for a in soup.select('h1')],h2=[a.get_text(' ',strip=True) for a in soup.select('h2')],fields=[a.get_text(' ',strip=True) for a in soup.select('.wiki-layout-artist-info li')],canonical=[a['href'] for a in soup.select('link[rel=canonical]')]);assert parsed==row['parsed']
 return row
def one(entity,prop):
 rows=[r for r in entity['claims'].get(prop,[]) if r['rank']!='deprecated'];assert len(rows)==1 and rows[0]['mainsnak']['snaktype']=='value','nonunique '+prop;return rows[0]
def value(entity,prop):return one(entity,prop)['mainsnak']['datavalue']['value']

def holding_records():
 scope=m.load(RUN/'existing-followup-scope-001.json.gz');ctx=m.load(RUN/'existing-followup-creator-context-001.json.gz');sources={r['url']:r for r in m.load(RUN/'existing-followup-exact-sources-001.json.gz')['records']};out=[]
 for sid,spec in HOLDINGS.items():
  aid=spec['artwork_id'];old=next(r for r in scope['before']['artworks'] if r['id']==aid);native=e.checked_object(reference(RUN/'native-objects-001'/(sid+'.json.gz')));facts=e.source_facts(native);source=checked_extra(sources[spec['url']]);links=[r for r in ctx['links'] if r['id']==aid]
  assert len(links)==1 and links[0]['display_name']==spec['creator'] and links[0]['attribution_role']=='primary'
  assert links[0]['status']==old['status']=='review' and old['published_at'] is None and old['current_institution_id'] is None
  assert facts['creator_label']==spec['native_creator'] and m.norm(facts['title'])==m.norm(old['title'])
  assert facts['date_issue'] is None and facts['first']==facts['last']==old['creation_year_start']==old['creation_year_end']<=1970
  ident=[r for r in scope['before']['identifiers'] if r['entity_id']==aid and r['scheme']==spec['scheme']];assert len(ident)==1 and ident[0]['external_id']==spec['external_id']
  artist_scheme='wikiart-artist' if spec['scheme']=='wikiart-artwork' else 'wikidata';assert any(r['entity_id']==links[0]['artist_id'] and r['scheme']==artist_scheme and r['external_id']==spec['artist_external'] for r in ctx['authorities'])
  if source['kind']=='wikiart':
   p=source['parsed'];assert p['h1'][0]==old['title'] and p['h2']==[spec['creator']];assert 'Date: '+str(facts['first']) in p['fields'] and 'Location: Fitzwilliam Museum (University of Cambridge), Cambridge, UK' in p['fields'];assert 'Public domain' in p['full_text'];assert ident[0]['canonical_url']==spec['url']
   if sid=='3637':assert 'Media: oil , panel' in p['fields'] and 'Dimensions: 20.3 x 27.9 cm' in p['fields'] and facts['dimensions_text']=='Height: 27.9 cm Width: 20.3 cm'
   else:assert 'Media: oil , canvas' in p['fields'] and facts['medium'].lower()=='oil on canvas'
  else:
   entity=source['parsed']['entities'][spec['external_id']];assert value(entity,'P8910')==sid and value(entity,'P217')==old['accession_number']==facts['inventory'];assert value(entity,'P195')['id']=='Q1421440' and value(entity,'P170')['id']==spec['artist_external'];assert not one(entity,'P170').get('qualifiers');d=value(entity,'P571');assert d['precision']==9 and int(d['time'][1:5])==facts['first'] and not d['before'] and not d['after']
  out.append(dict(artwork_id=aid,holding_id=m.uid(KEY+'/holding/'+aid),facts=facts,source=source,native=native,source_reference=reference(RUN/'native-objects-001'/(sid+'.json.gz')),decision=dict(state='approved_existing_holding',confidence=.95,basis=spec['basis'],limitation='Official catalogue last updated no later than April2026 upgrade cutoff; object revision and secondary-source limitations retained. Holding only, not present display, custody or ownership. Existing type, dates, inventory, images and publication state unchanged.')))
 assert len(out)==len({r['artwork_id'] for r in out})==HCOUNT;return out

def records():
 review=m.load(REVIEW);rows={r['source_id']:r for r in m.load(CANDIDATES)['rows']};comps={r['source_id']:r for r in m.load(COMPARISONS)['records']};selection=m.load(RUN/'editorial-selection-002.json');out=[]
 assert len(rows)==len(review['decisions'])==len({d['source_id'] for d in review['decisions']})==72
 for d in review['decisions']:
  if d['state']!='approved_review_only_addition':continue
  sid=d['source_id'];row=rows[sid];native=e.checked_object(row['source_reference']);facts=e.source_facts(native);assert row['state']=='candidate' and facts==row['facts']==d['facts'] and d['comparison']==comps[sid]
  assert d['confidence']==.95 and d['identity_note']==selection['notes'][sid] and not d['comparison']['source_hits'] and not [r for r in d['comparison']['inventory_hits'] if r['relevant']]
  assert facts['date_issue'] is None and 1<=facts['first']<=facts['last']<=1970
  out.append(dict(artwork_id=m.uid(KEY+'/'+sid),slug='museum-expansion-'+KEY+'-'+sid,facts=facts,decision=d,native=native))
 assert len(out)==len({r['artwork_id'] for r in out})==len({r['facts']['inventory'] for r in out})==COUNT and {r['facts']['source_id'] for r in out}==set(selection['selected_source_ids'])==set(review['selected_source_ids']);return out

def creator_context(db):
 x=m.load(RUN/'existing-followup-creator-context-001.json.gz');ids=x['artwork_ids'];rows=db.execute('SELECT a.id::text,a.title,a.status,a.published_at,a.current_institution_id::text,aa.artist_id::text,aa.attribution_role,ar.display_name FROM artworks a LEFT JOIN artwork_artists aa ON aa.artwork_id=a.id LEFT JOIN artists ar ON ar.id=aa.artist_id WHERE a.id=ANY(%s::uuid[]) ORDER BY a.id,aa.artist_id',(ids,)).fetchall();assert rows==x['links'];artists=sorted({r['artist_id'] for r in rows if r['artist_id']});auth=db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artist' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,scheme,external_id",(artists,)).fetchall();assert auth==x['authorities']
def preflight(db,plan):
 assert prior.snapshot(db,plan['scoped_ids'])==plan['before'];pp,pd=prior.validate_plan();assert pd==plan['prior_plan_sha256'];prior.verify(db,pp,pd);assert prior.counts(db)==dict(linked=176,eligible=170)
 x=m.load(IDENTITY);assert i.queries(db,x['params'])==x['state'];creator_context(db)
 ids=[r['artwork_id'] for r in plan['records']];urls=[r['facts']['source_url'] for r in plan['records']+plan['holdings']]
 assert not db.execute('SELECT 1 FROM artworks WHERE id=ANY(%s::uuid[]) LIMIT 1',(ids,)).fetchone();assert not db.execute('SELECT 1 FROM sources WHERE id=%s OR slug=%s',(SID,SLUG)).fetchone();assert not db.execute("SELECT 1 FROM external_identifiers WHERE entity_type='artwork' AND canonical_url=ANY(%s) LIMIT 1",(urls,)).fetchone()
 for r in plan['holdings']:
  spec=HOLDINGS[r['facts']['source_id']];hits=db.execute("SELECT entity_id::text FROM external_identifiers WHERE entity_type='artwork' AND scheme=%s AND external_id=%s ORDER BY entity_id",(spec['scheme'],spec['external_id'])).fetchall();assert hits==[dict(entity_id=r['artwork_id'])]

def prepare():
 assert not PLAN.exists();rs=records();holds=holding_records();pp,pd=prior.validate_plan();ids=sorted(set(pp['scoped_ids'])|{r['artwork_id'] for r in pp['records']}|{r['artwork_id'] for r in holds})
 with m.connect() as db:
  before=prior.snapshot(db,ids);plan=dict(at=m.now(),records=rs,holdings=holds,scoped_ids=ids,before=before,prior_plan_sha256=pd,prior_native_snapshot=prior.snapshot(db,[r['artwork_id'] for r in pp['records']]),policy='26 selected new review-only artworks and4 existing holding links. Preserve all existing metadata, media and publication status; supersede only two prior pending same-museum holding leads. No dates, inventories or types changed on existing records.')
  preflight(db,plan);backup=m.BACKUP/(KEY+'-before.json.gz');assert not backup.exists();m.save(backup,dict(at=m.now(),scoped_ids=ids,before=before));plan.update(backup_path=str(backup),backup_sha256=hashlib.sha256(backup.read_bytes()).hexdigest())
 paths=[Path(__file__).resolve(),prior.PLAN,RUN/(prior.KEY+'-applied.json'),REVIEW,CANDIDATES,IDENTITY,COMPARISONS,RUN/'editorial-selection-002.json',RUN/'native-index-002.json.gz',RUN/'native-object-queue-002.json',RUN/'existing-followup-scope-001.json.gz',RUN/'existing-followup-creator-context-001.json.gz',RUN/'existing-followup-exact-sources-001.json.gz',m.ROOT/'ops/museum-expansion-fitzwilliam-followup-review-20261007.py',m.ROOT/'ops/museum-expansion-fitzwilliam-followup-capture-20261007.py',m.ROOT/'ops/museum-expansion-fitzwilliam-followup-sources-20261007.py',m.ROOT/'AGENTS.md']
 paths += [m.ROOT/r['decision']['source_reference']['path'] for r in rs]+[m.ROOT/r['source_reference']['path'] for r in holds]
 plan['evidence']=[reference(p) for p in paths];m.save(PLAN,plan);print(json.dumps(dict(new=COUNT,existing_holdings=HCOUNT,sha256=hashlib.sha256(PLAN.read_bytes()).hexdigest())),flush=True)
def validate_plan():
 p=m.load(PLAN)
 for ref in p['evidence']:checked_reference(ref)
 assert hashlib.sha256(Path(p['backup_path']).read_bytes()).hexdigest()==p['backup_sha256'];assert prior.validate_plan()[1]==p['prior_plan_sha256'];assert p['records']==records() and p['holdings']==holding_records();return p,hashlib.sha256(PLAN.read_bytes()).hexdigest()
def citation_note(r,digest):return json.dumps(dict(plan_sha256=digest,source_record=r,policy='Source evidence retained. Existing catalogue metadata stays unchanged; new artworks remain in review. No image or display claim.'),ensure_ascii=False)
def holding_note(r,digest):return 'Official Fitzwilliam object identity and production/acquisition evidence. Editorial confidence0.95, not calibrated. '+r['decision'].get('identity_note',r['decision'].get('basis',''))+' '+r['decision']['limitation']+' Plan SHA-256 '+digest

def assert_delta(before,after,holdings,digest):
 targets={r['artwork_id'] for r in holdings};oldby={r['id']:r for r in before['artworks']};newby={r['id']:r for r in after['artworks']};assert set(oldby)==set(newby)
 for aid,old in oldby.items():
  ignored={'current_institution_id','updated_at'} if aid in targets else set();assert {k:v for k,v in old.items() if k not in ignored}=={k:v for k,v in newby[aid].items() if k not in ignored}
  if aid in targets:assert old['current_institution_id'] is None and newby[aid]['current_institution_id']==IID
 for key in ['artists','media','identifiers','museum']:assert before[key]==after[key],key
 assert [r for r in after['citations'] if r['source_id']!=SID]==before['citations'];newc=[r for r in after['citations'] if r['source_id']==SID];newh=[r for r in after['assertions'] if r['source_id']==SID];assert len(newc)==len(newh)==HCOUNT
 expected=[]
 for old in before['assertions']:
  if old['artwork_id'] in targets:
   assert old['review_state']=='review' and old['institution_id']==IID and old['superseded_by'] is None
   record=next(r for r in holdings if r['artwork_id']==old['artwork_id']);expected.append(dict(old,superseded_by=record['holding_id']))
  else:expected.append(old)
 assert [r for r in after['assertions'] if r['source_id']!=SID]==expected
 for r in holdings:
  c=next(x for x in newc if x['entity_id']==r['artwork_id']);h=next(x for x in newh if x['artwork_id']==r['artwork_id']);v=r['facts'];assert c['source_record_id']==v['source_id'] and c['source_url']==v['source_url'] and c['evidence_note']==citation_note(r,digest) and c['field_name']=='museum_expansion_holding_reconciliation'
  assert h['id']==r['holding_id'] and h['claim_type']=='holding' and h['institution_id']==IID and h['context']=='collection' and h['review_state']=='accepted' and h['superseded_by'] is None and h['source_url']==v['source_url'] and h['evidence_note']==holding_note(r,digest);assert not any(h.get(k) for k in ['display_state','gallery','venue_id','effective_from','effective_to'])

def verify(db,p,digest):
 assert_delta(p['before'],prior.snapshot(db,p['scoped_ids']),p['holdings'],digest)
 pp,pd=prior.validate_plan();assert pd==p['prior_plan_sha256'];assert prior.snapshot(db,[r['artwork_id'] for r in pp['records']])==p['prior_native_snapshot']
 rs=p['records'];ids=[r['artwork_id'] for r in rs];snap=prior.snapshot(db,ids);assert len(snap['artworks'])==len(snap['identifiers'])==len(snap['citations'])==len(snap['assertions'])==COUNT and not snap['artists'] and not snap['media']
 for r in rs:
  aid=r['artwork_id'];v=r['facts'];art=next(x for x in snap['artworks'] if x['id']==aid);assert all(art[k]==val for k,val in prior.expected_art(r).items())
  for k in ['alternate_title','description_md','primary_media_id','published_at','cultural_context','creation_place_display','creation_place_unknown_reason','current_location_text','current_location_unknown_reason','location_checked_at']:assert art[k] is None
  ident=next(x for x in snap['identifiers'] if x['entity_id']==aid);assert (ident['scheme'],ident['external_id'],ident['canonical_url'],ident['source_id'])==(prior.SCHEME,v['source_id'],v['source_url'],SID)
  c=next(x for x in snap['citations'] if x['entity_id']==aid);assert c['source_id']==SID and c['field_name']=='museum_expansion_native_metadata' and c['source_record_id']==v['source_id'] and c['source_url']==v['source_url'] and c['evidence_note']==citation_note(r,digest)
  h=next(x for x in snap['assertions'] if x['artwork_id']==aid);assert h['source_id']==SID and h['claim_type']=='holding' and h['institution_id']==IID and h['context']=='collection' and h['review_state']=='accepted' and h['superseded_by'] is None and h['source_url']==v['source_url'] and h['evidence_note']==holding_note(r,digest);assert not any(h.get(k) for k in ['display_state','gallery','venue_id','effective_from','effective_to'])
 allids=ids+[r['artwork_id'] for r in p['holdings']];assert db.execute("SELECT count(*) n FROM artworks WHERE id=ANY(%s::uuid[]) AND artline_creation_scope(creation_year_start,creation_year_end,date_precision)='eligible' AND artline_has_selection_evidence(id)",(allids,)).fetchone()['n']==30
 counts=prior.counts(db);assert counts==dict(linked=206,eligible=200)
 return dict(verified_new_records=26,existing_artworks_linked=4,previous_native_additions_preserved=163,scoped_artwork_metadata_preserved=len(p['before']['artworks']),old_citations_preserved=len(p['before']['citations']),artist_links_preserved=len(p['before']['artists']),media_links_preserved=len(p['before']['media']),identifiers_preserved=len(p['before']['identifiers']),prior_pending_assertions_superseded=2,new_citations=30,new_identifiers=26,new_accepted_holdings=30,new_images=0,new_publications=0,new_display_claims=0,current_counts=counts)

def apply(expected_sha):
 p,d=validate_plan();assert d==expected_sha
 with m.psycopg.connect('postgresql://localhost/artline',autocommit=True,row_factory=m.dict_row,options='-c timezone=UTC -c statement_timeout=180000') as db,db.transaction():
  db.execute("SET LOCAL lock_timeout='5s'");db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))");target=db.execute('SELECT current_database() db,host(inet_server_addr()) addr,inet_server_port() port').fetchone();assert target['db']=='artline' and target['addr'] in [None,'127.0.0.1','::1'] and target['port'] in [None,5432]
  if db.execute('SELECT 1 FROM sources WHERE id=%s',(SID,)).fetchone():verify(db,p,d);print('Unchanged replay:26 additions and4 holdings;zero writes',flush=True);return
  preflight(db,p);db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',([r['artwork_id'] for r in p['holdings']],));m.save(m.BACKUP/(KEY+'-reviewed-plan.json.gz'),p)
  db.execute('INSERT INTO sources(id,slug,name,source_type,base_url) VALUES(%s,%s,%s,%s,%s)',(SID,SLUG,'Fitzwilliam selected additions and reconciled holdings,7 October2026','collection_page',f.BASE))
  for r in p['records']:
   v=r['facts'];aid=r['artwork_id'];rc=r['native']['native']['capture']['receipt'];db.execute("""INSERT INTO artworks(id,slug,title,normalized_title,date_display,creation_year_start,creation_year_end,date_precision,work_type,medium_text,dimensions_text,accession_number,status,research_candidate,unlinked_creator_label,object_form,created_by,updated_by) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'review',true,%s,%s,%s,%s)""",(aid,r['slug'],v['title'],m.norm(v['title']),v['date_display'],v['first'],v['last'],v['date_precision'],v['work_type'],v['medium'],v['dimensions_text'],v['inventory'],v['creator_label'],v['object_form'],m.ACTOR,m.ACTOR))
   db.execute("INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at) VALUES('artwork',%s,%s,%s,%s,%s,%s)",(aid,prior.SCHEME,v['source_id'],v['source_url'],SID,rc['retrieved_at']))
   db.execute("INSERT INTO citations(entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by) VALUES('artwork',%s,'museum_expansion_native_metadata',%s,%s,%s,%s,%s,%s)",(aid,SID,v['source_id'],v['source_url'],citation_note(r,d),rc['retrieved_at'],m.ACTOR))
   db.execute("INSERT INTO artwork_location_assertions(artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state) VALUES(%s,'holding',%s,'collection',%s,%s,%s,%s,'accepted')",(aid,IID,SID,v['source_url'],holding_note(r,d),rc['retrieved_at']))
  for r in p['holdings']:
   aid=r['artwork_id'];v=r['facts'];rc=r['native']['native']['capture']['receipt'];db.execute("INSERT INTO citations(entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by) VALUES('artwork',%s,'museum_expansion_holding_reconciliation',%s,%s,%s,%s,%s,%s)",(aid,SID,v['source_id'],v['source_url'],citation_note(r,d),rc['retrieved_at'],m.ACTOR))
   db.execute("INSERT INTO artwork_location_assertions(id,artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state) VALUES(%s,%s,'holding',%s,'collection',%s,%s,%s,%s,'accepted')",(r['holding_id'],aid,IID,SID,v['source_url'],holding_note(r,d),rc['retrieved_at']))
   for old in [x for x in p['before']['assertions'] if x['artwork_id']==aid]:db.execute('UPDATE artwork_location_assertions SET superseded_by=%s WHERE id=%s',(r['holding_id'],old['id']))
  result=verify(db,p,d)
 m.save(RUN/(KEY+'-applied.json'),dict(at=m.now(),plan_sha256=d,created=26,existing_links=4,local_only=True,verification=result));print(json.dumps(result),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','apply','verify']);p.add_argument('--plan-sha');a=p.parse_args()
 if a.command=='prepare':prepare()
 elif a.command=='apply':assert a.plan_sha;apply(a.plan_sha)
 else:
  p,d=validate_plan()
  with m.connect() as db:print(json.dumps(verify(db,p,d)),flush=True)
