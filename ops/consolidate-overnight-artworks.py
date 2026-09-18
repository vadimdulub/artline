#!/usr/bin/env python3
"""Consolidate explicitly reviewed physical objects, preserving archival evidence.

The earlier primary-museum record remains canonical. Redundant records are
archived with redirects; no artwork/media row or authentic asset is deleted.
Immutable holding assertions remain on their original record and are linked
through the canonical reconciliation citation. Research links and authority
identifiers move to the canonical record. Conflicting authority schemes block.
"""
import argparse,importlib.util,json,uuid
from pathlib import Path
from psycopg import sql
s=importlib.util.spec_from_file_location('m',Path(__file__).with_name('apply-country-round.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
CORE=m.m.core;RUN=m.x.BASE/'duplicates/artwork-consolidation';SOURCE='overnight-physical-object-review-20260913';ACTOR=m.m.ACTOR
TABLES=['artwork_artists','artwork_location_assertions','artwork_media','artwork_places','curated_collection_items','research_artwork_enrichments','research_artwork_links','research_resolutions']
MOVE=['research_artwork_enrichments','research_artwork_links','research_resolutions']

def sorted_rows(rows):return sorted(rows,key=lambda r:json.dumps(r,sort_keys=True,ensure_ascii=False,default=str))

def snapshot(db,ids):
    out={'artworks':[r['row'] for r in db.execute('SELECT to_jsonb(a) row FROM artworks a WHERE id=ANY(%s::uuid[])',(ids,)).fetchall()]}
    for table in TABLES:
        out[table]=[r['row'] for r in db.execute(sql.SQL('SELECT to_jsonb(t) row FROM {} t WHERE artwork_id=ANY(%s::uuid[])').format(sql.Identifier(table)),(ids,)).fetchall()]
    for table in ('citations','external_identifiers','slug_redirects'):
        out[table]=[r['row'] for r in db.execute(sql.SQL("SELECT to_jsonb(t) row FROM {} t WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])").format(sql.Identifier(table)),(ids,)).fetchall()]
    out['possible_links']=[r['row'] for r in db.execute('SELECT to_jsonb(t) row FROM research_artwork_links t WHERE possible_artwork_ids && %s::uuid[]',(ids,)).fetchall()]
    mids=sorted({w['primary_media_id'] for w in out['artworks'] if w['primary_media_id']}|{w['media_id'] for w in out['artwork_media']})
    out['media_assets']=[r['row'] for r in db.execute('SELECT to_jsonb(t) row FROM media_assets t WHERE id=ANY(%s::uuid[])',(mids,)).fetchall()]
    out['media_rights_evidence']=[r['row'] for r in db.execute('SELECT to_jsonb(t) row FROM media_rights_evidence t WHERE media_id=ANY(%s::uuid[])',(mids,)).fetchall()]
    return {k:sorted_rows(v) for k,v in out.items()}

def ensure_schema(db):
    deps=db.execute("SELECT conrelid::regclass::text t,a.attname c FROM pg_constraint f JOIN pg_attribute a ON a.attrelid=f.conrelid AND a.attnum=f.conkey[1] WHERE contype='f' AND confrelid='artworks'::regclass ORDER BY 1,2").fetchall()
    assert [(d['t'],d['c']) for d in deps]==[(t,'artwork_id') for t in sorted(TABLES)],'Unexpected artwork dependency requires review'

def primary_proposals():
    evidence=json.loads((m.x.BASE/'duplicates/russian-same-image-primary.json').read_text())['records'];out=[]
    for e in evidence:
        assert len(e['works'])==2
        old=next(w for w in e['works'] if w['slug'].startswith('wikimedia-artwork-'));keep=next(w for w in e['works'] if w['slug'].startswith('europe-russian-session-museum-'))
        assert old['checksum_sha256']==keep['checksum_sha256']==e['sha256']
        assert (old['accession_number']==e['inventory'] or (e['inventory']=='Р-5895' and old['accession_number'] is None)) and not keep['accession_number']
        assert sorted((c['slug'],c['role']) for c in old['creators'])==sorted((c['slug'],c['role']) for c in keep['creators'])
        assert (old['creation_year_start'],old['creation_year_end'])==(keep['creation_year_start'],keep['creation_year_end'])
        from bs4 import BeautifulSoup
        raw=(m.x.ROOT/e['capture']).read_bytes();text=BeautifulSoup(raw,'html.parser').get_text(' ',strip=True);assert e['inventory'] in text
        if e['inventory']=='Р-5895':assert 'Рисунок и акварель' in text and 'Бумага' in text and keep['work_type']=='drawing'
        else:assert keep['work_type']=='painting'
        out.append(dict(key=old['slug'].removeprefix('wikimedia-artwork-'),old_slug=old['slug'],canonical_slug=keep['slug'],accession=e['inventory'],primary_url=e['primary_url'],primary_capture=e['capture'],primary_capture_sha256=CORE.sha(raw),evidence=e,decision='Same physical Russian Museum inventory, same maker attribution, compatible primary dating and identical reproduction. Preserve the earlier primary museum record, its date precision and work type; add the English alternate title and the missing inventory. Other painted versions, studies, copies and panels remain separate.'))
    return out

def plan():
    proposals=primary_proposals();targets={}
    for target in ('local','production'):
        snapshots={}
        with m.m.r.base.connect(target=='production') as db,db.transaction():
            db.execute('SET TRANSACTION READ ONLY');db.execute("SET LOCAL statement_timeout='120s'");ensure_schema(db)
            for e in proposals:
                rows={r['slug']:r for r in db.execute('SELECT id::text,slug FROM artworks WHERE slug=ANY(%s)',([e['old_slug'],e['canonical_slug']],)).fetchall()};assert len(rows)==2
                old=rows[e['old_slug']]['id'];keep=rows[e['canonical_slug']]['id'];snap=snapshot(db,[old,keep]);works={w['id']:w for w in snap['artworks']};a=works[old];b=works[keep]
                assert a['status']==b['status']=='review' and a['published_at'] is None and b['published_at'] is None
                assert a['current_institution_id']==b['current_institution_id'] and a['current_institution_id']
                assert (a['accession_number']==e['accession'] or (e['accession']=='Р-5895' and a['accession_number'] is None)) and b['accession_number'] is None
                assert not b['alternate_title'];assert a['title']!=b['title']
                assert b['date_precision']==next(w['date_precision'] for w in e['evidence']['works'] if w['slug']==e['canonical_slug'])
                links=lambda aid:{(r['artist_id'],r['attribution_role']) for r in snap['artwork_artists'] if r['artwork_id']==aid}
                assert links(old)==links(keep) and links(keep)
                oldschemes={r['scheme'] for r in snap['external_identifiers'] if r['entity_id']==old};keepschemes={r['scheme'] for r in snap['external_identifiers'] if r['entity_id']==keep};assert not oldschemes&keepschemes
                assert not any(r['artwork_id']==old for r in snap['artwork_places']), 'Artwork place relationships require dedicated merge'
                assert not any(r['artwork_id']==old for r in snap['curated_collection_items']), 'Curator selections require individual reconciliation'
                assert any(r['artwork_id']==keep and r['claim_type']=='holding' and r['review_state']=='accepted' and not r['superseded_by'] for r in snap['artwork_location_assertions'])
                media={r['id']:r for r in snap['media_assets']};assert a['primary_media_id'] and b['primary_media_id'] and media[a['primary_media_id']]['checksum_sha256']==media[b['primary_media_id']]['checksum_sha256']==e['evidence']['sha256']
                assert db.execute("SELECT 1 FROM citations WHERE entity_type='artwork' AND entity_id=%s AND source_url=%s",(keep,e['primary_url'])).fetchone()
                snapshots[e['key']]=snap
        targets[target]=snapshots;CORE.save_new(m.BACKUPS/('artwork-consolidation-'+target+'-preimages.json'),snapshots)
    for e in proposals:
        for target in ('local','production'):
            snap=targets[target][e['key']];works={w['slug']:w for w in snap['artworks']};e.setdefault('targets',{})[target]=dict(old_id=works[e['old_slug']]['id'],canonical_id=works[e['canonical_slug']]['id'])
        comparable=lambda target:[{k:w[k] for k in ('slug','title','date_display','creation_year_start','creation_year_end','date_precision','work_type','status','accession_number')} for w in sorted(targets[target][e['key']]['artworks'],key=lambda w:w['slug'])]
        assert comparable('local')==comparable('production')
    path=RUN/'plan.json';CORE.save_new(path,proposals);CORE.save_new(RUN/'manifest.json',dict(at=CORE.now(),plan_sha256=CORE.sha(path.read_bytes()),confirmed_pairs=len(proposals),policy='Archive and redirect confirmed duplicate physical objects; preserve source assertions, media, chronology, and review status on canonical objects. No physical deletion.'))
    print('Artwork consolidation plan',len(proposals),flush=True)

def read_plan():
    raw=(RUN/'plan.json').read_bytes();pin=json.loads((RUN/'manifest.json').read_text())['plan_sha256'];assert CORE.sha(raw)==pin;return json.loads(raw),pin

def apply():
    entries,pin=read_plan();qa=json.loads((RUN/'quality-review.json').read_text());assert qa['approved'] and qa['plan_sha256']==pin
    for target in ('local','production'):
        backup=json.loads((m.BACKUPS/('artwork-consolidation-'+target+'-preimages.json')).read_text())
        with m.m.r.base.connect(target=='production') as db:
            for e in entries:
                dest=RUN/'applied'/target/(e['key']+'.json')
                if dest.exists():continue
                old=e['targets'][target]['old_id'];keep=e['targets'][target]['canonical_id'];before=backup[e['key']]
                with db.transaction():
                    db.execute("SET LOCAL lock_timeout='5s'");db.execute("SET LOCAL statement_timeout='120s'");db.execute('SELECT pg_advisory_xact_lock(559220260914)');ensure_schema(db)
                    db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',([old,keep],)).fetchall()
                    sid=m.m.source(db,SOURCE,'Primary museum physical-object duplicate review','collection_page','https://rusmuseumvrm.ru/')
                    done=db.execute("SELECT 1 FROM citations WHERE entity_type='artwork' AND entity_id=%s AND source_id=%s AND field_name='duplicate_identity' AND source_record_id=%s AND evidence_note LIKE %s",(keep,sid,e['old_slug'],'%'+pin+'%')).fetchone()
                    if not done:
                        assert snapshot(db,[old,keep])==before,'Relationships changed since concrete merge review'
                        works={w['id']:w for w in before['artworks']};a=works[old];b=works[keep]
                        # Original artist links and immutable location assertions
                        # remain as archival evidence. Canonical links already
                        # contain the same attribution and accepted holding.
                        for table in MOVE:db.execute(sql.SQL('UPDATE {} SET artwork_id=%s WHERE artwork_id=%s').format(sql.Identifier(table)),(keep,old))
                        db.execute('UPDATE research_artwork_links SET possible_artwork_ids=array_replace(possible_artwork_ids,%s::uuid,%s::uuid) WHERE %s::uuid=ANY(possible_artwork_ids)',(old,keep,old))
                        for table in ('citations','external_identifiers','slug_redirects'):db.execute(sql.SQL("UPDATE {} SET entity_id=%s WHERE entity_type='artwork' AND entity_id=%s").format(sql.Identifier(table)),(keep,old))
                        # Preserve distinct views if any; equal checksums remain
                        # accessible in the archive without duplicate gallery tiles.
                        media={r['id']:r for r in before['media_assets']};canonical_shas={media[r['media_id']]['checksum_sha256'] for r in before['artwork_media'] if r['artwork_id']==keep};canonical_shas.add(media[b['primary_media_id']]['checksum_sha256'])
                        for rel in before['artwork_media']:
                            if rel['artwork_id']!=old or media[rel['media_id']]['checksum_sha256'] in canonical_shas:continue
                            copy={**rel,'artwork_id':keep};m.m.r.base.insert(db,'artwork_media',copy);canonical_shas.add(media[rel['media_id']]['checksum_sha256'])
                        db.execute("INSERT INTO slug_redirects(entity_type,entity_id,old_slug) VALUES('artwork',%s,%s)",(keep,e['old_slug']))
                        db.execute('UPDATE artworks SET accession_number=%s,alternate_title=%s,revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s',(e['accession'],a['title'],ACTOR,keep))
                        db.execute("UPDATE artworks SET status='archived',revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s",(ACTOR,old))
                        evidence=dict(plan_sha256=pin,primary=e,archived_artwork_id=old,canonical_artwork_id=keep,archival_location_assertions=[r for r in before['artwork_location_assertions'] if r['artwork_id']==old],archival_artist_links=[r for r in before['artwork_artists'] if r['artwork_id']==old],archival_media=[r for r in before['artwork_media'] if r['artwork_id']==old],preservation='Canonical primary museum title, date precision, type, holding and image preserved. English title retained as alternate. Original assertions, image assets and rights evidence retained. Redundant profile archived; no object or asset deleted.')
                        m.m.r.base.insert(db,'citations',dict(entity_type='artwork',entity_id=keep,field_name='duplicate_identity',source_id=sid,source_record_id=e['old_slug'],source_url=e['primary_url'],retrieved_at=CORE.now(),created_by=ACTOR,evidence_note=json.dumps(evidence,ensure_ascii=False)))
                CORE.save_new(dest,dict(at=CORE.now(),plan_sha256=pin,target=target,key=e['key'],canonical_slug=e['canonical_slug'],archived_slug=e['old_slug']));print(target,'artwork consolidated',e['key'],flush=True)

def verify():
    entries,pin=read_plan();out={}
    for target in ('local','production'):
        backup=json.loads((m.BACKUPS/('artwork-consolidation-'+target+'-preimages.json')).read_text());checked=[]
        with m.m.r.base.connect(target=='production') as db,db.transaction():
            db.execute('SET TRANSACTION READ ONLY')
            for e in entries:
                old=e['targets'][target]['old_id'];keep=e['targets'][target]['canonical_id'];before=backup[e['key']];after=snapshot(db,[old,keep]);wbefore={w['id']:w for w in before['artworks']};wafter={w['id']:w for w in after['artworks']}
                assert wafter[old]['status']=='archived' and wafter[keep]['status']=='review' and wafter[keep]['published_at'] is None
                for aid,allowed in [(old,{'status','revision','updated_at','updated_by'}),(keep,{'accession_number','alternate_title','revision','updated_at','updated_by'})]:assert {k:v for k,v in wbefore[aid].items() if k not in allowed}=={k:v for k,v in wafter[aid].items() if k not in allowed}
                assert wafter[keep]['accession_number']==e['accession'] and wafter[keep]['alternate_title']==wbefore[old]['title']
                for table in ['media_assets','media_rights_evidence','artwork_location_assertions','artwork_artists','artwork_places','curated_collection_items']:assert after[table]==before[table],table
                for table in MOVE:
                    expected=[{**r,'artwork_id':keep if r['artwork_id']==old else r['artwork_id']} for r in before[table]]
                    if table=='research_artwork_links':expected=[{**r,'possible_artwork_ids':[keep if i==old else i for i in r['possible_artwork_ids']]} for r in expected]
                    assert sorted_rows(after[table])==sorted_rows(expected),table
                for table in ['citations','external_identifiers','slug_redirects']:
                    afterrows={r['id']:r for r in after[table]}
                    for row in before[table]:assert afterrows[row['id']]=={**row,'entity_id':keep if row['entity_id']==old else row['entity_id']},table
                assert any(r['old_slug']==e['old_slug'] and r['entity_id']==keep for r in after['slug_redirects'])
                assert any(r['scheme']=='wikidata' and r['external_id']==e['key'].upper() and r['entity_id']==keep for r in after['external_identifiers'])
                assert db.execute('SELECT artline_has_selection_evidence(%s) yes',(keep,)).fetchone()['yes']
                checked.append(dict(key=e['key'],canonical_slug=e['canonical_slug'],archived_slug=e['old_slug'],primary_type=wafter[keep]['work_type'],date_precision=wafter[keep]['date_precision'],all_assets_and_rights_preserved=True))
        out[target]=checked
    assert out['local']==out['production'];CORE.save_new(RUN/'verification.json',dict(at=CORE.now(),plan_sha256=pin,verified_pairs=len(entries),targets=out));print('Artwork consolidations verified both databases',len(entries),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['plan','apply','verify']);a=p.parse_args();globals()[a.command]()
