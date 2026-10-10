#!/usr/bin/env python3
"""One review entry per artist, precision-aware artwork triage and scoped evidence."""
import collections,copy,csv,importlib.util,json,re
from pathlib import Path
s=importlib.util.spec_from_file_location('plan',Path(__file__).with_name('lifetimes-plan-20261010.py'));p=importlib.util.module_from_spec(s);s.loader.exec_module(p)
r=p.r;RUN=r.RUN
ACTION_FLAGS={'entirely_before_recorded_birth','entirely_after_recorded_death','creation_before_age_five','creation_range_equals_artist_life'}
IDENTITY_HOLDS={
 '3733a94c-b872-45d6-a48f-0c548f530545':'Pietro Giacomo Palmieri: existing life 1737–1804 versus assigned authority 1925–1964; authority identity conflict, not evidence to rewrite lifespan.',
 '341d00c4-2b03-4d60-b8d1-3cb6b484c7de':'Carl Albert Walters: existing life 1883–1955 versus authority birth 1944; identity conflict requires native source reconciliation.',
 'd8ead673-082d-49d5-8e79-260628ddd2bb':'Hans Collaert the Elder: existing dates differ by a generation from assigned authority; investigate Elder/Younger identity.',
 'f1177096-beb1-4c4f-9c99-a8c3ebcc56d9':'Julia Rogers: NGA literal birth 1962 conflicts with linked NGA prints c.1935–1943. Proposed birth addition held.',
}
def refined_flags(w,ar):
    flags=r.artwork_flags(w,ar)
    if not flags:return flags
    if any(x in flags for x in ACTION_FLAGS):
        if w['date_precision'] in ['circa','circa_range','before','after','uncertain']:flags.append('qualified_artwork_date_requires_review')
        if ('entirely_before_recorded_birth' in flags or 'creation_before_age_five' in flags) and ar['birth_precision'] not in [None,'exact']:flags.append('qualified_birth_boundary_requires_review')
        if 'entirely_after_recorded_death' in flags and ar['death_precision'] not in [None,'exact']:flags.append('qualified_death_boundary_requires_review')
    return sorted(set(flags))
def disposition(flags):
    if 'creation_date_unassessable' in flags:return 'creation_date_unknown'
    if 'creator_life_unassessable' in flags:return 'life_dates_unknown'
    if 'nonperson_use_activity_not_lifespan' in flags:return 'collective_or_workshop_not_individual_life'
    if 'qualified_attribution_preserve_distinction' in flags:return 'qualified_creator_requires_object_review'
    if 'posthumous_physical_production_possible' in flags:return 'possible_posthumous_edition_or_cast_verify_object'
    if any(x.startswith('qualified_') for x in flags):return 'uncertain_boundary_verify_source'
    if 'creation_range_equals_artist_life' in flags:return 'possible_inherited_lifespan_verify_object'
    if any(x in ACTION_FLAGS for x in flags):return 'chronology_conflict_requires_object_source_review'
    return 'broad_interval_overlaps_life'
def csv_write(path,rows,columns):
    assert not path.exists(),'Do not overwrite pinned review output'
    with path.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=columns);writer.writeheader()
        for row in rows:writer.writerow({k:json.dumps(row[k],ensure_ascii=False) if isinstance(row.get(k),(list,dict)) else row.get(k) for k in columns})
def report():
    fresh=r.load(RUN/'fresh-date-index.json.gz');cached=r.load(RUN/'cached-authority-index.json.gz');bindings=r.load(RUN/'research-identity-bindings.json.gz');primary=r.load(RUN/'primary-artist-comparison.json.gz');plan=r.load(RUN/'complete-execution-plan.json.gz');changes={x['artist_id']:x for x in plan['rows']}
    source=copy.deepcopy(cached)
    for q,data in fresh.items():
        source[q]={field:sorted({c['value'] for c in data['claims'].values() if c['property']==prop and c['rank']!='DeprecatedRank' and c['value'] and c['precision'] is not None and c['precision']>=9}) for field,prop in [('birth','P569'),('death','P570')]}
    summaries={}
    for target in ['production','local']:
        snapshot=r.load(RUN/(target+'-snapshot.json.gz'));artists={x['record']['id']:copy.deepcopy(x) for x in snapshot['artists']};allworks=collections.defaultdict(list);flagged=[];per=collections.defaultdict(collections.Counter);register=[]
        for aid,a in artists.items():
            if target=='production' and aid in changes:a['record'].update(changes[aid]['updates'])
        active_links=[w for w in snapshot['artwork_links'] if w['status']!='archived' and artists[w['artist_id']]['record']['status']!='archived']
        for w in active_links:
            a=artists[w['artist_id']]['record'];allworks[a['id']].append(w);flags=refined_flags(w,a)
            if flags:flagged.append(dict(**w,artist_name=a['display_name'],birth_year=a['birth_year'],death_year=a['death_year'],birth_precision=a['birth_precision'],death_precision=a['death_precision'],flags=flags,disposition=disposition(flags)));per[a['id']].update(flags)
        for aid,a in artists.items():
            ar=a['record'];qs=r.effective_qids(a,bindings);av=copy.deepcopy(a)
            for q in set(qs)-set(r.qids(a)):av['identifiers'].append(dict(scheme='wikidata',external_id=q))
            flags=r.artist_flags(av,source) if ar['status']!='archived' else ['archived_excluded'];coverage=[]
            for q in qs:
                coverage.append(dict(qid=q,state='fresh_statement_capture' if q in fresh else ('retained_authority_capture' if q in cached else 'no_date_capture'),claim_precision=collections.Counter(str(c['precision']) for c in fresh.get(q,{}).get('claims',{}).values()),qualified_claims=sum(bool(c['qualifiers']) for c in fresh.get(q,{}).get('claims',{}).values())))
                if ar['status']!='archived':
                    for c in fresh.get(q,{}).get('claims',{}).values():
                        if c['rank']=='DeprecatedRank' or c['property'] not in ['P569','P570']:continue
                        field='birth' if c['property']=='P569' else 'death';stored=ar[field+'_year'];qualifiers={x[0].rsplit('/',1)[-1] for x in c['qualifiers']}
                        if stored is not None and (c['precision'] is not None and c['precision']<9 or (r.year(c['value'])==stored and qualifiers&{'P1480','P1319','P1326'})) and ar[field+'_precision'] in [None,'exact']:flags.append('authority_'+field+'_precision_requires_review')
                        if stored is not None and r.year(c['value'])==stored and 'P31' in qualifiers:flags.append('authority_'+field+'_event_qualification_requires_review')
            native=primary['coverage'].get(aid,[])
            if aid in IDENTITY_HOLDS:flags.append('authority_or_native_identity_conflict')
            flags=sorted(set(flags))
            register.append(dict(artist_id=aid,name=ar['display_name'],slug=ar['slug'],status=ar['status'],entity_type=ar['entity_type'],birth_year=ar['birth_year'],birth_precision=ar['birth_precision'],death_year=ar['death_year'],death_precision=ar['death_precision'],timeline_start_year=ar['timeline_start_year'],timeline_end_year=ar['timeline_end_year'],timeline_display=ar['timeline_display'],timeline_basis=ar['timeline_basis'],artist_flags=flags,artwork_count=len(allworks[aid]),artwork_flags=dict(per[aid]),authority_coverage=coverage,primary_provider_ids=[{'provider':x['provider'],'id':x['native_id'],'literal':x['literal']} for x in native],correction_applied=target=='production' and aid in changes,identity_hold=IDENTITY_HOLDS.get(aid),review_limit='Automated complete-catalogue audit with source comparisons and selected primary corrections; unflagged records are not individually historically validated.'))
        active=[x for x in register if x['status']!='archived'];summary=dict(target=target,total_artists=len(register),active_artists=len(active),archived_excluded=len(register)-len(active),active_artwork_artist_links=len(active_links),distinct_active_artworks=len({w['id'] for w in active_links}),artists_with_fresh_authority=sum(any(c['state']=='fresh_statement_capture' for c in x['authority_coverage']) for x in active),artists_with_retained_authority=sum(any(c['state']=='retained_authority_capture' for c in x['authority_coverage']) for x in active),artists_with_exact_native_primary_comparison=sum(bool(x['primary_provider_ids']) for x in active),artists_without_date_authority_comparison=sum(not x['primary_provider_ids'] and not any(c['state']!='no_date_capture' for c in x['authority_coverage']) for x in active),artist_flags=dict(collections.Counter(f for x in active for f in x['artist_flags'])),artwork_flags=dict(collections.Counter(f for w in flagged for f in w['flags'])),artwork_dispositions=dict(collections.Counter(w['disposition'] for w in flagged)),actionable_artwork_links=sum(bool(ACTION_FLAGS&set(w['flags'])) for w in flagged),applied_artists=sum(x['correction_applied'] for x in active))
        r.save(RUN/(target+'-completed-review.json.gz'),dict(at=r.now(),artists=register,artwork_flags=flagged));r.save(RUN/(target+'-completed-summary.json'),summary);summaries[target]=summary
        csv_write(RUN/(target+'-completed-artist-review.csv'),register,['artist_id','name','slug','status','entity_type','birth_year','birth_precision','death_year','death_precision','timeline_start_year','timeline_end_year','timeline_display','timeline_basis','artist_flags','artwork_count','artwork_flags','authority_coverage','primary_provider_ids','correction_applied','identity_hold'])
        actionable=[w for w in flagged if ACTION_FLAGS&set(w['flags'])]
        csv_write(RUN/(target+'-completed-artwork-chronology.csv'),actionable,['id','slug','title','artist_id','artist_name','birth_year','birth_precision','death_year','death_precision','creation_year_start','creation_year_end','date_precision','date_display','work_type','attribution_role','attribution_note','flags','disposition'])
    print(json.dumps(summaries,indent=2),flush=True)
def object_evidence():
    review=r.load(RUN/'production-final-review.json.gz');works=[w for w in review['artwork_flags'] if ACTION_FLAGS&set(w['flags'])];ids=sorted({w['id'] for w in works});result={i:dict(citations=[],identifiers=[]) for i in ids}
    with r.m.connect() as db:
        for batch in r.chunks(ids,250):
            for x in db.execute("SELECT entity_id::text,to_jsonb(c) v FROM citations c WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id",(batch,)):result[x['entity_id']]['citations'].append(x['v'])
            for x in db.execute("SELECT entity_id::text,to_jsonb(e) v FROM external_identifiers e WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id",(batch,)):result[x['entity_id']]['identifiers'].append(x['v'])
    r.save(RUN/'flagged-object-source-evidence.json.gz',dict(at=r.now(),read_only=True,scoped_object_ids=ids,objects=result));print('Scoped object evidence',len(ids),'citations',sum(len(x['citations']) for x in result.values()),flush=True)
if __name__=='__main__':
    import sys
    globals()[sys.argv[1]]()
