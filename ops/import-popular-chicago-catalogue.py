#!/usr/bin/env python3
"""Apply the pinned Chicago metadata plan to the existing review schema.

Each target gets a fresh, read-only collision check and an external preimage
backup before writes. Safe to repeat; native identifiers and immutable plan
checksums are checked again. No images, publication or schema changes here.
"""
import argparse, importlib.util, json
from pathlib import Path
import psycopg
from psycopg.rows import dict_row

s=importlib.util.spec_from_file_location('research',Path(__file__).with_name('research-popular-chicago-catalogue.py'))
r=importlib.util.module_from_spec(s);s.loader.exec_module(r);core=r.core
SOURCE='popular-chicago-native-catalogue'

def verify(c):
    facts=r.check.metadata(c['source_object'],c['artist_evidence'],c['source_artist'])
    assert all(c[k]==v for k,v in facts.items()),'Pinned metadata differs from the independent source'
    assert c['external_id']==str(c['source_object']['id']) and c['scheme']==r.check.SCHEME
    assert c['page']=='https://www.artic.edu/artworks/'+c['external_id']
    assert c['artist_qid']==c['artist_evidence']['qid'] and c['artist_slug']==c['artist_evidence']['slug']
    receipt=c['metadata_capture']
    # The response checksum is preserved with the citation. Evidence receipts
    # are also pinned transitively by the complete plan checksum.
    assert receipt.get('sha256') and receipt['url'].startswith('https://api.artic.edu/api/v1/artworks?')

def apply(run,target):
    plan=json.loads((run/'plan.json').read_text());records=plan['records']
    assert core.sha((run/'plan.json').read_bytes())==json.loads((run/'plan-manifest.json').read_text())['sha256']
    originals={}
    for c in records:
        verify(c);receipt=c['metadata_capture'];url=receipt['url']
        if url not in originals:
            body=(run/'chicago/object-evidence'/(core.sha(url.encode())+'.json')).read_bytes()
            assert core.sha(body)==receipt['sha256'],'Original source response checksum differs'
            originals[url]={str(o['id']):o for o in json.loads(body)['data']}
        assert originals[url][c['external_id']]==c['source_object'],'Pinned object differs from captured source bytes'
    holding=json.loads((run/'holding-deaccession-check.json').read_text())
    assert not holding['conflicts'],'Museum holding change requires review'
    held_objects={str(o['id']):o for o in holding['records']}
    for c in records:
        o=held_objects[c['external_id']]
        assert 'fiscal_year_deaccession' in o and o['fiscal_year_deaccession'] is None
        assert o['title']==c['title'] and o['main_reference_number']==c['accession_number'] and o['credit_line']==c['source_object']['credit_line']
    dsn='postgres://localhost/artline' if target=='local' else core.cloud_dsn()
    with psycopg.connect(dsn,autocommit=True,row_factory=dict_row) as db:
        with db.transaction():
            db.execute('SET TRANSACTION READ ONLY');state=r.snapshot(db,records)
        selected,held=r.guard.conflicts(records,state)
        pre={'at':core.now(),'state':state,'held':held}
        backup=r.backup_root(run)/(target+'-metadata-preflight-'+core.sha(core.encode(state))[:16]+'.json')
        if backup.exists():
            assert core.encode(json.loads(backup.read_text())['state'])==core.encode(state),'Existing backup differs'
        else:core.save_new(backup,pre)
        if held:raise SystemExit('Target duplicate/version/identity conflicts: '+str(len(held)))
        with db.transaction():
            db.execute("INSERT INTO sources(slug,name,source_type,base_url,terms_url) VALUES(%s,'Art Institute of Chicago: independently verified popular painter catalogue','museum_api','https://api.artic.edu/api/v1/artworks/',%s) ON CONFLICT(slug) DO NOTHING",(SOURCE,r.check.CC0))
            sid=db.execute('SELECT id FROM sources WHERE slug=%s',(SOURCE,)).fetchone()['id']
        iid=state['institution_id'];results=[]
        for start in range(0,len(selected),25):
            group=selected[start:start+25]
            with db.transaction():
                db.execute('SELECT pg_advisory_xact_lock(559220260915)')
                active=[c for c in group if not c['already_present']]
                if active:
                    assert not db.execute("SELECT entity_id FROM external_identifiers WHERE entity_type='artwork' AND ((scheme=ANY(%s) AND external_id=ANY(%s)) OR canonical_url=ANY(%s))",(r.SCHEMES,[c['external_id'] for c in active],[c['page'] for c in active])).fetchall(),'Native identity appeared during import'
                with db.pipeline():
                    for c in group:
                        if c['already_present']:
                            results.append({'artwork_id':c['artwork_id'],'outcome':'already_present'});continue
                        aid=c['artwork_id'];checked=c['metadata_capture']['retrieved_at']
                        db.execute("""INSERT INTO artworks(id,slug,title,normalized_title,date_display,creation_year_start,creation_year_end,date_precision,work_type,medium_text,dimensions_text,current_institution_id,accession_number,status,research_candidate,created_by,updated_by)
                          VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'review',true,%s,%s)""",(aid,c['slug'],c['title'],r.guard.norm(c['title']),c['date_display'],c['creation_year_start'],c['creation_year_end'],c['date_precision'],c['work_type'],c['medium_text'],c['dimensions_text'],iid,c['accession_number'],core.ACTOR,core.ACTOR))
                        db.execute("INSERT INTO artwork_artists(artwork_id,artist_id,attribution_role,attribution_note) VALUES(%s,%s,'primary','Unqualified native museum artist ID and display; name/alias and corroborating life date matched to the existing painter authority.')",(aid,c['target_artist_id']))
                        db.execute("INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at) VALUES('artwork',%s,%s,%s,%s,%s,%s)",(aid,r.check.SCHEME,c['external_id'],c['page'],sid,checked))
                        db.execute("INSERT INTO artwork_location_assertions(artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state) VALUES(%s,'holding',%s,'collection',%s,%s,%s,%s,'accepted')",(aid,iid,sid,c['page'],'Museum collection record, accession '+c['accession_number']+' and acquisition/collection credit: '+c['source_object']['credit_line']+'. No current-display claim.',checked))
                        evidence={'primary_record':c['source_object'],'metadata_capture':c['metadata_capture'],'metadata_license':r.check.CC0,'creator_identity':{'existing_wikidata':c['artist_qid'],'existing_slug':c['artist_slug'],'source_artist':c['source_artist']},'holding_verification':{'object':held_objects[c['external_id']],'checked_at':holding['at']},'date_review':'Original artwork date text and museum interval retained, including abbreviated textual end years when omitted by numeric fields; qualified attribution, lifespan defaults and later impressions held separately.'}
                        db.execute("INSERT INTO citations(entity_type,entity_id,source_id,field_name,source_record_id,source_url,evidence_note,retrieved_at,created_by) VALUES('artwork',%s,%s,'official_object_identity',%s,%s,%s,%s,%s)",(aid,sid,c['external_id'],c['page'],json.dumps(evidence,ensure_ascii=False),checked,core.ACTOR))
                        results.append({'artwork_id':aid,'outcome':'inserted'})
            print(core.now(),target,'Chicago metadata',min(start+25,len(selected)),'/',len(selected),flush=True)
        counts=db.execute("SELECT count(*) n,count(*) FILTER(WHERE status='review' AND published_at IS NULL AND research_candidate AND artline_has_selection_evidence(id)) verified FROM artworks WHERE id=ANY(%s::uuid[])",([c['artwork_id'] for c in records],)).fetchone()
        assert counts['n']==counts['verified']==len(records)
        report=run/(target+'-metadata-verified.json')
        if not report.exists():core.save_new(report,{'at':core.now(),'counts':counts,'records':results,'backup':str(backup)})
        print(target,'verified',counts)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--target',choices=['local','cloud'],default='local');a=p.parse_args();apply(a.run,a.target)
