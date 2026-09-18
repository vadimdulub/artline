#!/usr/bin/env python3
"""Apply reviewed, source-named closed-life country matches in bounded rounds.

Country evidence is an explicit biographical cultural affiliation. Full name,
closed dates and the original museum creator citation establish identity.
Conflicting/global authority owners are held for separate duplicate research.
"""
import argparse,collections,importlib.util,json,re
from pathlib import Path

s=importlib.util.spec_from_file_location('g',Path(__file__).with_name('review-overnight-country-gaps.py'));g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
m=g.m;CORE=m.m.core;RUN=g.RUN/'closed-identity-research';SOURCE='overnight-closed-identity-countries-20260913'

def primary_proof(a,citations):
    years=rf"{a['birth_year']}\s*[–—-]\s*{a['death_year']}"
    good=[]
    for c in citations:
        if c['field_name'] not in ('museum_creator_record','round2_creator_authority'):continue
        if not c['source_url'] or not re.search(r'source biography:\s*'+years,c['evidence_note'] or ''):continue
        good.append(c)
    return good

def plan(n):
    folder=RUN/f'round-{n:02d}';dest=folder/'country-plan.json'
    if dest.exists():return
    research=json.loads((folder/'research.json').read_text());proposals=research['country_proposals']
    targets={};holds=[];entries=[];grouped=collections.Counter(p['candidate']['qid'] for p in proposals)
    for target in ('local','production'):
        with m.m.r.base.connect(target=='production') as db,db.transaction():
            db.execute('SET TRANSACTION READ ONLY');db.execute("SET LOCAL statement_timeout='120s'")
            rows=g.c.selected(db,[{'artist':{'slug':p['artist']['slug']}} for p in proposals]) if proposals else {}
            qids=[p['candidate']['qid'] for p in proposals]
            owners=db.execute("SELECT e.external_id,a.slug,a.status FROM external_identifiers e JOIN artists a ON a.id=e.entity_id WHERE e.entity_type='artist' AND e.scheme='wikidata' AND e.external_id=ANY(%s)",(qids,)).fetchall()
            citations=db.execute("SELECT c.entity_id::text,c.field_name,c.source_record_id,c.source_url,c.evidence_note,c.retrieved_at::text,s.slug source_slug FROM citations c JOIN sources s ON s.id=c.source_id WHERE c.entity_type='artist' AND c.entity_id=ANY(%s::uuid[]) AND c.field_name IN ('museum_creator_record','round2_creator_authority') ORDER BY c.entity_id,c.field_name,c.source_url",([a['row']['id'] for a in rows.values()],)).fetchall()
            countries={r['code'] for r in db.execute('SELECT code FROM countries')}
        targets[target]=dict(rows=rows,owners={o['external_id']:o for o in owners},citations=citations,countries=sorted(countries))
    for p in proposals:
        slug=p['artist']['slug'];qid=p['candidate']['qid'];reasons=[];proofs={}
        if grouped[qid]>1:reasons.append('multiple_local_candidates_for_one_wikidata_person')
        # Textual and structured source dates must not silently contradict.
        desc_years={int(y) for y in re.findall(r'(?<!\d)(?:1[0-9]{3}|20[0-9]{2})(?!\d)',p['candidate']['description'])}
        if desc_years-set([p['artist']['birth_year'],p['artist']['death_year']]):reasons.append('source_description_lifespan_conflict')
        if re.search(r'\b(?:circa|ca\.|c\.)\s*\d',p['candidate']['description']):reasons.append('source_description_uncertain_lifespan')
        intro=p['wikipedia_evidence']['intro']
        identity_prefix=re.split(r'\b(?:was|is)\s+(?:a|an)\b',intro,maxsplit=1)[0]
        biography_years={int(y) for y in re.findall(r'(?<!\d)(?:1[0-9]{3}|20[0-9]{2})(?!\d)',identity_prefix)}
        if biography_years-set([p['artist']['birth_year'],p['artist']['death_year']]):reasons.append('wikipedia_introductory_lifespan_conflict')
        for target,t in targets.items():
            row=t['rows'][slug];a=row['row'];owner=t['owners'].get(qid)
            if a['status']!='review' or a['entity_type']!='person' or a['published_at'] is not None:reasons.append('record_not_unpublished_review_person')
            if row['countries']:reasons.append('country_already_present_requires_context')
            if any(a[k]!=p['artist'][k] for k in ('display_name','birth_year','death_year')):reasons.append('museum_identity_changed')
            if owner and owner['slug']!=slug:reasons.append('wikidata_identity_owned_by_'+owner['slug'])
            if any(x['scheme']=='wikidata' and x['id']!=qid for x in row['authorities']):reasons.append('existing_wikidata_identity_conflict')
            if set(p['country_codes'])-set(t['countries']):reasons.append('country_not_configured')
            proofs[target]=primary_proof(a,[c for c in t['citations'] if c['entity_id']==a['id']])
            if not proofs[target]:reasons.append('exact_closed_museum_creator_citation_missing')
        if g.signature(targets['local']['rows'][slug])!=g.signature(targets['production']['rows'][slug]):reasons.append('cross_database_identity_or_country_disagreement')
        if reasons:holds.append(dict(slug=slug,qid=qid,reasons=sorted(set(reasons))));continue
        entries.append(dict(slug=slug,qid=qid,codes=p['country_codes'],research=p,primary_identity_evidence=proofs))
    selected={t:{e['slug']:data['rows'][e['slug']] for e in entries} for t,data in targets.items()}
    for t,rows in selected.items():CORE.save_new(m.BACKUPS/f'closed-country-round-{n:02d}-{t}-preimages.json',rows)
    data=dict(at=CORE.now(),round=n,research_sha256=CORE.sha((folder/'research.json').read_bytes()),entries=entries,holds=holds,targets=selected)
    CORE.save_new(dest,data);manifest=dict(at=CORE.now(),round=n,plan_sha256=CORE.sha(dest.read_bytes()),painters=len(entries),affiliations=sum(len(e['codes']) for e in entries),countries=dict(collections.Counter(c for e in entries for c in e['codes'])),holds=len(holds))
    CORE.save_new(folder/'country-manifest.json',manifest);print(json.dumps(manifest),flush=True)

def apply(n):
    folder=RUN/f'round-{n:02d}';raw=(folder/'country-plan.json').read_bytes();data=json.loads(raw);pin=CORE.sha(raw)
    assert json.loads((folder/'country-manifest.json').read_text())['plan_sha256']==pin
    qa=json.loads((folder/'country-quality-review.json').read_text());assert qa['approved'] and qa['plan_sha256']==pin
    held=qa.get('held_painters',{})
    assert set(held)<=set(e['slug'] for e in data['entries'])
    entries=[e for e in data['entries'] if e['slug'] not in held]
    for target in ('local','production'):
        dest=folder/f'country-{target}-verified.json'
        if dest.exists():continue
        with m.m.r.base.connect(target=='production') as db:
            with db.transaction():
                db.execute("SET LOCAL statement_timeout='120s'");db.execute('SELECT pg_advisory_xact_lock(559220260914)')
                sid=m.m.source(db,SOURCE,'Closed museum creator identity and documented cultural affiliation','authority_data','https://www.wikidata.org/')
                for e in entries:
                    old=data['targets'][target][e['slug']];a=old['row']
                    db.execute('SELECT id FROM artists WHERE id=%s FOR UPDATE',(a['id'],))
                    done=db.execute("SELECT 1 FROM citations WHERE entity_type='artist' AND entity_id=%s AND source_id=%s AND field_name='geography' AND evidence_note LIKE %s",(a['id'],sid,'%'+pin+'%')).fetchone()
                    if done:continue
                    now=g.c.selected(db,[{'artist':{'slug':e['slug']}}])[e['slug']];assert now==old,e['slug']
                    owner=db.execute("SELECT entity_type,entity_id::text FROM external_identifiers WHERE scheme='wikidata' AND external_id=%s",(e['qid'],)).fetchone()
                    assert not owner or owner==dict(entity_type='artist',entity_id=a['id'])
                    for code in e['codes']:
                        db.execute("INSERT INTO artist_countries(artist_id,country_code,relationship_type,is_primary,note) VALUES(%s,%s,'cultural_affiliation',false,%s)",(a['id'],code,'Museum-named creator identity corroborated by exact full-name/alias and closed lifespan; explicit cultural affiliation in Wikidata description and Wikipedia biography. Nonexclusive; not birthplace, museum location or imperial citizenship.'))
                    ev=e['research'];receipt=ev['candidate']['entity_receipt']
                    if not owner:m.m.r.base.insert(db,'external_identifiers',dict(entity_type='artist',entity_id=a['id'],scheme='wikidata',external_id=e['qid'],canonical_url='https://www.wikidata.org/wiki/'+e['qid'],source_id=sid,retrieved_at=receipt['retrieved_at']))
                    m.m.r.base.insert(db,'citations',dict(entity_type='artist',entity_id=a['id'],source_id=sid,field_name='geography',source_record_id=e['qid'],source_url=ev['wikipedia_evidence']['url'],retrieved_at=ev['wikipedia_evidence']['receipt']['retrieved_at'],created_by=m.m.ACTOR,evidence_note=json.dumps(dict(plan_sha256=pin,country_codes=e['codes'],identity=e['primary_identity_evidence'][target],entity_receipt=receipt,source_description=ev['candidate']['description'],biography_receipt=ev['wikipedia_evidence']['receipt'],description_affiliations=ev['description_affiliations'],biography_affiliations=ev['biography_affiliations'],publication_status='review'),ensure_ascii=False)))
                    db.execute("UPDATE artists SET geography_review_state=CASE WHEN geography_review_state='not_reviewed' THEN 'classified' ELSE geography_review_state END,revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s",(m.m.ACTOR,a['id']))
            with db.transaction():
                db.execute('SET TRANSACTION READ ONLY');rows=g.c.selected(db,[{'artist':{'slug':e['slug']}} for e in entries]) if entries else {}
                for e in entries:
                    now=rows[e['slug']];old=data['targets'][target][e['slug']];ignore={'geography_review_state','revision','updated_at','updated_by'}
                    assert {k:v for k,v in now['row'].items() if k not in ignore}=={k:v for k,v in old['row'].items() if k not in ignore}
                    assert {c['country_code'] for c in now['countries']}==set(e['codes'])
                    assert {(x['scheme'],x['id']) for x in now['authorities']}=={(x['scheme'],x['id']) for x in old['authorities']+[dict(scheme='wikidata',id=e['qid'])]}
                    assert now['row']['status']=='review' and now['row']['published_at'] is None
        CORE.save_new(dest,dict(at=CORE.now(),plan_sha256=pin,painters_verified=len(entries),affiliations=sum(len(e['codes']) for e in entries),review_preserved=True));print(target,'closed identity country round',n,'verified',len(entries),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['plan','apply']);p.add_argument('--round',required=True,type=int);a=p.parse_args();assert 1<=a.round<=20;globals()[a.command](a.round)
