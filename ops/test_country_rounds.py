"""Offline counterexamples for country and duplicate guards; no DB fixtures."""
import importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('m',Path(__file__).with_name('apply-country-round.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def claim(value):return {'rank':'normal','mainsnak':{'snaktype':'value','datavalue':{'value':value}}}
def creator(desc='Dutch painter',qid='Q10'):
 return {'id':qid,'labels':{'en':{'value':'Jan van Example'}},'descriptions':{'en':{'value':desc}},'claims':{'P27':[claim({'id':'Q55'})],'P31':[claim({'id':'Q5'})]}}
def record():return {'creator_entity':creator(),'creator_qid':'Q10','creator_label':'Jan van Example','entity':{'claims':{}},'titles':['Landscape'],'date':{'first':1700,'last':1700}}
def artist(**kw):
 a={'id':'one','display_name':'Jan van Example','aliases':[],'authorities':[],'status':'review','entity_type':'person','birth_year':None,'death_year':None};a.update(kw);return a
class Guards(unittest.TestCase):
 def test_primary_activity_can_distinguish_later_born_namesake_without_inventing_life(self):
  r=record();a=artist(slug='later',birth_year=1560,death_year=1627,authorities=[{'scheme':'wikidata','id':'Q99'}])
  decision={'kind':'distinct_named_person','primary_life':[None,None],'primary_activity':[1440,1470],'excluded':[{'slug':'later','life':[1560,1627],'wikidata':'Q99'}]}
  source={'artist_dates':{'birth':None,'death':None,'active_start':1440,'active_end':1470},'existing_identity_decision':decision};r['primary_creator_review']={'source':source}
  found,why=m.resolve(r,m.f.Matcher([a]));self.assertIsNone(why);self.assertIsNone(found['artist'])
  for activity in ([1550,1570],[1440,1469]):
   decision['primary_activity']=activity
   found,why=m.resolve(r,m.f.Matcher([a]));self.assertIsNone(found)
  decision['primary_activity']=[1440,1470];source.pop('artist_dates')
  found,why=m.resolve(r,m.f.Matcher([a]));self.assertIsNone(found)
 def test_primary_activity_does_not_exclude_namesake_with_unknown_lifespan(self):
  r=record();a=artist(slug='later',birth_year=1560,death_year=None,authorities=[{'scheme':'wikidata','id':'Q99'}])
  r['primary_creator_review']={'source':{'artist_dates':{'birth':None,'death':None,'active_start':1440,'active_end':1470},'existing_identity_decision':{'kind':'distinct_named_person','primary_life':[None,None],'primary_activity':[1440,1470],'excluded':[{'slug':'later','life':[1560,None],'wikidata':'Q99'}]}}}
  found,why=m.resolve(r,m.f.Matcher([a]));self.assertIsNone(found)
 def test_shared_name_precedes_arbitrary_transliteration_when_english_is_absent(self):
  entity={'id':'Q1354695','labels':{'el':{'value':'Γιούζεφ Μεχόφερ'},'mul':{'value':'Józef Mehoffer'}}}
  self.assertEqual(m.m.r.label(entity),'Józef Mehoffer')
  entity['labels']['en']={'value':'English preferred name'}
  self.assertEqual(m.m.r.label(entity),'English preferred name')
 def test_primary_inventory_finds_object_despite_changed_title(self):
  r=record();r.update(primary_metadata_review={'override':{'accession':'98.8M'}},accession='98.8M')
  existing={'id':'one','accession_number':'98.8M','title':'Earlier title','alternate_title':None,'creator_qids':['Q10'],'creator_names':['Jan van Example']}
  found,reason=m.m.choose_existing(r,[existing]);self.assertEqual(found,existing);self.assertIsNone(reason)
 def test_reproduction_retry_after_is_not_replaced_with_short_backoff(self):
  self.assertEqual(m.m.core.retry_delay('120'),120)
  self.assertEqual(m.m.core.retry_delay(None),60)
  self.assertEqual(m.m.core.retry_delay('invalid'),60)
 def test_rejected_artwork_date_cannot_survive_as_artist_activity(self):
  r=record();r['date']={'first':None,'last':None,'eligible':False}
  self.assertIsNone(m.reviewed_new_artist(r,{'Q1':r},{}))
 def test_primary_activity_does_not_adopt_conflicting_secondary_life_dates(self):
  r=record();r['creator_entity']['claims'].update(P569=[claim({'precision':9,'time':'+1759-01-01T00:00:00Z'})],P570=[claim({'precision':9,'time':'+1812-01-01T00:00:00Z'})])
  r['primary_creator_review']={'source':{'artist_dates':{'birth':None,'death':None,'active_start':1776,'active_end':1806}}}
  a=m.reviewed_new_artist(r,{'Q1':r},{})
  self.assertEqual((a['birth'],a['death'],a['first'],a['last'],a['basis']),(None,None,1776,1806,'activity'))
 def test_dated_sibling_supports_undated_work_without_invented_life_dates(self):
  r=record();r['date']={'first':None,'last':None,'eligible':False};other=record();other['date']={'first':1663,'last':1663,'eligible':True}
  a=m.reviewed_new_artist(r,{'Q1':r,'Q2':other},{})
  self.assertEqual((a['first'],a['last'],a['basis']),(1663,1663,'activity'));self.assertIsNone(a['birth']);self.assertIsNone(a['death'])
 def test_held_wrong_creator_work_cannot_supply_activity_dates(self):
  r=record();r['date']={'first':1663,'last':1663,'eligible':True}
  self.assertIsNone(m.reviewed_new_artist(r,{'Q1':r},{'Q1':'wrong creator'}))
 def test_finnish_object_identity_is_independent_of_missing_institution_fk(self):
  r=record();r['entity']['claims']['P9834']=[claim('1699758')]
  self.assertEqual(m.museum_object_authorities(r),[('fng-object','1699758')])
 def test_unlinked_smk_placeholder_source_is_checked_by_exact_object_number(self):
  r=record();r.update(qid='Q20355651',collection={'qid':'Q671384'});r['entity']['claims']['P217']=[claim('KMS4523')]
  self.assertIn('https://open.smk.dk/artwork/image/KMS4523',m.vetted_object_urls(r))
 def test_other_museum_inventory_is_not_mapped_to_smk(self):
  r=record();r.update(qid='Q20355651',collection={'qid':'Q190804'});r['entity']['claims']['P217']=[claim('KMS4523')]
  self.assertEqual(m.vetted_object_urls(r),{'https://www.wikidata.org/wiki/Q20355651'})
 def test_conventional_masters_in_multiple_languages_are_not_named_people(self):
  for name in ('Meister des Altenberger Altars','Meister von Sierentz','Mestre dos Arcos','Maestro del Altar','Maître de Moulins','Meester van Alkmaar'):
   e=creator();e['labels']['en']['value']=name
   with self.subTest(name=name):self.assertTrue(m.x.unnamed_creator_context(e))
 def test_real_documented_forename_is_not_rejected_as_a_conventional_master(self):
  e=creator();e['labels']['en']['value']='Maestro Bartolomé';self.assertFalse(m.x.unnamed_creator_context(e))
 def test_title_lookup_finds_curly_and_straight_apostrophe_candidates(self):
  self.assertIn('children’s concert',m.m.title_lookup_variants(["Children's Concert"]))
  self.assertIn("children's concert",m.m.title_lookup_variants(['Children’s Concert']))
 def test_title_lookup_preserves_cyrillic_under_c_database_locale(self):
  variants=m.m.title_lookup_variants(['Степан Разин','Portrait Σοφία'])
  for expected in ['Степан Разин','степан разин','portrait Σοφία','portrait σοφία']:self.assertIn(expected,variants)
 def test_rank_reason_does_not_erase_exact_year(self):
  c=claim({'precision':11,'time':'+1853-01-11T00:00:00Z'});c['qualifiers']={'P7452':[]};self.assertEqual(m.m.r.year({'claims':{'P569':[c]}},'P569'),1853)
 def test_circa_year_remains_uncertain_for_identity(self):
  c=claim({'precision':9,'time':'+1853-01-01T00:00:00Z'});c['qualifiers']={'P1480':[]};self.assertIsNone(m.m.r.year({'claims':{'P569':[c]}},'P569'))
 def test_imperial_citizenship_does_not_make_ukrainian_artist_russian(self):
  e=creator('Ukrainian painter');e['claims']['P27']=[claim({'id':'Q34266'})];self.assertIsNone(m.x.artist_country(e,'RU'))
 def test_historical_russian_affiliation_requires_biography(self):
  e=creator('Russian painter');e['claims']['P27']=[claim({'id':'Q34266'})];self.assertTrue(m.x.artist_country(e,'RU')['requires_biographical_affiliation_corroboration'])
 def test_venetian_citizenship_does_not_make_italian_artist_greek(self):
  e=creator('Italian painter');e['claims']['P27']=[claim({'id':'Q4948'})];self.assertIsNone(m.x.artist_country(e,'GR'))
 def test_southern_netherlands_not_blindly_dutch(self):self.assertIsNone(m.x.artist_country(creator('Southern Netherlands painter active in Austria'),'NL'))
 def test_flemish_not_blindly_dutch(self):self.assertIsNone(m.x.artist_country(creator('Flemish still-life painter'),'NL'))
 def test_northern_netherlands_affiliation_supported(self):self.assertIsNotNone(m.x.artist_country(creator('painter from the Northern Netherlands'),'NL'))
 def test_birthplace_not_affiliation(self):self.assertIsNone(m.x.artist_country(creator('Dutch-born French painter'),'NL'))
 def test_museum_country_not_affiliation(self):self.assertIsNone(m.x.artist_country(creator('French painter with works in Dutch museums'),'NL'))
 def test_alias_collision_blocks_new_person_without_dates(self):
  a=artist(display_name='Other Label',aliases=['Jan van Example']);found,why=m.resolve(record(),m.f.Matcher([a]));self.assertIsNone(found);self.assertIn('collision',why)
 def test_surname_first_museum_name_blocks_uncertain_new_person(self):
  a=artist(display_name='Example Jan van');found,why=m.resolve(record(),m.f.Matcher([a]));self.assertIsNone(found);self.assertEqual(why,'name_or_alias_collision_without_closed_identity_evidence')
 def test_shared_surname_alone_does_not_merge_people(self):
  a=artist(display_name='Willem van Example');found,why=m.resolve(record(),m.f.Matcher([a]));self.assertIsNone(why);self.assertIsNone(found['artist'])
 def test_named_son_requires_every_colliding_profile_to_match_reviewed_father(self):
  r=record();r['creator_entity']['claims'].update(P569=[claim({'precision':9,'time':'+1856-01-01T00:00:00Z'})],P570=[claim({'precision':9,'time':'+1927-01-01T00:00:00Z'})])
  a=artist(slug='father',birth_year=1825,death_year=1855,authorities=[{'scheme':'wikidata','id':'Q99'}])
  decision={'kind':'distinct_named_person','primary_life':[1856,1927],'excluded':[{'slug':'father','life':[1825,1855],'wikidata':'Q99'}]}
  r['primary_creator_review']={'source':{'existing_identity_decision':decision}}
  found,why=m.resolve(r,m.f.Matcher([a]));self.assertIsNone(why);self.assertIsNone(found['artist'])
  a['death_year']=1860
  found,why=m.resolve(r,m.f.Matcher([a]));self.assertIsNone(found);self.assertEqual(why,'name_or_alias_collision_without_closed_identity_evidence')
 def test_exact_museum_id_resolves_existing_person(self):
  r=record();r['creator_entity']['claims']['P2252']=[claim('123')];a=artist(authorities=[{'scheme':'nga-constituent','id':'123'}]);found,why=m.resolve(r,m.f.Matcher([a]));self.assertIsNone(why);self.assertEqual(found['artist']['id'],'one')
 def test_conflicting_museum_and_wiki_id_held(self):
  r=record();r['creator_entity']['claims']['P2252']=[claim('123')];a=artist(authorities=[{'scheme':'nga-constituent','id':'123'},{'scheme':'wikidata','id':'Q999'}]);found,why=m.resolve(r,m.f.Matcher([a]));self.assertIsNone(found);self.assertEqual(why,'existing_wikidata_conflict')
 def test_title_only_is_duplicate_lead(self):
  row={'title':'Landscape','alternate_title':None,'creator_qids':['Q10'],'creator_names':[],'accession_number':None};found,why=m.choose_existing(record(),[row]);self.assertIsNone(found);self.assertEqual(why,'title_creator_match_needs_exact_object_evidence')
 def test_primary_museum_inventory_is_checked_even_when_wikidata_omits_it(self):
  r=record();r.update(accession='77P8',primary_museum_review={'receipt':{'url':'https://gulbenkian.pt/cam/'}})
  row={'title':'Different translated title','alternate_title':None,'creator_qids':['Q10'],'creator_names':[],'accession_number':'77P8','creation_year_start':1700,'creation_year_end':1700}
  found,why=m.choose_existing(r,[row]);self.assertIsNone(why);self.assertEqual(found,row)
 def test_accession_with_conflicting_creator_held(self):
  r=record();r['entity']['claims']['P217']=[claim('A1')];row={'title':'Landscape','alternate_title':None,'creator_qids':['Q99'],'creator_names':[],'accession_number':'A1'};found,why=m.choose_existing(r,[row]);self.assertIsNone(found);self.assertEqual(why,'accession_has_conflicting_creator')
class PrimaryOverrideGuards(unittest.TestCase):
 def test_primary_creator_correction_must_match_exact_object_and_original_assertion(self):
  import tempfile,json
  with tempfile.TemporaryDirectory(prefix='artline-creator-') as tmp:
   run=Path(tmp)
   source={'review':'primary_object_creator_and_country_individually_reviewed','qid':'Q20','creator_qid':'Q11','country_code':'DE','receipt':{'url':'https://museum.example/object/20','retrieved_at':'2026-09-14T12:00:00Z'},'object':{'accession':'A20'},'original_creator_qids':['Q10'],'country_evidence':{'explicit':'German painter'},'creator_identity_evidence':{'exact_primary_birth':1840}}
   raw=json.dumps(source).encode();(run/'proof.json').write_bytes(raw)
   r={'qid':'Q20','creator_qid':'Q11','creator_entity':{'id':'Q11'},'country_code':'DE','accession':'A20','entity':{'claims':{'P170':[claim({'id':'Q10'})]}},'primary_creator_review':{'evidence_file':'proof.json','evidence_sha256':m.m.core.sha(raw)}}
   m.validate_primary_creator_review(r,run);self.assertEqual(r['primary_creator_review']['source'],source)
   r['accession']='A21'
   with self.assertRaises(AssertionError):m.validate_primary_creator_review(r,run)
   r['accession']='A20';r['entity']['claims']['P170']=[claim({'id':'Q99'})]
   with self.assertRaises(AssertionError):m.validate_primary_creator_review(r,run)
 def test_rendered_artwork_identity_is_exact(self):
  self.assertTrue(m.image_review.rendered_object_qid('Q123','<a href="https://www.wikidata.org/wiki/Q123#P1476">edit title</a>'))
  self.assertFalse(m.image_review.rendered_object_qid('Q123','<a href="https://www.wikidata.org/wiki/Q1234#P1476">edit title</a>'))
 def test_modern_artwork_photo_license_needs_underlying_permission(self):
  r={'creator_entity':{'claims':{'P570':[claim({'precision':9,'time':'+1957-01-01T00:00:00Z'})]}}}
  with self.assertRaises(ValueError):m.image_review.check_rights_chronology(r,'CC BY-SA 4.0','{{Art Photo | photo license = {{CC BY-SA 4.0}} }}')
 def test_unknown_primary_date_removes_prepared_image(self):
  import tempfile,json
  from pathlib import Path
  with tempfile.TemporaryDirectory(prefix='artline-override-') as tmp:
   run=Path(tmp);raw=json.dumps({'qid':'Q10','receipt':{'url':'https://museum.example/object/10'}}).encode();(run/'evidence.json').write_bytes(raw)
   item={'record':{'qid':'Q10'},'image':{'path':'already-prepared.jpg'}}
   override={'date':{'first':None,'last':None,'precision':'unknown','display':'Creation date under review','eligible':False},'evidence_file':'evidence.json','evidence_sha256':m.m.core.sha(raw),'reason':'Primary museum has no creation dating; broad secondary activity range is not an object date.'}
   m.reviewed_metadata_override(item,override,run);self.assertIsNone(item['image']);self.assertIsNone(item['record']['date']['first'])
 def test_primary_override_cannot_escape_evidence_directory(self):
  import tempfile
  from pathlib import Path
  with tempfile.TemporaryDirectory(prefix='artline-override-') as tmp:
   with self.assertRaises(AssertionError):m.reviewed_metadata_override({'record':{'qid':'Q10'}},{'evidence_file':'../outside.json','evidence_sha256':'x','reason':'test'},Path(tmp))
 def test_historical_context_is_not_czech_affiliation(self):
  e=creator('Austrian painter');e['claims']['P27']=[claim({'id':'Q28513'})];self.assertIsNone(m.x.artist_country(e,'CZ'))
class InventoryPreimageGuards(unittest.TestCase):
 def test_reviewed_concurrent_image_does_not_allow_unreviewed_field_changes(self):
  import tempfile,json
  spec=importlib.util.spec_from_file_location('inventory',Path(__file__).with_name('enrich-country-expansion-russian-inventories.py'));inv=importlib.util.module_from_spec(spec);spec.loader.exec_module(inv)
  with tempfile.TemporaryDirectory(prefix='artline-inventory-') as tmp:
   inv.RUN=Path(tmp)/'evidence';inv.BACK=Path(tmp)/'backups';inv.RUN.mkdir();inv.BACK.mkdir()
   old={'id':'one','slug':'example','title':'Original title','revision':1,'primary_media_id':None,'accession_number':None};now={**old,'revision':2,'primary_media_id':'documented-media'}
   (inv.BACK/'local-preimages.json').write_text(json.dumps({'example':old}));(inv.RUN/'plan.json').write_text('[]');proof=inv.RUN/'image-proof.json';proof.write_text('{}')
   add={'approved':True,'plan_sha256':inv.CORE.sha(b'[]'),'image_proof_file':str(proof),'image_proof_sha256':inv.CORE.sha(b'{}'),'preserved_existing_media_id':'documented-media','targets':{'local':{'example':{'original':old,'reviewed':now,'reason':'Reviewed image attachment'}}}}
   path=inv.RUN/'preimage-addendum.json';path.write_text(json.dumps(add));self.assertEqual(inv.reviewed_preimages('local')['example'],now)
   for field,value in [('title','Another painting'),('accession_number','Different inventory'),('revision',3),('primary_media_id','different-media')]:
    with self.subTest(field=field):
     add['targets']['local']['example']['reviewed']={**now,field:value};path.write_text(json.dumps(add))
     with self.assertRaises(AssertionError):inv.reviewed_preimages('local')
   add['targets']['local']['example']['reviewed']=now;path.write_text(json.dumps(add));proof.write_text('{"changed":true}')
   with self.assertRaises(AssertionError):inv.reviewed_preimages('local')

if __name__=='__main__':unittest.main()
