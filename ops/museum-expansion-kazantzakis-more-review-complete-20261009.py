"""Finish immutable editorial review after production authentication expired.

A fresh full comparator snapshot remains mandatory in the apply preflight.
No live credentials or production state are inferred from offline evidence.
"""
import collections,importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('r',Path(__file__).with_name('museum-expansion-kazantzakis-more-review-20261009.py'));r=importlib.util.module_from_spec(z);z.loader.exec_module(r);m=r.m;RUN=r.RUN;ref=r.ref
ds=r.build();visual=m.load(RUN/'visual-assessment-001.json');assert visual['images_seen']==110
for v in ['institution-reconciliation-001.json','visual-assessment-001.json']:assert (RUN/v).exists()
deps=[RUN/v for v in ['candidate-facts-001.json.gz','production-identity-001.json.gz','production-identity-citations-001.json.gz','production-initial-scope-001.json.gz','native-selection-001.json.gz','visual-assessment-001.json','visual-reference-captures-001.json','institution-reconciliation-001.json']]
m.save(RUN/'editorial-reviewed-001.json.gz',dict(at=m.now(),decisions=ds,dependencies=[ref(v)for v in deps],reviewer_reference=ref(Path(r.__file__).resolve()),completion_reference=ref(Path(__file__).resolve()),policy='105new review artworks:104drawings andone mixed-technique scenery detail with unknown physical type. Four reproductions andone image/description mismatch held. Source title corruption corrected in2records from clean text onthe same objectpage; literals preserved. Explicit1940–1941objectdates,unknown creators,and source/enrichment discrepancy retained. No inferred artist identities,materials,accessions or dates. Local catalogue read-only. Editorial review uses the completed read-only identity snapshot. Google Cloud reauthentication is required to capture the full comparator snapshot and perform fresh production preflight; this artifact is not a write receipt.'))
print(json.dumps(dict(states=dict(collections.Counter(v['state']for v in ds)),types=dict(collections.Counter(v['facts']['work_type']for v in ds if v['state']=='approved_review_only_addition')))),flush=True)
