#!/usr/bin/env python3
"""Guarded creator-only reconciliation of explicit supplied lifespans.

No approximate dates, activity spans, shortened names or name-only matching.
Planning/auditing is read-only; application reuses the preimage-guarded writer.
"""
import argparse, collections, importlib.util, json, re, subprocess
from pathlib import Path
spec=importlib.util.spec_from_file_location('reconcile',Path(__file__).with_name('reconcile-creators-followup.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
m.RUN=m.ROOT/'docs/research/creator-lifespans-20260913'
m.BACKUPS=Path('/Users/vadimdulub/Library/Application Support/Artline/backups/creator-lifespans-20260913')
m.FIELD='creator_lifespan_reconciled_20260913'
m.SOURCE_SLUG='creator-lifespans-20260913'
m.SOURCE_NAME='Supplied creator lifespans reconciled with documented painter authorities'
PATTERN=re.compile(r'(.+?)\s*\((\d{4})\s*[-–]\s*(\d{4})\)')

def parse(label):
    match=PATTERN.fullmatch(label.strip())
    if not match:return None
    return {'name':match[1].strip(),'birth':int(match[2]),'death':int(match[3]),'role':'artist'}

def snapshot():
    assert not (m.RUN/'unlinked-artworks.json').exists()
    with m.r.base.connect(False) as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
        db.execute("SET LOCAL statement_timeout='120s'")
        rows=db.execute("""SELECT id::text,slug,title,unlinked_creator_label,creation_year_start,creation_year_end,date_precision,work_type,research_candidate,status,revision
        FROM artworks w WHERE w.unlinked_creator_label IS NOT NULL AND w.status='review' AND NOT EXISTS(SELECT 1 FROM artwork_artists aa WHERE aa.artwork_id=w.id) ORDER BY slug""").fetchall()
        m.save('unlinked-artworks.json',rows)
        artists=db.execute("""SELECT id::text,slug,display_name,normalized_name,birth_year,death_year,status,entity_type,
        coalesce((SELECT jsonb_agg(alias ORDER BY alias) FROM artist_aliases WHERE artist_id=a.id),'[]') aliases,
        coalesce((SELECT jsonb_agg(jsonb_build_object('scheme',scheme,'id',external_id) ORDER BY scheme,external_id) FROM external_identifiers WHERE entity_type='artist' AND entity_id=a.id),'[]') authorities
        FROM artists a WHERE status<>'archived' ORDER BY slug""").fetchall();m.save('artists.json',artists)
        ids=[w['id'] for w in rows]
        originals=db.execute("""SELECT w.id::text,w.slug,l.research_record_id,l.entry_sha256,rr.raw_json#>'{csv,cells}' cells
        FROM research_artwork_links l JOIN artworks w ON w.id=l.artwork_id
        JOIN research_records rr ON rr.snapshot_id=l.snapshot_id AND rr.source_key=l.source_key AND rr.record_kind=l.record_kind AND rr.source_record_id=l.research_record_id
        WHERE w.id=ANY(%s::uuid[]) AND l.disposition='created' ORDER BY w.slug""",(ids,)).fetchall();m.save('unlinked-original-identities.json',originals)
        facts=db.execute("""SELECT w.id::text,w.slug,r.research_record_id,r.source_kind,r.state,r.note,r.facts_sha256,r.facts_json->'painter' painter,r.facts_json->'object_context' context,r.review_evidence,r.object_url
        FROM research_artwork_links l JOIN artworks w ON w.id=l.artwork_id
        JOIN research_resolutions r ON r.snapshot_id=l.snapshot_id AND r.research_record_id=l.research_record_id
        WHERE w.id=ANY(%s::uuid[]) AND l.disposition='created' ORDER BY w.slug""",(ids,)).fetchall();m.save('museum-creator-facts.json',facts)
    print('Fresh snapshot:',len(rows),'unlinked artworks;',len(artists),'active painters',flush=True)

def plan():
    assert not (m.RUN/'plan.json').exists()
    works=m.read('unlinked-artworks.json');matcher=m.Matcher(m.read('artists.json'))
    originals={w['id']:w for w in m.read('unlinked-original-identities.json')}
    facts={w['id']:w for w in m.read('museum-creator-facts.json')}
    entries=[];holds=[];parsed=0
    for w in works:
        painter=parse(w['unlinked_creator_label'])
        if not painter:continue
        parsed+=1;reason=None;fact=facts.get(w['id']);original=originals.get(w['id'])
        check={'painter':painter,'context':(fact or {}).get('context'),'state':(fact or {}).get('state','needs_review'),'review':(fact or {}).get('review_evidence') or {},'note':(fact or {}).get('note') or '', 'precision':w['date_precision'],'first':w['creation_year_start'],'last':w['creation_year_end'],'type':w['work_type']}
        reason=m.old.blocked(check)
        if not original or original['cells'][0]!=w['unlinked_creator_label']:reason='original_supplied_label_not_confirmed'
        if fact:
            p=fact['painter']
            if m.old.QUALIFIED.search(p['name']):reason='official_creator_qualification'
            if any(p.get(k) is not None and p[k]!=painter[k] for k in ('birth','death')):reason='official_biography_conflict'
            if m.names.namekey(p['name'])!=m.names.namekey(painter['name']):reason='official_creator_name_differs'
        match=None
        if not reason:match,reason=matcher.match(painter,'supplied-lifespan')
        if not reason:
            a=match['artist']
            if (w['creation_year_end'] is not None and w['creation_year_end']<a['birth_year']) or (w['creation_year_start'] is not None and w['creation_year_start']>a['death_year']):reason='artwork_outside_painter_lifetime'
            if fact:
                authoritative,authority_reason=matcher.match(fact['painter'],fact['source_kind'])
                if authority_reason in ('conflicting_authority_ids','authority_biography_conflict','existing_wikidata_conflict') or (authoritative and authoritative['artist']['id']!=a['id']):reason='official_creator_authority_conflict'
        if reason:
            holds.append({'slug':w['slug'],'label':w['unlinked_creator_label'],'reason':reason});continue
        authority_urls=[('https://www.wikidata.org/wiki/'+x['id']) for x in a['authorities'] if x['scheme']=='wikidata']
        url=(fact or {}).get('object_url') or (authority_urls[0] if authority_urls else 'https://github.com/vadimdulub/artline')
        entries.append({'before':w,'artist':a,'basis':'explicit_supplied_creator_name_and_both_lifespan_years_match_documented_painter','painter':painter,'source':'supplied-lifespan','source_guard':fact,'original':original,'evidence':{'object_url':url,'research_record_id':original['research_record_id'],'entry_sha256':original['entry_sha256'],'literal_creator_label':w['unlinked_creator_label'],'parsed_creator_lifespan':painter,'artist_authorities':a['authorities'],'museum_object_url':(fact or {}).get('object_url'),'policy':'Creator identity only. Supplied lifespan is not an artwork creation date. Unknown fields and editorial status remain unchanged.'}})
    m.save('plan.json',entries);m.save('holds.json',holds)
    manifest={'at':m.r.core.now(),'sha256':m.r.core.sha((m.RUN/'plan.json').read_bytes()),'audited_unlinked_artworks':len(works),'strict_lifespan_labels':parsed,'links':len(entries),'existing_painters':len({e['artist']['id'] for e in entries}),'sources':dict(collections.Counter(e['source'] for e in entries)),'held_reasons':dict(collections.Counter(h['reason'] for h in holds)),'museum_scope':'All existing and new museums and collections; no institution exclusion.'}
    m.save('manifest.json',manifest);print(json.dumps(manifest,indent=2),flush=True)

def backup_local():
    access=m.module('access','/tmp/artline-deploy-20260912/database_migration.py')
    m.BACKUPS.mkdir(parents=True,exist_ok=True);path=m.BACKUPS/'local-before.dump'
    assert not path.exists()
    subprocess.run(['pg_dump','--format=custom','--no-owner','--no-acl','--file',str(path)],env=access.environment(False),check=True)
    listed=subprocess.check_output(['pg_restore','--list',str(path)])
    m.r.core.save_new(m.BACKUPS/'local-backup-receipt.json',{'at':m.r.core.now(),'path':str(path),'bytes':path.stat().st_size,'sha256':m.r.core.sha(path.read_bytes()),'archive_listing_entries':len(listed.splitlines())})
    print('Local backup verified',path.stat().st_size,flush=True)

def verification(target):
    v=m.module('verifier',m.ROOT/'ops/verify-creator-followup.py');v.m=m
    v.live() if target=='live' else v.verify(target)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['snapshot','plan','backup-local','preflight','apply','verify']);p.add_argument('--target',choices=['local','production','live']);a=p.parse_args()
    if a.command=='snapshot':snapshot()
    elif a.command=='plan':plan()
    elif a.command=='backup-local':backup_local()
    elif a.command=='preflight':m.preflight(a.target)
    elif a.command=='apply':m.apply(a.target)
    else:verification(a.target)
