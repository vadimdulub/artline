"""Reparse literal source facts and recompute fresh identity without DB writes."""
import importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('r',Path(__file__).with_name('museum-expansion-france-seventeenth-review-20261008.py'));r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
def main():
 rows=r.m.load(r.CANDIDATES)['rows'];ix=r.m.load(r.IDENTITY);c=r.m.load(r.CITATIONS)
 assert rows==r.i.rows()[0]
 for row in rows:assert row==r.f.parse(row['index'],r.checked(row['source_reference']))
 augmented=r.i.rows()[1];assert r.identity.params_for(augmented)==ix['params']
 assert r.identity.comparisons(augmented,ix['state'],c['citations'])==ix['comparisons']
 batch=r.m.load(r.RUN/'within-batch-identity-001.json.gz')
 assert all(batch[k]==v for k,v in r.identity.within_batch(augmented).items())
 triage=r.m.load(r.RUN/'comparison-triage-001.json.gz');audit=[]
 for row in triage['rows']:
  if row['number'] not in r.NOTES:continue
  for e in row['entries']:
   if not e['needs_individual_review'] and any(v['rule']=='disjoint_explicit_source_creation_bounds' for v in e['physical_exclusion_proposal']):
    contexts=triage['existing_contexts'][e['existing_artwork_id']]['primary_contexts']
    assert contexts and row['number'] in r.n.FOLLOWUP
    if row['number']==428:
     for ctx in contexts:
      d=ctx['literal_primary_record'];domain=d.get('Domaine') or ''
      assert any(k in domain.split(';') for k in ['peinture','dessin','estampe']) or ('sculpture' in domain and 'CL 11635 A' in d['Numero_inventaire'] and 'bois' in d['Materiaux_techniques'])
    audit.append(dict(number=row['number'],existing_artwork_id=e['existing_artwork_id'],primary_contexts=contexts,triage_proposal=e['physical_exclusion_proposal'],editorial_basis=r.n.FOLLOWUP[row['number']],policy='Date-only proposal checked against source physical medium/domain, measured format, composition and object history; no automatic duplicate exclusion from dates alone.'))
 r.m.save(r.RUN/'physical-date-audit-001.json.gz',dict(at=r.m.now(),rows=audit,triage_reference=r.ref(r.RUN/'comparison-triage-001.json.gz'),notes_reference=r.ref(Path(r.n.__file__).resolve()),database_writes=0))
 r.m.save(r.RUN/'identity-recomputed-001.json',dict(at=r.m.now(),candidates_reparsed_equal=len(rows),comparisons_recomputed_equal=True,within_batch_recomputed_equal=True,identity_reference=r.ref(r.IDENTITY),candidate_reference=r.ref(r.CANDIDATES),database_writes=0))
 print(json.dumps(dict(reparsed=len(rows),comparisons_equal=True,date_proposals_reviewed=len(audit))),flush=True)
if __name__=='__main__':main()
