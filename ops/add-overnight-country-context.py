#!/usr/bin/env python3
"""Preserve eight artists' documented additional cultural affiliations."""
import argparse,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('g',Path(__file__).with_name('review-overnight-country-gaps.py'));g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
m=g.m;CORE=m.m.core;RUN=m.x.BASE/'country-context-corrections';SOURCE='overnight-additional-country-context-20260913'
ADDITIONS={'2422':'US','4138':'FR','4972':'FR','6284':'US','9817':'GB','10136':'DE','34221':'MX','52591':'US'}

def plan():
    dest=RUN/'additional-affiliation-plan.json'
    if dest.exists():return
    registry,receipts=g.c.museum_rows();leads=json.loads((RUN/'additional-current-identities.json').read_text());entries=[];targets={}
    for a in leads:
        sid=a['external_id'];rec=registry['nga-constituent'][sid];code=ADDITIONS[sid];context=g.c.nga_display_context(rec['raw'])
        assert code in context['explicit_codes'],context
        entries.append(dict(slug=a['slug'],person_id=sid,add_code=code,primary_record=rec['raw'],receipt=receipts['nga-constituent'],context='The NGA exact person record explicitly names this affiliation before its birthplace/activity qualifier. Retain the previously documented affiliation too; these are nonexclusive cultural affiliations. No country inferred from a place of birth, no chronology changed.'))
    for target in ('local','production'):
        with m.m.r.base.connect(target=='production') as db,db.transaction():
            db.execute('SET TRANSACTION READ ONLY');rows=g.c.selected(db,[{'artist':{'slug':e['slug']}} for e in entries])
            for e in entries:
                a=rows[e['slug']];assert a['row']['status']=='review' and a['row']['published_at'] is None
                assert {'scheme':'nga-constituent','id':e['person_id']} in a['authorities']
                assert e['add_code'] not in {c['country_code'] for c in a['countries'] if c['relationship_type']=='cultural_affiliation'}
                rec=registry['nga-constituent'][e['person_id']]
                assert all(rec[k] is None or a['row'][k+'_year'] is None or rec[k]==a['row'][k+'_year'] for k in ('birth','death'))
        targets[target]=rows;CORE.save_new(m.BACKUPS/('additional-country-context-'+target+'-preimages.json'),rows)
    for e in entries:assert g.signature(targets['local'][e['slug']])==g.signature(targets['production'][e['slug']])
    CORE.save_new(dest,dict(at=CORE.now(),entries=entries,targets=targets));CORE.save_new(RUN/'additional-affiliation-manifest.json',dict(at=CORE.now(),plan_sha256=CORE.sha(dest.read_bytes()),affiliations=len(entries)));print('Additional country context plan',len(entries),flush=True)

def apply():
    raw=(RUN/'additional-affiliation-plan.json').read_bytes();data=json.loads(raw);pin=CORE.sha(raw);assert pin==json.loads((RUN/'additional-affiliation-manifest.json').read_text())['plan_sha256']
    qa=json.loads((RUN/'additional-affiliation-quality-review.json').read_text());assert qa['approved'] and qa['plan_sha256']==pin
    for target in ('local','production'):
        dest=RUN/('additional-affiliation-'+target+'-verified.json')
        if dest.exists():continue
        with m.m.r.base.connect(target=='production') as db:
            with db.transaction():
                db.execute('SELECT pg_advisory_xact_lock(559220260914)');sid=m.m.source(db,SOURCE,'NGA primary biographical context: additional artist affiliations','authority_data','https://www.nga.gov/')
                for e in data['entries']:
                    old=data['targets'][target][e['slug']];aid=old['row']['id'];db.execute('SELECT id FROM artists WHERE id=%s FOR UPDATE',(aid,))
                    done=db.execute("SELECT 1 FROM citations WHERE entity_type='artist' AND entity_id=%s AND source_id=%s AND evidence_note LIKE %s",(aid,sid,'%'+pin+'%')).fetchone()
                    if done:continue
                    assert g.c.selected(db,[{'artist':{'slug':e['slug']}}])[e['slug']]==old
                    db.execute("INSERT INTO artist_countries(artist_id,country_code,relationship_type,is_primary,note) VALUES(%s,%s,'cultural_affiliation',false,%s)",(aid,e['add_code'],e['context']+' NGA display biography: '+e['primary_record']['displaydate']))
                    m.m.r.base.insert(db,'citations',dict(entity_type='artist',entity_id=aid,source_id=sid,field_name='geography',source_record_id=e['person_id'],source_url=e['receipt']['url'],retrieved_at=e['receipt']['retrieved_at'],created_by=m.m.ACTOR,evidence_note=json.dumps(dict(plan_sha256=pin,evidence=e,review_status='review'),ensure_ascii=False)))
                    db.execute("UPDATE artists SET geography_review_state=CASE WHEN geography_review_state='not_reviewed' THEN 'classified' ELSE geography_review_state END,revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s",(m.m.ACTOR,aid))
            with db.transaction():
                db.execute('SET TRANSACTION READ ONLY');rows=g.c.selected(db,[{'artist':{'slug':e['slug']}} for e in data['entries']])
                for e in data['entries']:
                    now=rows[e['slug']];old=data['targets'][target][e['slug']];ignore={'geography_review_state','revision','updated_at','updated_by'}
                    assert {k:v for k,v in now['row'].items() if k not in ignore}=={k:v for k,v in old['row'].items() if k not in ignore};assert now['authorities']==old['authorities']
                    assert all(c in now['countries'] for c in old['countries'])
                    assert {(c['country_code'],c['relationship_type']) for c in now['countries']}=={(c['country_code'],c['relationship_type']) for c in old['countries']}|{(e['add_code'],'cultural_affiliation')}
        CORE.save_new(dest,dict(at=CORE.now(),plan_sha256=pin,additional_affiliations=len(data['entries']),original_relationships_and_review_preserved=True));print(target,'additional country contexts verified',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['plan','apply']);a=p.parse_args();globals()[a.command]()
