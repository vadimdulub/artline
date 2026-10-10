#!/usr/bin/env python3
"""Correct this campaign's own additions while preserving older catalogue data."""
import argparse
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('delivery',ROOT/'ops/deliver-random-200-painters-20261006.py')
d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
m=d.m;r=d.r;s=d.s;RUN=d.RUN;BACKUP=d.BACKUP


def consolidate():
    done=RUN/'alias-consolidation-applied.json'
    if done.exists():print('Alias consolidation already complete');return
    proof_path=RUN/'alias-consolidation-evidence.json.gz';proofs=r.load(proof_path);pin=r.sha(proof_path.read_bytes())
    assert len(proofs)==6 and r.load(BACKUP/'cloud-backup.json')['status']=='SUCCESSFUL'
    ids=[x[k] for x in proofs for k in ['artwork_id','existing_id']]
    with r.connect('production',readonly=False) as db,db.transaction():
        db.execute("SET LOCAL lock_timeout='5s'");db.execute('SELECT pg_advisory_xact_lock(2026100607)')
        db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(ids,)).fetchall()
        before=s.snapshots(db,ids);assert len(before)==12
        for proof in proofs:
            fresh=before[proof['artwork_id']];original=before[proof['existing_id']]
            assert fresh['artwork']['created_by']==m.ACTOR and fresh['artwork']['status']=='review' and fresh['artwork']['published_at'] is None
            assert fresh['artwork']['slug']=='wikiart-'+proof['wikiart_row']['source_id']
            assert not original['creators'] and not original['artwork']['primary_media_id'] and not original['attachments']
            assert original['artwork']['status']=='review'
            assert fresh['creators'][0]['artist_id']==proof['artist_id']
        r.save_gz(BACKUP/'alias-consolidation-before.json.gz',{'evidence_sha256':pin,'records':before})
        source=m.uid('source/alias-reconciliation')
        db.execute("INSERT INTO sources(id,slug,name,source_type,base_url) VALUES(%s,%s,%s,'collection_page','https://www.wikiart.org/')",
                   (source,m.OP+'-aliases','Selected painter alias and same-object reconciliation, 6 October 2026'))
        for proof in proofs:
            fresh=proof['artwork_id'];original=proof['existing_id'];image=before[fresh]['artwork']['primary_media_id']
            db.execute("INSERT INTO artwork_artists(artwork_id,artist_id,attribution_role,attribution_note) VALUES(%s,%s,'primary',%s)",
                       (original,proof['artist_id'],proof['identity_basis']))
            if image:
                db.execute("INSERT INTO artwork_media(artwork_id,media_id,sort_order,view_label) VALUES(%s,%s,0,'Complete source reproduction; same-object reconciliation')",(original,image))
            db.execute('UPDATE artworks SET primary_media_id=%s,revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s',(image,m.ACTOR,original))
            # Archive only the redundant row introduced by this operation; no pre-existing row is archived/deleted.
            db.execute("UPDATE artworks SET status='archived',revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s",(m.ACTOR,fresh))
            changed=db.execute("UPDATE external_identifiers SET entity_id=%s WHERE entity_type='artwork' AND entity_id=%s AND scheme='wikiart-artwork' AND external_id=%s",
                               (original,fresh,proof['wikiart_row']['source_id']));assert changed.rowcount==1
            note={'operation':m.OP,'evidence_sha256':pin,'existing_artwork_id':original,'redundant_campaign_record':fresh,
                  'identity_basis':proof['identity_basis'],'confidence':proof['confidence'],'prior_source_citation':proof['source_citation'],
                  'source_record':proof['source_record'],'wikiart_page':proof['wikiart_row']['page'],
                  'scope':'Reuse the older review record, preserve its title/date/holding/publication and object-level creator label; add source-supported creator link and share the existing authorized image. Archive only this operation\'s redundant new row. No data or media deleted.'}
            for aid in [original,fresh]:
                db.execute('''INSERT INTO citations(id,entity_type,entity_id,source_id,field_name,source_record_id,source_url,evidence_note,retrieved_at,created_by)
                  VALUES(%s,'artwork',%s,%s,'random_200_alias_reconciliation',%s,%s,%s,%s,%s)''',
                  (m.uid('alias-citation/'+aid),aid,source,proof['wikiart_row']['source_id'],proof['wikiart_row']['source_url'],json.dumps(note,ensure_ascii=False),r.now(),m.ACTOR))
        after=s.snapshots(db,ids)
        for proof in proofs:
            original=proof['existing_id'];fresh=proof['artwork_id'];a=after[original];b=before[original]
            allowed={'primary_media_id','revision','updated_at','updated_by'}
            assert {k:v for k,v in a['artwork'].items() if k not in allowed}=={k:v for k,v in b['artwork'].items() if k not in allowed}
            assert a['locations']==b['locations'] and len(a['creators'])==1 and a['creators'][0]['artist_id']==proof['artist_id']
            assert after[fresh]['artwork']['status']=='archived'
            assert after[fresh]['artwork']['primary_media_id']==a['artwork']['primary_media_id']
    r.save_gz(BACKUP/'alias-consolidation-after.json.gz',{'evidence_sha256':pin,'records':after})
    r.save(done,{'at':r.now(),'evidence_sha256':pin,'creator_links_added':6,'redundant_campaign_records_archived':6,
                'images_reused':sum(bool(before[p['artwork_id']]['artwork']['primary_media_id']) for p in proofs),
                'moves':[{'from':p['artwork_id'],'to':p['existing_id'],'artist_id':p['artist_id']} for p in proofs],
                'existing_metadata_and_publication_preserved':True,'deletions':0})
    print('Consolidated six same-object aliases; older records preserved, six creator links added.',flush=True)


def dates():
    """Repair omitted circa qualifiers on campaign-created records only."""
    corrections=[]
    with r.connect('production',readonly=False) as db:
        for data,pin in d.pinned_deliveries():
            artist_id=data['artist']['id'];done=RUN/'date-corrections'/(artist_id+'.json')
            if done.exists():continue
            if not (RUN/'applied'/(artist_id+'.json')).exists():continue
            rows=[]
            for row in data['rows']:
                if row['action']!='create':continue
                actual=s.source_date(row['page'])
                if actual and any(row['work'].get(k)!=v for k,v in actual.items()):rows.append((row,actual))
            ids=[row['artwork_id'] for row,actual in rows]
            if not rows:
                # Plans built after the precision fix already preserve the visible date.
                # Final production verification checks those rows; no empty write transaction.
                empty={'records':{},'plan_sha256':pin}
                r.save_gz(BACKUP/'date-preimages'/(artist_id+'.json.gz'),empty)
                r.save_gz(BACKUP/'date-after'/(artist_id+'.json.gz'),empty)
                result={'at':r.now(),'artist_id':artist_id,'corrected':0,'artwork_ids':[]}
                r.save(done,result);corrections.append(result);continue
            with db.transaction():
                db.execute("SET LOCAL lock_timeout='5s'");db.execute('SELECT pg_advisory_xact_lock(2026100607)')
                db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(ids,)).fetchall()
                before=s.snapshots(db,ids);changed=[]
                for row,actual in rows:
                    old=before[row['artwork_id']]['artwork'];assert old['created_by']==m.ACTOR and old['published_at'] is None
                    if all(old[k]==v for k,v in actual.items()):continue
                    # This is precision preservation, never a different creation-year assertion.
                    assert old['creation_year_start']==actual['creation_year_start'] and old['creation_year_end']==actual['creation_year_end']
                    changed.append((row,actual))
                r.save_gz(BACKUP/'date-preimages'/(artist_id+'.json.gz'),{'records':before,'plan_sha256':pin})
                for row,actual in changed:
                    db.execute('UPDATE artworks SET date_display=%s,date_precision=%s,revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s',
                               (actual['date_display'],actual['date_precision'],m.ACTOR,row['artwork_id']))
                    db.execute('''INSERT INTO citations(id,entity_type,entity_id,source_id,field_name,source_record_id,source_url,evidence_note,retrieved_at,created_by)
                      VALUES(%s,'artwork',%s,%s,'random_200_date_precision',%s,%s,%s,%s,%s)''',
                      (m.uid('date-precision/'+row['artwork_id']),row['artwork_id'],m.uid('source/wikiart'),row['source_id'],row['source_url'],
                       json.dumps({'reason':'Preserve the visible WikiArt Date qualifier omitted by its embedded gallery JSON. Correct only this campaign\'s newly created record; existing catalogue records are untouched.',
                                   'previous':{k:before[row['artwork_id']]['artwork'][k] for k in actual},'source_date':row['page']['fields'].get('Date'),'corrected':actual,'plan_sha256':pin},ensure_ascii=False),r.now(),m.ACTOR))
                after=s.snapshots(db,ids)
            r.save_gz(BACKUP/'date-after'/(artist_id+'.json.gz'),{'records':after,'plan_sha256':pin})
            result={'at':r.now(),'artist_id':artist_id,'corrected':len(changed),'artwork_ids':[row['artwork_id'] for row,actual in changed]}
            r.save(done,result);corrections.append(result)
    print('Preserved source date qualifiers on',sum(x['corrected'] for x in corrections),'new campaign records',flush=True)


def refresh_retries():
    state=r.load(RUN/'progress/source-retries.json');ids=state['pending_artist_ids']
    if not ids:print('Source retry plans already refreshed');return
    pairs={x['artist']['id']:x for x in m.cohort()};revised=[]
    for failure in r.load(RUN/'transient-page-failures.json'):
        path=RUN/'page-retries'/failure['artist_id']/(r.sha(failure['index']['url'].encode())+'.json.gz')
        assert r.load(path)['outcome']=='captured'
    with r.connect('production') as db:
        for aid in ids:
            assert not (RUN/'delivery-plans'/(aid+'.json.gz')).exists() and not (RUN/'applied'/(aid+'.json')).exists()
            oldpin=r.load(RUN/'selection-pins'/(aid+'.json'))['sha256']
            for folder,filename in [('selections',aid+'.json.gz'),('selection-pins',aid+'.json'),('image-audits',aid+'.json')]:
                path=RUN/folder/filename
                if path.exists():
                    target=RUN/'revisions/before-source-retry'/folder/filename;target.parent.mkdir(parents=True,exist_ok=True);path.rename(target)
            path=BACKUP/'selection-preimages'/(aid+'.json.gz');target=BACKUP/'revisions/before-source-retry/selection-preimages'/(aid+'.json.gz')
            target.parent.mkdir(parents=True,exist_ok=True);path.rename(target)
            data=s.artist_plan(pairs[aid],db);assert data
            newpin=r.load(RUN/'selection-pins'/(aid+'.json'))['sha256'];repinned=0
            for row in d.image_rows(data):
                path=RUN/'prepared-images'/(row['artwork_id']+'.json')
                if not path.exists():continue
                im=r.load(path);assert im['selection_pin']==oldpin
                assert im['source_id']==row['source_id'] and im['artist_id']==aid and im['source_page_url']==row['source_url']
                assert im['source_rights_label']==row['source_rights_label'] and im['rights_status']==row['rights_status']
                if im['outcome']=='prepared':assert r.sha(Path(im['visual_path']).read_bytes())==im['sha256']
                archive=RUN/'revisions/before-source-retry/prepared-images'/path.name;archive.parent.mkdir(parents=True,exist_ok=True);path.rename(archive)
                im.update(selection_pin=newpin,identity_basis=row['identity_basis'],confidence=row['confidence'],previous_selection_pin=oldpin)
                r.save(path,im);repinned+=1
            revised.append({'artist_id':aid,'artist':data['artist']['display_name'],'before_pin':oldpin,'after_pin':newpin,'reused_prepared_files':repinned,'counts':data['counts']})
            print('Refreshed recovered source plan',data['artist']['display_name'],data['counts'],repinned,'existing image files reused',flush=True)
    r.save(RUN/'source-retry-plan-revisions.json',{'at':r.now(),'revisions':revised})
    m.status('source-retries',pending_artist_ids=[],recovered_pages=61,revised_artist_ids=ids)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['consolidate','dates','refresh_retries']);args=parser.parse_args();globals()[args.phase]()
