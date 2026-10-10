#!/usr/bin/env python3
"""Source-gate the72 selected Fitzwilliam follow-up records, retaining all holds."""
import importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('prior',Path(__file__).with_name('museum-expansion-fitzwilliam-apply-20261007.py'));prior=importlib.util.module_from_spec(s);s.loader.exec_module(prior);e=prior.e;m=prior.m;RUN=prior.RUN
def candidates():
 dest=RUN/'native-candidates-003.json.gz';assert not dest.exists();queue=m.load(RUN/'native-object-queue-002.json');old={r['source_id'] for r in m.load(RUN/'native-object-queue-001.json')['objects']};rows=[]
 for lead in sorted(queue['objects'],key=lambda r:int(r['source_id'])):
  sid=lead['source_id'];assert sid not in old;p=RUN/'native-objects-002'/(sid+'.json.gz');ref=prior.reference(p);native=e.checked_object(ref);facts=e.source_facts(native);holds=[]
  if facts['date_issue']:holds.append(facts['date_issue'])
  elif not 1<=facts['first']<=facts['last']<=1970:holds.append('outside pre-1971 creation scope')
  if not facts['title'] or not facts['inventory'] or not facts['creator_label']:holds.append('incomplete title/inventory/creator')
  if facts['entity_names']!=['painting']:holds.append('object type requires separate review')
  if len(facts['owners'])!=1 or facts['owners'][0]['summary_title']!='The Fitzwilliam Museum':holds.append('holding identity requires separate review')
  methods=[a.get('method',{}).get('value') for a in facts['acquisition']]
  if len(methods)!=1 or methods[0] not in ['bought','bequeathed','given']:holds.append('acquisition/loan status requires separate review')
  rows.append(dict(source_id=sid,facts=facts,state='source_hold' if holds else 'candidate',holds=holds,source_reference=ref))
 assert len(rows)==72
 m.save(dest,dict(at=m.now(),rows=rows,captured=72,policy='Source gates only; candidate is not approval. Creation, acquisition and prototype dates remain distinct. Explicit native periods retain literal wording and conservative full-period envelopes. No database writes.'))
 print(json.dumps(dict(captured=72,candidates=sum(r['state']=='candidate' for r in rows),held=sum(r['state']=='source_hold' for r in rows))))
if __name__=='__main__':candidates()
