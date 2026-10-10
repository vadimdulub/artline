"""Source-grounded comparison triage; unresolved pairs require editorial review."""
import collections,importlib.util,json,re
from pathlib import Path
s=importlib.util.spec_from_file_location('i',Path(__file__).with_name('museum-expansion-france-sixteenth-identity-20261008.py'));i=importlib.util.module_from_spec(s);s.loader.exec_module(i);m=i.m;RUN=i.RUN;ref=i.ref
KEYS=['leads','exact_title_hits','inventory_hits','untitled_creator_hits','lexical_hits','object_alias_hits','related_inventory_hits']
def family(d):
    med=m.norm(d.get('Materiaux_techniques'));dom=set(m.norm(d.get('Domaine')).split(';'));dom={m.norm(v) for v in (d.get('Domaine') or '').split(';')};form=m.norm(d.get('Denomination'))
    if re.search(r'collage|assemblage|mixte|mixed|combinaison',med):return None
    if 'sculpture' in dom:
        materials=[(key,pat) for key,pat in [('wax','cire'),('terracotta','terre cuite'),('plaster','platre'),('marble','marbre'),('stone','pierre|calcaire|gres|albatre'),('ivory','ivoire'),('wood','bois|chene|noyer|ebene|tilleul'),('bronze','bronze')] if re.search(r'\b(?:'+pat+r')\b',med)]
        if len(materials)==1:return 'sculpture_'+materials[0][0]
        return None
    if 'estampe' in dom and re.search(r'papier|paper',med) and re.search(r'burin|eau forte|gravure|lithograph|aquatinte|serigraph|pointe seche',med):return 'paper_print'
    if dom&{'dessin','arts graphiques'} and re.search(r'papier|paper',med) and not re.search(r'huile|imprime|lithograph|gravure|burin|eau forte|email|ivoire',med) and re.search(r'crayon|mine de plomb|graphite|pierre noire|sanguine|pastel|aquarelle|gouache|lavis|encre|plume|fusain|craie',med):return 'paper_drawing'
    if 'peinture' in dom:
        if re.search(r'\bcire\b',med):return None
        if re.search(r'\bemail\b',med):return 'enamel_painting'
        if re.search(r'\bivoire\b',med) and re.search(r'aquarelle|gouache',med):return 'ivory_painting'
        if re.search(r'\bhuile\b',med) and not re.search(r'pastel|fusain|sanguine|crayon|graphite|encre|aquarelle|gouache',med):return 'oil_painting'
    return None
def bounds(d):
    dates,issue=i.f.n.date_facts(d)
    if not dates or issue:return None
    return (dates['first'],dates['last']-(1 if dates['date_precision']=='before' else 0))
def reason(candidate,primary,identity_signal=False):
    if identity_signal:return None
    ca=family(candidate);cb=family(primary)
    if ca and cb and ca!=cb:return dict(rule='incompatible_explicit_physical_family',candidate_family=ca,comparator_family=cb)
    da=bounds(candidate);db=bounds(primary)
    if da and db and ((da[0] is not None and db[1]<da[0]) or (db[0] is not None and da[1]<db[0])):return dict(rule='disjoint_explicit_source_creation_bounds',candidate_bounds=da,comparator_bounds=db)
    return None
def main():
    dest=RUN/'comparison-triage-001.json.gz';assert not dest.exists();rows=m.load(RUN/'remaining-candidates-001.json.gz')['rows'];ix=m.load(RUN/'native-identity-001.json.gz');contexts={}
    oldctx=m.load(i.OLD/'physical-comparison-context-002.json.gz')
    for p in oldctx['rows']:contexts.setdefault(p['existing_artwork_id'],[]).append(dict(literal_primary_record=p['literal_primary_record'],evidence_reference=p['evidence_reference'],source_url=p['source_url']))
    plan=m.load(i.prior.PLAN)
    for p in plan['records']:contexts.setdefault(p['artwork_id'],[]).append(dict(literal_primary_record=p['facts']['source_fields'],evidence_reference=p['decision']['source_reference'],source_url=p['facts']['source_url']))
    result=[];existing={};rules=collections.Counter()
    for row,cmp in zip(rows,ix['comparisons']):
        assert row['source_id']==cmp['source_id'];leads={};kinds={}
        for key in KEYS:
            for art in cmp[key]:leads[art['id']]=art;kinds.setdefault(art['id'],[]).append(key)
        entries=[]
        for aid,art in sorted(leads.items()):
            existing.setdefault(aid,dict(artwork=art,primary_contexts=contexts.get(aid,[])))
            signal=bool(set(kinds[aid])&{'inventory_hits','object_alias_hits','related_inventory_hits','untitled_creator_hits'})
            decisions=[reason(row['facts']['source_fields'],p['literal_primary_record'],signal) for p in contexts.get(aid,[])]
            decision=decisions if decisions and all(decisions) else None
            if decision:
                for item in decision:rules[item['rule']]+=1
            entries.append(dict(existing_artwork_id=aid,comparison_kinds=kinds[aid],physical_exclusion_proposal=decision,needs_individual_review=decision is None))
        result.append(dict(number=row['number'],source_id=row['source_id'],candidate_family=family(row['facts']['source_fields']),entries=entries))
    m.save(dest,dict(at=m.now(),rows=result,existing_contexts=existing,identity_reference=ref(RUN/'native-identity-001.json.gz'),candidate_reference=ref(RUN/'remaining-candidates-001.json.gz'),primary_context_reference=ref(i.OLD/'physical-comparison-context-002.json.gz'),delivered_plan_reference=ref(i.prior.PLAN),classifier_reference=ref(Path(__file__).resolve()),database_writes=0,policy='Comparison triage only, not an artwork approval. Each proposed exclusion preserves explicit source fields and reason. No exclusion without primary metadata; conflicting/mixed material families and inventory/related-object signals require individual review. Source chronology is not repaired or broadened. Unresolved pairs remain visible.'))
    print(json.dumps(dict(candidates=len(result),unique_comparators=len(existing),pair_proposals=sum(not e['needs_individual_review'] for r in result for e in r['entries']),individual_pairs=sum(e['needs_individual_review'] for r in result for e in r['entries']),rules=rules)),flush=True)
    print(json.dumps([{ 'number':r['number'],'all':len(r['entries']),'remaining':sum(e['needs_individual_review'] for e in r['entries'])} for r in result if r['entries']]),flush=True)
if __name__=='__main__':main()
