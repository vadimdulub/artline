"""Offline source-boundary checks; never creates a database or fixtures in one."""
import importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('f',Path(__file__).with_name('museum-expansion-courtauld-facts-20261007.py'));f=importlib.util.module_from_spec(s);s.loader.exec_module(f)

class CourtauldEvidenceTests(unittest.TestCase):
 def row(self,sid):
  v,p=f.checked_record(f.RUN/'objects'/(sid+'.json.gz'));return f.facts(v,p)
 def test_names_in_submit_values_not_lifespans(self):
  r=self.row('p-2024-xx-1');self.assertEqual(r['creator_label'],'Vanessa Bell');self.assertEqual((r['first'],r['last']),(1944,1944));self.assertEqual(r['creator_parts'][0]['biographical_lines'],['1879-1961']);self.assertIn('2024',r['acquisition'])
 def test_plaintext_maker_without_search_form(self):self.assertEqual(self.row('p-1966-gp-9')['creator_label'],'Giuseppe Angeli')
 def test_missing_maker_not_inferred(self):self.assertIsNone(self.row('p-1978-pg-106')['creator_label'])
 def test_multiple_maker_roles_preserved(self):self.assertEqual(self.row('p-1978-pg-1--missing-')['creator_label'],'Hans von Aachen; After Federico Barocci')
 def test_workshop_role_preserved(self):self.assertEqual(self.row('p-1947-lf-38')['creator_label'],'Sandro Botticelli; Workshop of Sandro Botticelli')
 def test_prototype_biography_not_creator_name_or_object_date(self):
  r=self.row('p-1978-pg-439');self.assertEqual(r['creator_label'],'David Teniers the Younger; After Antonello da Messina');self.assertEqual(r['creator_parts'][1]['biographical_lines'],['ca.1430-1479 (Life dates)']);self.assertGreater(r['first'],1600)
 def test_recto_and_verso_remain_one_inventory(self):
  r=self.row('p-1978-pg-3');self.assertEqual(r['inventory'],'P.1978.PG.3');self.assertEqual(r['titles'],['Christ Bearing the Cross (Front)','The Annunciation (Back)']);self.assertIn('Frame of carved wood',r['medium'])
 def test_loan_credit_is_explicit_in_retained_probe(self):
  v=f.m.load(f.RUN/'object-probe-002.json.gz');p=f.c.parsed_object(f.c.saved_body(v['capture']));credit=next(x['text'] for x in p['fields'] if x['label']=='Credit');self.assertEqual(credit,'Private Collection. On long-term loan to the Courtauld Gallery, London')
 def test_missing_object_statement_preserved(self):
  r=self.row('p-1978-pg-1--missing-');self.assertIn('(MISSING)',r['inventory']);self.assertIn('reported missing in 1998',r['provenance'])
 def test_reassembled_fragments_not_assumed_separate_works(self):
  a=self.row('p-1947-lf-31');b=self.row('p-1999-xx-1');self.assertIn('single large painting',a['description']);self.assertEqual(a['description'],b['description']);self.assertNotEqual(a['inventory'],b['inventory'])
 def test_qualified_date_interval(self):
  r=f.creation('(circa) 1750 - 1760');self.assertEqual((r['first'],r['last'],r['date_precision']),(1750,1760,'circa_range'))
 def test_decade_qualifier_has_matching_numeric_interval(self):self.assertEqual(f.creation("(1920's) 1920 - 1929")['last'],1929)
 def test_disagreeing_decade_qualifier_held(self):self.assertIsNotNone(f.creation("(1920's) 1930 - 1939")['date_issue'])
 def test_unknown_and_cutoff_dates_stay_held(self):
  for value in [None,'1978','1970 - 1972','c. 1970','20th century','(?) 1812','21.9.1822']:
   with self.subTest(value=value):self.assertIsNotNone(f.creation(value)['date_issue'])
 def test_unqualified_1970_eligible(self):self.assertEqual(f.creation('1970')['last'],1970)
 def test_source_rights_preserved_without_image_approval(self):self.assertIn('DACS 2024',self.row('p-2024-xx-1')['copyright'])
 def test_active_and_qualified_life_dates_are_separate(self):
  for sid,label in [('p-1947-lf-20','Barnaba da Modena'),('p-1966-gp-83','Bernardo Daddi'),('p-1982-xx-96','Lino Dinetto'),('p-1966-gp-196','Gerino da Pistoia')]:
   with self.subTest(sid=sid):self.assertEqual(self.row(sid)['creator_label'],label)
 def test_geographical_period_label_is_not_a_biography(self):self.assertEqual(self.row('p-1966-gp-14')['creator_label'],'Netherlands (Antwerp) 16th century (Artists)')
 def test_review_selection_excludes_children_and_source_conflicts(self):
  decisions=f.m.load(f.RUN/'editorial-reviewed-001.json.gz')['decisions'];ids={r['source_id'] for r in decisions};self.assertEqual(len(ids),90)
  for sid in ['p-1966-gp-10','p-1966-gp-264','p-1966-gp-82']:self.assertIn(sid,ids)
  for sid in ['p-1966-gp-10-1','p-1966-gp-264-1','p-1966-gp-82-1','p-1947-lf-31','p-1999-xx-1','p-1947-lf-50','p-1982-lb-177']:self.assertNotIn(sid,ids)
 def test_copy_and_forgery_labels_are_not_original_authorship(self):
  self.assertEqual(self.row('p-1935-rf-148')['creator_label'],'Roger Eliot Fry; Copy after Paul Cézanne')
  r=self.row('p-1947-lf-40');self.assertEqual(r['creator_label'],'Umberto Giunti; Forgery in the manner of Sandro Botticelli');self.assertEqual((r['first'],r['last']),(1920,1929))

if __name__=='__main__':unittest.main()
