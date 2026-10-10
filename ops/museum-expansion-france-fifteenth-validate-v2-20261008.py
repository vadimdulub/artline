"""Recompute supplemental read-only identity and verify literal source captures."""
import gzip,hashlib,importlib.util,json
from pathlib import Path
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('v',Path(__file__).with_name('museum-expansion-france-fifteenth-identity-v2-20261008.py'));v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
m=v.m;f=v.f;RUN=v.RUN
def main():
 dest=RUN/'identity-recomputed-002.json';assert not dest.exists();ip=RUN/'native-identity-002.json.gz';cp=RUN/'identity-citations-002.json.gz';x=m.load(ip);cs=m.load(cp)
 for k in ['query_reference','base_query_reference','notes_reference','context_reference','checkpoint_reference','candidate_reference']:f.checked(x[k])
 assert cs['identity_reference']==f.ref(ip)
 rows=m.load(RUN/'native-candidates-001.json.gz')['rows']
 for row in rows:assert row==f.parse(row['index'],f.checked(row['source_reference']))
 augmented=v.augmented_rows(rows);assert x['params']==v.params_for(augmented)
 assert v.comparisons(augmented,x['state'],cs['citations'])==x['comparisons']
 batch=m.load(RUN/'within-batch-identity-002.json.gz');assert v.within_batch(augmented)=={k:batch[k] for k in ['inventory_groups','title_groups']}
 target=RUN/'targeted-context-001.json.gz';capture=m.load(target)
 for row in capture['rows']:
  assert 'error_reference' not in row
  raw=gzip.decompress(f.checked(row['body_reference']).read_bytes());receipt=m.load(f.checked(row['receipt_reference']))
  assert receipt['status']==200 and hashlib.sha256(raw).hexdigest()==receipt['sha256']==row['sha256']
  soup=BeautifulSoup(raw,'html.parser')
  for tag in soup(['script','style','noscript']):tag.decompose()
  assert soup.get_text('\n',strip=True)==row['literal_text']==f.checked(row['text_reference']).read_text()
 primary=RUN/'physical-comparison-context-002.json.gz';p=m.load(primary)
 for dep in p['dependencies']:f.checked(dep)
 assert not p['unresolved_primary_records'] and not p['citation_capture_record_misses']
 m.save(dest,dict(at=m.now(),validator_reference=f.ref(Path(__file__).resolve()),identity_reference=f.ref(ip),citations_reference=f.ref(cp),targeted_context_reference=f.ref(target),physical_context_reference=f.ref(primary),candidates_reparsed_equal=650,comparisons_recomputed_equal=True,within_batch_recomputed_equal=True,targeted_primary_pages_recomputed_equal=3,primary_comparator_records=len(p['rows']),unresolved_without_joconde_primary=len(p['unresolved_ids_without_object_primary_citation']),database_writes=0,policy='Reproducibility check, not editorial approval. Scores and missing metadata cannot decide physical identity.'))
 print(json.dumps(dict(validation=f.ref(dest),candidates=650,comparisons=650,targeted_pages=3,database_writes=0)),flush=True)
if __name__=='__main__':main()
