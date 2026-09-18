#!/usr/bin/env python3
"""Consolidate individually corroborated painter identities with full recovery.

No title/name-only matching, artwork deletion, asset deletion or publication.
All source/relationship rows move to the canonical painter. The redundant
profile is archived and its old slug resolves to the canonical profile.
Any unique-key overlap requiring editorial merging blocks that pair in planning.
"""
import argparse,collections,importlib.util,json,re
from pathlib import Path
from psycopg import sql

s=importlib.util.spec_from_file_location('m',Path(__file__).with_name('apply-country-round.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
RUN=m.x.BASE/'duplicates'/'painter-consolidation'
SOURCE='overnight-person-identity-review-20260913';ACTOR='local-european-research'
SOURCE_ROOT='https://www.getty.edu/research/tools/vocabularies/ulan/'

def signature(a):return {k:a[k] for k in ('slug','display_name','birth_year','death_year','entity_type','status','published_at','biography_md','portrait_media_id')}

def dependencies(db):
    rows=db.execute("""SELECT conrelid::regclass::text table_name,att.attname column_name
    FROM pg_constraint c JOIN pg_attribute att ON att.attrelid=c.conrelid AND att.attnum=c.conkey[1]
    WHERE c.contype='f' AND c.confrelid='artists'::regclass ORDER BY 1,2""").fetchall()
    return [(r['table_name'],r['column_name']) for r in rows]

def snapshot(db,old,keep,deps):
    pair=[old,keep];data={}
    data['artists']=[r['row'] for r in db.execute('SELECT to_jsonb(a) row FROM artists a WHERE id=ANY(%s::uuid[]) ORDER BY slug',(pair,)).fetchall()]
    for table,column in deps:
        query=sql.SQL('SELECT to_jsonb(t) row FROM {} t WHERE {}=ANY(%s::uuid[])').format(sql.Identifier(table),sql.Identifier(column))
        data[table+':'+column]=[r['row'] for r in db.execute(query,(pair,)).fetchall()]
    for table in ('citations','external_identifiers','slug_redirects'):
        data[table]=[r['row'] for r in db.execute(sql.SQL("SELECT to_jsonb(t) row FROM {} t WHERE entity_type='artist' AND entity_id=ANY(%s::uuid[])").format(sql.Identifier(table)),(pair,)).fetchall()]
    aids={r['artwork_id'] for r in data.get('artwork_artists:artist_id',[])}
    data['linked_artworks']=[r['row'] for r in db.execute('SELECT to_jsonb(a) row FROM artworks a WHERE id=ANY(%s::uuid[]) ORDER BY slug',(list(aids),)).fetchall()] if aids else []
    return data

def overlaps(db,old,keep,deps):
    problems=[]
    for table,column in deps:
        # For each unique index containing the artist FK, compare every other
        # indexed column. NULLS NOT DISTINCT aliases are compared explicitly.
        indexes=db.execute("""SELECT array_agg(a.attname ORDER BY k.ordinality) cols
        FROM pg_index i CROSS JOIN LATERAL unnest(i.indkey) WITH ORDINALITY k(attnum,ordinality)
        JOIN pg_attribute a ON a.attrelid=i.indrelid AND a.attnum=k.attnum
        WHERE i.indrelid=%s::regclass AND i.indisunique GROUP BY i.indexrelid""",(table,)).fetchall()
        for idx in indexes:
            if column not in idx['cols']:continue
            comparisons=[sql.SQL('a.{} IS NOT DISTINCT FROM b.{}').format(sql.Identifier(c),sql.Identifier(c)) for c in idx['cols'] if c!=column]
            predicate=sql.SQL(' AND ').join(comparisons) if comparisons else sql.SQL('true')
            query=sql.SQL('SELECT count(*) n FROM {} a JOIN {} b ON {} WHERE a.{}=%s AND b.{}=%s').format(sql.Identifier(table),sql.Identifier(table),predicate,sql.Identifier(column),sql.Identifier(column))
            if db.execute(query,(old,keep)).fetchone()['n']:problems.append(table+':'+','.join(idx['cols']))
    if db.execute("SELECT 1 FROM external_identifiers a JOIN external_identifiers b ON a.scheme=b.scheme WHERE a.entity_type='artist' AND b.entity_type='artist' AND a.entity_id=%s AND b.entity_id=%s",(old,keep)).fetchone():problems.append('external_identifier_scheme_overlap')
    return problems

def plan():
    path=RUN/'plan.json'
    if path.exists():return
    draft=json.loads((m.x.BASE/'duplicates/artist-primary-identity-review-draft.json').read_text())
    extra={r['qid']:r for r in json.loads((m.x.BASE/'duplicates/museum-person-reviewed-facts.json').read_text())}
    original=json.loads((m.x.BASE/'duplicates/preliminary/local-audit.json').read_text())
    groups={next(e['id'] for a in g['artists'] for e in a['authorities'] if e['scheme']=='wikidata'):g for g in original['leads']['same_artist_name_closed_lifespan']}
    proposals=[];held=[]
    for r in draft:
        q=r['qid'];ev=extra.get(q)
        if not r['primary_lifespan_corroborated'] and not ev:held.append(dict(qid=q,reason='Primary identity/lifespan remains unresolved',review=r));continue
        g=groups[q];keepers=[a for a in g['artists'] if any(e['scheme']=='wikidata' and e['id']==q for e in a['authorities'])]
        assert len(keepers)==1 and len(g['artists'])==2
        keep=keepers[0];old=next(a for a in g['artists'] if a['id']!=keep['id'])
        assert m.f.names.namekey(old['display_name'])==m.f.names.namekey(keep['display_name'])
        if ev:assert [ev['birth'],ev['death']]==r['life']
        getty=None
        if r['primary_lifespan_corroborated']:
            getty=next(json.loads(p.read_text()) for p in (m.x.BASE/'duplicates/getty-captures').glob('*.json') if json.loads(p.read_text())['qid']==q)
        country=None
        if getty:country=next((code for word,code in [('French','FR'),('Spanish','ES'),('Belgian','BE'),('Dutch','NL')] if re.search(r'\('+word+r'\b',r['getty_preferred'])),None)
        evidence={'primary_url':ev['url'] if ev else getty['url'],'primary_person_facts':ev or {k:getty[k] for k in ('qid','ulan','name','retrieved_at','sha256','url')},'primary_preferred_biography':r['getty_preferred'],'country_code':country,'basis':'Same full creator identity and closed lifespan in original museum creator evidence, existing exact Wikidata identity, and independently reviewed primary museum/ULAN person facts. Primary-source date conflicts recorded; numeric dates preserved.'}
        proposals.append(dict(qid=q,old_slug=old['slug'],canonical_slug=keep['slug'],life=r['life'],evidence=evidence,targets={}))
    for target in ('local','production'):
        with m.m.r.base.connect(target=='production') as db,db.transaction():
            db.execute('SET TRANSACTION READ ONLY');db.execute("SET LOCAL statement_timeout='120s'");deps=dependencies(db)
            for e in proposals:
                rows={a['slug']:a for a in db.execute('SELECT to_jsonb(a) row FROM artists a WHERE slug=ANY(%s)',([e['old_slug'],e['canonical_slug']],)).fetchall() for a in [a['row']]}
                assert len(rows)==2;eold=rows[e['old_slug']];keep=rows[e['canonical_slug']]
                assert all(a['status']=='review' and a['entity_type']=='person' and [a['birth_year'],a['death_year']]==e['life'] for a in (eold,keep))
                assert not eold['biography_md'] and not eold['portrait_media_id'],'Original profile content needs field-level merge'
                assert db.execute("SELECT 1 FROM external_identifiers WHERE entity_type='artist' AND entity_id=%s AND scheme='wikidata' AND external_id=%s",(keep['id'],e['qid'])).fetchone()
                issues=overlaps(db,eold['id'],keep['id'],deps)
                museum=db.execute("SELECT source_url,evidence_note FROM citations WHERE entity_type='artist' AND entity_id=%s AND field_name IN ('round2_creator_authority','creator_identity','creator_authority')",(eold['id'],)).fetchall()
                # Some earlier researched creators use a versioned identity field.
                if not museum:museum=db.execute("SELECT source_url,evidence_note FROM citations WHERE entity_type='artist' AND entity_id=%s",(eold['id'],)).fetchall()
                assert museum,'Original museum creator evidence required'
                e['targets'][target]=dict(old_id=eold['id'],canonical_id=keep['id'],old_signature=signature(eold),canonical_signature=signature(keep),overlaps=issues,museum_creator_evidence=museum,dependencies=deps)
    approved=[]
    for e in proposals:
        if any(t['overlaps'] for t in e['targets'].values()):held.append(dict(qid=e['qid'],reason='Dependent relationship overlap requires field-level reconciliation',targets=e['targets']));continue
        assert e['targets']['local']['old_signature']==e['targets']['production']['old_signature']
        assert e['targets']['local']['canonical_signature']==e['targets']['production']['canonical_signature']
        approved.append(e)
    m.m.core.save_new(path,approved);m.m.core.save_new(RUN/'holds.json',held)
    manifest=dict(at=m.m.core.now(),plan_sha256=m.m.core.sha(path.read_bytes()),confirmed_pairs=len(approved),held_pairs=len(held),policy='Preserve all artist-linked relationships, citations, authorities, media and artwork records. Archive redundant profile and redirect old slug. Review status remains review on canonical profile. No automatic duplicate artwork removal.')
    m.m.core.save_new(RUN/'manifest.json',manifest);print(json.dumps(manifest,indent=2),flush=True)

def apply(targets=('local','production')):
    raw=(RUN/'plan.json').read_bytes();entries=json.loads(raw);pin=json.loads((RUN/'manifest.json').read_text())['plan_sha256'];assert m.m.core.sha(raw)==pin
    review=json.loads((RUN/'quality-review.json').read_text());assert review['approved'] and review['plan_sha256']==pin
    # Both-target concrete preimages are captured before the first mutation.
    for target in targets:
        backup=m.BACKUPS/('painter-consolidation-'+target+'-preimages.json')
        if backup.exists():continue
        with m.m.r.base.connect(target=='production') as db,db.transaction():
            db.execute('SET TRANSACTION READ ONLY');deps=dependencies(db);snapshots={}
            for e in entries:
                t=e['targets'][target];snap=snapshot(db,t['old_id'],t['canonical_id'],deps);rows={a['slug']:a for a in snap['artists']}
                assert signature(rows[e['old_slug']])==t['old_signature'] and signature(rows[e['canonical_slug']])==t['canonical_signature']
                assert not overlaps(db,t['old_id'],t['canonical_id'],deps)
                snapshots[e['qid']]=snap
        m.m.core.save_new(backup,dict(at=m.m.core.now(),plan_sha256=pin,pairs=snapshots))
    for target in targets:
        with m.m.r.base.connect(target=='production') as db:
            with db.transaction():
                db.execute('SELECT pg_advisory_xact_lock(559220260914)')
                db.execute("INSERT INTO sources(slug,name,source_type,base_url,is_active) VALUES(%s,%s,'authority_data',%s,true) ON CONFLICT(slug) DO NOTHING",(SOURCE,'Overnight primary-source person identity reconciliation',SOURCE_ROOT))
            sid=db.execute('SELECT id FROM sources WHERE slug=%s',(SOURCE,)).fetchone()['id']
            for e in entries:
                dest=RUN/'applied'/target/(e['qid']+'.json')
                if dest.exists():continue
                t=e['targets'][target];old=t['old_id'];keep=t['canonical_id'];moved={}
                with db.transaction():
                    db.execute('SELECT pg_advisory_xact_lock(559220260914)')
                    rows={r['slug']:r for r in db.execute('SELECT * FROM artists WHERE id=ANY(%s::uuid[]) FOR UPDATE',([old,keep],)).fetchall()}
                    # Crash recovery: a committed transaction with no receipt is
                    # recognized only through this exact plan's canonical citation.
                    done=db.execute("SELECT 1 FROM citations WHERE entity_type='artist' AND entity_id=%s AND source_id=%s AND field_name='duplicate_identity' AND source_record_id=%s AND evidence_note LIKE %s",(keep,sid,e['old_slug'],'%'+pin+'%')).fetchone()
                    if done:
                        assert rows[e['old_slug']]['status']=='archived';moved={'recovered_committed_transaction':True}
                    else:
                        assert rows[e['old_slug']]['status']==rows[e['canonical_slug']]['status']=='review'
                        deps=dependencies(db);assert [list(d) for d in deps]==t['dependencies'];assert not overlaps(db,old,keep,deps)
                        workids=[r['artwork_id'] for r in db.execute('SELECT artwork_id FROM artwork_artists WHERE artist_id=%s',(old,)).fetchall()]
                        for table,column in deps:
                            query=sql.SQL('UPDATE {} SET {}=%s WHERE {}=%s').format(sql.Identifier(table),sql.Identifier(column),sql.Identifier(column));moved[table+':'+column]=db.execute(query,(keep,old)).rowcount
                        for table in ('citations','external_identifiers','slug_redirects'):
                            moved[table]=db.execute(sql.SQL("UPDATE {} SET entity_id=%s WHERE entity_type='artist' AND entity_id=%s").format(sql.Identifier(table)),(keep,old)).rowcount
                        db.execute("INSERT INTO artist_aliases(artist_id,alias,normalized_alias,alias_type) VALUES(%s,%s,%s,'historical') ON CONFLICT DO NOTHING",(keep,rows[e['old_slug']]['display_name'],m.m.r.norm(rows[e['old_slug']]['display_name'])))
                        db.execute("INSERT INTO slug_redirects(entity_type,entity_id,old_slug) VALUES('artist',%s,%s)",(keep,e['old_slug']))
                        db.execute("UPDATE artists SET status='archived',revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s",(ACTOR,old))
                        code=e['evidence']['country_code']
                        if code:
                            db.execute("INSERT INTO artist_countries(artist_id,country_code,relationship_type,is_primary,note) VALUES(%s,%s,'cultural_affiliation',false,'Explicit primary authority affiliation; not birthplace or museum location. See geography citation.') ON CONFLICT DO NOTHING",(keep,code))
                        db.execute("UPDATE artists SET geography_review_state=CASE WHEN %s AND geography_review_state='not_reviewed' THEN 'classified' ELSE geography_review_state END,revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s",(bool(code),ACTOR,keep))
                        if workids:db.execute('UPDATE artworks SET revision=revision+1,updated_at=now(),updated_by=%s WHERE id=ANY(%s::uuid[])',(ACTOR,workids))
                        evidence=json.dumps(dict(plan_sha256=pin,old_slug=e['old_slug'],canonical_slug=e['canonical_slug'],review=e['evidence'],preservation='All dependent rows moved; original painter archived with redirect; artwork records and images retained'),ensure_ascii=False)
                        for field in (['duplicate_identity','geography'] if code else ['duplicate_identity']):
                            m.m.r.base.insert(db,'citations',dict(entity_type='artist',entity_id=keep,field_name=field,source_id=sid,source_record_id=e['old_slug'],source_url=e['evidence']['primary_url'],retrieved_at=m.m.core.now(),created_by=ACTOR,evidence_note=evidence))
                m.m.core.save_new(dest,dict(at=m.m.core.now(),plan_sha256=pin,target=target,qid=e['qid'],old_slug=e['old_slug'],canonical_slug=e['canonical_slug'],moved=moved));print(target,'consolidated',e['old_slug'],'->',e['canonical_slug'],flush=True)

def verify(targets=('local','production')):
    entries=json.loads((RUN/'plan.json').read_text());out={}
    for target in targets:
        backup=json.loads((m.BACKUPS/('painter-consolidation-'+target+'-preimages.json')).read_text());checked=[]
        with m.m.r.base.connect(target=='production') as db,db.transaction():
            db.execute('SET TRANSACTION READ ONLY')
            for e in entries:
                t=e['targets'][target];old=t['old_id'];keep=t['canonical_id'];before=backup['pairs'][e['qid']];rows={r['slug']:r for r in db.execute('SELECT * FROM artists WHERE id=ANY(%s::uuid[])',([old,keep],)).fetchall()}
                assert rows[e['old_slug']]['status']=='archived' and rows[e['canonical_slug']]['status']=='review' and rows[e['canonical_slug']]['published_at'] is None
                assert db.execute("SELECT 1 FROM slug_redirects WHERE entity_type='artist' AND old_slug=%s AND entity_id=%s",(e['old_slug'],keep)).fetchone()
                for table,column in dependencies(db):
                    assert db.execute(sql.SQL('SELECT count(*) n FROM {} WHERE {}=%s').format(sql.Identifier(table),sql.Identifier(column)),(old,)).fetchone()['n']==0
                    expected=len(before[table+':'+column]);actual=db.execute(sql.SQL('SELECT count(*) n FROM {} WHERE {}=%s').format(sql.Identifier(table),sql.Identifier(column)),(keep,)).fetchone()['n'];assert actual>=expected,(table,expected,actual)
                for table in ('citations','external_identifiers'):
                    ids=[r['id'] for r in before[table]]
                    assert db.execute(sql.SQL("SELECT count(*) n FROM {} WHERE id=ANY(%s::uuid[]) AND entity_type='artist' AND entity_id=%s").format(sql.Identifier(table)),(ids,keep)).fetchone()['n']==len(ids)
                for w in before['linked_artworks']:
                    now=db.execute('SELECT to_jsonb(a) row FROM artworks a WHERE id=%s',(w['id'],)).fetchone()['row']
                    assert {k:v for k,v in now.items() if k not in ('revision','updated_at','updated_by')}=={k:v for k,v in w.items() if k not in ('revision','updated_at','updated_by')},w['slug']
                for key in ('birth_year','death_year','birth_display','death_display','biography_md','portrait_media_id'):
                    expected=next(a for a in before['artists'] if a['id']==keep)[key];assert rows[e['canonical_slug']][key]==expected
                checked.append(dict(old_slug=e['old_slug'],canonical_slug=e['canonical_slug'],linked_artworks_preserved=len(before['linked_artworks'])))
        out[target]=checked
    if len(targets)==2:assert out['local']==out['production']
    name='verification.json' if len(targets)==2 else 'verification-'+targets[0]+'.json'
    m.m.core.save_new(RUN/name,dict(at=m.m.core.now(),targets=out,verified_pairs=len(entries),both_targets_verified=len(targets)==2,publication='Canonical profiles remain in review; redundant profiles archived with redirects; no artworks/assets deleted.'))
    print('Verified painter consolidation',list(targets),len(entries),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['plan','apply','verify']);a=p.parse_args();globals()[a.command]()
