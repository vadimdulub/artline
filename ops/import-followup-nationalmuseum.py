#!/usr/bin/env python3
"""Idempotently import reviewed official painting facts, preserving editorial review."""
import argparse,importlib.util,json
from pathlib import Path
import psycopg
from psycopg.rows import dict_row

ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('nationalmuseum',ROOT/'ops/followup-nationalmuseum-images.py')
nm=importlib.util.module_from_spec(s);s.loader.exec_module(nm);core=nm.core

def apply(run,target,limit):
    assert (run.parent/'backups.json').exists()
    data=json.loads((run/'plan.json').read_text());assert core.sha((run/'plan.json').read_bytes())==json.loads((run/'plan-manifest.json').read_text())['sha256']
    records=data['records'][:limit] if limit else data['records'];dsn='postgres://localhost/artline' if target=='local' else core.cloud_dsn()
    backup=Path.home()/'Library/Application Support/Artline/backups'/run.parent.name/run.name
    ids=[r['targets'][target]['artwork_id'] for r in records]
    with nm.util.ro(dsn) as db:
        pre=db.execute('SELECT to_jsonb(a) artwork FROM artworks a WHERE id=ANY(%s::uuid[])',(ids,)).fetchall()
        backup_path=backup/(target+('-canary' if limit else '')+'-artwork-preimages.json')
        if not backup_path.exists():core.save_new(backup_path,pre)
    out=[];planned_by_id={r['targets'][target]['artwork_id']:r for r in data['records']}
    with psycopg.connect(dsn,autocommit=True,row_factory=dict_row) as db:
        sid=None
        # Resume by checking a bounded ID set once, rather than repeating every
        # already committed metadata write and its dependent network queries.
        completed=db.execute("""SELECT a.id::text,a.title,a.accession_number,a.date_display,a.creation_year_start,a.creation_year_end,a.date_precision,a.work_type,a.status,
            a.current_institution_id::text,e.external_id,
            ARRAY(SELECT aa.artist_id::text FROM artwork_artists aa WHERE aa.artwork_id=a.id) artist_ids
            FROM artworks a JOIN external_identifiers e ON e.entity_type='artwork' AND e.entity_id=a.id AND e.scheme=%s
            WHERE a.id=ANY(%s::uuid[]) AND EXISTS(SELECT 1 FROM citations c JOIN sources s ON s.id=c.source_id WHERE c.entity_type='artwork' AND c.entity_id=a.id AND c.field_name='official_object_identity' AND s.slug=%s)
            AND EXISTS(SELECT 1 FROM artwork_location_assertions l WHERE l.artwork_id=a.id AND l.institution_id=a.current_institution_id AND l.claim_type='holding' AND l.review_state='accepted' AND l.superseded_by IS NULL)""",(nm.SCHEME,ids,nm.SOURCE)).fetchall()
        done={}
        for old in completed:
            r=planned_by_id[old['id']];t=r['targets'][target]
            assert old['status']=='review' and old['external_id']==r['external_id'] and old['current_institution_id']==t['institution_id'] and old['artist_ids']==[t['artist_id']]
            assert all(old[k]==r[k] for k in ('title','accession_number','date_display','creation_year_start','creation_year_end','date_precision','work_type'))
            assert old['id'] not in done;done[old['id']]=old
        for r in records:
            facts=nm.fact_check(r['raw']['lead'],r['raw']['official_capture'])
            assert all(r[k]==v for k,v in facts.items());t=r['targets'][target];oid=r['external_id'];aid=t['artwork_id'];iid=t['institution_id'];page=r['page'];at=r['raw']['official_capture']['retrieved_at']
            if aid in done:
                out.append({'artwork_id':aid,'outcome':'already_present','source_object_id':oid});continue
            with db.transaction(),db.pipeline():
                db.execute("SET LOCAL lock_timeout='5s'")
                db.execute('SELECT pg_advisory_xact_lock(559220260915)')
                inst=db.execute("SELECT i.id::text,p.country_code FROM institutions i JOIN places p ON p.id=i.place_id WHERE i.slug='nationalmuseum-stockholm' AND i.status<>'archived'").fetchone()
                assert inst and inst['id']==iid and inst['country_code']=='SE'
                artist=db.execute("SELECT id::text,slug,display_name,birth_year,death_year FROM artists WHERE id=%s AND status<>'archived'",(t['artist_id'],)).fetchone()
                sourceartist=r['raw']['lead']['artist']
                assert artist and all(artist[k]==sourceartist[k] for k in ('slug','display_name','birth_year','death_year'))
                qids=db.execute("SELECT external_id FROM external_identifiers WHERE entity_type='artist' AND entity_id=%s AND scheme='wikidata'",(t['artist_id'],)).fetchall()
                if r['artist_qid']:assert r['artist_qid'] in [q['external_id'] for q in qids]
                else:assert not qids,'Creator authority changed since the exact source name and life-date check'
                current=db.execute("SELECT id::text,title,status,accession_number,date_display,creation_year_start,creation_year_end,date_precision,work_type,current_institution_id::text FROM artworks WHERE id=%s FOR UPDATE",(aid,)).fetchone()
                if current:
                    assert current['status']=='review' and current['current_institution_id']==iid and all(current[k]==r[k] for k in ('title','accession_number','date_display','creation_year_start','creation_year_end','date_precision','work_type'))
                else:
                    assert t['mode']=='new'
                    assert not db.execute("SELECT 1 FROM external_identifiers WHERE entity_type='artwork' AND ((scheme=%s AND external_id=%s) OR (scheme='wikidata' AND external_id=%s) OR canonical_url=%s)",(nm.SCHEME,oid,r['qid'],page)).fetchone(),'Existing native or Wikidata object identity'
                    assert not db.execute('SELECT 1 FROM artworks WHERE current_institution_id=%s AND accession_number=%s',(iid,r['accession_number'])).fetchone(),'Museum accession collision'
                    same_titles=db.execute("SELECT a.id::text,a.accession_number FROM artworks a JOIN artwork_artists aa ON aa.artwork_id=a.id WHERE aa.artist_id=%s AND lower(a.title)=lower(%s)",(t['artist_id'],r['title'])).fetchall()
                    for other in same_titles:
                        known=planned_by_id.get(other['id'])
                        assert known and known['external_id']!=oid and other['accession_number']==known['accession_number']!=r['accession_number'],'Same artist/title requires separate physical-object evidence'
                        assert db.execute("SELECT 1 FROM external_identifiers WHERE entity_type='artwork' AND entity_id=%s AND scheme=%s AND external_id=%s",(other['id'],nm.SCHEME,known['external_id'])).fetchone(),'Distinct current museum identifiers required'
                    assert not db.execute("SELECT 1 FROM slug_redirects WHERE entity_type='artwork' AND (old_slug=%s OR entity_id=%s)",(t['slug'],aid)).fetchone()
                    db.execute("""INSERT INTO artworks(id,slug,title,normalized_title,date_display,creation_year_start,creation_year_end,date_precision,work_type,medium_text,current_institution_id,accession_number,status,research_candidate,created_by,updated_by)
                        VALUES(%s,%s,%s,%s,%s,%s,%s,%s,'painting',%s,%s,%s,'review',true,%s,%s)""",
                        (aid,t['slug'],r['title'],nm.norm(r['title']),r['date_display'],r['creation_year_start'],r['creation_year_end'],r['date_precision'],r['medium'],iid,r['accession_number'],core.ACTOR,core.ACTOR))
                    db.execute("INSERT INTO artwork_artists(artwork_id,artist_id,attribution_role,attribution_note) VALUES(%s,%s,'primary','Single current unqualified museum artist; source name, lifespan and existing authority independently reconciled.')",(aid,t['artist_id']))
                if sid is None:
                    db.execute("INSERT INTO sources(slug,name,source_type,base_url,terms_url) VALUES(%s,'Nationalmuseum: current official painting records','collection_page',%s,%s) ON CONFLICT(slug) DO NOTHING",(nm.SOURCE,nm.HOST,'https://github.com/NationalmuseumSWE/WikidataCollection/blob/master/license.md'))
                    sid=db.execute('SELECT id FROM sources WHERE slug=%s',(nm.SOURCE,)).fetchone()['id']
                for scheme,value,url in [(nm.SCHEME,oid,page)]+([('wikidata',r['qid'],'https://www.wikidata.org/wiki/'+r['qid'])] if r['qid'] else []):
                    existing=db.execute("SELECT entity_id::text FROM external_identifiers WHERE entity_type='artwork' AND scheme=%s AND external_id=%s",(scheme,value)).fetchall()
                    if existing:assert len(existing)==1 and existing[0]['entity_id']==aid
                    else:db.execute("INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at) VALUES('artwork',%s,%s,%s,%s,%s,%s)",(aid,scheme,value,url,sid,at))
                holding=db.execute("SELECT institution_id::text,review_state FROM artwork_location_assertions WHERE artwork_id=%s AND claim_type='holding' AND superseded_by IS NULL",(aid,)).fetchall()
                if holding:assert len(holding)==1 and holding[0]['institution_id']==iid and holding[0]['review_state']=='accepted','Current institutional holding differs'
                else:
                    db.execute("INSERT INTO artwork_location_assertions(artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state) VALUES(%s,'holding',%s,'collection',%s,%s,%s,%s,'accepted')",(aid,iid,sid,page,'Official Nationalmuseum painting collection and accession '+r['accession_number']+'. Institution country Sweden. No current display assertion.',at))
                if not db.execute("SELECT 1 FROM citations WHERE entity_type='artwork' AND entity_id=%s AND source_id=%s AND field_name='official_object_identity'",(aid,sid)).fetchone():
                    evidence={'official_url':page,'source_object_id':oid,'source_page_sha256':r['raw']['official_capture']['sha256'],
                        'facts':facts,'artist_source_id':r['source_artist_id'],'museum':'Nationalmuseum','museum_country':'SE',
                        'discovery_metadata_license':nm.CC0,'discovery_source':'https://github.com/NationalmuseumSWE/WikidataCollection',
                        'facts_verified_against_current_page_at':at,'date_policy':'Original date wording retained with source-provided bounds; no dates inferred from the creator lifespan.',
                        'image_rights_status':r['image_license'][1] if r['image_url'] else 'rights_unresolved',
                        'image_license_url':r['image_license'][0] if r['image_url'] else None,
                        'institution_responsibility_evidence':r['raw']['official_capture']['holding_administration_evidence']}
                    db.execute("INSERT INTO citations(entity_type,entity_id,source_id,field_name,source_record_id,source_url,evidence_note,retrieved_at,created_by) VALUES('artwork',%s,%s,'official_object_identity',%s,%s,%s,%s,%s)",(aid,sid,oid,page,json.dumps(evidence,ensure_ascii=False),at,core.ACTOR))
                out.append({'artwork_id':aid,'outcome':'already_present' if current else 'inserted','source_object_id':oid})
            if len(out)%50==0:print(core.now(),target,'Nationalmuseum imported',len(out),'of',len(records),flush=True)
        rows=db.execute("SELECT count(*) n,count(*) FILTER(WHERE status='review' AND published_at IS NULL AND artline_has_selection_evidence(id) AND artline_creation_scope(creation_year_start,creation_year_end,date_precision)='eligible') ok FROM artworks WHERE id=ANY(%s::uuid[])",(ids,)).fetchone()
        assert rows['n']==rows['ok']==len(records)
    result_path=run/(target+'-metadata-verified'+('-canary' if limit else '')+'.json')
    if not result_path.exists():core.save_new(result_path,{'at':core.now(),'records':out,'counts':rows})
    print(target,'Nationalmuseum metadata verified',rows,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--target',choices=['local','cloud'],required=True);p.add_argument('--limit',type=int,default=0);a=p.parse_args();apply(a.run,a.target,a.limit)
