#!/usr/bin/env python3
"""Evidence-pinned reconciliation in ten-exhibition iterations.

plan is offline after the read-only inventory; apply only touches production.
No title-only identity matches, guessed dates, image delivery, or local DB writes.
"""
import collections,datetime,gzip,json,re,sys
from pathlib import Path
from psycopg.types.json import Jsonb
import exhibitions_common as c
OP='exhibition-catalogue-links-20261013'
OUT=c.DATA.parent/OP
DOC=c.ROOT/'docs/research'/OP
BACKUP=Path.home()/'Library/Application Support/Artline/backups'/OP
SID=c.uid(OP+'/source');ACTOR='local-european-research'
PLAN='plan-v3.json.gz'
CMA='729385eb-92b0-4cc8-9229-1ac3a46aee1f';FITZ='5dc5171c-7a3d-5f36-bc85-6c56f6afeb64'
def normal(x):return json.loads(json.dumps(x,default=str))
def year(x):
 s=str(x or '')
 return int(s[:4]) if re.fullmatch(r'[12]\d{3}(?:-\d\d-\d\d)?',s) else None

def namekeys(s):
 n=c.norm(s);return {n,' '.join(sorted(n.split()))}-{''}

def validate_receipt(rc):
 path=Path(rc['body_path']);raw=gzip.decompress(path.read_bytes());assert c.sha(raw)==rc['sha256'];return raw

def cached_entry_object(e):
 if e['source_key'].startswith('historical-exhibitions-fitzwilliam'):
  path=Path(e['capture_url'])
  if path.is_file():
   raw=gzip.decompress(path.read_bytes());assert c.sha(raw)==e['capture_sha256'];d=json.loads(raw)
   if isinstance(d,dict) and 'lifecycle'in d:return d
 return None

class Identities:
 def __init__(self,pins):
  self.artists={a['id']:a for a in pins['artists']};self.byname=collections.defaultdict(set);self.external=collections.defaultdict(set);self.new={};self.accepted={};self.held={}
  for a in pins['artists']:self.add_names(a['id'],[a['display_name']])
  for a in pins['aliases']:
   if a['artist_id']in self.artists:self.add_names(a['artist_id'],[a['alias']])
  for a in pins['identifiers']:self.external[(a['scheme'],a['external_id'])].add(a['entity_id'])
 def add_names(self,aid,names):
  for name in names:
   for key in namekeys(name):self.byname[key].add(aid)
 def resolve(self,scheme,nid,names,birth,death,url,source,can_create=True):
  key=scheme+':'+nid
  if key in self.accepted:return self.accepted[key]
  names=list(dict.fromkeys(n for n in names if n));assert names
  candidates=set();basis=''
  native=self.external[(scheme,nid)]
  qid=(source.get('authority')or{}).get('wikiID')
  authoritative=native or (self.external[('wikidata',qid)]if qid else set())
  if any(aid not in self.artists for aid in authoritative):
   self.held[key]=dict(reason='Source authority points to an archived artist; no automatic revival',names=names);return None
  name_candidates=set().union(*(self.byname[k]for name in names for k in namekeys(name)))
  if authoritative:candidates=authoritative;basis='Unique source-native artist ID or explicit authority Wikidata ID'
  else:
   candidates={aid for aid in name_candidates if birth is not None and self.artists[aid]['birth_year']==birth and not(death is not None and self.artists[aid]['death_year'] is not None and self.artists[aid]['death_year']!=death)}
   basis='Unique exact source name/alias (allowing given/family order) plus exact birth year and no conflicting death year'
  if len(candidates)==1:
   aid=next(iter(candidates));a=self.artists[aid]
   if (birth is not None and a['birth_year']is not None and birth!=a['birth_year'])or(death is not None and a['death_year']is not None and death!=a['death_year']):
    self.held[key]=dict(reason='Identity has conflicting source life dates',candidates=[aid],names=names);return None
   result=dict(id=aid,scheme=scheme,nativeID=nid,url=url,basis=basis,names=names,source=source,new=aid in self.new)
  elif authoritative or name_candidates:
   self.held[key]=dict(reason='Ambiguous identity or insufficient independent evidence for a same-name existing artist',candidates=sorted(authoritative or name_candidates),names=names);return None
  elif not can_create or birth is None or death is None or birth>death:
   self.held[key]=dict(reason='Source identity retained; new profile lacks supported scope or complete life bounds required by current artist schema',names=names);return None
  else:
   aid=c.uid(OP+'/artist/'+key);a=dict(id=aid,slug=scheme+'-'+nid.lower(),display_name=names[0],birth_year=birth,death_year=death,status='published',entity_type='person')
   self.new[aid]=dict(**a,names=names,scheme=scheme,nativeID=nid,url=url,source=source,basis='New exact official source identity; all known name/authority candidates checked; documented life dates')
   self.artists[aid]=a;self.add_names(aid,names)
   result=dict(id=aid,scheme=scheme,nativeID=nid,url=url,basis=self.new[aid]['basis'],names=names,source=source,new=True)
  self.external[(scheme,nid)].add(aid)
  if qid:self.external[('wikidata',qid)].add(aid)
  self.accepted[key]=result;return result

def plan():
 for folder in ['cma-pages','apj-pages']:
  for path in (OUT/folder).glob('*.json.gz'):validate_receipt(c.load(path)['receipt'])
 baseline=c.load(OUT/'baseline.json.gz');pins=c.load(OUT/'artists-before.json.gz');wp=c.load(OUT/'works-before.json.gz');hp=c.load(OUT/'holding-candidates.json.gz')
 identities=Identities(pins);events={e['id']:e for e in baseline['events']};entries=baseline['entries'];participants=baseline['participants'];works={w['id']:w for w in wp['works']+hp['works']};links=collections.defaultdict(list)
 for x in wp['links']:links[x['artwork_id']].append(x)
 bynative=collections.defaultdict(set);byaccession=collections.defaultdict(set)
 for x in wp['identifiers']+hp['identifiers']:
  if 'cleveland'in x['scheme']:bynative[('cleveland',x['external_id'])].add(x['entity_id'])
  if x['scheme']=='fitzwilliam-native-object':bynative[('fitzwilliam',x['external_id'])].add(x['entity_id'])
 for w in hp['works']:
  if w['accession_number']:byaccession[(w['current_institution_id'],w['accession_number'])].add(w['id'])
 newworks={};entrylinks=[];participantlinks=[];newparticipants={};holds=[];work_resolutions={}
 # APJ's explicit authority IDs and original/native aliases resolve Japanese labels.
 apj=c.load(OUT/'apj-selected.json.gz')['artists'];apjrefs={}
 for nid,r in sorted(apj.items()):
  d=r['data'];names=[d['displayName'].get('en')or d['name'].get('en')or d['name'].get('ja'),d['name'].get('ja'),d['name'].get('en')]+[a['name']for a in d.get('alternateNames',[])];fields={x.get('en')for x in d.get('fields',[])}
  approved=bool(fields&{'Painting','Printmaking','Drawing','Watercolor','Japanese-style painting','Western-style painting'})
  apjrefs[nid]=identities.resolve('apj-artist',nid,names,year(d.get('birthDate')),year(d.get('deathDate')),'https://artplatform.go.jp/artists/'+nid,d|{'receipt':r['receipt']},approved)
 for p in participants:
  if not p['artist_id'] and p['source_key']=='apj_full':
   r=apjrefs.get(p['source_person_id'])
   if r:
    end=events[p['exhibition_id']]['end_year']or events[p['exhibition_id']]['start_year'];birth=identities.artists[r['id']]['birth_year']
    if birth is not None and end is not None and birth>end:
     holds.append(dict(kind='participant',id=p['id'],exhibitionID=p['exhibition_id'],reason='Creator birth follows exhibition; source identity needs correction'));continue
    # Reject a source reference whose Japanese label contradicts its native profile.
    label=p['evidence'].get('label',{}).get('ja')or p['name_label'];names=r['names']
    if c.norm(label)not in {c.norm(n)for n in names}:
     holds.append(dict(kind='participant',id=p['id'],exhibitionID=p['exhibition_id'],reason='APJ source ID/profile name differs from original exhibition label'));continue
    participantlinks.append(dict(before=p,artistID=r['id'],identityKey='apj-artist:'+p['source_person_id'],basis=r['basis']))
   else:holds.append(dict(kind='participant',id=p['id'],exhibitionID=p['exhibition_id'],reason='No resolved official source identity',sourcePersonID=p['source_person_id']))
 # Source-native Fitzwilliam maker IDs already linked to exact catalogue works.
 fitz_makers=collections.defaultdict(set);fitzdocs={}
 for e in entries:
  d=cached_entry_object(e)
  if not d:continue
  fitzdocs[e['id']]=d
  if e['artwork_id']:
   makers=[m for cr in d['lifecycle'].get('creation',[])for m in cr.get('maker',[])];primary=[x['artist_id']for x in links[e['artwork_id']]if x['attribution_role']=='primary']
   if len(makers)==1 and len(primary)==1 and not makers[0].get('@link',{}).get('qualifier'):
    fitz_makers[makers[0]['admin']['id']].add(primary[0])
 cma=c.load(OUT/'cma-selected.json.gz')['objects'];cma_creators={};type_map={'Painting':'painting','Drawing':'drawing','Print':'print','drawing':'drawing','painting':'painting','miniature (painting)':'painting','print':'print'}
 source_entries=collections.defaultdict(list)
 for e in entries:
  if e['artwork_id']:continue
  provider='cleveland'if e['source_key']=='cleveland'else'fitzwilliam'if e['id']in fitzdocs else None
  if provider:source_entries[(provider,e['source_artwork_id'].split('/')[-1])].append(e)
  else:holds.append(dict(kind='entry',id=e['id'],exhibitionID=e['exhibition_id'],reason='Requires individual catalogue/object identity research; not matched by title alone'))
 for (provider,nid),es in sorted(source_entries.items()):
  creators=[];creator_label='';date_basis='';first=last=None;precision='unknown'
  try:
   if provider=='cleveland':
    r=cma.get(nid);assert r,'No eligible painting/drawing/print metadata in official export';d=r['data'];rc=r['receipt'];iid=CMA
    assert str(d['id'])==nid
    acc=d['accession_number'];title=d['title'];kind=type_map[d['type']];medium=d.get('technique');url=d['url'];date=d.get('creation_date')or'Date unknown'
    assert d.get('record_type')in ('object','component','part'),'Whole bound volume/portfolio requires component review'
    first,last=d.get('creation_date_earliest'),d.get('creation_date_latest')
    assert isinstance(first,int)and isinstance(last,int)and -10000<=first<=last<=1979,'Creation interval missing, invalid or crossing 1980'
    precision='circa_range'if re.search(r'\bc\.|circa|about',date,re.I)and first!=last else'circa'if re.search(r'\bc\.|circa|about',date,re.I)else'range'if first!=last else'exact'
    assert not any(int(y)>=1980 for y in re.findall(r'\b(?:19|20)\d{2}\b',date)),'Original date label contains a post-1979 date'
    # A plate date is not an impression date. Preserve both in the display label
    # and source evidence; only the explicit printing year dates the physical sheet.
    printed=re.search(r'printed\s+(?:in\s+)?(c\.\s*)?(\d{4})(?!\d)',date,re.I)
    if printed:first=last=int(printed[2]);precision='circa'if printed[1]else'exact'
    elif '?'in date or re.search(r'printed later|or later|or after',date,re.I):first=last=None;precision='unknown'
    elif re.search(r'\bafter\b',date,re.I):last=None;precision='after'
    assert d.get('legal_status')=='accessioned'and d.get('on_loan')is False,'Current source holding not accessioned or object on loan'
    for e in es:assert e['evidence'].get('accession_number')==acc,'Source exhibition accession differs'
    for maker in d.get('creators',[]):
     if maker.get('role')!='artist':continue
     desc=maker.get('description')or'';name=desc.split(' (',1)[0].strip();qual=maker.get('qualifier');creator_label+='; 'if creator_label else'';creator_label+=(str(qual)+' 'if qual else'')+desc
     if qual or maker.get('extent'):continue
     if not name or re.search(r'unknown|anonymous|unidentified|workshop|school of|circle of',name,re.I):continue
     mid=str(maker['id']);ref=identities.resolve('cleveland-creator',mid,[name,maker.get('name_in_original_language')],year(maker.get('birth_year')),year(maker.get('death_year')),'https://openaccess-api.clevelandart.org/api/creators/'+mid,maker|{'objectURL':url,'receipt':rc})
     if ref:creators.append(ref['id']);cma_creators[mid]=ref
    dimensions=None;date_basis='Official museum creation interval ends before 1980; original date wording retained.'
   else:
    e=es[0];d=fitzdocs[e['id']];iid=FITZ;rc=c.load(c.RUN/'captures'/Path(e['capture_url']).name.replace('.body.gz','.json'));validate_receipt(rc)
    assert d['admin']['id']in ('object-'+nid,nid),'Native Fitzwilliam object mismatch'
    acc=next(x['value']for x in d['identifier']if x.get('primary')and x.get('type')=='accession number');title=e['title_label'];kind=type_map[e['medium_label']];medium=e['medium_label'];url='https://data.fitzmuseum.cam.ac.uk/id/object/'+nid;date=e['date_label']or'Date unknown';creator_label=e['creator_label']or'';dimensions=None
    assert [x['summary_title']for x in d.get('owners',[])]==['The Fitzwilliam Museum'],'Source owner unresolved'
    cr=d['lifecycle'].get('creation',[]);assert len(cr)==1,'Multiple creation phases require review';dates=cr[0].get('date',[])
    assert len(dates)<=1,'Multiple date ranges require individual review'
    if dates:
     dt=dates[0];lo,hi=dt.get('earliest'),dt.get('latest');assert isinstance(lo,int)and isinstance(hi,int)and lo<=hi<=1979,'Date bounds missing or crossing 1980'
     questioned=any(x.get('precision')=='?'for x in [dt,dt.get('from',{}),dt.get('to',{})])
     if not questioned:first,last=lo,hi;precision='circa_range'if dt.get('precision')=='circa'and lo!=hi else'circa'if dt.get('precision')=='circa'else'range'if lo!=hi else'exact'
     date_basis='Source date bounds predate 1980; questioned structured years remain unknown.'
    else:
     acquisition=[x for a in d['lifecycle'].get('acquisition',[])for x in a.get('date',[])]
     assert any(isinstance(x.get('latest'),int)and x['latest']<=1979 for x in acquisition),'Unknown creation date without explicit pre-1980 acquisition evidence'
     date_basis='Source acquisition by 1979 establishes prior existence only; creation years remain unknown.'
    for maker in cr[0].get('maker',[]):
     if maker.get('@link',{}).get('qualifier'):continue
     found=fitz_makers[maker['admin']['id']]
     if len(found)==1:creators.append(next(iter(found)))
   if len(creator_label)>500:raise AssertionError('Creator labels require bounded individual transcription')
   candidates=bynative[(provider,nid)]or byaccession[(iid,acc)]
   if candidates:
    assert len(candidates)==1,'Multiple existing native/accession identities';aid=next(iter(candidates));w=works[aid];assert w['status']!='archived'and w['accession_number']==acc and w['current_institution_id']==iid,'Existing native object metadata conflicts'
    assert c.norm(w['title'])==c.norm(title),'Existing title differs; inspect version before linking'
    resolution=dict(id=aid,new=False,provider=provider,nativeID=nid,basis='Exact native object or holding institution plus accession; matching title',creators=[x['artist_id']for x in links[aid]if x['attribution_role']=='primary'])
   else:
    aid=c.uid(OP+'/artwork/'+provider+'/'+nid);resolution=dict(id=aid,new=True,provider=provider,nativeID=nid,basis='New source-native object; native identifiers and institution/accession candidates checked',creators=sorted(set(creators)))
    newworks[aid]=dict(**resolution,slug=provider+'-exhibition-'+nid,title=title,first=first,last=last,precision=precision,date=date,dateBasis=date_basis,type=kind,medium=medium,dimensions=dimensions,accession=acc,institutionID=iid,creatorLabel=creator_label or None,url=url,source=d,receipt=rc,status='published')
    works[aid]=dict(id=aid,creation_year_start=first,creation_year_end=last)
   work_resolutions[(provider,nid)]=resolution
   for e in es:
    event=events[e['exhibition_id']];event_end=event['end_year']or event['start_year'];earliest=works[aid]['creation_year_start']
    if earliest is not None and event_end is not None and earliest>event_end:
     holds.append(dict(kind='entry',id=e['id'],exhibitionID=e['exhibition_id'],reason='Creation begins after exhibition ends; chronology requires source correction'));continue
    entrylinks.append(dict(before=e,artworkID=aid,basis=resolution['basis'],provider=provider,nativeID=nid))
  except (AssertionError,KeyError,StopIteration)as error:
   for e in es:holds.append(dict(kind='entry',id=e['id'],exhibitionID=e['exhibition_id'],reason=str(error)or'Unresolved source metadata'))
 # Canonical artist participation follows exact unqualified artwork authorship only.
 known={(p['exhibition_id'],p['artist_id'])for p in participants if p['artist_id']}
 for link in entrylinks:
  e=link['before'];res=work_resolutions[(link['provider'],link['nativeID'])]
  if e['participation']not in ('exhibited','catalogued'):continue
  for aid in res['creators']:
   key=(e['exhibition_id'],aid)
   if key in known:continue
   known.add(key);newparticipants[key]=dict(id=c.uid(OP+'/participant/'+key[0]+'/'+aid),exhibitionID=key[0],artistID=aid,sourceRecordID=e['source_record_id'],entryID=e['id'],artworkID=link['artworkID'],name=identities.artists[aid]['display_name'],basis='Exact linked object with unqualified primary creator; source participation preserved, no added venue or current-display assertion')
 for e in entries:
  if not e['artwork_id']or e['participation']not in ('exhibited','catalogued'):continue
  w=works[e['artwork_id']]
  if w['status']=='archived'or w['work_type']not in ('painting','drawing','watercolor','print','fresco','manuscript_illumination'):continue
  if w['creation_year_start']is not None and w['creation_year_start']>=1980:continue
  for author in links[e['artwork_id']]:
   aid=author['artist_id'];key=(e['exhibition_id'],aid)
   if author['attribution_role']!='primary'or key in known or aid not in identities.artists:continue
   known.add(key);newparticipants[key]=dict(id=c.uid(OP+'/participant/'+key[0]+'/'+aid),exhibitionID=key[0],artistID=aid,sourceRecordID=e['source_record_id'],entryID=e['id'],artworkID=e['artwork_id'],name=identities.artists[aid]['display_name'],basis='Existing exact exhibition artwork connection and current unqualified primary catalogue authorship; original historical labels retained; no participation or venue claims changed')
 # Prune candidates that have no accepted connection; never create placeholder totals.
 usedworks={l['artworkID']for l in entrylinks};newworks={k:v for k,v in newworks.items()if k in usedworks}
 usedartists={l['artistID']for l in participantlinks}|{a for w in newworks.values()for a in w['creators']}
 newartists={k:v for k,v in identities.new.items()if k in usedartists}
 # Every event is assessed once, ten per full iteration. Unknown checklists remain gaps.
 ee=collections.defaultdict(list);pp=collections.defaultdict(list);hh=collections.defaultdict(list)
 for e in entries:ee[e['exhibition_id']].append(e)
 for p in participants:pp[p['exhibition_id']].append(p)
 for h in holds:hh[h['exhibitionID']].append(h)
 batches=[];ordered=baseline['events']
 for start in range(0,len(ordered),10):
  es=ordered[start:start+10];ids={e['id']for e in es}
  batches.append(dict(iteration=start//10+1,eventIDs=[e['id']for e in es],events=[dict(id=e['id'],title=e['title'],checklist=e['checklist_state'],entryCount=len(ee[e['id']]),participantCount=len(pp[e['id']]),checklistGap=not ee[e['id']]and e['checklist_state']!='complete')for e in es],entryLinks=[l for l in entrylinks if l['before']['exhibition_id']in ids],participantLinks=[l for l in participantlinks if l['before']['exhibition_id']in ids],newParticipants=[p for p in newparticipants.values()if p['exhibitionID']in ids],holds=[h for eid in ids for h in hh[eid]]))
 result=dict(at=c.now(),operation=OP,cutoff=1979,publication='Directly published after assistant verification; user explicitly waived manual review',batches=batches,newWorks=newworks,newArtists=newartists,identities=identities.accepted,identityHolds=identities.held,counts=dict(events=len(ordered),fullIterations=sum(len(b['eventIDs'])==10 for b in batches),tailEvents=len(ordered)%10,newArtworks=len(newworks),newArtists=len(newartists),entryLinks=len(entrylinks),participantLinks=len(participantlinks),newParticipants=len(newparticipants),unresolved=len(holds),eventsWithoutEntries=sum(not ee[e['id']]for e in ordered)))
 c.save(OUT/PLAN,result);c.save(BACKUP/'plan-v3-and-preimages.json.gz',result);print(json.dumps(result['counts']),flush=True)

def evidence_note(record,basis):
 return json.dumps(dict(operation=OP,basis=basis,source=record,creationCutoff=1979,manualUserReviewRequired=False),ensure_ascii=False,default=str)

def apply():
 p=c.load(OUT/PLAN);assert p==c.load(BACKUP/'plan-v3-and-preimages.json.gz')
 assert p['counts']['fullIterations']>=1000
 assert len({eid for b in p['batches']for eid in b['eventIDs']})==p['counts']['events']
 baseline=c.load(OUT/'baseline.json.gz');event_before={e['id']:e for e in baseline['events']};artist_before={a['id']:a for a in c.load(OUT/'artists-before.json.gz')['artists']}
 newartists=p['newArtists'];newworks=p['newWorks'];allidentities=p['identities'];identity_by_artist=collections.defaultdict(list)
 for r in allidentities.values():identity_by_artist[r['id']].append(r)
 created_artists=set();created_works=set();saved_identities=set();totals=collections.Counter();plan_sha=c.sha((OUT/PLAN).read_bytes())
 with c.connect(write=True)as db:
  # Persistent connection; each iteration remains an independent checked transaction.
  db.autocommit=True
  with db.transaction():
   db.execute("SELECT set_config('artline.actor_user_id',%s,true)",(ACTOR,))
   db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
   db.execute("INSERT INTO sources(id,slug,name,source_type) VALUES(%s,%s,'Official Cleveland, Fitzwilliam and Art Platform Japan exhibition records','collection_page') ON CONFLICT(id)DO NOTHING",(SID,OP))
  def ensure_identity(aid):
   for r in identity_by_artist[aid]:
    key=(r['scheme'],r['nativeID'])
    if key in saved_identities:continue
    collisions=db.execute("SELECT entity_id::text FROM external_identifiers WHERE entity_type='artist'AND scheme=%s AND external_id=%s",key).fetchall();assert all(x['entity_id']==aid for x in collisions),'Native artist identity changed during preparation'
    if not collisions:
     same_scheme=db.execute("SELECT 1 FROM external_identifiers WHERE entity_type='artist'AND entity_id=%s AND scheme=%s",(aid,r['scheme'])).fetchone()
     if not same_scheme:db.execute("INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at) VALUES('artist',%s,%s,%s,%s,%s,%s)",(aid,r['scheme'],r['nativeID'],r['url'],SID,r['source']['receipt']['retrieved_at']))
     db.execute("INSERT INTO citations(entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by) VALUES('artist',%s,'exhibition_creator_identity',%s,%s,%s,%s,%s,%s)",(aid,SID,r['nativeID'],r['url'],evidence_note(r['source'],r['basis']),r['source']['receipt']['retrieved_at'],ACTOR))
    saved_identities.add(key)
  def ensure_artist(aid):
   if aid in created_artists:return
   found=normal(db.execute('SELECT id,display_name,birth_year,death_year,status FROM artists WHERE id=%s FOR SHARE',(aid,)).fetchone())
   if aid in newartists:
    a=newartists[aid]
    if found:assert found['display_name']==a['display_name']and found['birth_year']==a['birth_year']and found['death_year']==a['death_year']and found['status']=='published'
    else:
     # Recheck exact names immediately before insertion under the ingestion lock.
     similar=db.execute("SELECT id FROM artists WHERE status<>'archived'AND normalized_name=%s AND birth_year=%s",(c.norm(a['display_name']),a['birth_year'])).fetchall();assert not similar,'A new matching creator appeared after planning'
     db.execute("INSERT INTO artists(id,slug,display_name,sort_name,normalized_name,entity_type,birth_year,death_year,birth_display,death_display,birth_precision,death_precision,timeline_start_year,timeline_end_year,timeline_display,timeline_basis,status,published_at,created_by,updated_by) VALUES(%s,%s,%s,%s,%s,'person',%s,%s,%s,%s,'exact','exact',%s,%s,%s,'life','published',now(),%s,%s)",(aid,a['slug'],a['display_name'],a['display_name'],c.norm(a['display_name']),a['birth_year'],a['death_year'],str(a['birth_year']),str(a['death_year']),a['birth_year'],a['death_year'],str(a['birth_year'])+'–'+str(a['death_year']),ACTOR,ACTOR))
     counts['newArtists']+=1
     for name in a['names']:
      db.execute("INSERT INTO artist_aliases(artist_id,alias,normalized_alias,alias_type)VALUES(%s,%s,%s,'alternate')ON CONFLICT DO NOTHING",(aid,name,c.norm(name)))
   else:
    assert found and found['status']!='archived','Existing artist missing/archived'
    old=artist_before[aid]
    for key in ['display_name','birth_year','death_year']:assert found[key]==old[key],'Existing artist identity changed'
   ensure_identity(aid);created_artists.add(aid)
  def ensure_work(aid):
   if aid not in newworks or aid in created_works:return
   w=newworks[aid];found=batch_existing_works.get(aid)
   if found:
    assert found['title']==w['title']and found['accession_number']==w['accession']and found['status']=='published';created_works.add(aid);return
   for artist in w['creators']:ensure_artist(artist)
   collision=batch_accessions.get((w['institutionID'],w['accession']));assert not collision,'Accession now exists; reconcile instead of duplicating'
   scheme='cleveland-object'if w['provider']=='cleveland'else'fitzwilliam-native-object'
   schemes=['cleveland','cleveland-object','continuous-cleveland-object','european-cleveland-cleveland-museum-of-art-object']if w['provider']=='cleveland'else['fitzwilliam-native-object']
   assert not any((scheme,w['nativeID'])in batch_natives for scheme in schemes),'Native object ID now exists'
   rc=w['receipt'];note=evidence_note(w['source'],w['basis']+'; '+w['dateBasis'])
   db.execute("INSERT INTO artworks(id,slug,title,normalized_title,date_display,creation_year_start,creation_year_end,date_precision,work_type,medium_text,dimensions_text,accession_number,status,research_candidate,unlinked_creator_label,current_institution_id,published_at,created_by,updated_by)VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'published',false,%s,%s,now(),%s,%s)",(aid,w['slug'],w['title'],c.norm(w['title']),w['date'],w['first'],w['last'],w['precision'],w['type'],w['medium'],w['dimensions'],w['accession'],w['creatorLabel'],w['institutionID'],ACTOR,ACTOR))
   db.execute("INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at)VALUES('artwork',%s,%s,%s,%s,%s,%s)",(aid,scheme,w['nativeID'],w['url'],SID,rc['retrieved_at']))
   db.execute("INSERT INTO citations(entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by)VALUES('artwork',%s,'exhibition_native_object_metadata',%s,%s,%s,%s,%s,%s)",(aid,SID,w['nativeID'],w['url'],note,rc['retrieved_at'],ACTOR))
   db.execute("INSERT INTO artwork_location_assertions(artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state)VALUES(%s,'holding',%s,'collection',%s,%s,%s,%s,'accepted')",(aid,w['institutionID'],SID,w['url'],note,rc['retrieved_at']))
   for artist in w['creators']:db.execute("INSERT INTO artwork_artists(artwork_id,artist_id,attribution_role,attribution_note)VALUES(%s,%s,'primary',%s)",(aid,artist,'Official native creator identity; original source label retained in artwork and citation.'))
   counts['newArtworks']+=1;created_works.add(aid);batch_accessions[(w['institutionID'],w['accession'])]=aid;batch_natives.add((scheme,w['nativeID']))
  for batch in p['batches']:
   receipt_path=OUT/'iterations'/f"{batch['iteration']:04d}.json"
   if receipt_path.exists():continue
   started=c.now();counts=collections.Counter()
   with db.transaction():
    db.execute("SELECT set_config('artline.actor_user_id',%s,true)",(ACTOR,));db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))");db.execute('SELECT pg_advisory_xact_lock(2026101201)')
    current=normal(db.execute('SELECT id,title,status,start_year,end_year FROM exhibitions WHERE id=ANY(%s::uuid[])ORDER BY id FOR SHARE',(batch['eventIDs'],)).fetchall());assert len(current)==len(batch['eventIDs'])
    for event in current:
     for key in ['title','status','start_year','end_year']:assert event[key]==event_before[event['id']][key],'Exhibition changed since inventory'
    before_entries={str(x['id']):normal(x)for x in db.execute('SELECT * FROM exhibition_entries WHERE exhibition_id=ANY(%s::uuid[]) FOR UPDATE',(batch['eventIDs'],))}
    before_people={str(x['id']):normal(x)for x in db.execute('SELECT * FROM exhibition_participants WHERE exhibition_id=ANY(%s::uuid[]) FOR UPDATE',(batch['eventIDs'],))}
    needed={l['artworkID']:newworks[l['artworkID']]for l in batch['entryLinks']if l['artworkID']in newworks and l['artworkID']not in created_works}
    batch_existing_works={};batch_accessions={};batch_natives=set()
    if needed:
     batch_existing_works={str(x['id']):normal(x)for x in db.execute('SELECT id,title,accession_number,status FROM artworks WHERE id=ANY(%s::uuid[])',(list(needed),))}
     batch_accessions={(str(x['current_institution_id']),x['accession_number']):str(x['id'])for x in db.execute("SELECT id,current_institution_id,accession_number FROM artworks WHERE current_institution_id=ANY(%s::uuid[])AND accession_number=ANY(%s)AND status<>'archived'",(list({w['institutionID']for w in needed.values()}),list({w['accession']for w in needed.values()})))}
     batch_natives={(x['scheme'],x['external_id'])for x in db.execute("SELECT scheme,external_id FROM external_identifiers WHERE entity_type='artwork'AND scheme=ANY(%s)AND external_id=ANY(%s)",(['cleveland','cleveland-object','continuous-cleveland-object','european-cleveland-cleveland-museum-of-art-object','fitzwilliam-native-object'],list({w['nativeID']for w in needed.values()})))}
    with db.pipeline():
     for link in batch['entryLinks']:
      e=link['before'];aid=link['artworkID'];now=before_entries[e['id']]
      for key in now:
       if key not in ('artwork_id','evidence','match_basis'):assert now[key]==e[key],'Original exhibition source fields changed'
      assert now['artwork_id']in (None,aid),'Entry matched elsewhere after planning'
      ensure_work(aid)
      if now['artwork_id']is None:
       assert now['evidence']==e['evidence']and now['match_basis']==e['match_basis']
       ev=dict(operation=OP,artworkID=aid,sourceNativeID=link['nativeID'],basis=link['basis'],manualUserReviewRequired=False)
       db.execute('UPDATE exhibition_entries SET artwork_id=%s,evidence=evidence||%s::jsonb,match_basis=%s WHERE id=%s',(aid,Jsonb({'catalogue_link_20261013':ev}),link['basis'],e['id']));counts['entryLinks']+=1
     for link in batch['participantLinks']:
      old=link['before'];aid=link['artistID'];now=before_people[old['id']]
      for key in now:
       if key not in ('artist_id','evidence'):assert now[key]==old[key]
      assert now['artist_id']in (None,aid);ensure_artist(aid)
      if now['artist_id']is None:
       assert now['evidence']==old['evidence'];db.execute('UPDATE exhibition_participants SET artist_id=%s,evidence=evidence||%s::jsonb WHERE id=%s',(aid,Jsonb({'catalogue_link_20261013':dict(operation=OP,basis=link['basis'],identityKey=link['identityKey'])}),old['id']));counts['participantLinks']+=1
     current_people={(str(x['exhibition_id']),str(x['artist_id']))for x in db.execute("SELECT exhibition_id,artist_id FROM exhibition_participants WHERE exhibition_id=ANY(%s::uuid[])AND role='artist'",(batch['eventIDs'],))}
     current_authorship={(str(x['id']),str(x['artwork_id']),str(x['artist_id']))for x in db.execute("SELECT e.id,e.artwork_id,aa.artist_id FROM exhibition_entries e JOIN artwork_artists aa ON aa.artwork_id=e.artwork_id WHERE e.exhibition_id=ANY(%s::uuid[])AND aa.attribution_role='primary'AND e.participation IN ('exhibited','catalogued')",(batch['eventIDs'],))}
     for row in batch['newParticipants']:
      key=(row['exhibitionID'],row['artistID'])
      if key in current_people:continue
      ensure_artist(row['artistID']);assert(row['entryID'],row['artworkID'],row['artistID'])in current_authorship,'Exact source object/creator relation changed'
      db.execute("INSERT INTO exhibition_participants(id,exhibition_id,source_record_id,artist_id,name_label,role,evidence)VALUES(%s,%s,%s,%s,%s,'artist',%s)",(row['id'],row['exhibitionID'],row['sourceRecordID'],row['artistID'],row['name'],Jsonb(dict(operation=OP,**row))));counts['newParticipants']+=1;current_people.add(key)
    # Scoped post-write verification, with one set query for each child type.
    actual={str(e['id']):str(e['artwork_id'])for e in db.execute('SELECT id,artwork_id FROM exhibition_entries WHERE exhibition_id=ANY(%s::uuid[])',(batch['eventIDs'],))}
    assert all(actual[l['before']['id']]==l['artworkID']for l in batch['entryLinks'])
    actual={str(e['id']):str(e['artist_id'])for e in db.execute('SELECT id,artist_id FROM exhibition_participants WHERE exhibition_id=ANY(%s::uuid[])',(batch['eventIDs'],))}
    assert all(actual[l['before']['id']]==l['artistID']for l in batch['participantLinks'])
   receipt=dict(iteration=batch['iteration'],startedAt=started,verifiedAt=c.now(),eventIDs=batch['eventIDs'],events=len(batch['eventIDs']),counts=dict(counts),unresolved=len(batch['holds']),checklistGaps=sum(e['checklistGap']for e in batch['events']),committed=True,verified=True,planSHA256=plan_sha)
   c.save(receipt_path,receipt);totals.update(counts)
   if batch['iteration']%10==0 or counts:print(json.dumps(dict(iteration=batch['iteration'],events=len(batch['eventIDs']),counts=dict(counts),cumulative=dict(totals))),flush=True)
 print('All frozen exhibition iterations committed and checked',flush=True)

if __name__=='__main__':
 assert sys.argv[1]in ['plan','apply'];globals()[sys.argv[1]]()
