#!/usr/bin/env python3
"""Bounded selected reproductions with independent underlying-artwork rights."""
import importlib.util,json
from pathlib import Path
spec=importlib.util.spec_from_file_location('b',Path(__file__).with_name('research-armenian-georgian-artworks.py'));b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
spec=importlib.util.spec_from_file_location('p',Path(__file__).with_name('prepare-wikimedia-catalogue-images.py'));p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
spec=importlib.util.spec_from_file_location('safe',Path(__file__).with_name('apply-russian-deep-images.py'));safe=importlib.util.module_from_spec(spec);spec.loader.exec_module(safe)
p.r=b.r;safe.IMAGES=b.s.RUN/'images';safe.r.PREVIOUS=b.s.RUN/'images';p.r.core.Fetcher=safe.Fetcher
# Only selected full-frame reproductions. Dates still use backend-equivalent scope.
records=json.loads((b.s.RUN/'selected/catalogue.json').read_bytes())['selected'];image_budget=100;selected=0
for record in records:
 q=record['qid'];output=b.s.RUN/'ready'/(q+'.json')
 if output.exists():continue
 reason=None;death=b.r.year(record['creator_entity'],'P570')
 if not record['images']:reason='No source-linked image; metadata retained'
 elif not record['date']['eligible']:reason='Unknown or unresolved creation date; metadata retained'
 elif death is None or death>1951:reason='Underlying artwork copyright requires individual review; museum image availability is not permission'
 elif selected>=image_budget:reason='Bounded image budget reached'
 if reason:b.s.save(output,{'record':record,'image':None,'image_outcome':'metadata_retained_image_deferred','image_reason':reason})
 else:selected+=1
print('Rights-screened image candidates',selected,flush=True)
p.main()
