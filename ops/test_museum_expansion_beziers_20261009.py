"""Offline source-policy checks; no database fixtures or writes."""
import importlib.util,unittest
from pathlib import Path
z=importlib.util.spec_from_file_location('r',Path(__file__).with_name('museum-expansion-beziers-review-v2-20261009.py'));r=importlib.util.module_from_spec(z);z.loader.exec_module(r);f=r.i.f
class EvidenceBoundaries(unittest.TestCase):
 def test_after_does_not_borrow_quarter_or_lifespan_end(self):self.assertEqual(f.dates({'Millesime_de_creation':'après 1922','Periode_de_creation':'1er quart 20e siècle','Auteur':'Moulin Jean (1899-1943)'})[:3],(1922,None,'after'))
 def test_twentieth_century_not_truncated(self):self.assertEqual(f.dates({'Periode_de_creation':'20e siècle'})[:3],(1901,2000,'century'))
 def test_cross_century_explicit_period(self):self.assertEqual(f.dates({'Periode_de_creation':'4e quart 19e siècle;1ère moitié 20e siècle'})[:3],(1876,1950,'range'))
 def test_before_keeps_unknown_start(self):self.assertEqual(f.dates({'Millesime_de_creation':'avant 1867'})[:3],(None,1867,'before'))
 def test_questioned_century_remains_unknown(self):self.assertEqual(f.dates({'Periode_de_creation':'19e siècle;?'})[:3],(None,None,'unknown'))
 def test_acquisition_is_not_creation(self):self.assertEqual(f.dates({'Date_d_acquisition':'1979','Auteur':'Boussac (1846-1942)'})[:3],(None,None,'unknown'))
 def test_unrecognized_numeric_date_rejected(self):
  with self.assertRaises(ValueError):f.dates({'Millesime_de_creation':'1930 ou 1934'})
 def test_qualified_inscriptions_take_precedence(self):
  ds={d['number']:d for d in r.build()}
  for n,year in r.CIRCA.items():self.assertEqual((ds[n]['facts']['first'],ds[n]['facts']['last'],ds[n]['facts']['date_precision']),(year,year,'circa'))
 def test_existing_delacroix_not_recreated(self):self.assertEqual(next(d for d in r.build() if d['number']==23)['state'],'already_catalogued')
 def test_all_discovered_sources_tracked(self):
  rows,held,known=f.rows();self.assertEqual(len(rows)+len(held)+len(known),485);self.assertEqual(len({v['source_id'] for v in rows+held+known}),485)
 def test_original_cartoon_not_documentary_postcard(self):
  d=next(d for d in r.build() if d['number']==149);self.assertEqual(d['facts']['work_type'],'drawing');self.assertIn('encre de Chine',d['facts']['medium'])
 def test_sheets_and_group_holds(self):
  rows,held,known=f.rows();self.assertTrue({59,134,166,167,168,169,170,171,172,173,174,175,176,177,178,179}<={d['number'] for d in held})
if __name__=='__main__':unittest.main()
