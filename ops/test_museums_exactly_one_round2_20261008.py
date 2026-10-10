"""Real-source mutation proofs; no database fixtures or writes."""
import copy,gzip,importlib.util,json,unittest
from pathlib import Path
from bs4 import BeautifulSoup

s=importlib.util.spec_from_file_location('round2',Path(__file__).with_name('museums-exactly-one-round2-20261008.py'))
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

class CrockerSourceGuards(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.row=m.d.load(m.RUN/'waves/crocker-reviewed/source-verified.json.gz')['records'][0]
        cls.raw=gzip.decompress((m.ROOT/cls.row['body_path']).read_bytes())

    def changed(self,art_changes,visible_changes=None):
        soup=BeautifulSoup(self.raw,'html.parser');node=soup.select_one('#__NEXT_DATA__');data=json.loads(node.text)
        data['props']['pageProps']['art'].update(art_changes);node.string=json.dumps(data)
        for li in soup.select('li'):
            cells=li.select('div.grid > div')
            if len(cells)==2 and cells[0].get_text(' ',strip=True) in (visible_changes or {}):
                cells[1].string=visible_changes[cells[0].get_text(' ',strip=True)]
        return str(soup).encode()

    def test_preserved_native_object_recomputes(self):
        facts,_,_=m.crocker_facts(self.raw);self.assertEqual(facts,self.row['facts'])

    def test_visible_and_native_inventory_must_agree(self):
        with self.assertRaises(AssertionError):m.crocker_facts(self.changed({'accessionNumber':'different-work'}))

    def test_creation_after_1970_is_rejected(self):
        with self.assertRaises(AssertionError):m.crocker_facts(self.changed({'madeDate':{'date':'1971'}},{'date':'1971'}))

    def test_unknown_date_is_not_invented_from_acquisition(self):
        with self.assertRaises(AssertionError):m.crocker_facts(self.changed({'madeDate':{'date':'n.d.'}},{'date':'n.d.'}))

    def test_loan_credit_does_not_become_holding(self):
        credit='Crocker Art Museum, on loan from a private collection'
        with self.assertRaises(AssertionError):m.crocker_facts(self.changed({'creditLine':credit},{'credit line':credit}))

    def test_display_flag_is_not_a_display_assertion(self):
        baseline=m.crocker_facts(self.raw)[0]
        changed=m.crocker_facts(self.changed({'onView':False}))[0]
        self.assertEqual(changed,baseline);self.assertNotIn('display_state',changed)

if __name__=='__main__':unittest.main()
