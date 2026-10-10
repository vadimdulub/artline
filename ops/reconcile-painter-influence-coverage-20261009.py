#!/usr/bin/env python3
"""Read-only discovery for painter profiles added while round four was running.

Keeps the committed production plan and every pinned input unchanged.
"""
import importlib.util
from pathlib import Path
import json
from collections import Counter,defaultdict
s=importlib.util.spec_from_file_location('m',Path(__file__).with_name('apply-painter-influences-round4-20261009.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
r=m.r; P=m.RUN; LATE=P/'catalogue-catchup'; CACHE=Path.home()/'Library/Application Support/Artline/research/painter-influences-round4-20261009/catalogue-catchup'


def discover():
    assert not (LATE/'production-snapshot.json').exists(), 'Preserve completed snapshot'
    known={v['id'] for v in r.load(P/'production-artists.json.gz')}
    with m.d.connections.connect('production',readonly=True) as db:
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        current=db.execute("SELECT id::text,slug,display_name,entity_type,birth_year,death_year,active_start_year,active_end_year,status,influence_review_state,biography_md FROM artists WHERE status<>'archived' ORDER BY id").fetchall()
        new=[v for v in current if v['id'] not in known];ids=[v['id'] for v in new];byid={v['id']:v for v in new}
        for a in new:a.update(identifiers=[],citations=[],aliases=[],countries=[],popular=False)
        for e in db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artist' AND entity_id=ANY(%s::uuid[])",(ids,)):
            byid[e.pop('entity_id')]['identifiers'].append(e)
        for e in db.execute("SELECT artist_id::text,alias FROM artist_aliases WHERE artist_id=ANY(%s::uuid[])",(ids,)):byid[e['artist_id']]['aliases'].append(e['alias'])
        for e in db.execute("SELECT entity_id::text,field_name,source_url,source_record_id,evidence_note FROM citations WHERE entity_type='artist' AND entity_id=ANY(%s::uuid[])",(ids,)):byid[e.pop('entity_id')]['citations'].append(e)
    r.save(LATE/'production-artists.json.gz',new)
    r.save(LATE/'production-snapshot.json',dict(at=r.now(),read_only=True,active_profiles=len(current),new_profiles=len(new),active_artist_ids=[v['id'] for v in current]))
    print('New profiles since pinned import snapshot',len(new),flush=True)


def fetch():
    fresh=r.load(LATE/'production-artists.json.gz'); prior=m.authority_index(); reader=r.authority_index
    r.RUN=LATE;r.CACHE=CACHE;r._bindings=None;r.roster=lambda:fresh;r.authority_index=lambda:{**prior,**reader()}
    r.identity_search();r.wikidata();r.authorities();r.resolve_names();r._bindings=None;r.wikidata();r.authorities()
    r.wikipedia();r.native_articles();r.wikipedia_native();r.biography_leads()


def reconcile():
    register=r.load(P/'painter-research-register.json.gz');snap=r.load(LATE/'production-snapshot.json');active=set(snap['active_artist_ids'])
    assert {v['artist_id'] for v in register}<=active, 'Unexpected archived profiles; review before reconciling'
    baseline=r.load(P/'coverage-summary.json');r.save(LATE/'pre-catchup-coverage-summary.json',baseline)
    bindings={v['artist_id']:v['qid'] for v in r.load(LATE/'research-identity-bindings.json') if v['decision']=='supported_research_identity'}
    newleads=r.load(LATE/'biography-leads.json.gz');byq=defaultdict(set)
    for v in newleads:byq[v['subject_qid']].add(v['id'])
    reviewed={v['lead_id'] for v in r.load(m.r.RUN/'reviewed-biography-decisions.json')}
    for directory in m.PREVIOUS+[P]:
        queue=r.load(directory/'candidate-passages.json.gz');reviewed.update(queue[json.loads(line)['i']]['id'] for line in (directory/'reviews.jsonl').read_text().splitlines())
    checked_qids={q for v in r.load(LATE/'wikidata-statement-coverage.json')['results'] if v['ok'] for q in v['qids']}
    for a in r.load(LATE/'production-artists.json.gz'):
        qs={v['external_id'] for v in a['identifiers'] if v['scheme']=='wikidata'}
        if a['id'] in bindings:qs.add(bindings[a['id']])
        search=r.load(LATE/'identity-search'/(a['id']+'.json'));assert 'error' not in search
        pending=sorted({lead for q in qs for lead in byq[q]}-reviewed)
        status='biography_passages_require_review' if pending else 'identity_unresolved_after_lookup' if len(qs)!=1 else 'further_source_research_needed'
        register.append(dict(artist_id=a['id'],name=a['display_name'],slug=a['slug'],entity_type=a['entity_type'],historical_status=a['status'],wikidata_ids=sorted(qs),research_attempted=True,previous_register_artist_id=None,previous_research_status=None,newcomer_search=dict(at=search['at'],url=search.get('url'),status='candidates_found' if search.get('data',{}).get('search') else 'no_candidate_found'),fresh_wikidata_statement_check=bool(qs & checked_qids),relationship_counts={},reviewed_biography_passages=len({lead for q in qs for lead in byq[q]} & reviewed),pending_biography_passages=len(pending),pending_lead_ids=pending,research_status=status,coverage_catchup=True,limitation='Lookup coverage is not historical completeness. Newly discovered passages remain unreviewed and are not production relationship claims.'))
    assert len(register)==len({v['artist_id'] for v in register})==snap['active_profiles']
    allleads={v['id']:v for v in r.load(m.r.RUN/'biography-leads.json.gz')+r.load(P/'biography-leads.json.gz')+newleads}
    reviewed={v['lead_id'] for v in r.load(m.r.RUN/'reviewed-biography-decisions.json')}
    for directory in m.PREVIOUS+[P]:
        queue=r.load(directory/'candidate-passages.json.gz');reviewed.update(queue[json.loads(line)['i']]['id'] for line in (directory/'reviews.jsonl').read_text().splitlines())
    summary=dict(baseline,at=r.now(),snapshot_at=snap['at'],import_snapshot_at=baseline['snapshot_at'],active_production_profiles=len(register),lookup_attempted_profiles=sum(v['research_attempted'] for v in register),catalogue_catchup_profiles=snap['new_profiles'],catalogue_catchup_discovered_passages=len(newleads),profiles_without_artistic_influence=sum(not v['relationship_counts'].get('influenced',0) for v in register),pending_discovered_passages=len(set(allleads)-reviewed),research_status_counts=dict(Counter(v['research_status'] for v in register)))
    r.save(P/'painter-research-register.json.gz',register);r.save(P/'coverage-summary.json',summary)
    r.save(LATE/'remaining-biography-leads.json.gz',[v for k,v in allleads.items() if k in {x['id'] for x in newleads} and k not in reviewed])
    print(json.dumps(summary,indent=2),flush=True)


if __name__=='__main__':
    import sys
    {'discover':discover,'fetch':fetch,'reconcile':reconcile}[sys.argv[1]]()
