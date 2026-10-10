#!/usr/bin/env python3
"""Next bounded Chicago image-only recovery; exact native photograph grants required."""
import argparse,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('chicago',Path(__file__).with_name('recover-local-chicago-native-images-20261006.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
RUN=m.core.ROOT/'docs/research/local-chicago-more-images-20261007';m.RUN=m.base.RUN=RUN;m.LIMIT=60
PRIOR=m.core.ROOT/'docs/research/local-image-recovery-20261006/report.json'
# Freeze the exclusion list so later combined-report updates cannot alter this run.
EXCLUDED=['local-chicago-native-images-20261006','local-chicago-followup-images-20261006','local-chicago-next-images-20261006','local-chicago-download-recovery-20261006','local-chicago-breadth-images-20261006','local-chicago-reviewed-authorities-20261006','local-chicago-further-images-20261006','local-chicago-further-authorities-20261006','local-chicago-moronobu-image-20261006']
m.EXCLUDE_RUNS=[RUN.parent/x for x in EXCLUDED]

# Decisions apply only to the exact objects and captured creator authorities
# in this operation. Shared native matching remains strict for all other rows.
original_facts,original_verify,original_attach=m.facts,m.verify_image,m.attach
BASIS='Exact existing Chicago object and inventory, independently reviewed creator identity or individual title concordance pinned to current sources. The complete decision and unchanged conflicting biography/title assertions are retained in image evidence and attribution. Exact native photo-specific CC0 grant verified separately. Image-only local attachment preserves catalogue metadata, creator links, holdings and review status.'
s=importlib.util.spec_from_file_location('individual',Path(__file__).with_name('recover-local-chicago-reviewed-authorities-20261006.py'));individual=importlib.util.module_from_spec(s);s.loader.exec_module(individual)
individual.RUN=individual.native.RUN=individual.base.RUN=RUN

def decision(file,aid):
 path=RUN/file
 rows=json.loads(path.read_bytes())['images'] if path.exists() else []
 matches=[x for x in rows if x['artwork_id']==aid]
 if len(matches)>1:raise ValueError('Ambiguous individual review')
 if matches and matches[0]['decision']!='approved':raise ValueError('Individual review remains held')
 return matches[0] if matches else None

def captured_json(path,receipt,url):
 raw=path.read_bytes()
 if json.loads(path.with_suffix('.receipt.json').read_bytes())!=receipt or receipt['url']!=url or m.core.sha(raw)!=receipt['sha256'] or len(raw)!=receipt['bytes']:
  raise ValueError('Pinned independent creator capture differs')
 return json.loads(raw)

def japanese_review(c,o,person,d):
 if c['roles']!=['primary'] or len(c['creator_links'])!=1 or len(c['creator_authorities'])!=1:raise ValueError('Unique local primary creator absent')
 proof=c['creator_authorities'][0];artist=proof['artist_record'];qid=d['existing_qid'];ulan=d['ulan'];lccn=d['lccn']
 if artist['id']!=d['local_artist_id'] or artist['id']!=c['creator_links'][0]['artist_id'] or [x['external_id'] for x in proof['artist_identifiers'] if x['scheme']=='wikidata']!=[qid]:raise ValueError('Existing Japanese creator authority differs')
 if (o['id'],o['artist_id'],person['id'])!=(d['native_object_id'],d['native_person_id'],d['native_person_id']) or m.core.sha(m.core.encode(o))!=d['native_object_sha256'] or m.core.sha(m.core.encode(person))!=d['native_person_sha256']:raise ValueError('Reviewed Japanese object/person evidence differs')
 url='https://www.wikidata.org/wiki/Special:EntityData/'+qid+'.json'
 entity=captured_json(RUN/'metadata/creator-authorities'/(m.core.sha(url.encode())+'.json'),d['wikidata_capture'],url)['entities'][qid]
 if entity['id']!=qid or any(v not in m.base.m.values(entity,p) for p,v in [('P6295',str(person['id'])),('P245',ulan),('P244',lccn)]):raise ValueError('Explicit native and independent creator crosswalk absent')
 getty=captured_json(RUN/'metadata/independent-creator'/('getty-'+ulan+'.json'),d['getty_capture'],'https://vocab.getty.edu/ulan/'+ulan+'.json')
 names={m.check.norm(x['content']) for x in getty.get('identified_by',[]) if x.get('type')=='Name'}
 if getty.get('type')!='Person' or getty.get('id')!='http://vocab.getty.edu/ulan/'+ulan or m.check.norm(artist['display_name']) not in names:raise ValueError('Independent Getty creator identity differs')
 if not any(x.get('id')=='http://id.loc.gov/authorities/names/'+lccn and x.get('type')=='Person' for x in getty.get('equivalent',[])):raise ValueError('Getty-to-LoC creator crosswalk absent')
 loc=captured_json(RUN/'metadata/independent-creator'/('loc-'+lccn+'.json'),d['loc_capture'],'https://id.loc.gov/authorities/names/'+lccn+'.json')
 records=[x for x in loc if x.get('@id')=='http://id.loc.gov/authorities/names/'+lccn];ns='http://www.loc.gov/mads/rdf/v1#'
 if len(records)!=1 or d['loc_authoritative_label'] not in {x.get('@value') for x in records[0].get(ns+'authoritativeLabel',[])}:raise ValueError('Unique LoC creator label differs')
 if not {'http://vocab.getty.edu/ulan/'+ulan,'http://www.wikidata.org/entity/'+qid}.issubset({x.get('@id') for x in records[0].get(ns+'hasCloseExternalAuthority',[])}):raise ValueError('LoC-to-Getty/Wikidata crosswalk absent')
 expected={'Q360978':('Suzuki Harunobu 鈴木 春信 \nJapanese, 1725 (?)-1770','Suzuki, Harunobu, 1725?-1770'),'Q746217':('Hishikawa Moronobu\nJapanese, (?)-1694','Hishikawa, Moronobu, approximately 1618-approximately 1694')}
 if qid not in expected or (o['artist_display'],d['loc_authoritative_label'])!=expected[qid] or d['biographical_display']!=o['artist_display'] or d['qualification'] is not None:raise ValueError('Individual biographical uncertainty review differs')
 return dict(wikidata=entity,getty=getty,loc=records[0])

def facts(c,o,person):
 d=decision('creator-identity-review.json',c['artwork_id']);title=decision('catalogue-concordance-review.json',c['artwork_id'])
 if d:
  authority=individual.review(c,o,person)[1] if d['authority_kind']=='nga' else japanese_review(c,o,person,d)
  if str(o['id'])!=c['external_id'] or c['institution_slug']!=m.check.SLUG or {x['external_id'] for x in c['identifiers'] if x['scheme'] in m.SCHEMES}!={c['external_id']}:raise ValueError('Exact existing native object differs')
  proof=c['creator_authorities'][0];artist=proof['artist_record']
  # Identity is established by the independent identifiers above. Supply native
  # lifespan values solely for the shared object's creation-date sanity checks;
  # preserve every original biography assertion in the individual review.
  checked=dict(artist,aliases=[x['alias'] for x in proof['artist_aliases']],qid=d['existing_qid'],birth_year=person['birth_date'],death_year=person['death_date'])
  result=m.check.metadata(o,checked,person)
  for k in ('accession_number','creation_year_start','creation_year_end','date_precision','work_type'):
   if c[k]!=result[k]:raise ValueError('Reviewed object catalogue field differs: '+k)
  if m.check.norm(c['title']) not in {m.check.norm(x) for x in [o['title'],*(o.get('alt_titles') or [])]} or not m.check.same_date_wording(c['date_display'],result['date_display']):raise ValueError('Reviewed object title or date wording differs')
  return dict(result,creator_identity_review=d,independent_creator_authority=authority)
 if title:
  frozen=[x for x in json.loads((RUN/'candidates.json').read_bytes())['candidates'] if x['artwork_id']==c['artwork_id']]
  if len(frozen)!=1 or any(c[k]!=frozen[0][k] for k in ('creator_authorities','creator_links','identifiers','roles')):raise ValueError('Title-reviewed local identity authority differs')
  if (c['external_id'],c['title'],c['accession_number'],o['title'])!=(title['external_id'],title['local_title'],title['accession_number'],title['native_title']) or m.core.sha(m.core.encode(o))!=title['native_object_sha256'] or m.core.sha(m.core.encode(person))!=title['native_person_sha256']:raise ValueError('Individual title concordance differs')
  page=RUN/'metadata/current-pages'/(c['external_id']+'.html');rc=title['page_capture']
  if m.core.sha(page.read_bytes())!=rc['sha256'] or json.loads(page.with_suffix('.receipt.json').read_bytes())!=rc:raise ValueError('Reviewed title page capture differs')
  result=original_facts(dict(c,title=title['native_title']),o,person)
  return dict(result,catalogue_concordance_review=title)
 return original_facts(c,o,person)
m.facts=facts

def verify_image(im,require_notes=True):
 original_verify(im)
 if im['artwork_id']=='224daf2a-ecd2-4eac-868c-3afd0e1831c6' and 'source_sha256' in im:
  if im.get('view_label')!='Cancelled copper etching plate':raise ValueError('Exact Whistler plate requires explicit physical-object view')
  m.verify_view(im)
 for key in ('creator_identity_review','catalogue_concordance_review'):
  d=im['raw']['native_facts'].get(key)
  if d and require_notes and d['note'] not in im['attribution_text']:raise ValueError('Individual source discrepancy omitted from image credit')
m.verify_image=verify_image

def research():
 m.verify_image=lambda im:verify_image(im,False)
 try:m.research(True)
 finally:m.verify_image=verify_image
 for path in (RUN/'selected'/m.PROVIDER).glob('*.json'):
  im=json.loads(path.read_bytes());notes=[im['raw']['native_facts'][k]['note'] for k in ('creator_identity_review','catalogue_concordance_review') if k in im['raw']['native_facts']]
  if any(note not in im['attribution_text'] for note in notes):
   m.core.save_new(RUN/'history/before-individual-notes'/path.name,path.read_bytes())
   im['attribution_text']+=' '+' '.join(notes);path.write_bytes(m.core.encode(im))
  verify_image(im)

def attach(db,im,target):
 verify_image(im)
 approved=[x for x in json.loads((RUN/'visual-review.json').read_bytes())['images'] if x['artwork_id']==im['artwork_id']]
 if len(approved)!=1 or approved[0]['decision']!='approved' or any(approved[0][k]!=im[k] for k in ('sha256','source_sha256')):raise ValueError('Exact original and derivative need visual approval')
 result=original_attach(db,im,target)
 if result=='attached' and any(k in im['raw']['native_facts'] for k in ('creator_identity_review','catalogue_concordance_review')):
  db.execute('UPDATE media_rights_evidence SET rights_basis=%s WHERE media_id=%s',(BASIS,im['media_id']))
 return result
m.base.m.attach=attach

def verify():
 m.verify();checks=[]
 with m.base.connect() as db:
  for im in m.base.prepared():
   if not any(k in im['raw']['native_facts'] for k in ('creator_identity_review','catalogue_concordance_review')):continue
   row=db.execute('SELECT rights_basis,source_record_id FROM media_rights_evidence WHERE media_id=%s',(im['media_id'],)).fetchone()
   if row!=dict(rights_basis=BASIS,source_record_id=im['external_id']):raise ValueError('Stored individual authority/title basis differs')
   checks.append(im['artwork_id'])
 m.core.save_new(RUN/'individual-review-database-verification.json',dict(at=m.core.now(),passed=True,images=checks,biography_and_title_assertions_preserved=True))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['select','current_pages','native_downloads','prepare','apply','verify']);a=p.parse_args()
 if a.phase=='select':
  if not (RUN/'selection-origin.json').exists():
   raw=PRIOR.read_bytes();prior=json.loads(raw)
   assert prior['new_images_attached']==1155 and all(x in prior['operations'] for x in EXCLUDED)
   m.core.save_new(RUN/'selection-origin.json',dict(at=m.core.now(),prior_report_sha256=m.core.sha(raw),prior_attached=1155,excluded_operations=EXCLUDED,source='Existing exact-ID open-image discovery, independently revalidated before attachment.',database_scope='Local existing eligible missing-image review records only. No catalogue import or publication.'))
  m.select()
 elif a.phase=='current_pages':research()
 elif a.phase=='native_downloads':m.native_downloads()
 elif a.phase=='prepare':
  for path in (RUN/'selected'/m.PROVIDER).glob('*.json'):m.verify_image(json.loads(path.read_bytes()))
  m.base.prepare(m.PROVIDER)
 elif a.phase=='apply':m.base.apply()
 else:verify()
