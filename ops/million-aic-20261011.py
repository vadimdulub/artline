#!/usr/bin/env python3
"""Select physical AIC collection objects from the official metadata dump."""
import collections,gzip,importlib.util,json,re
from pathlib import Path
s=importlib.util.spec_from_file_location('nga',Path(__file__).with_name('million-nga-20261010.py'));n=importlib.util.module_from_spec(s);s.loader.exec_module(n);m=n.m
RUN=m.RUN/'aic';MID='9e75033c-8e6b-464b-974b-d94fcc91c6a3';SELECTION='selection-v2.json.gz'
TYPES={'Painting':'painting','Drawing and Watercolor':'drawing','Print':'print','Photograph':'photograph','Sculpture':'sculpture'}

def records(kind):
 with gzip.open(m.DATA/'aic'/(kind+'.jsonl.gz'),'rt') as file:
  for line in file:yield json.loads(line)

def creation(row):
 # Numeric date_start/date_end can be the artist's working span for an
 # explicitly undated object. Only the source display statement is parsed.
 qualifier=row.get('date_qualifier_title') or ''
 if qualifier not in ['','Made','Printed','Published']:return None
 parsed=n.dates(row.get('date_display') or '')
 if parsed and not (parsed[1]==1970 and 'circa' in parsed[2]):return parsed
 return None

def physical_reason(row,parents):
 accession=row.get('main_reference_number') or ''
 if row.get('fiscal_year_deaccession'):return 'deaccessioned_object'
 if not re.fullmatch(r'[12]\d{3}\.\d+',accession):return 'complex_or_component_inventory'
 if accession in parents:return 'parent_inventory_has_component_records'
 if re.search(r'\b(?:album|portfolio|book|sketchbook|notebook|leaf|leaves|fragment|recto|verso)\b',row.get('title') or '',re.I):return 'physical_unit_or_view_requires_review'
 if re.search(r'\b(?:on loan|lent|loaned)\s+(?:from|by)\b',row.get('credit_line') or '',re.I):return 'incoming_loan_not_established_holding'
 return None

def creator(row,agents):
 ids=row.get('artist_ids') or []
 if len(ids)!=1 or row.get('artist_id')!=ids[0] or ids[0] not in agents:return [],'multiple_or_missing_native_creator_authorities'
 authority=agents[ids[0]]['data'];name=authority.get('title') or ''
 if authority.get('agent_type_title')!='Individual':return [],'culture_corporation_or_other_nonindividual_label_preserved'
 if re.search(r'\b(?:imitator|imitation|copyist|circle|follower|workshop|school of|manner of|style of|studio of|attributed to|after)\b|^pseudo[- ]',name,re.I):return [],'qualified_authority_name_is_not_a_separate_named_painter'
 if m.norm(row.get('artist_title'))!=m.norm(name):return [],'native_creator_title_conflict'
 label=row.get('artist_display') or '';prefix=''
 if re.search(r'\b(?:after|copy|copies|workshop|circle|follower|manner|style of|formerly|probably|possibly)\b',label,re.I):return [],'qualified_creator_label_requires_role_review'
 if re.search(r'\battributed to\b',label,re.I):prefix='attributed to'
 # Preserve literal biographical wording, including approximations/activity.
 # Numeric authority life fields remain in raw evidence; they are not silently
 # substituted for a missing or qualified literal biography.
 life=label.split('\n')[-1].strip().rstrip(')').replace('ca.','c.')
 if '(' in life:life=life.rsplit('(',1)[-1].strip()
 qid=authority.get('wikidata_id') or '';qid=qid if re.fullmatch(r'Q[1-9]\d*',qid) else ''
 person=dict(constituentid=str(ids[0]),forwarddisplayname=name,preferreddisplayname=authority.get('sort_title') or name,displaydate=life,wikidataid=qid,constituenttype='individual',role='Artist',prefix=prefix,suffix='',source_uri=authority['api_link'],native_authority=authority,authority_record_sha256=agents[ids[0]]['record_sha256'],identity_basis='Exact single AIC native agent ID; Individual agent type; object artist_title agrees with authority title. Literal object biography retained without substituting numeric birth/death fields.')
 if re.match(r'^(?:Master\s|Monogrammist\s)',name,re.I):person['entity_type_hint']='anonymous_master'
 return [person],None

def select():
 dest=RUN/SELECTION
 if dest.exists():return
 summary=m.load(RUN/'dataset-summary.json');rc=m.load(m.RUN/'sources/aic/api-data.tar.bz2.receipt.json')
 assert summary['source_archive_sha256']==rc['sha256']
 for kind in ['artworks','agents']:assert m.sha((m.DATA/'aic'/(kind+'.jsonl.gz')).read_bytes())==summary['files'][kind]['sha256']
 agents={x['data']['id']:x for x in records('agents')};assert len(agents)==summary['counts']['agents']
 parents=set();native_counts=collections.Counter()
 for item in records('artworks'):
  row=item['data'];native_counts[row['id']]+=1
  match=re.match(r'^([12]\d{3}\.\d+)(?:[.a-zA-Z,;/\-])',row.get('main_reference_number') or '')
  if match:parents.add(match[1])
 selected=[];held=[];people=collections.defaultdict(list);creator_holds=[]
 for item in records('artworks'):
  row=item['data'];native=str(row['id']);kind=TYPES.get(row.get('artwork_type_title'));date=creation(row);reason=None
  if not kind:reason='type_outside_selected_fine_art_scope'
  elif not date:reason='unknown_complex_noncreation_or_after_cutoff_date'
  elif row.get('api_model')!='artworks' or not native.isdigit() or native_counts[row['id']]!=1 or not row.get('title'):reason='native_identity_requires_review'
  elif (unit:=physical_reason(row,parents)):reason=unit
  if reason:held.append(dict(native_id=native,reason=reason));continue
  creators,creator_reason=creator(row,agents)
  if creator_reason:creator_holds.append(dict(native_id=native,reason=creator_reason,label=row.get('artist_display')))
  for person in creators:
   if person not in people[person['constituentid']]:people[person['constituentid']].append(person)
  # Full immutable raw records remain in the official archive and JSONL.
  # Search/autocomplete data and inline preview pixels are not catalogue data.
  raw={k:v for k,v in row.items() if k not in ['thumbnail','suggest_autocomplete_all','suggest_autocomplete_boosted']};raw.update(archive_member=item['archive_member'],record_sha256=item['record_sha256'])
  selected.append(dict(artwork_id=m.uid('artwork/aic/'+native),native_id=native,title=row['title'],normalized_title=m.norm(row['title']),first=date[0],last=date[1],precision=date[2],date_display=row['date_display'],work_type=kind,accession_number=row['main_reference_number'],medium=row.get('medium_display') or '',dimensions=row.get('dimensions') or '',creator_label=row.get('artist_display') or row.get('artist_title') or 'Creator not supplied by the Art Institute of Chicago',cultural_context='',wikidata_id='',creators=creators,source_url='https://www.artic.edu/artworks/'+native,raw=raw,images=[]))
 out=dict(at=m.now(),source_receipt=rc,selected=selected,people=dict(people),held=held,creator_holds=creator_holds,policy='Official AIC collection metadata only. Literal creation statements through 1970; numeric date search/working-span bounds ignored. Simple standalone accession numbers; parent, component, book, view, incoming-loan and deaccessioned records held. Single Individual native creator authorities only; qualified, culture and multiple-creator labels preserved on objects. No display assertion or image download.')
 m.save(dest,out);print(json.dumps(dict(source_objects=summary['counts']['artworks'],selected=len(selected),held=dict(collections.Counter(x['reason'] for x in held)),types=dict(collections.Counter(x['work_type'] for x in selected)),creator_holds=dict(collections.Counter(x['reason'] for x in creator_holds)))),flush=True)

if __name__=='__main__':select()
