"""Final review after the complete museum-local historical inventory audit."""
import collections,importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('review_base',Path(__file__).with_name('museum-expansion-italy-third-review-20261008.py'));base=importlib.util.module_from_spec(z);z.loader.exec_module(base)
CONFLICTS={239:'Historical source inventory1153 also belongs to existing e9c1bdcf-b3f2-428a-aaba-d964f3b4c350 (1600035718). Reconcile before adding this Roch record.',289:'Historical source inventory455/36 also belongs to existing7148d0e9-b18f-4cba-92f0-01664df3b893 (0900523936). Possible catalogue reidentification/recatalogue; no duplicate added.',322:'Historical IstitutoArte171 also occurs on existing Bronzino CosimoI7924863f-ad45-4b10-856b-35ab8ef7bc6d (0900067695). Resolve inventory history before release.',339:'Historical IstitutoArte186 also occurs on existingbec57dac-3df9-4352-a0be-a636363c8f5f (0900067674). Resolve possible inventory reuse or duplicate identity.',245:'Inventory2101 is also used by selected source246; resolve historical numbering before adding either Apollonia or Casimir canvas.',246:'Inventory2101 is also used by source245; different subjects alone do not resolve a shared inventory.'}
for n,note in CONFLICTS.items():assert n in base.NOTES;base.NOTES.pop(n);base.DEFERRED[n]=note
i=base.i;f=base.f;s=base.s;m=base.m;RUN=base.RUN;ref=base.ref;checked=base.checked;NOTES=base.NOTES;DEFERRED=base.DEFERRED;dimensions=base.dimensions;values=base.values
def build(reparse=False):
 ds=base.build(reparse);rs=[v for v in ds if v['state']=='approved_review_only_addition'];assert len(rs)==242
 audit=m.load(RUN/'comparison-source-context-002.json.gz');assert not {v['number'] for v in audit['museum_local_inventory_hits']}&set(NOTES)
 assert not [v for v in i.within_batch(rs) if v['kind']=='inventory'];return ds
def main():
 dest=RUN/'editorial-reviewed-002.json.gz';assert not dest.exists();ds=build(True);previous=m.load(RUN/'editorial-reviewed-001.json.gz');checked(previous['reviewer_reference'])
 m.save(dest,dict(at=m.now(),decisions=ds,reviewer_reference=ref(Path(__file__).resolve()),dependencies=previous['dependencies']+[ref(RUN/'editorial-reviewed-001.json.gz'),ref(Path(base.__file__).resolve()),ref(RUN/'comparison-source-context-002.json.gz')],supersedes_reference=ref(RUN/'editorial-reviewed-001.json.gz'),inventory_holds=CONFLICTS,policy='Six preliminary additions withdrawn before any database writes after full historical source inventory audit. Final242 individual objects; no unresolved selected inventory collisions. All original source, identity, attribution, date and publication safeguards retained.',reparsed_candidates=len(ds)))
 print(json.dumps(dict(states=collections.Counter(v['state'] for v in ds),approved_by_museum=collections.Counter(v['museum']['name'] for v in ds if v['state']=='approved_review_only_addition'))),flush=True)
if __name__=='__main__':main()
