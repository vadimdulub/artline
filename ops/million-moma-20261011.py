#!/usr/bin/env python3
"""Conservative standalone MoMA metadata selection; images are not licensed here."""
import collections,csv,importlib.util,json,re
from pathlib import Path
s=importlib.util.spec_from_file_location('nga',Path(__file__).with_name('million-nga-20261010.py'));n=importlib.util.module_from_spec(s);s.loader.exec_module(n);m=n.m
RUN=m.RUN/'moma';MID='038c9af4-f059-50ae-aae5-085fcabc8842';SELECTION='selection-v1.json.gz'
TYPES={'Painting':'painting','Drawing':'drawing','Print':'print','Photograph':'photograph','Sculpture':'sculpture'}
def dates(text):
 value=text.strip()
 if value.startswith('(') and value.endswith(')'):value=value[1:-1].strip()
 return n.dates(value)
def physical_reason(row,component_roots):
 accession=row['AccessionNumber'].strip()
 if not re.fullmatch(r'\d+\.\d{4}',accession):return 'multipart_or_complex_inventory_requires_review'
 if accession in component_roots:return 'inventory_parent_of_component_records'
 if re.search(r'\b(?:book|album|portfolio|sketchbook|notebook|frontispiece|wrapper|verso|recto|plates|leaves)\b|\b(?:set|suite|series) of\b',row['Title']+' '+row['Medium'],re.I):return 'book_series_or_view_unit_requires_review'
 return None
def creators(row,authorities):
 raw=row['ConstituentID'].strip()
 if not raw or not re.fullmatch(r'\d+(?:\s*,\s*\d+)*',raw):return [],'missing_or_unparsed_native_creator_ids'
 ids=re.split(r'\s*,\s*',raw)
 if len(ids)!=len(set(ids)) or any(key not in authorities for key in ids):return [],'native_creator_authority_not_unique_or_missing'
 people=[authorities[key] for key in ids]
 if m.norm(', '.join(p['DisplayName'] for p in people))!=m.norm(row['Artist']):return [],'object_creator_names_and_authorities_disagree'
 after=re.search(r',\s*after\s+([^,;]+)$',row.get('Title',''),re.I);after_ids=set()
 if after:
  target=m.norm(after[1])
  after_ids={p['ConstituentID'] for p in people if target in [m.norm(p['DisplayName']),m.norm(p['DisplayName']).split()[-1]]}
  if len(after_ids)!=1:return [],'title_after_creator_requires_individual_review'
 result=[]
 for person in people:
  qid=person['Wiki QID'].strip();qid=qid if re.fullmatch(r'Q[1-9]\d*',qid) else ''
  result.append(dict(constituentid=person['ConstituentID'],forwarddisplayname=person['DisplayName'],preferreddisplayname=person['DisplayName'],displaydate=person['ArtistBio'],wikidataid=qid,constituenttype='individual',role='Artist',prefix='after' if person['ConstituentID'] in after_ids else '',suffix='',native_authority=person,identity_basis='Exact native ConstituentID linked to the same pinned repository Artists dataset; literal biography, never numeric search fields.'))
 return result,None
def select():
 dest=RUN/SELECTION
 if dest.exists():return
 receipt=m.load(m.RUN/'sources/moma/Artworks.csv.receipt.json');artist_receipt=m.load(m.RUN/'sources/moma/Artists-full.csv.receipt.json')
 for name,rc in [('Artworks.csv',receipt),('Artists-full.csv',artist_receipt)]:assert m.sha((m.DATA/'moma'/name).read_bytes())==rc['sha256']
 with (m.DATA/'moma/Artists-full.csv').open(newline='',encoding='utf-8-sig') as file:authority_rows=list(csv.DictReader(file))
 authorities={p['ConstituentID']:p for p in authority_rows};assert len(authorities)==len(authority_rows)
 with (m.DATA/'moma/Artworks.csv').open(newline='',encoding='utf-8-sig') as file:objects=list(csv.DictReader(file))
 native_counts=collections.Counter(r['ObjectID'] for r in objects);component_roots={match[1] for row in objects if (match:=re.match(r'^(\d+\.\d{4})(?:[.a-zA-Z,;/\-])',row['AccessionNumber']))}
 selected=[];held=[];people=collections.defaultdict(list);creator_holds=[]
 for row in objects:
  native=row['ObjectID'];worktype=TYPES.get(row['Classification']);date=dates(row['Date']);reason=None
  if not worktype:reason='type_outside_selected_fine_art_scope'
  elif not date or date[1]==1970 and 'circa' in date[2]:reason='date_unknown_complex_or_after_cutoff'
  elif not row['Title'].strip() or not native.isdigit() or native_counts[native]!=1:reason='native_identity_or_title_requires_review'
  elif (unit_reason:=physical_reason(row,component_roots)):reason=unit_reason
  if reason:held.append(dict(native_id=native,reason=reason));continue
  creator_rows,creator_reason=creators(row,authorities)
  if creator_reason:creator_holds.append(dict(native_id=native,reason=creator_reason,source_label=row['Artist']))
  for person in creator_rows:
   if person not in people[person['constituentid']]:people[person['constituentid']].append(person)
  first,last,precision=date
  selected.append(dict(artwork_id=m.uid('artwork/moma/'+native),native_id=native,title=row['Title'],normalized_title=m.norm(row['Title']),first=first,last=last,precision=precision,date_display=row['Date'],work_type=worktype,accession_number=row['AccessionNumber'],medium=row['Medium'],dimensions=row['Dimensions'],creator_label=row['Artist'] or 'Creator not supplied by MoMA',cultural_context='',wikidata_id='',creators=creator_rows,source_url='https://www.moma.org/collection/works/'+native,raw=row,images=[]))
 out=dict(at=m.now(),source_receipt=receipt,artist_source_receipt=artist_receipt,repository_pin=m.load(RUN/'repository-pin.json'),selected=selected,held=held,people=dict(people),creator_holds=creator_holds,policy='Museum-supported, literal pre-1971 dates and simple standalone inventories only. Complex accessions, parent inventories, books, portfolios and view records held. Numeric artist BeginDate/EndDate ignored in favour of literal biography. Metadata CC0 does not license ImageURL reproductions; no MoMA images downloaded. Cataloged state retained as source evidence, never treated as publication authorization.')
 m.save(dest,out);print(json.dumps(dict(source_objects=len(objects),selected=len(selected),held=dict(collections.Counter(r['reason'] for r in held)),creator_holds=len(creator_holds),source_people=len(people),types=dict(collections.Counter(r['work_type'] for r in selected)))),flush=True)
if __name__=='__main__':select()
