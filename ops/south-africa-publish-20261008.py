#!/usr/bin/env python3
"""Source-pinned, bounded South African catalogue additions; explicit apply only."""
import argparse,collections,copy,csv,gzip,importlib.util,json,re,subprocess
from pathlib import Path
from psycopg import sql
from psycopg.types.json import Jsonb

spec=importlib.util.spec_from_file_location('sa',Path(__file__).with_name('south-africa-20261008.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
RUN=m.RUN;BACKUP=m.BACKUP;ROOT=m.ROOT;norm=m.norm;uid=m.uid
DRAFT=RUN/'publication-plan.json.gz';PLAN=RUN/'publication-plan-final.json.gz';FIELD='south_africa_20261008';ACTOR=m.m.ACTOR
def safe(x):return json.loads(json.dumps(x,default=str))
def nk(x):return ' '.join(sorted(norm(x).split()))
def raw(rc):
 assert rc['status']==200
 b=gzip.decompress((ROOT/rc['body_path']).read_bytes());assert m.m.sha(b)==rc['sha256'];return b
def records(db,t,ids,col='id'):
 order='artwork_id' if t in ['artwork_artists','artwork_media'] else 'id'
 return [r['r'] for r in db.execute(sql.SQL('SELECT to_jsonb(t) r FROM {} t WHERE {}=ANY(%s::uuid[]) ORDER BY {}').format(sql.Identifier(t),sql.Identifier(col),sql.Identifier(order)),(ids,))]

def supplement():
 out=[]
 def add(inst,source,sid,title,artist,date,medium,dimensions,accession,rc,fields,basis,**extra):
  d=m.dates(date);assert d
  out.append(dict(key=source+'/'+sid,source_kind=source,source_id=sid,institution_key=inst,title=title,creator_label=artist,medium=medium,dimensions=dimensions,accession=accession,work_type=m.kind(medium),receipt=rc,source_url=rc['final_url'],raw_fields=fields,identity_basis=basis,**d,**extra))
 rc=m.load(RUN/'jag-handbook-receipt.json');pages=subprocess.check_output(['pdftotext','-layout','-','-'],input=raw(rc)).decode().split('\f')
 for sid,title,date,dim in [('yellow-houses','Yellow Houses: A Street in Sophiatown','1940','50,8 x 74,5 cm'),('beyond-the-gate','Beyond the Gate','c.1940','30,5 x 40,3 cm')]:
  assert title in pages[4]
  add('jag','jag-handbook',sid,title,'Gerard Sekoto',date,'Oil on board',dim,None,rc,dict(pdf_page=5,printed_page=4,caption_verified_visually=True,collection='Johannesburg Art Gallery'), 'JAG Education Officer-authored handbook, printed page 4: original captions visually verified, including two distinct works and collection credit. No current display claim.')
 rc=m.load(RUN/'tatham-thesis-receipt.json');pages=subprocess.check_output(['pdftotext','-layout','-','-'],input=raw(rc)).decode().split('\f')
 rows=[
  ('636/79','Pont de la rivière du Fay (Indre)','Jules Dupré','1837','Oil on canvas laid down on panel','603 mm x 494 mm',[35]),
  ('130/24','Palais des Césars','Henri-Joseph Harpignies','1864','Watercolour on paper','255 mm x 389 mm',[47]),
  ('149/24','Col de Balbin','Johan Barthold Jongkind','1870','Watercolour on paper','150 mm x 230 mm',[48,50,51]),
  ('150/24','The shepherd','Johan Barthold Jongkind','1864','Watercolour on paper','165 mm x 305 mm',[51,53,54]),
  ('133/24','The wayside','Auguste-Louis Lepère','1893','Pastel on paper (brown pastel paper)','201 mm x 277 mm',[65,66,67]),
  ('135/24','Calle Roquebrune','Auguste-Louis Lepère','1910','Gouache on paper','330 mm x 410 mm',[69]),
  ('738/83','Self-sown pines','Lucien Pissarro','1916','Oil on board','340 mm x 452 mm',[78,79,80]),
  ('810/86','Petit lac entouré de peupliers','Auguste Herbin','1903','Oil on canvas','352 mm x 460 mm',[85,86,87]),
 ]
 for acc,title,artist,date,medium,dim,pp in rows:
  excerpt='\n'.join(pages[p-1] for p in pp);assert acc in excerpt
  assert re.search(r'Date of composition:\s*'+r'\s*'.join(date),excerpt)
  add('tatham','tatham-thesis',acc,title,artist,date,medium,dim,acc,rc,dict(pdf_pages=pp,caption_verified_visually=True,transcription_note='Accents and italic OCR errors transcribed from rendered original; acquisition year excluded.',catalogue_year=2004), 'Hua Yang 2004 primary collection catalogue, prepared with gallery access and 2003 photographs. Exact inventory and explicit composition date, visually verified. Historical holding evidence; present display and subsequent movement unverified.',confidence=.88)
 d=m.load(RUN/'wits-page.json');rc=d['receipt'];soup=m.m.BeautifulSoup(raw(rc),'html.parser');caption=next(i['alt'] for i in soup.select('img[alt]') if 'Black Hair' in i['alt'])
 assert caption=='Gerard Sekoto, South Africa, Black Hair, Charcoal on paper, 1949, The Sekoto Collection'
 add('wits','wits','black-hair','Black Hair','Gerard Sekoto','1949','Charcoal on paper',None,None,rc,dict(caption=caption,collection='The Sekoto Collection'), 'Official Wits collection page caption and collection history identify this drawing and its 2010 donation to WAM.')
 d=m.load(RUN/'oliewenhuis-more-page.json');rc=d['receipt'];text=m.m.BeautifulSoup(raw(rc),'html.parser').get_text(' ',strip=True)
 assert 'Eduardo Villa’s' in text and 'Torso (1968)' in text
 add('oliewenhuis','oliewenhuis','torso-1968','Torso','Eduardo Villa','1968','Bronze',None,None,rc,dict(exhibition='Creatively Contrasted: New views on the Permanent Collection',date='1 December 2023 – 3 March 2024',museum_creation_caption='Eduardo Villa’s Torso (1968) in bronze'), 'National Museum official Oliewenhuis exhibition history explicitly identifies Torso (1968) as a permanent collection purchase. Exhibition is historical, not a current display assertion.')
 # Individually selected medieval gold artworks, including anonymous creators.
 gold={'owFMZ5MvsbYhOA','SwFtsedzESvAHQ','SQFYXk0Zy1__eQ','3QHVKTxhHeBcpw','tgGs6Od1HTU9YA','YgFcxBQKmKZLfg'}
 index={r['source_id']:r for r in m.load(RUN/'gac-index-selection.json.gz')['rows']}
 for h in m.load(RUN/'gac-held.json.gz'):
  if h['source_id'] not in gold:continue
  f=h['fields'];r=copy.deepcopy(index[h['source_id']]);assert h['provider']=='University of Pretoria Museums Pretoria, South Africa' and f['Medium']=='Gold'
  r.update(m.dates(f['Date Created']));r.update(key='gac/'+h['source_id'],source_kind='gac',title=f['Title'],creator_label=None,cultural_context='Mapungubwe',medium='Gold',dimensions=f.get('Physical Dimensions'),accession=None,work_type='metalwork',receipt=h['receipt'],raw_fields=f,provider=h['provider'],identity_basis='Individual university collection record for a distinct medieval gold object. Archive credit is retained as source evidence, not treated as a medieval maker. Close-up duplicate view of the rhinoceros excluded.')
  out.append(r)
 m.save(RUN/'supplement-selected.json.gz',out);print('Supplement',len(out))

INSTITUTIONS={
 'rupert-foundation':('Rupert Art Foundation','Stellenbosch','foundation','https://rupertmuseum.org/collections/','Collection managed by the Rupert Museum in Stellenbosch.'),
 'rembrandt-foundation':('Rembrandt van Rijn Art Foundation','Stellenbosch','foundation','https://rupertmuseum.org/collections/','Collection managed by the Rupert Museum in Stellenbosch.'),
 'mandela':('Nelson Mandela Metropolitan Art Museum','Port Elizabeth','museum','https://www.artmuseum.co.za/','Municipal art museum in Port Elizabeth.'),
 'up':('University of Pretoria Museums','Pretoria','museum','https://artsandculture.google.com/partner/university-of-pretoria-museums','University collections in Pretoria, including the Mapungubwe Collection.'),
 'wits':('Wits Art Museum','Johannesburg','museum','https://www.wits.ac.za/wam/','Art museum at the University of the Witwatersrand.'),
 'oliewenhuis':('Oliewenhuis Art Museum','Bloemfontein','museum','https://nationalmuseum.co.za/oliewenhuis-collections/','Art museum at 16 Harry Smith Street, Bloemfontein, administered by the National Museum.'),
 'tatham':('Tatham Art Gallery','Pietermaritzburg','museum','https://www.tathamartgallery.org.za/','Municipal art collection in Pietermaritzburg.'),
}
SOURCE_DEFS={
 'rupert':('Rupert Museum — managed foundation collection catalogue','https://rupertmuseum.org/collections/'),
 'mandela':('Nelson Mandela Metropolitan Art Museum — collection catalogue','https://www.artmuseum.co.za/'),
 'wits':('Wits Art Museum — official collection catalogue','https://www.wits.ac.za/wam/collections/'),
 'oliewenhuis':('National Museum — Oliewenhuis permanent collection','https://nationalmuseum.co.za/oliewenhuis-collections/'),
 'jag-handbook':('Johannesburg Art Gallery — official Art Handbook','https://arts-culture-heritage.joburg/'),
 'tatham-thesis':('Hua Yang — Tatham collection catalogue, University of Natal, 2004','https://researchspace.ukzn.ac.za/items/2ffd4da9-497e-4c3f-8310-4f363857c44b'),
}
QUALIFIED=r'\b(?:after|workshop|studio|circle|school|follower|formerly|possibly|probably|attributed|copy|publisher|printer|nee|unattributed|onbekend)\b'
ALIASES={
 'Jacob Hendrik Pierneef':['Hendrik Pierneef','JH Pierneef','Jacobus Hendrik Pierneef'],
 'George Pemba':['George Milwa Mnyaluza Pemba'],
 'Maggie Laubser':['Maggie (Maria Magdalena) Laubser'],
 'Walter Battiss':['Walter Whall Battiss'],
 'Maud Sumner':['Maud Eyston Sumner'],
 'Gregoire Boonzaier':['Gregoire Johannes Boonzaier'],
 'Jean Welz':['Jean Max Friedrich Welz'],
 'Adolph Jentsch':['Adolph Stephan Friedrich Jentsch'],
 'Thomas Baines':['(John) Thomas Baines'],
 'Alexander Podlashuc':['Alexander Cecil Podlashuc'],
 'Erich Mayer':['Erich (Ernst Karl) Mayer'],
 'Fred Page':['Fred (Frederick Hutchinson) Page'],
 'Sydney Kumalo':['Sidney Kumalo'],
 'Sir Cedric, Bt Morris':['Cedric Lockwood Morris'],
 'Sir Robert Strange':['Robert Strange'],
 'Kunisada':['Utagawa Kunisada I'],
}

def candidates():
 base=m.load(RUN/'production-baseline.json.gz');works=sum([m.load(RUN/f) for f in ['rupert-selected-v2.json.gz','mandela-selected.json.gz','gac-selected.json.gz','supplement-selected.json.gz']],[])
 held=[];retained=[]
 for w in works:
  reason=None;f=w['raw_fields']
  if w['source_kind']=='gac':
   if re.search(r'private|courtesy|Ditsong',f.get('Rights') or '',re.I):reason='Provider includes borrowed/private material; ownership not confirmed'
   elif w['institution_key']=='iziko' and (w['date_display'] in ['1900','c.1600']):reason='Demonstrated default/creator-lifespan date conflict in Iziko feed; no invented correction'
   elif w['source_id']=='fQGTV_nXMcXQow':reason='Wilhelmina jubilee plate 1850 field conflicts with subject and maker birth date; do not treat birth/acquisition as creation'
   elif w['source_id']=='cwGFtnpJiV0jrQ':reason='Duplicate Google record of Rembrandt Pottery New Year 1914 plate; same exact title, maker, date, dimensions and medium as rQFPEEThDdD-1g; retain one object pending distinct inventory evidence'
   elif w['institution_key']=='iziko' and '/south-african-national-gallery' not in f.get('External Link',''):reason='Iziko umbrella provider does not establish specific gallery'
   if f.get('Type') in ['Ceramic','Ceramics']:w['work_type']='ceramic'
  if w['source_kind']=='rupert' and w['work_type']=='sculpture' and ('Bourdelle' in w['creator_label'] or re.search(r'\d/\d',w['medium'])):reason='Edition-numbered bronze/model date; physical casting date remains unresolved'
  if reason:held.append(dict(key=w['key'],reason=reason));continue
  if w['source_kind']=='mandela':
   sub=f.get('Sub number')
   if sub:w['accession']=sub.lstrip(': ').strip()
   if w['source_id']=='10468':w['creator_label']='Edward Orme (Publisher); Clarke & M Dubourg, Printer';w['creator_label_note']='Individual page publisher and index printmaker labels preserved together, without assigning publisher a primary creator role.'
   if w['source_id']=='9979':held.append(dict(key=w['key'],reason="Title Palma '62 conflicts with Date 1961; retain evidence for resolution"));continue
  w.setdefault('confidence',.96);w['confidence_basis']='Editorial confidence, not a calibrated probability: official collection record, native object identity and explicit creation date. '+('Historical 2004 primary catalogue; subsequent collection movement not independently established.' if w['source_kind']=='tatham-thesis' else 'Current display is unknown.')
  w.update(id=uid('artwork/'+w['key']),slug='south-africa-'+norm(w['title']).replace(' ','-')[:80]+'-'+uid(w['key'])[:8],external_scheme='south-africa-object',external_id=w['key'],description=None,creation_place=None,object_form=None,artist_id=None,attribution_role='primary',creator_basis='Original creator label retained without an unverified person link.')
  w.setdefault('cultural_context',None)
  retained.append(w)
 works=retained
 # One selected museum-managed authority page identifies a person; dated objects
 # support documented activity only. No invented birth/death or biography.
 byname=collections.defaultdict(set);amap={a['id']:a for a in base['artists']}
 for a in base['artists']:
  for name in [a['display_name'],a['sort_name'],a['normalized_name']]:byname[nk(name)].add(a['id'])
 for a in base['artist_aliases']:byname[nk(a['alias'])].add(a['artist_id'])
 for name,aliases in ALIASES.items():
  ids=byname[nk(name)]
  if len(ids)==1:
   for alias in aliases:byname[nk(alias)].update(ids)
 artists=[];authority_holds=[]
 for a in m.load(RUN/'rupert-artist-pages.json.gz'):
  selected=[w for w in works if w['source_kind']=='rupert' and w['creator_label']==a['label']]
  if not selected:continue
  name=' '.join(reversed([x.strip() for x in a['label'].split(',',1)])) if ',' in a['label'] else a['label'].strip()
  if byname[nk(name)]:continue
  if len(norm(name).split())<2 or any(len(x)==1 for x in norm(name).split()) or name=='Paul Du Toit' or norm(name)=='paul du toit':
   authority_holds.append(dict(name=name,reason='Initial-only/surname-only or ambiguous namesake; preserve source label'));continue
  assert norm(a['heading'])==norm(a['label'])
  aliases=ALIASES.get(name,[]);ids=set().union(*(byname[nk(x)] for x in aliases)) if aliases else set()
  if ids:
   authority_holds.append(dict(name=name,reason='Alternate name already links another authority'));continue
  # Flag a possible fuller name before making a second person authority.
  tokens=set(norm(name).split());near=[old for old in base['artists'] if len(tokens)>=2 and tokens<=set(norm(old['display_name']).split())]
  if near:
   authority_holds.append(dict(name=name,reason='Possible longer existing name',candidates=near));continue
  first=min(w['first'] for w in selected);last=max(w['last'] for w in selected);display='Documented works: '+(str(first) if first==last else str(first)+'–'+str(last))
  art=dict(id=uid('artist/'+a['url']),slug='south-africa-'+norm(name).replace(' ','-'),display_name=name,sort_name=a['label'].strip(),normalized_name=norm(name),entity_type='person',birth_year=None,death_year=None,birth_display=None,death_display=None,birth_precision='unknown',death_precision='unknown',active_start_year=first,active_end_year=last,activity_display=display,timeline_start_year=first,timeline_end_year=last,timeline_display=display,timeline_basis='activity',source_url=a['url'],receipt=a['receipt'],source_record_id=a['url'].rstrip('/').rsplit('/',1)[-1],aliases=[a['label'].strip()]+aliases,evidence_work_keys=[w['key'] for w in selected])
  artists.append(art);amap[art['id']]=art
  for label in [name,a['label']]+aliases:byname[nk(label)].add(art['id'])
 for w in works:
  ids=byname[nk(w['creator_label'])]
  # An explicitly listed expanded personal name is accepted; role and attribution
  # qualifications elsewhere remain object-level labels.
  mapped_alias=any(w['creator_label'] in vals for vals in ALIASES.values())
  if len(ids)==1 and (mapped_alias or not re.search(QUALIFIED,w['creator_label'] or '',re.I)):
   a=amap[next(iter(ids))]
   if a.get('birth_year') and w['last']<a['birth_year'] or a.get('death_year') and w['first']>a['death_year']:
    held.append(dict(key=w['key'],reason='Creation conflicts with matched creator lifespan'));w['hold']=True;continue
   w['artist_id']=a['id'];w['creator_basis']='Unique exact full name/authority alias, or individually reconciled expanded name; compatible explicit creation date. Source spelling retained in citation.'
 works=[w for w in works if not w.get('hold')]
 used={w['artist_id'] for w in works};artists=[a for a in artists if a['id'] in used]
 result=dict(at=m.m.now(),authorization='User requests South African expansion; prior explicit direct production publication and permission to add painters persist. Keep known information; do not invent missing details.',artworks=works,artists=artists,held=held,authority_holds=authority_holds)
 m.save(RUN/'candidate-plan.json.gz',result)
 print('Candidates',len(works),'new artists',len(artists),'linked works',sum(bool(w['artist_id']) for w in works),'held',len(held),'institutions',dict(collections.Counter(w['institution_key'] for w in works)))

def duplicate_audit(db,works):
 keys=[w['key'] for w in works];urls=[w['source_url'] for w in works if w['source_kind'] in ['gac','rupert','mandela']]
 external=safe(db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND (external_id=ANY(%s) OR canonical_url=ANY(%s))",(keys,urls)).fetchall())
 citations=safe(db.execute("SELECT entity_id::text,source_url FROM citations WHERE entity_type='artwork' AND source_url=ANY(%s)",(urls,)).fetchall())
 scoped=safe(db.execute('SELECT id::text,current_institution_id::text,title,accession_number FROM artworks WHERE current_institution_id=ANY(%s::uuid[])',([w['institution_id'] for w in works],)).fetchall())
 bykey=collections.defaultdict(set);byurl=collections.defaultdict(set);byacc=collections.defaultdict(set);bytitle=collections.defaultdict(set)
 for r in external:
  bykey[r['external_id']].add(r['entity_id'])
  if r['canonical_url']:byurl[r['canonical_url']].add(r['entity_id'])
 for r in citations:byurl[r['source_url']].add(r['entity_id'])
 for r in scoped:
  if r['accession_number']:byacc[(r['current_institution_id'],norm(r['accession_number']))].add(r['id'])
  bytitle[(r['current_institution_id'],norm(r['title']))].add(r['id'])
 found={}
 for w in works:
  ids=bykey[w['key']]|byurl[w['source_url']]|byacc[(w['institution_id'],norm(w['accession']))]|bytitle[(w['institution_id'],norm(w['title']))]
  if ids:found[w['key']]=sorted(ids)
 return dict(at=m.m.now(),matches=found,external=external,citations=citations,scoped_count=len(scoped))

def prepare():
 plan=m.load(RUN/'candidate-plan.json.gz');base=m.load(RUN/'production-baseline.json.gz')
 existing={r['r']['slug']:r['r'] for r in base['institutions']};inst={'jag':existing['africa-jag'],'iziko':existing['wikimedia-museum-q1419469']}
 places={p['name']:p for p in base['places']};newplaces=[];newinst=[]
 identities=m.load(RUN/'institution-identities.json.gz')['institutions'];used_keys={w['institution_key'] for w in plan['artworks']}
 for key,(name,city,kind,website,description) in INSTITUTIONS.items():
  if key not in used_keys:continue
  assert not any(norm(i['name'])==norm(name) for i in identities)
  if city not in places:
   p=dict(id=uid('place/'+city),name=city,normalized_name=norm(city),country_code='ZA');places[city]=p;newplaces.append(p)
  i=dict(id=uid('institution/'+key),slug='south-africa-'+key,name=name,normalized_name=norm(name),place_id=places[city]['id'],website_url=website,kind=kind,status='published',description=description)
  inst[key]=i;newinst.append(i)
 sources={};newsrc=[]
 for key,(name,url) in SOURCE_DEFS.items():
  src=dict(id=uid('source/'+key),slug='south-africa-20261008-'+key,name=name,source_type='book' if key=='tatham-thesis' else 'collection_page',base_url=url,is_active=True);sources[key]=src;newsrc.append(src)
 sources['gac']=next(s for s in base['sources'] if s['slug']=='africa-research-20261008-artsandculture-google-com')
 for w in plan['artworks']:
  i=inst[w['institution_key']];w.update(institution_id=i['id'],institution_name=i['name'],institution_slug=i['slug'],source_database_id=sources[w['source_kind']]['id'])
 with m.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY')
  audit=duplicate_audit(db,plan['artworks']);m.save(RUN/'publication-duplicate-audit.json.gz',audit)
  selected=[];seen=set()
  for w in plan['artworks']:
   if w['key'] in audit['matches']:
    plan['held'].append(dict(key=w['key'],reason='Existing production object retained unchanged',ids=audit['matches'][w['key']]));continue
   assert w['key'] not in seen;seen.add(w['key']);selected.append(w)
  plan['artworks']=selected
  used={w['artist_id'] for w in selected};plan['artists']=[a for a in plan['artists'] if a['id'] in used]
  for a in plan['artists']:
   works=[w for w in selected if w['artist_id']==a['id']];first=min(w['first'] for w in works);last=max(w['last'] for w in works);display='Documented works: '+(str(first) if first==last else str(first)+'–'+str(last))
   a.update(active_start_year=first,active_end_year=last,timeline_start_year=first,timeline_end_year=last,activity_display=display,timeline_display=display,evidence_work_keys=[w['key'] for w in works])
  oldartists=sorted(used-{a['id'] for a in plan['artists']}-{None})
  protected={t:records(db,t,ids) for t,ids in [('artists',oldartists),('institutions',[inst[k]['id'] for k in ['jag','iziko']]),('sources',[sources['gac']['id']]),('places',[p['id'] for p in base['places']]),('artworks',[w['id'] for w in base['artworks']])]}
  for table,col in [('artwork_artists','artwork_id'),('artwork_media','artwork_id'),('artwork_location_assertions','artwork_id'),('external_identifiers','entity_id'),('citations','entity_id')]:
   protected[table]=records(db,table,[w['id'] for w in base['artworks']],col)
  for table,rows in [('artists',plan['artists']),('artworks',selected),('institutions',newinst),('sources',newsrc)]:
   assert not db.execute(sql.SQL('SELECT 1 FROM {} WHERE id=ANY(%s::uuid[]) OR slug=ANY(%s) LIMIT 1').format(sql.Identifier(table)),([r['id'] for r in rows],[r['slug'] for r in rows])).fetchone(),table+' conflict'
  # Check the current artist directory and aliases, not just the earlier snapshot.
  now_names={nk(r['display_name']) for r in db.execute('SELECT display_name FROM artists')}|{nk(r['alias']) for r in db.execute('SELECT alias FROM artist_aliases')}
  assert not any(nk(a['display_name']) in now_names for a in plan['artists'])
  # Record the actual bounded, indexed artist lookup plan. No collection-wide CTE.
  explain=db.execute('EXPLAIN (FORMAT JSON) SELECT a.id,a.title FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id WHERE aa.artist_id=ANY(%s::uuid[])',(oldartists,)).fetchone();m.save(RUN/'artist-lookup-query-plan.json',explain)
 plan.update(at=m.m.now(),places=newplaces,institutions=newinst,institution_map=inst,sources=newsrc,source_map=sources,protected=protected)
 plan['validation']=validate(plan);m.save(DRAFT,plan);m.save(BACKUP/DRAFT.name,plan)
 print('Prepared',plan['validation'],'collections',dict(collections.Counter(w['institution_name'] for w in selected)),flush=True)

def finalize():
 plan=m.load(DRAFT);rc=m.load(RUN/'vucht-wikidata-receipt.json');entity=json.loads(raw(rc))['entities']['Q18516533']
 assert entity['labels']['en']['value']=='Gerrit van Vucht' and 'Gerrit Van Vught' in [v['value'] for v in entity['aliases']['en']]
 removed=next(a for a in plan['artists'] if a['display_name']=='Gerrit Van Vught');existing='3c2fa641-da1a-5574-8376-b5bec68bae57'
 with m.connect() as db:
  assert db.execute("SELECT 1 FROM external_identifiers WHERE entity_type='artist' AND entity_id=%s AND scheme='wikidata' AND external_id='Q18516533'",(existing,)).fetchone()
  known=records(db,'artists',[existing]);assert known[0]['birth_year']==1610 and known[0]['death_year']==1697
 plan['artists']=[a for a in plan['artists'] if a['id']!=removed['id']]
 for w in plan['artworks']:
  if w['artist_id']==removed['id']:
   w['artist_id']=existing;w['creator_basis']='Rupert artist label Gerrit Van Vught is an explicit alias of Wikidata Q18516533, already attached to the existing Gerrit van Vucht profile; 1642 is compatible with the documented 1610–1697 lifespan. Source spelling preserved.';w['creator_identity_evidence']=dict(receipt=rc,entity_id='Q18516533',alias='Gerrit Van Vught')
 plan['protected']['artists']=sorted(plan['protected']['artists']+known,key=lambda a:a['id'])
 plan['authority_holds'].append(dict(name=removed['display_name'],reason='Reconciled spelling variant with existing Gerrit van Vucht; duplicate profile not created.',existing_artist_id=existing,evidence=rc))
 plan['supersedes_sha256']=m.m.sha(DRAFT.read_bytes());plan['at']=m.m.now();plan['validation']=validate(plan)
 m.save(PLAN,plan);m.save(BACKUP/PLAN.name,plan);print('Final plan',plan['validation'],flush=True)

def validate(plan):
 works=plan['artworks'];assert 1<=len(works)<=600
 assert len({w['key'] for w in works})==len(works)==len({w['id'] for w in works})
 assert len({w['id'] for w in plan['artists']})==len(plan['artists'])
 verified={};within=collections.defaultdict(list)
 for w in works:
  assert w['title'] and w['work_type']!='unknown' and w['confidence']>=.8
  assert m.dates(w['date_display'])=={k:w[k] for k in ['first','last','date_display','date_precision']}
  assert w['first']<=w['last']<=1970 and not w.get('display_state') and not w.get('venue_id')
  assert not w['artist_id'] or not re.search(r'\b(?:publisher|printer|unattributed|onbekend|after|workshop|circle|attributed)\b',w['creator_label'] or '',re.I)
  assert w['institution_id']==plan['institution_map'][w['institution_key']]['id']
  assert w['source_database_id']==plan['source_map'][w['source_kind']]['id']
  rc=w['receipt'];b=verified.setdefault(rc['sha256'],raw(rc));f=w['raw_fields']
  if w['source_kind'] in ['rupert','mandela','gac']:
   soup=m.m.BeautifulSoup(b,'html.parser')
   if w['source_kind']=='rupert':
    lines=soup.select_one('.collection-left-sub').get_text('\n',strip=True).splitlines()
    assert lines==f['lines'] and norm(lines[0])==norm(w['title']) and lines[1]==w['date_display'] and lines[-1]==w['accession'] and lines[-2]==w['collection_owner']
    assert 'Medium: '+w['medium'] in lines
    assert norm(soup.select_one('a[href*="/artist/"]').get_text(' ',strip=True))==norm(w['creator_label'])
    assert w['work_type']!='sculpture' or not ('Bourdelle' in w['creator_label'] or re.search(r'\d/\d',w['medium']))
   elif w['source_kind']=='mandela':
    label=soup.find('b',string=re.compile('Name of Artist'));actual=m.labelled_fields(label.find_parent('table'));assert actual==f
    assert actual['Title of artwork']==w['title'] and actual['Date']==w['date_display'] and actual['Medium']==w['medium']
    assert w['accession']==(actual.get('Sub number') or actual['Accession number']).lstrip(': ').strip()
    assert w['creator_label']==actual['Name of Artist'] or w['source_id']=='10468' and w['creator_label']=='Edward Orme (Publisher); Clarke & M Dubourg, Printer' and w['index_fields']['Name of Artist']=='Clarke & M Dubourg, Printer'
   else:
    actual={}
    for li in soup.select('li.XD0Pkb'):
     label=li.select_one('.PUhAff')
     if label:actual[label.get_text(' ',strip=True).rstrip(':')]=li.get_text(' ',strip=True)[len(label.get_text(' ',strip=True)):].strip()
    assert actual==f and f['Title']==w['title'] and f['Date Created']==w['date_display'] and f.get('Medium')==w['medium']
    assert w['creator_label']==f.get('Creator') or w['creator_label'] is None and w['work_type']=='metalwork' and f.get('Creator') in ['Unattributed','Mapungubwe Archive']
    assert not re.search(r'private|courtesy|Ditsong',f.get('Rights') or '',re.I)
    if w['institution_key']=='iziko':assert '/south-african-national-gallery' in f.get('External Link','') and w['date_display'] not in ['1900','c.1600']
  if w['accession']:within[(w['institution_id'],norm(w['accession']))].append(w['key'])
 assert not any(len(v)>1 for v in within.values()),[(k,v) for k,v in within.items() if len(v)>1]
 for a in plan['artists']:
  soup=m.m.BeautifulSoup(raw(a['receipt']),'html.parser');assert norm(soup.select_one('h1').get_text(' ',strip=True))==norm(a['sort_name'])
  assert a['birth_year'] is None and a['death_year'] is None and a['timeline_basis']=='activity'
  aw=[w for w in works if w['artist_id']==a['id']];assert aw and a['active_start_year']==min(w['first'] for w in aw) and a['active_end_year']==max(w['last'] for w in aw)
 return dict(artworks=len(works),artists=len(plan['artists']),institutions_added=len(plan['institutions']),collections=len({w['institution_id'] for w in works}),source_captures=len(verified))

def insert(db,table,rows):
 if not rows:return
 cols=list(rows[0]);assert all(list(r)==cols for r in rows)
 cmd=sql.SQL('INSERT INTO {} ({}) VALUES ({})').format(sql.Identifier(table),sql.SQL(',').join(map(sql.Identifier,cols)),sql.SQL(',').join(sql.Placeholder() for _ in cols))
 with db.cursor() as cur:
  for part in m.m.chunks(rows,200):cur.executemany(cmd,[[r[c] for c in cols] for r in part])

def payloads(plan,digest):
 out=collections.defaultdict(list);when=m.m.now()
 for t in ['places','institutions','sources']:out[t]=copy.deepcopy(plan[t])
 def citation(entity,ident,source,url,record,evidence,retrieved):
  out['citations'].append(dict(id=uid('citation/'+entity+'/'+ident),entity_type=entity,entity_id=ident,field_name=FIELD,source_id=source,source_record_id=record,source_url=url,evidence_note=json.dumps(dict(plan_sha256=digest,decision=evidence),ensure_ascii=False),retrieved_at=retrieved,created_by=ACTOR))
 for i in plan['institutions']:
  w=next(w for w in plan['artworks'] if w['institution_id']==i['id']);citation('institution',i['id'],w['source_database_id'],w['source_url'],w['source_id'],dict(institution=i,holding_evidence=w['identity_basis'],receipt=w['receipt']),w['receipt']['retrieved_at'])
 acols='id slug display_name sort_name normalized_name entity_type birth_year death_year birth_display death_display birth_precision death_precision active_start_year active_end_year activity_display timeline_start_year timeline_end_year timeline_display timeline_basis'.split()
 for a in plan['artists']:
  row={k:a[k] for k in acols};row.update(status='published',created_by=ACTOR,updated_by=ACTOR,published_at=when);out['artists'].append(row)
  seen={norm(a['display_name'])}
  for label in a['aliases']:
   key=norm(label)
   if key in seen:continue
   seen.add(key);out['artist_aliases'].append(dict(id=uid('alias/'+a['id']+'/'+key),artist_id=a['id'],alias=label,normalized_alias=key,alias_type='alternate'))
  sid=plan['source_map']['rupert']['id'];out['external_identifiers'].append(dict(id=uid('external/artist/'+a['id']),entity_type='artist',entity_id=a['id'],scheme='rupert-artist',external_id=a['source_record_id'],canonical_url=a['source_url'],source_id=sid,retrieved_at=a['receipt']['retrieved_at']))
  citation('artist',a['id'],sid,a['source_url'],a['source_record_id'],dict(authority=a,policy='Official named person catalogue. Timeline shows only documented artwork activity; lifespan and biography remain unknown.'),a['receipt']['retrieved_at'])
 mapping=dict(title='title',date_display='date_display',creation_year_start='first',creation_year_end='last',date_precision='date_precision',work_type='work_type',medium_text='medium',dimensions_text='dimensions',description_md='description',creation_place_display='creation_place',accession_number='accession',unlinked_creator_label='creator_label',cultural_context='cultural_context',object_form='object_form')
 for w in plan['artworks']:
  row=dict(id=w['id'],slug=w['slug'],normalized_title=norm(w['title']));row.update({k:w[v] for k,v in mapping.items()});row.update(status='published',research_candidate=False,created_by=ACTOR,updated_by=ACTOR,published_at=when);out['artworks'].append(row)
  if w['artist_id']:out['artwork_artists'].append(dict(artwork_id=w['id'],artist_id=w['artist_id'],attribution_role=w['attribution_role'],attribution_note=w['creator_basis']+' Original source label: '+w['creator_label']))
  out['external_identifiers'].append(dict(id=uid('external/artwork/'+w['key']),entity_type='artwork',entity_id=w['id'],scheme=w['external_scheme'],external_id=w['external_id'],canonical_url=w['source_url'],source_id=w['source_database_id'],retrieved_at=w['receipt']['retrieved_at']))
  citation('artwork',w['id'],w['source_database_id'],w['source_url'],w['source_id'],dict(artwork=w,policy='Selected, source-backed creation through 1970; accepted collection holding only. Unknown details retained; no current display assertion or image attachment.'),w['receipt']['retrieved_at'])
  out['artwork_location_assertions'].append(dict(id=uid('holding/'+w['key']),artwork_id=w['id'],claim_type='holding',institution_id=w['institution_id'],context='collection',source_id=w['source_database_id'],source_url=w['source_url'],evidence_note=w['identity_basis']+' '+w['confidence_basis'],checked_at=w['receipt']['retrieved_at'],review_state='accepted'))
 out['source_institutions']=[dict(source_id=s,institution_id=i) for s,i in sorted({(w['source_database_id'],w['institution_id']) for w in plan['artworks']})]
 return out

def protect(db,plan,lock=False):
 for table,expected in plan['protected'].items():
  if table in ['artwork_artists','artwork_media','artwork_location_assertions','external_identifiers','citations']:
   col='entity_id' if table in ['external_identifiers','citations'] else 'artwork_id';ids=[r['id'] for r in plan['protected']['artworks']]
  else:col='id';ids=[r['id'] for r in expected]
  if lock and col=='id':db.execute(sql.SQL('SELECT id FROM {} WHERE id=ANY(%s::uuid[]) ORDER BY id FOR SHARE').format(sql.Identifier(table)),(ids,)).fetchall()
  assert records(db,table,ids,col)==expected,'Protected '+table+' changed'

def verify(db,plan,digest):
 protect(db,plan);expected=payloads(plan,digest);rows={};wids=[w['id'] for w in plan['artworks']];aids=[a['id'] for a in plan['artists']];iids=[i['id'] for i in plan['institutions']]
 for table,want in expected.items():
  if table=='source_institutions':
   present={(str(r['source_id']),str(r['institution_id'])) for r in db.execute('SELECT source_id,institution_id FROM source_institutions WHERE institution_id=ANY(%s::uuid[])',([w['institution_id'] for w in plan['artworks']],))};assert all((r['source_id'],r['institution_id']) in present for r in want);continue
  if table in ['artwork_artists','artwork_location_assertions']:ids=wids;col='artwork_id'
  elif table=='artist_aliases':ids=aids;col='artist_id'
  elif table in ['citations','external_identifiers']:ids=wids+aids+iids;col='entity_id'
  else:ids=[r['id'] for r in want];col='id'
  got=records(db,table,ids,col);rows[table]=got
  key=(lambda r:(r['artwork_id'],r['artist_id'],r['attribution_role'])) if table=='artwork_artists' else (lambda r:r['id'])
  actual={key(r):r for r in got};assert len(actual)==len(want),(table,len(actual),len(want))
  for r in want:
   for c,v in r.items():
    if c in ['published_at','retrieved_at','checked_at']:assert actual[key(r)][c] is not None;continue
    assert actual[key(r)][c]==v,(table,key(r),c)
 imap={w['id']:w['institution_id'] for w in plan['artworks']}
 assert all(w['current_institution_id']==imap[w['id']] and w['primary_media_id'] is None and w['location_checked_at'] is None for w in rows['artworks'])
 assert all(w['display_state'] is None and w['venue_id'] is None for w in rows['artwork_location_assertions'])
 assert not records(db,'artwork_media',wids,'artwork_id')
 scope=safe(db.execute('SELECT artline_creation_scope(creation_year_start,creation_year_end,date_precision) scope,count(*) n,bool_and(artline_has_selection_evidence(id)) supported FROM artworks WHERE id=ANY(%s::uuid[]) GROUP BY 1',(wids,)).fetchall())
 assert scope==[dict(scope='eligible',n=len(wids),supported=True)],scope
 return dict(at=m.m.now(),scope=scope,rows=rows)

def apply():
 plan=m.load(PLAN);validate(plan);digest=m.m.sha(PLAN.read_bytes());path=RUN/'production-publication-receipt.json'
 if path.exists():assert m.load(path)['plan_sha256']==digest;print('Already applied; use verify_live');return
 data=payloads(plan,digest)
 with m.connect(write=True) as db,db.transaction():
  db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))");db.execute("SELECT set_config('artline.user_id',%s,true)",(ACTOR,));protect(db,plan,True)
  assert not duplicate_audit(db,plan['artworks'])['matches'],'Conflicting artwork identity appeared'
  for table,rows in [('artists',plan['artists']),('institutions',plan['institutions']),('sources',plan['sources'])]:
   assert not db.execute(sql.SQL('SELECT 1 FROM {} WHERE id=ANY(%s::uuid[]) OR slug=ANY(%s) LIMIT 1').format(sql.Identifier(table)),([r['id'] for r in rows],[r['slug'] for r in rows])).fetchone()
  assert not db.execute('SELECT 1 FROM artists WHERE normalized_name=ANY(%s)',([a['normalized_name'] for a in plan['artists']],)).fetchone()
  for table in ['places','sources','institutions','artists','artist_aliases','artworks','artwork_artists','external_identifiers','citations','artwork_location_assertions']:
   insert(db,table,data[table]);print('Inserted',table,len(data[table]),flush=True)
  for row in data['source_institutions']:db.execute('INSERT INTO source_institutions(source_id,institution_id) VALUES(%s,%s) ON CONFLICT DO NOTHING',(row['source_id'],row['institution_id']))
  result=verify(db,plan,digest);print('Transactional readback passed; committing',flush=True)
 m.save(BACKUP/'production-postimages.json.gz',result)
 receipt=dict(at=m.m.now(),production=True,plan_sha256=digest,**plan['validation'],by_collection=dict(collections.Counter(w['institution_name'] for w in plan['artworks'])),existing_records_preserved=True,images_attached=0,current_display_claims=0,backup=str(BACKUP),site='https://artlines.org')
 m.save(path,receipt);print(json.dumps(receipt,ensure_ascii=False,indent=2),flush=True)

def verify_live():
 plan=m.load(PLAN);digest=m.m.sha(PLAN.read_bytes())
 with m.connect() as db:result=verify(db,plan,digest)
 summary=dict(at=result['at'],scope=result['scope'],counts={t:len(rs) for t,rs in result['rows'].items()},plan_sha256=digest);m.save(RUN/'production-readback.json',summary);print(summary)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['supplement','candidates','prepare','finalize','apply','verify_live']);args=p.parse_args();globals()[args.action]()
