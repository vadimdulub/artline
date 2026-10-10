#!/usr/bin/env python3
"""Read-only evidence for ambiguous existing Thyssen identity leads."""
import importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('i',Path(__file__).with_name('museum-expansion-thyssen-identity-20261007.py'));i=importlib.util.module_from_spec(s);s.loader.exec_module(i);m=i.m;f=i.f;RUN=i.RUN
NUMBERS=[2,8,9,14,15,17,19,20,29,34,36,38,41,44,45,48,49,50,53,55,59,63,67,68,69,87,92,116,118,120,123,124,129,130,131,133,134,135,137,138,139,141,144,146,150,151,153,155,156,158,160,162,164,173,180,193,204,207,208]
def main():
 rows=[r for r in m.load(RUN/'native-candidates-002.json.gz')['rows'] if r['state']=='candidate'];cm={r['source_id']:r for r in m.load(RUN/'identity-comparisons-002.json.gz')['records']};ids=set();selected=[]
 for num in NUMBERS:
  r=rows[num-1];c=cm[r['source_id']];ls=c['focused_top'][:8]+c['leads'][:8]
  ids.update(a['id'] for a in ls);ids.update(a['entity_id'] for a in c['source_hits']+c['native_url_hits']+c['institution_native_id_hits']);selected.append(dict(number=num,source_id=r['source_id'],compared_ids=sorted({a['id'] for a in ls})))
 ids=sorted(ids);assert len(ids)<600
 with m.connect() as db:
  arts=db.execute('SELECT '+i.i.ARTCOLS+' FROM artworks a WHERE a.id=ANY(%s::uuid[]) ORDER BY a.id',(ids,)).fetchall()
  cites=db.execute("SELECT entity_id::text,source_url,source_record_id,field_name,evidence_note FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id",(ids,)).fetchall()
  ext=db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id",(ids,)).fetchall()
 m.save(RUN/'version-scope-001.json.gz',dict(at=m.now(),selected=selected,ids=ids,artworks=arts,citations=cites,identifiers=ext,candidate_reference=f.ref(RUN/'native-candidates-002.json.gz'),comparison_reference=f.ref(RUN/'identity-comparisons-002.json.gz'),reviewer_reference=f.ref(Path(__file__).resolve()),policy='Bounded read-only existing citation and identifier evidence for title/physical-version leads; not an identity decision.'))
 print(json.dumps(dict(records=len(arts),citations=len(cites),identifiers=len(ext))),flush=True)
if __name__=='__main__':main()
