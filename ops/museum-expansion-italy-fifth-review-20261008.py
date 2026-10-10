"""Reconstruct source facts and bind explicit three-museum editorial decisions."""
import collections,copy,importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('w',Path(__file__).with_name('museum-expansion-italy-fifth-working-20261008.py'));w=importlib.util.module_from_spec(z);z.loader.exec_module(w)
s=w.s;i=s.i;f=s.f;m=s.m;RUN=s.RUN;SOURCE=s.SOURCE;ref=s.ref;checked=s.checked;NOTES=w.NOTES
working=m.load(RUN/'source-editorial-working-001.json');DEFERRED={int(k):v for k,v in working['prior_source_holds'].items()};DEFERRED.update(w.HOLDS)
values=s.prior.r.values;dimensions=s.prior.r.dimensions
def build(reparse=False):
 original=m.load(SOURCE/'native-candidates-002.json.gz')['rows'];x=m.load(RUN/'selected-identity-001.json.gz');comps={v['number']:v for v in x['comparisons']};assert x['rows']==s.rows();checked(x['script_reference']);checked(x['base_script_reference']);checked(working['script_reference']);assert {int(k):v['basis'] for k,v in working['notes'].items()}==NOTES;g=values()
 if reparse:
  fresh,_=f.build();assert fresh==original
 assert len(NOTES)==211 and not(set(NOTES)&set(DEFERRED));ds=[]
 context=m.load(RUN/'comparison-source-context-001.json.gz');assert not {v['number'] for v in context['museum_local_inventory_hits']}&set(NOTES)
 for row in original:
  if row['institution_id'] not in s.TARGETS:continue
  n=row['number']
  if n not in NOTES:
   ds.append(dict(number=n,institution_id=row['institution_id'],museum=row['museum'],source_id=row['index_record']['source_record_id'],state='editorial_hold' if row['state']!='candidate' or n in DEFERRED else 'deferred_identity_review',basis=DEFERRED.get(n,'Source issues: '+', '.join(row['issues']) if row['issues'] else 'Physical version/source-note identity review pending; no artwork approved.')));continue
  assert row['state']=='candidate' and not row['issues'];v=copy.deepcopy(row['facts']);cmp=comps[n];assert not cmp['source_hits'] and v['last']<=1970
  v['dimensions_text']=dimensions(v,g);derived=dict(dimensions_text=dict(value=v['dimensions_text'],basis='Literal measurements, explicit units only; frame notes preserved.',source_reference=ref(SOURCE/'measurement-values-002.json.gz')))
  ds.append(dict(row,facts=v,state='approved_review_only_addition',confidence=.88,existing_artwork_id=None,basis=NOTES[n],comparison=cmp,derived_fields=derived,limitation='Editorial confidence, not calibrated probability. Qualified/unnamed makers, questioned subjects, dates and source rights retained. Physical support, composition, provenance and inventory distinguish versions. Holdings are catalogue evidence, not a fresh display observation. Review status retained as audit data; unified catalogue visibility follows current application policy. No images or painter authority links.'))
 assert len(ds)==401;assert not [v for v in i.within_batch([v for v in ds if v['state']=='approved_review_only_addition']) if v['kind']=='inventory'];return ds
def main():
 dest=RUN/'editorial-reviewed-001.json.gz';assert not dest.exists();ds=build(True)
 deps=[ref(RUN/n) for n in ['selected-identity-001.json.gz','selected-citations-001.json.gz','comparison-source-context-001.json.gz','source-editorial-working-001.json']]+[ref(SOURCE/n) for n in ['native-candidates-002.json.gz','measurement-values-002.json.gz','source-editorial-working-002.json']]
 m.save(dest,dict(at=m.now(),decisions=ds,reviewer_reference=ref(Path(__file__).resolve()),dependencies=deps,policy='211 individually reviewed works from401 notices at Cenacolo, Cremona and Guinigi. Remaining190 notices retained; prior Vicenza/Devanna queue unchanged. No quota-based approval.',reparsed_candidates=698))
 print(json.dumps(dict(states=collections.Counter(v['state'] for v in ds),approved_by_museum=collections.Counter(v['museum']['name'] for v in ds if v['state']=='approved_review_only_addition'))),flush=True)
if __name__=='__main__':main()
