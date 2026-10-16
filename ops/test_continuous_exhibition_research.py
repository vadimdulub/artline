"""Supervisor recovery tests; no catalogue, cloud, or actual research workers."""
import fcntl
import importlib.util
import pathlib
import subprocess
import sys
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('exhibition_supervisor',pathlib.Path(__file__).with_name('continuous-exhibition-research.py'))
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)

class SupervisorTests(unittest.TestCase):
 def test_paths_are_isolated(self):
  self.assertEqual(s.DATA.name,'continuous-exhibition-research')
  self.assertEqual(s.PROMPT.name,'INFINITE_EXHIBITION_RESEARCH_PROMPT.md')
  self.assertNotIn('new_painters',s.schema()['properties']['verified_counts']['properties'])
 def test_atomic_checkpoint(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=pathlib.Path(tmp)/'state.json';s.save(p,{'inflight':1});s.save(p,{'next_batch':2})
   self.assertEqual(s.read(p),{'next_batch':2});self.assertFalse(p.with_suffix('.json.tmp').exists())
 def test_missing_evidence_rejected(self):
  counts={k:0 for k in s.schema()['properties']['verified_counts']['properties']};counts['new_exhibitions']=1
  with self.assertRaises(AssertionError):s.result_valid(dict(outcome='progress',verified_counts=counts,evidence_paths=[]))
 def test_orphan_worker_retains_singleton(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=pathlib.Path(tmp)/'lock';lock=p.open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
   child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(10)'],pass_fds=(lock.fileno(),))
   lock.close()
   try:
    with p.open('a+') as contender:
     with self.assertRaises(BlockingIOError):fcntl.flock(contender,fcntl.LOCK_EX|fcntl.LOCK_NB)
   finally:child.terminate();child.wait()
   with p.open('a+') as contender:fcntl.flock(contender,fcntl.LOCK_EX|fcntl.LOCK_NB)
 def test_bounded_worker_and_shared_locks(self):
  p=s.prompt_for(1,{})
  for phrase in ['ONE bounded batch','2026101201','artline-curated-ingestion','Do not create or launch another supervisor','1600 through 1989']:
   self.assertIn(phrase,p)

if __name__=='__main__':unittest.main()
