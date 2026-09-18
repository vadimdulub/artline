import importlib.util,json,tempfile,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('report',Path(__file__).with_name('report-overnight-images.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class VerifiedReporting(unittest.TestCase):
 def test_retries_do_not_increase_count_and_withdrawal_removes(self):
  with tempfile.TemporaryDirectory(prefix='artline-report-test-') as root:
   path=Path(root)/'journal.jsonl';rows=[{'artwork_id':'a','outcome':'attached'},{'artwork_id':'a','outcome':'already_attached'},{'artwork_id':'b','outcome':'attached'},{'artwork_id':'a','outcome':'withdrawn'}];path.write_text(''.join(json.dumps(x)+'\n' for x in rows));self.assertEqual(set(m.journal_state(path)),{'b'})
 def audit(self):return {'target':'cloud','errors':[],'journal_snapshot_artworks':10,'source_and_file_verified':10,'db_verified':10,'google_storage_verified':10}
 def test_complete_target_passes(self):m.audit_matches(self.audit(),10,'cloud',True)
 def test_stale_snapshot_fails(self):
  with self.assertRaises(AssertionError):m.audit_matches(self.audit(),11,'cloud',True)
 def test_failed_source_check_fails(self):
  a=self.audit();a['errors']=[{'error':'source mismatch'}]
  with self.assertRaises(AssertionError):m.audit_matches(a,10,'cloud',True)
 def test_missing_storage_object_fails(self):
  a=self.audit();a['google_storage_verified']=9
  with self.assertRaises(AssertionError):m.audit_matches(a,10,'cloud',True)
 def test_wrong_target_fails(self):
  with self.assertRaises(AssertionError):m.audit_matches(self.audit(),10,'local')
 def test_hold_registry_prevents_delivery_before_withdrawal_journal_arrives(self):
  with tempfile.TemporaryDirectory(prefix='artline-hold-test-') as root:
   run=Path(root);(run/'withdrawn-images.json').write_text(json.dumps({'records':[{'artwork_id':'held','status':'withdrawn'}]}));(run/'local-attachments.jsonl').write_text('\n'.join(json.dumps(x) for x in [{'artwork_id':'held','outcome':'attached'},{'artwork_id':'ready','outcome':'attached'}]))
   self.assertEqual(set(m.delivery.pending_journal(run,set(),set())),{'ready'})
 def test_late_receipt_cannot_reintroduce_a_held_image(self):
  with tempfile.TemporaryDirectory(prefix='artline-hold-test-') as root:
   run=Path(root);(run/'withdrawn-images.json').write_text(json.dumps({'records':[{'artwork_id':'held','status':'withdrawn'}]}));(run/'local-attachments.jsonl').write_text('\n'.join(json.dumps(x) for x in [{'artwork_id':'held','outcome':'withdrawn'},{'artwork_id':'held','outcome':'already_attached'}]))
   self.assertEqual(m.delivery.pending_journal(run,set(),set()),{})
if __name__=='__main__':unittest.main()
