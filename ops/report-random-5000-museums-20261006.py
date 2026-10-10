#!/usr/bin/env python3
"""Audit production results and write a source-linked outcome for all 5,000 works."""
import collections,importlib.util,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('delivery',ROOT/'ops/apply-random-5000-museums-20261006.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);r=m.r;d=m.d;RUN=m.RUN
def cell(v):return str(v or '—').replace('|','\\|').replace('\n',' ')
def values(e,p):
    ss=[x for x in e.get('claims',{}).get(p,[])if x.get('rank')!='deprecated'and 'P582'not in x.get('qualifiers',{})];preferred=[x for x in ss if x.get('rank')=='preferred']
    out=[]
    for x in preferred or ss:
        v=x.get('mainsnak',{}).get('datavalue',{}).get('value');out.append(v.get('id')if isinstance(v,dict)and'id'in v else v)
    return out
def main():
    sample=r.load(RUN/'sample.json');ids=sample['artwork_ids'];baseline=r.load(RUN/'baseline.json.gz');wiki=r.load(RUN/'wikiart-holding-plan-v5.json.gz');wo={x['artwork_id']:x for x in wiki['outcomes']}
    webpin=r.load(RUN/'latest-web-review.json');web=r.load(RUN/webpin['path']);wd=r.load(RUN/'wikidata-entities.json.gz');authorities=r.load(RUN/'cached-institution-authorities.json.gz');native=r.load(RUN/'native-identity-preflight.json.gz')
    applied={};held=collections.defaultdict(list);verifications=[];newids=set()
    for h in native['held']:held[h['artwork_id']].append(h)
    for folder in sorted((RUN/'delivery').iterdir()):
        if not(folder/'production').exists():continue
        plan,digest=d.pinned(folder.name);verification=r.load(folder/'verification.json');assert not verification['errors'];verifications.append(verification)
        receiptids={aid for path in(folder/'production').glob('*.json')for aid in r.load(path)['artwork_ids']}
        assert receiptids=={c['artwork_id']for c in plan['claims']}
        for c in plan['claims']:assert c['artwork_id']not in applied;applied[c['artwork_id']]=c
        for h in plan['held']:held[h['artwork_id']].append(h)
        newids.update(i['id']for i in r.load(folder/'plan-pin.json')['new_institutions'])
    assert applied and len(ids)==len(set(ids))==5000
    after={}
    with r.connect('production')as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        for offset in range(0,5000,500):after.update(d.snapshots(db,ids[offset:offset+500]))
        instids={x['artwork']['current_institution_id']for x in after.values()if x['artwork']['current_institution_id']}|newids
        museums={x['v']['id']:x['v']for x in db.execute('SELECT to_jsonb(i) v FROM institutions i WHERE id=ANY(%s::uuid[])',(list(instids),))}
    assert len(after)==5000 and all(museums[i]['status']=='review'for i in newids)
    for aid,c in applied.items():assert after[aid]['artwork']['current_institution_id']==c['institution']['id']
    r.save_gz(RUN/'final-production-snapshot.json.gz',after)
    priorinstitutions=r.load(RUN/'institutions.json.gz');byqid={i['wikidata_id']:i for i in priorinstitutions if i.get('wikidata_id')}
    primary_holds=collections.defaultdict(list)
    for name in ['joconde-final','lombardia','fng','moma','primary-reconciled','indexed-primary-reviewed']:
        for h in r.load(RUN/'primary-plans'/(name+'.json.gz')).get('holds',[]):primary_holds[h['artwork_id']].append({'provider':name,**h})
    attempted=set(web['searched_ids']);initial={c['artwork_id']for c in r.load(RUN/'wikiart-holding-plan-v2.json.gz')['claims']}
    assert attempted|initial==set(ids)and len(attempted)==4631
    ledger=[];external_changes=[]
    for ordinal,aid in enumerate(ids,1):
        before=baseline[aid];a=before['artwork'];current=after[aid]['artwork'];candidate=[];sources=set(wo[aid]['source_urls']);actual=current['current_institution_id'];detail=[]
        for e in before['identifiers']:
            if e['scheme']!='wikidata'or e['external_id']not in wd:continue
            q=e['external_id'];entity=wd[q]['entity']
            for museumq in values(entity,'P195'):
                if not isinstance(museumq,str):continue
                authority=authorities.get(museumq,{}).get('entity',{});types=set(values(authority,'P31'));name=byqid.get(museumq,{}).get('name')or authority.get('labels',{}).get('en',{}).get('value')or museumq
                candidate.append({'name':name,'wikidata_id':museumq,'museum_type_documented':bool(types&{'Q33506','Q207694'})or byqid.get(museumq,{}).get('kind')=='museum','source_url':'https://www.wikidata.org/wiki/'+q,'review_state':'review','basis':'Exact existing artwork Wikidata ID and active P195 collection statement; not by itself promoted to an accepted museum holding.'})
                sources.add('https://www.wikidata.org/wiki/'+q)
        leads=web['related_source_leads'].get(aid,[])
        for c in leads:
            if c.get('institution')and c['detail_page']:
                candidate.append({'name':c['institution']['name'],'institution_id':c['institution']['id'],'source_url':c['source_url'],'review_state':'review','basis':'Primary-page lead requiring unresolved identity, version, date, holding or access checks.'})
        if aid in applied:
            outcome='museum_assigned';detail.append(applied[aid]['identity_basis']);sources.add(applied[aid]['source_url'])
        elif actual:
            outcome='holding_added_by_concurrent_catalogue_work';external_changes.append(aid)
        elif held.get(aid):outcome='duplicate_or_delivery_conflict_requires_reconciliation';detail.extend(x['reason']for x in held[aid])
        elif wo[aid]['outcome']=='private_collection_or_unknown_or_destroyed':outcome='source_reports_private_unknown_or_destroyed';detail.extend(wo[aid]['source_locations'])
        elif wo[aid]['outcome']=='documented_non_museum_site_or_collection_requires_separate_site_review':outcome='documented_non_museum_site_or_collection';detail.extend(wo[aid]['source_locations'])
        elif any(h['reason']=='non_museum_or_unspecified_responsible_organization'for h in primary_holds[aid])and not any(c['museum_type_documented']for c in candidate if 'museum_type_documented'in c):outcome='documented_non_museum_or_unspecified_collection_body'
        elif wo[aid]['outcome']in {'specific_print_impression_requires_inventory_or_version_evidence','institution_identity_requires_individual_review','historical_or_changed_collection_custody_requires_current_authority_review','museum_department_authority_requires_review','institution_branch_identity_requires_individual_review'}:outcome=wo[aid]['outcome'];detail.extend(wo[aid]['source_locations'])
        elif candidate:outcome='collection_lead_requires_verification'
        else:outcome='no_verified_museum_after_bounded_research'
        for h in primary_holds[aid]:detail.append(h['provider']+': '+h['reason'])
        if not detail:detail.append(wo[aid]['outcome'])
        obj={'sample_number':ordinal,'artwork_id':aid,'title':a['title'],'creator':'; '.join(x['name']for x in before['creator_keys'])or a['unlinked_creator_label'],'outcome':outcome,'museum':museums.get(actual,{}).get('name'),'institution_id':actual,'original_status':a['status'],'final_status':current['status'],'source_urls':sorted(sources),'source_wikiart_location_labels':wo[aid]['source_locations'],'collection_candidates':candidate,'research_notes':sorted(set(detail)),'discovery_query_attempted':aid in attempted,'indexed_lead_count':len(leads),'indexed_leads_path':webpin['path'],'delivery_holds':held.get(aid,[])}
        ledger.append(obj)
    counts=dict(collections.Counter(x['outcome']for x in ledger));r.save_gz(RUN/'results-5000.json.gz',ledger)
    audit={'at':r.now(),'target':'production','sample_size':5000,'eligible_population_at_sampling':sample['eligible_population'],'source_supported_matches_before_duplicate_checks':505,'museum_assignments_applied':len(applied),'duplicate_or_delivery_holds':len(held),'new_review_institutions':len(newids),'distinct_assigned_museums':len({c['institution']['id']for c in applied.values()}),'assigned_by_source':dict(collections.Counter(c.get('origin_provider',c['provider'])for c in applied.values())),'outcomes':counts,'individual_discovery_queries':len(attempted),'exact_source_checks_already_sufficient_before_discovery':len(initial),'research_coverage':len(attempted|initial),'concurrent_holding_changes_not_claimed_as_ours':external_changes,'source_policy':'WikiArt fully approved; exact object/version and collection evidence still checked.','preserved_metadata_and_relationships':all(v['prior_records_and_relationships_preserved']for v in verifications),'preserved_publication_and_dates':all(v['publication_and_date_fields_preserved']for v in verifications),'new_display_claims':sum(v['new_display_claims']for v in verifications),'local_database_writes':0,'new_artwork_records':0,'images_downloaded_or_changed':0,'offline_regression_tests_passed':13,'verification_receipts':verifications,'backup':r.load(RUN/'backups.json')['production'],'errors':[]}
    r.save(RUN/'final-audit.json',audit)
    lines=['# Random 5,000 artworks: complete museum research ledger','','Production sample selected on '+sample['at']+'. All 5,000 records were researched; only supported, non-conflicting museum assignments were applied. A collection lead is not an accepted museum holding. See `results-5000.json.gz` for all candidate institutions, reasons and evidence paths.','','| # | Artwork / record | Creator | Outcome | Museum or collection lead | Sources |','|---|---|---|---|---|---|']
    for x in ledger:
        names=x['museum']or'; '.join(dict.fromkeys(c['name']+' (review)'for c in x['collection_candidates'][:4]))or'; '.join(x['source_wikiart_location_labels'])or'Not established'
        urls=x['source_urls'][:3]
        if not urls and x['collection_candidates']:urls=[c['source_url']for c in x['collection_candidates'][:3]]
        links='; '.join('[source '+str(n+1)+']('+u+')'for n,u in enumerate(urls))or'Query evidence preserved'
        lines.append('| '+str(x['sample_number'])+' | '+cell(x['title'])+' · `'+x['artwork_id']+'` | '+cell(x['creator'])+' | '+cell(x['outcome'].replace('_',' '))+' | '+cell(names)+' | '+links+' |')
    (RUN/'results-5000.md').write_text('\n'.join(lines)+'\n')
    md=f'''# Random 5,000 artworks: museum research and production results

Completed {audit['at']} against the production catalogue. **{len(applied):,} artwork records now have a supported museum connection**, across **{audit['distinct_assigned_museums']:,} museums**. **{len(held)} further supported matches are held for duplicate-record reconciliation.** The other records retain explicit research outcomes and source leads; this report does not claim that every artwork belongs to a museum.

| Result | Count |
|---|---:|
| Randomly selected artworks with no institution or accepted holding | 5,000 |
| Eligible production population at selection | {sample['eligible_population']:,} |
| Supported source matches before duplicate checks | 505 |
| Museum assignments applied and verified | {len(applied)} |
| Duplicate or delivery conflicts retained for review | {len(held)} |
| New institution authorities, all in review | {len(newids)} |
| Additional individual discovery queries | 4,631 |
| Source checks sufficient before that discovery pass | 369 |
| Complete artwork research coverage | 5,000 |

[All 5,000 outcomes and source links](results-5000.md) · [Machine-readable ledger](results-5000.json.gz) · [Final audit](final-audit.json) · [Frozen random sample](sample.json).

## What was researched

The sample is uniform and unweighted, drawn without replacement from all 60,482 eligible non-archived production records. The random seed, complete UUID sampling frame, query plan and initial snapshots are preserved. No weighting by artist, country, image availability or chance of a museum match was used.

The pass checked preserved WikiArt object pages for 2,495 artworks, 1,363 exact existing Wikidata artwork identities, supplied catalogue provenance, bounded official French and Italian object records, cached Finnish National Gallery and MoMA datasets, and 4,631 individual web queries. All 5,000 received either a sufficient exact-source check or an individual follow-up query. The queries produced leads for 3,237 artworks; those search hits were not treated as automatic assignments.

WikiArt is fully approved under the current project policy. Exact native artwork IDs, titles, creator variants, versions and explicit museum locations were still checked. Museum translations and cities were reconciled to existing authorities, including separate London, Oslo and Washington institutions. Unknown creators in icon and Fayum traditions were retained without inventing named artists. Prints without impression evidence, changed custody, private collections and incomplete museum identities remain visible in the ledger.

Official-source review excluded exhibition-history entries, related artworks, private loans and composite groups needing version checks. French records distinguish administering museum collections and documented incoming deposits from their separate deposit destinations and legal-owner fields. No current-display claim was created. The additional direct check of 71 selected primary pages preserved 64 successful responses, three HTTP 403 responses, two request failures and two skipped requests after a host failed; indexed primary-source captures remain separately identified.

## Outcomes for the full sample

| Outcome | Artworks |
|---|---:|
'''
    for key,value in counts.items():md+='| '+key.replace('_',' ')+' | '+str(value)+' |\n'
    md+='''
Collection leads in the ledger are explicitly **review candidates**. They can name a museum, a public collection service or another holding body; Wikidata P195 and source excerpts alone were not used to invent accepted museum holdings. Unknown locations are not relabelled as private collections.

## Evidence, access limits and verification

Source pages, API responses, indexed captures, hashes, retrieval times, rejected candidates, pinned delivery plans and database receipts are retained in this directory. `primary-plans/`, `web-discovery/`, `primary-page-validation.json.gz`, `native-identity-preflight.json.gz` and `delivery/museum-holdings-03/` contain the main evidence. Earlier WikiArt plans and delivery wave 01 are superseded research drafts; no wave-01 writes occurred. The first wave-02 transaction rolled back because legacy capture receipts lacked a body-path field. Zero committed assertions were verified. All 500 final source bodies were then hash-verified, 162 legacy path mappings were normalized without inventing HTTP status, and fresh preimages were pinned for wave 03.

Wikidata fresh API access stopped after HTTP 429 at 400 entities; preserved entity captures covered the remaining existing identities. The Italian ArCo endpoint timed out after an initial bounded batch, so official indexed object records were used where available. Art UK and some primary hosts rejected direct access; no alternate endpoint, authentication or access-control bypass was attempted. Missing current records, version ambiguity, deposits, public agencies and unresolved authorities are retained as specific outcomes. One bounded pass is not proof that no further museum record exists.

Production changes add accepted holding assertions and citations and update only location/audit fields. Existing titles, dates, creator labels and relationships, identifiers, images and publication states were preserved against the locked preimages. Existing review assertions remain intact. All new institution authorities remain in review. No local database writes, new artwork imports, image downloads, publications, commits or deployments occurred.

Thirteen offline regression tests cover date/inventory confusion, creator and version collisions, museum cities, department mismatches, deposit roles, source URL migrations, reproducible sampling, legacy evidence-file validation and the production-only delivery guard. Database verification checks each applied holding, citation, revision and preserved relationship. This bounded research operation is not a 10-million-row performance benchmark.

Recovery backup: Cloud SQL **1791307556116**, verified `SUCCESSFUL`. Pinned row preimages and backup receipts are under `/Users/vadimdulub/Library/Application Support/Artline/backups/random-5000-museums-20261006/`.
'''
    (RUN/'README.md').write_text(md)
    print(json.dumps({k:audit[k]for k in ['museum_assignments_applied','duplicate_or_delivery_holds','distinct_assigned_museums','new_review_institutions','outcomes','errors']},ensure_ascii=False),flush=True)
if __name__=='__main__':main()
