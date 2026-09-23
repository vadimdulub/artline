#!/usr/bin/env python3
"""Separate six verified homonyms; preserve prior catalogue records and images."""
import argparse,csv,importlib.util,json,os,uuid
from pathlib import Path
s=importlib.util.spec_from_file_location('uk',Path(__file__).with_name('uk-painters-20260920.py'))
u=importlib.util.module_from_spec(s);s.loader.exec_module(u)
m,RUN=u.m,u.RUN
COR=RUN/'identity-corrections'
QIDS=['Q12060389','Q445433','Q456083','Q56600514','Q98765809','Q97948829']

def read(p):return json.loads(p.read_bytes())

def plan():
    original=read(RUN/'authority-plan.json')
    selected=[]
    nga_path=u.ROOT/'content/imports/nga-catalogue-20260909/constituents.csv'
    nga={r['constituentid']:r for r in csv.DictReader(nga_path.open())}
    baseline={r['record']['id']:r for r in read(RUN/'artist-baseline.json')['artists']}
    for old in original['selected']:
        if old['qid'] not in QIDS:continue
        q=old['qid'];e=read(Path(old['capture']))['entity'];birth=u.life(e,'P569');death=u.life(e,'P570')
        b=birth['first'] if birth else None;d=death['first'] if death else None
        artist=dict(id=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.local/wikimedia-catalogue/artist/'+q)),slug='wikimedia-painter-'+q.lower(),display_name=u.label(e),sort_name=u.label(e),normalized_name=m.norm(u.label(e)),entity_type='person',birth_year=b,death_year=d,birth_display=birth['display'] if birth else None,death_display=death['display'] if death else None,birth_precision=birth['precision'] if birth else None,death_precision=death['precision'] if death else None,timeline_start_year=b if b is not None else d,timeline_end_year=d if d is not None else b,timeline_display=(birth['display'] if birth else '?')+'–'+(death['display'] if death else '?'),timeline_basis='life',status='review',created_by=u.ACTOR,updated_by=u.ACTOR)
        if b is None and d is None:
            activity=u.source_activity(e);assert activity
            artist.update(activity)
        previous=baseline[old['artist']['id']]
        native=[nga[v['external_id']] for v in previous['identifiers'] if v['scheme']=='nga-constituent']
        evidence={'source_capture':old['capture'],'capture_sha256':m.core.sha(Path(old['capture']).read_bytes()),'previous_catalogue':previous,'nga_constituents':native,'nga_file':str(nga_path),'nga_sha256':m.core.sha(nga_path.read_bytes())}
        if q=='Q97948829':
            tate=Path('/tmp/artline-uk-tate-jones.json');raw=tate.read_bytes();data=json.loads(raw);assert data['id']==2221
            u.save(COR/'sources/tate-jones-2221.json',raw)
            evidence.update(tate_capture=str(COR/'sources/tate-jones-2221.json'),tate_sha256=m.core.sha(raw),tate_source='https://raw.githubusercontent.com/tategallery/collection/master/artists/j/jones-william-2221.json',getty_source='https://www.getty.edu/vow/ULANFullDisplay?find=jean+nicolas+louis+durand&nation=&role=&subjectid=500011006',activity_basis='Wikidata P2031/P2032: 1764–1777, corroborated by Getty ULAN 500011006 / RKD 118201. The shorter free-text source description is retained in the capture, not treated as a lifespan.')
        selected.append(dict(old,artist=artist,action='new',old_artist_id=old['artist']['id'],identity_basis='Separate source identity after native museum chronology and authority review',correction_evidence=evidence))
    assert len(selected)==6
    u.save(COR/'plan.json',{'selected':selected,'basis':'Five NGA namesakes have incompatible historical/native identity context. William Jones of Bath is separate from Tate 2221. Only this campaign source assertions and its newly created artwork links are reassigned.'})
    print('Planned identity corrections',[(v['name'],v['artist']['timeline_display']) for v in selected],flush=True)

def replace_receipt(path,updated,archive):
    if read(path)==updated:return
    if not archive.exists():u.save(archive,path.read_bytes())
    tmp=path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp')
    u.save(tmp,updated);os.replace(tmp,path)

def snapshot(db,aid):
    result={'artist':db.execute('SELECT to_jsonb(a) record FROM artists a WHERE id=%s',(aid,)).fetchone()}
    for key,table,where in [('identifiers','external_identifiers',"entity_type='artist' AND entity_id=%s"),('citations','citations',"entity_type='artist' AND entity_id=%s"),('countries','artist_countries','artist_id=%s'),('aliases','artist_aliases','artist_id=%s'),('artwork_links','artwork_artists','artist_id=%s')]:
        result[key]=[v['record'] for v in db.execute('SELECT to_jsonb(t) record FROM '+table+' t WHERE '+where,(aid,)).fetchall()]
    return result

def apply():
    planned=read(COR/'plan.json')['selected']
    index=read(RUN/'selected-museum/catalogue-index.json')['selected']
    collection=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.local/personal-artwork-collection'))
    for target,dsn in [('local','postgres://localhost/artline'),('cloud',m.core.cloud_dsn())]:
        with m.psycopg.connect(dsn,autocommit=True,row_factory=m.dict_row) as db:
            sid=u.source(db)
            for item in planned:
                q=item['qid'];old_id=item['old_artist_id'];new_id=item['artist']['id']
                marker=COR/'applied'/target/(q+'.json')
                if marker.exists():continue
                receipt_path=RUN/'authorities-applied'/target/(q+'.json')
                backup=m.BACKUP/'identity-corrections'/target/(q+'.json')
                archive=m.BACKUP/'identity-corrections/previous-authorities'/target/(q+'.json')
                prior=read(archive if archive.exists() else receipt_path)
                assert not prior['created']
                assert prior['after']['slug']==item['correction_evidence']['previous_catalogue']['record']['slug']
                old_id=prior['artist_id']
                original_backup=read(Path(prior['backup']))
                before=next(v['before'] for v in original_backup['selected'] if v['item']['qid']==q)
                assert {(v['scheme'],v['external_id']) for v in before['identifiers']}=={(v['scheme'],v['external_id']) for v in item['correction_evidence']['previous_catalogue']['identifiers']}
                works=[]
                for rec in index:
                    path=RUN/'museum-applied'/target/(rec['qid']+'.json')
                    if rec['creator_qid']!=q or not path.exists():continue
                    old_path=m.BACKUP/'identity-corrections/previous-artworks'/target/path.name
                    receipt=read(old_path if old_path.exists() else path)
                    assert receipt['created'] and receipt['artist_id']==old_id
                    works.append((path,receipt,old_path))
                with db.transaction():
                    db.execute("SET LOCAL lock_timeout='15s'")
                    db.execute('SELECT id FROM curated_collections WHERE id=%s FOR UPDATE',(collection,))
                    db.execute('SELECT id FROM artists WHERE id=ANY(%s::uuid[]) FOR UPDATE',([old_id,new_id],))
                    current=snapshot(db,old_id);new_current=snapshot(db,new_id)
                    assert current['artist']['record']==prior['after'],'Old profile changed outside this campaign'
                    if not backup.exists():u.save(backup,{'old':current,'new':new_current,'plan':item,'previous_authority_receipt':prior,'artwork_receipts':[v[1] for v in works]})
                    saved=read(backup)
                    if not new_current['artist']:
                        assert not db.execute('SELECT id FROM artists WHERE slug=%s',(item['artist']['slug'],)).fetchone()
                        u.w.base.insert(db,'artists',item['artist'])
                    else:
                        assert all(new_current['artist']['record'][k]==v for k,v in item['artist'].items()),'Conflicting target profile'
                    identity=db.execute("SELECT to_jsonb(e) record FROM external_identifiers e WHERE entity_type='artist' AND scheme='wikidata' AND external_id=%s FOR UPDATE",(q,)).fetchall()
                    assert len(identity)==1 and identity[0]['record']['entity_id'] in (old_id,new_id) and identity[0]['record']['source_id']==str(sid)
                    db.execute("UPDATE external_identifiers SET entity_id=%s WHERE entity_type='artist' AND scheme='wikidata' AND external_id=%s",(new_id,q))
                    e=read(Path(item['capture']))['entity']
                    for lang,value in e.get('labels',{}).items():
                        db.execute("INSERT INTO artist_aliases(artist_id,alias,normalized_alias,language_code,alias_type) VALUES(%s,%s,%s,%s,'alternate') ON CONFLICT DO NOTHING",(new_id,value['value'],m.norm(value['value']),lang))
                    # Shared names remain valid aliases. The nineteenth-century
                    # middle name is specifically invalid on the old engraver.
                    if q=='Q12060389':
                        assert 'William Brassey Hole' not in item['correction_evidence']['previous_catalogue']['aliases']
                        db.execute("DELETE FROM artist_aliases WHERE artist_id=%s AND alias='William Brassey Hole' AND language_code='fr' AND alias_type='alternate'",(old_id,))
                    relationship=item['country_relationships'][0]
                    baseline_country=any(v['country_code']=='GB' and v['relationship_type']==relationship for v in before['countries'])
                    if not baseline_country:
                        country=db.execute("SELECT to_jsonb(ac) record FROM artist_countries ac WHERE artist_id=%s AND country_code='GB' AND relationship_type=%s",(old_id,relationship)).fetchone()
                        if country:
                            assert country['record']['note'].startswith('Source description: '+item['source_description'])
                            db.execute("DELETE FROM artist_countries WHERE artist_id=%s AND country_code='GB' AND relationship_type=%s",(old_id,relationship))
                    db.execute("INSERT INTO artist_countries(artist_id,country_code,relationship_type,is_primary,note) VALUES(%s,'GB',%s,false,%s) ON CONFLICT DO NOTHING",(new_id,relationship,'Source affiliation retained on the separately reconciled UK authority '+q+'. See identity correction citation.'))
                    cid=str(uuid.uuid5(uuid.NAMESPACE_URL,u.SOURCE+'/authority/'+q))
                    db.execute("UPDATE citations SET entity_id=%s WHERE id=%s AND entity_type='artist' AND entity_id IN (%s,%s)",(new_id,cid,old_id,new_id))
                    correction_id=str(uuid.uuid5(uuid.NAMESPACE_URL,u.SOURCE+'/identity-correction/'+q))
                    if not db.execute('SELECT id FROM citations WHERE id=%s',(correction_id,)).fetchone():
                        u.w.base.insert(db,'citations',dict(id=correction_id,entity_type='artist',entity_id=new_id,source_id=sid,field_name='homonym_identity_corrected',source_record_id=q,source_url='https://www.wikidata.org/wiki/'+q,evidence_note=json.dumps(item['correction_evidence']),retrieved_at=m.core.now(),created_by=u.ACTOR))
                    for path,receipt,old_path in works:
                        aid=receipt['artwork_id'];actual=db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE id=%s FOR UPDATE',(aid,)).fetchone()['record'];assert actual==receipt['after']
                        links=db.execute('SELECT artist_id::text,attribution_role FROM artwork_artists WHERE artwork_id=%s',(aid,)).fetchall()
                        assert len(links)==1 and links[0]['artist_id'] in (old_id,new_id) and links[0]['attribution_role']=='primary'
                        db.execute('UPDATE artwork_artists SET artist_id=%s WHERE artwork_id=%s AND artist_id=%s',(new_id,aid,old_id))
                    after=snapshot(db,old_id);new_after=snapshot(db,new_id)
                    moved_ids={v[1]['artwork_id'] for v in works}
                    assert after['artist']==saved['old']['artist']
                    assert sorted(after['artwork_links'],key=lambda v:v['artwork_id'])==sorted([v for v in saved['old']['artwork_links'] if v['artwork_id'] not in moved_ids],key=lambda v:v['artwork_id'])
                    assert all(v in after['identifiers'] for v in before['identifiers'])
                    assert all(v in after['countries'] for v in before['countries'])
                digest=m.core.sha(backup.read_bytes())
                u.save(archive,m.core.encode(prior))
                updated=dict(prior,artist_id=new_id,created=True,after=new_after['artist']['record'],backup=str(backup),backup_sha256=digest,previous_receipt=str(archive),previous_receipt_sha256=m.core.sha(archive.read_bytes()),identity_correction=str(marker))
                replace_receipt(receipt_path,updated,archive)
                for path,receipt,old_path in works:
                    u.save(old_path,m.core.encode(receipt))
                    updated=dict(receipt,artist_id=new_id,backup=str(backup),backup_sha256=digest,previous_receipt=str(old_path),previous_receipt_sha256=m.core.sha(old_path.read_bytes()),identity_correction=str(marker))
                    replace_receipt(path,updated,old_path)
                u.save(marker,{'qid':q,'old_artist_id':old_id,'new_artist_id':new_id,'old_after':after,'new_after':new_after,'artworks_reassigned':sorted(moved_ids),'backup':str(backup),'backup_sha256':digest})
                print('Separated homonym',target,q,'artworks',len(works),flush=True)

def recover_delivery():
    """Recover committed batch receipts lost when the earlier process stopped."""
    selected={v['qid'] for v in read(RUN/'selected-museum/catalogue-index.json')['selected']}
    for target,dsn in [('local','postgres://localhost/artline'),('cloud',m.core.cloud_dsn())]:
        pending=selected-{p.stem for p in (RUN/'museum-applied'/target).glob('*.json')}-{p.stem for p in (RUN/'museum-held'/target).glob('*.json')}
        with m.read_only(dsn) as db:
            current={r['external_id']:r['record'] for r in db.execute("SELECT e.external_id,to_jsonb(a) record FROM external_identifiers e JOIN artworks a ON e.entity_type='artwork' AND e.entity_id=a.id WHERE e.scheme='wikidata' AND e.external_id=ANY(%s)",(list(pending),)).fetchall()}
            print('Interrupted delivery audit',target,'pending',len(pending),'existing',len(current),flush=True)
            missing=set(current)
            for backup in sorted((m.BACKUP/'museum-artworks'/target).glob('*.json')):
                if not missing:break
                data=read(backup)
                for entry in data['selected']:
                    rec=entry['item']['record'];q=rec['qid']
                    if q not in missing:continue
                    actual=current[q];aid=entry['artwork_id'];artist_id=entry['artist']['id'] if entry['artist'] else None
                    assert actual['id']==aid and actual['primary_media_id']==(entry['media_id'] or (entry['before'] or {}).get('primary_media_id'))
                    if entry['before']:
                        assert all(actual[k]==v for k,v in entry['before'].items() if k not in ('primary_media_id','revision','updated_at','updated_by'))
                    else:
                        assert actual['title']==rec['title'] and actual['status']=='review' and actual['research_candidate'] and actual['current_institution_id'] is None
                        assert (actual['creation_year_start'],actual['creation_year_end'])==(rec['date']['first'],rec['date']['last'])
                    links=db.execute('SELECT artist_id::text,attribution_role FROM artwork_artists WHERE artwork_id=%s',(aid,)).fetchall()
                    assert links==([{'artist_id':artist_id,'attribution_role':'primary'}] if artist_id else [])
                    if entry['media_id']:
                        media=db.execute('SELECT checksum_sha256,byte_size FROM media_assets WHERE id=%s',(entry['media_id'],)).fetchone()
                        assert media['checksum_sha256']==entry['image']['sha256'] and media['byte_size']==entry['image']['bytes']<=100000
                    u.save(RUN/'museum-applied'/target/(q+'.json'),{'qid':q,'artwork_id':aid,'artist_id':artist_id,'created':entry['before'] is None,'image_attached':bool(entry['media_id']),'media_id':entry['media_id'],'after':actual,'backup':str(backup),'backup_sha256':m.core.sha(backup.read_bytes()),'at':m.core.now(),'recovered_committed_receipt':True})
                    missing.remove(q)
            # Existing independently created works are left to ordinary source
            # reconciliation; only a matching saved batch is recovered here.
            print('Recovered committed receipts',target,len(current)-len(missing),'other existing source records',len(missing),flush=True)

def verify_public():
    checks=[]
    for path in sorted((COR/'applied/cloud').glob('*.json')):
        correction=read(path)
        for aid in correction['artworks_reassigned']:
            url='https://artline-web-lpuqqlugnq-ew.a.run.app/api/backend/v1/atlas/artworks/'+aid
            response=m.requests.get(url,timeout=(15,45));response.raise_for_status();body=response.json()
            assert [(v['id'],v['role']) for v in body['creators']]==[(correction['new_artist_id'],'primary')]
            assert body['status']=='review'
            checks.append({'artwork_id':aid,'url':url,'checked_at':m.core.now(),'creators':body['creators'],'media_url':body['media_url'],'http_status':response.status_code})
    assert len(checks)==8
    u.save(COR/'public-verification.json',{'checks':checks,'errors':[]})
    print('Corrected artwork identities verified through live API',len(checks),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['plan','apply','recover_delivery','verify_public']);args=p.parse_args();globals()[args.phase]()
