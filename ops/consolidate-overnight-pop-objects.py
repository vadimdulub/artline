#!/usr/bin/env python3
"""Review exact POP physical-object overlaps, retaining every original assertion.

The richer museum record stays canonical. Only exact source notice, title,
inventory and compatible attribution/date pairs qualify. Research placeholders
and duplicate institution catalogue imports are archived with redirects.
"""
import argparse,collections,importlib.util,json,re
from pathlib import Path
from psycopg import sql

s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('consolidate-overnight-artworks.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
m=a.m;CORE=a.CORE;RUN=m.x.BASE/'duplicates/pop-object-followup';BACK=m.BACKUPS/'pop-object-followup';SOURCE='overnight-pop-physical-objects-20260913'
SOURCE_NAME='Exact primary POP museum physical-object reconciliation';SOURCE_ROOT='https://pop.culture.gouv.fr/'

def key(value):return m.f.names.namekey(value or '')
def words(value):return tuple(sorted(key(value).split()))
def plan():
    if (RUN/'plan.json').exists():return
    leads=json.loads((m.x.BASE/'duplicates/primary-url-coverage/local-audit.json').read_text())['leads']['same_object_source_url'];proposals=[];holds=[]
    for lead in leads:
        oid=lead['url'].rsplit('/',1)[-1];capture=RUN/'captures'/(oid+'.json')
        if not capture.exists():holds.append(dict(key=oid,reason='primary_capture_unavailable'));continue
        ev=json.loads(capture.read_text());assert CORE.sha(capture.with_suffix('.html').read_bytes())==ev['receipt']['sha256'];f=ev['fields'];works=lead['works']
        reasons=[]
        if len(works)!=2:holds.append(dict(key=oid,reason='not_an_isolated_pair'));continue
        ranked=sorted(works,key=lambda w:(not bool(w['creators']),not bool(w['current_institution_id']),bool((w['institution_slug'] or '').startswith('joconde-')),not bool(w['accession_number']),w['slug']))
        keep,old=ranked
        if not keep['creators'] or not keep['current_institution_id'] or not keep['accession_number']:reasons.append('canonical_identity_incomplete')
        if key(keep['title'])!=key(old['title']) or key(keep['title'])!=key(f.get('Titre')):reasons.append('source_title_needs_individual_review')
        if m.m.accession_key(keep['accession_number'] or '')!=m.m.accession_key(f.get("Numéro d'inventaire",'')):reasons.append('primary_inventory_needs_review')
        if old['accession_number'] and m.m.accession_key(old['accession_number'])!=m.m.accession_key(keep['accession_number']):reasons.append('conflicting_inventory')
        creator=lambda w:{(c['slug'],c['role']) for c in w['creators']}
        if not creator(old)<=creator(keep):reasons.append('creator_identity_or_attribution_conflict')
        if any(old[k]!=keep[k] for k in ('creation_year_start','creation_year_end','date_precision','work_type')):reasons.append('source_chronology_or_type_conflict')
        maker=re.sub(r'\([^)]*\)','',f.get('Auteur','')).strip()
        if len(keep['creators'])!=1 or words(maker)!=words(keep['creators'][0]['name']):reasons.append('primary_creator_name_or_qualification_needs_review')
        if re.search(r'attribu|atelier|copie|entourage|anonyme|école de|d.apr[eè]s',f.get('Auteur',''),re.I):reasons.append('qualified_source_attribution')
        if old['primary_media_id']:reasons.append('redundant_record_has_primary_image_to_reconcile')
        pair={keep['institution_slug'],old['institution_slug']}
        institution_context='Same exact primary object notice; duplicate placeholder has no holding.'
        if old['current_institution_id'] and old['current_institution_id']!=keep['current_institution_id']:
            if pair=={'musee-beaux-arts-rouen','joconde-m0729'} and 'rouen' in key(f.get('Lieu de conservation')):institution_context='Both institution entries refer to the Rouen fine-arts museum; exact current primary notice confirms Rouen. Original holding assertions retained on their original rows.'
            elif pair=={'muma-le-havre','joconde-m0720'} and 'havre' in key(f.get('Lieu de conservation')):institution_context='Both institution entries refer to the Le Havre Malraux museum; exact primary notice confirms Le Havre. Original holding assertions retained.'
            else:reasons.append('institution_identity_needs_review')
        if reasons:holds.append(dict(key=oid,reason=sorted(set(reasons)),canonical_slug=keep['slug'],old_slug=old['slug']));continue
        proposals.append(dict(key=oid,canonical_slug=keep['slug'],old_slug=old['slug'],primary=ev,institution_context=institution_context,targets={}))
    snapshots={t:{} for t in ('local','production')};approved=[]
    for target in snapshots:
        with m.m.r.base.connect(target=='production') as db,db.transaction():
            db.execute('SET TRANSACTION READ ONLY');db.execute("SET LOCAL statement_timeout='120s'");a.ensure_schema(db)
            for e in proposals:
                rows={r['slug']:r['id'] for r in db.execute('SELECT id::text,slug FROM artworks WHERE slug=ANY(%s)',([e['old_slug'],e['canonical_slug']],))};assert len(rows)==2
                old=rows[e['old_slug']];keep=rows[e['canonical_slug']];snap=a.snapshot(db,[old,keep]);w={r['id']:r for r in snap['artworks']};issues=[]
                assert all(r['status']=='review' and r['published_at'] is None for r in w.values())
                artist=lambda aid:{(r['artist_id'],r['attribution_role']) for r in snap['artwork_artists'] if r['artwork_id']==aid}
                if not artist(old)<=artist(keep) or not artist(keep):issues.append('fresh_creator_relationships_conflict')
                for table in ('artwork_places','curated_collection_items','artwork_media'):
                    if any(r['artwork_id']==old for r in snap[table]):issues.append('redundant_'+table+'_needs_merge')
                if not any(r['artwork_id']==keep and r['claim_type']=='holding' and r['review_state']=='accepted' and not r['superseded_by'] for r in snap['artwork_location_assertions']):issues.append('canonical_accepted_holding_missing')
                common={r['scheme'] for r in snap['external_identifiers'] if r['entity_id']==old}&{r['scheme'] for r in snap['external_identifiers'] if r['entity_id']==keep}
                e['targets'][target]=dict(old_id=old,canonical_id=keep,preserve_archived_schemes=sorted(common),issues=issues)
                snapshots[target][e['key']]=snap
                print(target,'POP duplicate preflight',e['key'],issues,flush=True)
    for e in proposals:
        if any(t['issues'] for t in e['targets'].values()):holds.append(dict(key=e['key'],reason='fresh_dependent_relationship_review',targets=e['targets']));continue
        def comparable(target):return [{k:w[k] for k in ('slug','title','date_display','creation_year_start','creation_year_end','date_precision','work_type','status','accession_number')} for w in sorted(snapshots[target][e['key']]['artworks'],key=lambda w:w['slug'])]
        assert comparable('local')==comparable('production');approved.append(e)
    for target in snapshots:CORE.save_new(BACK/(target+'-preimages.json'),{e['key']:snapshots[target][e['key']] for e in approved})
    CORE.save_new(RUN/'plan.json',approved);CORE.save_new(RUN/'holds.json',holds);manifest=dict(at=CORE.now(),plan_sha256=CORE.sha((RUN/'plan.json').read_bytes()),pairs=len(approved),holds=len(holds));CORE.save_new(RUN/'manifest.json',manifest);print(manifest,flush=True)

def read_plan():
    raw=(RUN/'plan.json').read_bytes();pin=json.loads((RUN/'manifest.json').read_text())['plan_sha256'];assert CORE.sha(raw)==pin;return json.loads(raw),pin

def apply(targets=('local','production')):
    entries,pin=read_plan();qa=json.loads((RUN/'quality-review.json').read_text());assert qa['approved'] and qa['plan_sha256']==pin
    held=qa.get('held_objects',{});assert set(held)<=set(e['key'] for e in entries)
    assert targets and set(targets)<= {'local','production'}
    for target in targets:
        backup=json.loads((BACK/(target+'-preimages.json')).read_text())
        with m.m.r.base.connect(target=='production') as db:
            for e in entries:
                if e['key'] in held:continue
                dest=RUN/'applied'/target/(e['key']+'.json')
                if dest.exists():continue
                t=e['targets'][target];old=t['old_id'];keep=t['canonical_id'];before=backup[e['key']]
                with db.transaction():
                    db.execute("SET LOCAL lock_timeout='30s'");db.execute("SET LOCAL statement_timeout='120s'");db.execute('SELECT pg_advisory_xact_lock(559220260914)');a.ensure_schema(db);db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',([old,keep],)).fetchall()
                    sid=m.m.source(db,SOURCE,SOURCE_NAME,'collection_page',SOURCE_ROOT)
                    done=db.execute("SELECT 1 FROM citations WHERE entity_type='artwork' AND entity_id=%s AND source_id=%s AND field_name='duplicate_identity' AND source_record_id=%s AND evidence_note LIKE %s",(keep,sid,e['old_slug'],'%'+pin+'%')).fetchone()
                    if not done:
                        assert a.snapshot(db,[old,keep])==before,'Relationships changed after source review'
                        for table in a.MOVE:db.execute(sql.SQL('UPDATE {} SET artwork_id=%s WHERE artwork_id=%s').format(sql.Identifier(table)),(keep,old))
                        db.execute('UPDATE research_artwork_links SET possible_artwork_ids=array_replace(possible_artwork_ids,%s::uuid,%s::uuid) WHERE %s::uuid=ANY(possible_artwork_ids)',(old,keep,old))
                        for table in ('citations','slug_redirects'):db.execute(sql.SQL("UPDATE {} SET entity_id=%s WHERE entity_type='artwork' AND entity_id=%s").format(sql.Identifier(table)),(keep,old))
                        db.execute("UPDATE external_identifiers SET entity_id=%s WHERE entity_type='artwork' AND entity_id=%s AND NOT(scheme=ANY(%s))",(keep,old,t['preserve_archived_schemes']))
                        db.execute("UPDATE artworks SET status='archived',revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s",(m.m.ACTOR,old))
                        db.execute('UPDATE artworks SET revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s',(m.m.ACTOR,keep))
                        db.execute("INSERT INTO slug_redirects(entity_type,entity_id,old_slug) VALUES('artwork',%s,%s)",(keep,e['old_slug']))
                        evidence=dict(plan_sha256=pin,primary=e['primary'],institution_context=e['institution_context'],archived_id=old,canonical_id=keep,archived_authorities=[r for r in before['external_identifiers'] if r['entity_id']==old and r['scheme'] in t['preserve_archived_schemes']],archived_attributions=[r for r in before['artwork_artists'] if r['artwork_id']==old],archived_location_assertions=[r for r in before['artwork_location_assertions'] if r['artwork_id']==old],preservation='All original artwork fields, media, rights and immutable holding assertions preserved. No creation date, maker, museum display or publication assertion added. Shared source notice identifies the same physical object; alternate authority schemes remain recoverable through this citation and slug redirect.')
                        m.m.r.base.insert(db,'citations',dict(entity_type='artwork',entity_id=keep,field_name='duplicate_identity',source_id=sid,source_record_id=e['old_slug'],source_url=e['primary'].get('object_url') or e['primary']['receipt']['url'],retrieved_at=e['primary']['receipt']['retrieved_at'],created_by=m.m.ACTOR,evidence_note=json.dumps(evidence,ensure_ascii=False)))
                CORE.save_new(dest,dict(at=CORE.now(),plan_sha256=pin,key=e['key'],canonical_slug=e['canonical_slug'],archived_slug=e['old_slug']));print(target,'POP duplicate consolidated',e['key'],flush=True)

def verify(targets=('local','production')):
    entries,pin=read_plan();held=json.loads((RUN/'quality-review.json').read_text()).get('held_objects',{});out={}
    assert targets and set(targets)<= {'local','production'}
    for target in targets:
        backup=json.loads((BACK/(target+'-preimages.json')).read_text());checked=[]
        with m.m.r.base.connect(target=='production') as db,db.transaction():
            db.execute('SET TRANSACTION READ ONLY');db.execute("SET LOCAL statement_timeout='120s'")
            for e in entries:
                if e['key'] in held:continue
                t=e['targets'][target];old=t['old_id'];keep=t['canonical_id'];before=backup[e['key']];now=a.snapshot(db,[old,keep]);works={w['id']:w for w in now['artworks']}
                assert works[old]['status']=='archived' and works[keep]['status']=='review' and works[keep]['published_at'] is None
                for row in before['artworks']:
                    allowed={'revision','updated_at','updated_by'}|({'status'} if row['id']==old else set());assert {k:v for k,v in works[row['id']].items() if k not in allowed}=={k:v for k,v in row.items() if k not in allowed}
                for table in ('media_assets','media_rights_evidence','artwork_artists','artwork_places','curated_collection_items','artwork_media','artwork_location_assertions'):assert now[table]==before[table],table
                for table in ('citations','external_identifiers','slug_redirects'):
                    rowkey=lambda r:(r['entity_type'],r['old_slug']) if table=='slug_redirects' else r['id']
                    current={rowkey(r):r for r in now[table]}
                    for row in before[table]:
                        move=row['entity_id']==old and not(table=='external_identifiers' and row['scheme'] in t['preserve_archived_schemes']);assert current[rowkey(row)]=={**row,'entity_id':keep if move else row['entity_id']}
                for table in a.MOVE:
                    expected_rows=[]
                    for row in before[table]:
                        expected={**row,'artwork_id':keep if row['artwork_id']==old else row['artwork_id']}
                        if table=='research_artwork_links':expected['possible_artwork_ids']=[keep if x==old else x for x in (row['possible_artwork_ids'] or [])] if row['possible_artwork_ids'] is not None else None
                        expected_rows.append(expected)
                    assert a.sorted_rows(now[table])==a.sorted_rows(expected_rows),(table,e['key'])
                expected_rows=[]
                for row in before['possible_links']:
                    expected={**row,'artwork_id':keep if row['artwork_id']==old else row['artwork_id'],'possible_artwork_ids':[keep if x==old else x for x in row['possible_artwork_ids']]}
                    expected_rows.append(expected)
                assert a.sorted_rows(now['possible_links'])==a.sorted_rows(expected_rows),('possible_links',e['key'])
                assert any(r['old_slug']==e['old_slug'] and r['entity_id']==keep for r in now['slug_redirects'])
                assert db.execute('SELECT artline_has_selection_evidence(%s) yes',(keep,)).fetchone()['yes'];checked.append(dict(key=e['key'],canonical_slug=e['canonical_slug'],archived_slug=e['old_slug']))
        out[target]=checked;print(target,'POP duplicates verified',len(checked),flush=True)
    if set(targets)=={'local','production'}:assert out['local']==out['production']
    name='verification.json' if len(targets)==2 else 'verification-'+targets[0]+'.json'
    CORE.save_new(RUN/name,dict(at=CORE.now(),plan_sha256=pin,verified_pairs=len(out[targets[0]]),targets=out,both_targets_verified=len(targets)==2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['plan','apply','verify']);args=p.parse_args();globals()[args.command]()
