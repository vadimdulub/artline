"""Regression checks from preserved catalogue objects; no database fixtures."""
import copy,importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('expansion',Path(__file__).with_name('museum-1-100-expansion-20261007.py'))
x=importlib.util.module_from_spec(s);s.loader.exec_module(x)
x.c.d.scheme=x.scheme


class BatchIdentityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records=x.c.load(x.c.RUN/'waves/expand-1-100-reuse-001/source-verified.json.gz')['records']
        cls.byid={r['source_record_id']:r for r in cls.records}

    def review(self,*ids):
        rows=[self.byid[i]for i in ids]
        return rows,x.c.d.batch_identity_conflicts(rows)

    def test_shared_inventory_series_requires_review(self):
        rows,held=self.review('HistoricOrArtisticProperty/1600035521-1','HistoricOrArtisticProperty/1600035521-10')
        self.assertEqual(set(held),{r['artwork_id']for r in rows})
        self.assertTrue(all('within_batch_inventory_identity_requires_reconciliation'in v for v in held.values()))

    def test_two_qids_do_not_resolve_identical_title_without_inventory(self):
        rows,held=self.review('Q119142337','Q119142344')
        self.assertEqual(set(held),{r['artwork_id']for r in rows})

    def test_distinct_inventoried_objects_can_share_title(self):
        _,held=self.review('HistoricOrArtisticProperty/0900197033','HistoricOrArtisticProperty/0900197035')
        self.assertFalse(held)

    def test_shared_native_crosswalk_requires_reconciliation(self):
        rows,_=self.review('HistoricOrArtisticProperty/0900197033','HistoricOrArtisticProperty/0900197035')
        rows=copy.deepcopy(rows);rows[1]['alternate_native_urls']=[rows[0]['facts']['source_url']]
        held=x.c.d.batch_identity_conflicts(rows)
        self.assertEqual(set(held),{r['artwork_id']for r in rows})

    def test_missing_inventory_does_not_prove_distinct_object(self):
        rows,held=self.review('HistoricOrArtisticProperty/0500165707','HistoricOrArtisticProperty/0500165722')
        self.assertEqual(set(held),{r['artwork_id']for r in rows})

    def test_single_verified_candidate_has_no_batch_conflict(self):
        _,held=self.review('HistoricOrArtisticProperty/0900197033')
        self.assertFalse(held)


if __name__=='__main__':unittest.main()
