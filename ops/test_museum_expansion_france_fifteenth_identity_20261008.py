"""Pure guards for physical subinventory identity and search-only augmentation."""
import copy,importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('v',Path(__file__).with_name('museum-expansion-france-fifteenth-identity-v2-20261008.py'));v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
class InventoryTests(unittest.TestCase):
 def test_portfolio_subinventory_is_not_parent(self):
  self.assertNotEqual(v.accession_tokens('2008.2.7(10)'),v.accession_tokens('2008.2.7(11)'))
  self.assertNotEqual(v.accession_tokens('2008.2.7(10)'),v.accession_tokens('2008.2.7'))
 def test_only_annotation_removed(self):
  self.assertEqual(v.inventory_parts("2008.2.7(10) (Numéro d'inventaire)"),['2008.2.7(10)'])
  self.assertEqual(v.inventory_parts('978.15.2 ; D 978.3.2 (Autres n°) ; R.F. 37078 (Autres n°)'),['978.15.2','D 978.3.2','R.F. 37078'])
 def test_parenthetic_old_inventory_survives(self):
  self.assertNotEqual(v.accession_tokens('20(2)'),v.accession_tokens('20'))
 def test_citation_is_inventory_field_only(self):
  self.assertEqual(list(v.citation_inventories({'facts':{'inventory':'INV 431','title':'INV 432','source_fields':{'Numero_inventaire':'CL 22282'}},'unrelated':{'description':'INV 433'}})),['INV 431','CL 22282'])
 def test_comparison_augmentation_preserves_literal(self):
  rows=v.m.load(v.RUN/'native-candidates-001.json.gz')['rows'];before=copy.deepcopy(rows)
  augmented=v.augmented_rows(rows)
  self.assertEqual(rows,before)
  self.assertEqual(augmented[0]['facts']['inventory'],rows[0]['facts']['inventory'])
  self.assertIn('RF 37078',augmented[329]['comparison_only']['related_inventory_forms'])
  self.assertNotIn('RF 37078',augmented[329]['facts']['inventory'].split(';'))
  self.assertIn('batoni',v.terms(augmented[213]['facts']))
  self.assertIn('The Offer of Love',augmented[318]['facts']['titles'])
if __name__=='__main__':unittest.main()
