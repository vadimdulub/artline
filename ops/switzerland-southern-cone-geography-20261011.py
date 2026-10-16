#!/usr/bin/env python3
"""Apply evidenced city/country placement only to delivered, nonempty museums."""
import importlib.util
import json
import sys
from pathlib import Path

s=importlib.util.spec_from_file_location('d',Path(__file__).with_name('switzerland-southern-cone-delivery-20261011.py'))
d=importlib.util.module_from_spec(s);s.loader.exec_module(d)


def run(phase):
    folder=d.RUN/phase
    assert not (folder/'geography-applied.json').exists()
    plan,digest=d.pinned(phase)
    assert d.load(folder/'applied.json')['plan_sha256']==digest
    assert d.load(d.RUN/'cloud-sql-backup.json')['status']=='SUCCESSFUL'
    registry=d.load(d.RUN/'institution-registry.json')
    for path in d.RUN.glob('institution-registry-wave*.json'):
        registry.update(d.load(path))
    reviewed=[]
    for name,institution in plan['institutions'].items():
        if not any(x['institution_id']==institution['id'] for x in plan['records']):
            continue
        r=registry[name]
        if r.get('directory_id'):
            source=d.ROOT/'docs/research/switzerland-india-museums-20261011' if r['country_code']=='CH' else d.RUN
            directory=d.load(source/r['country_code']/'directory.json.gz')['records']
            entry=next(x for x in directory if x['directory_id']==r['directory_id'])
            detail=d.load(source/r['country_code']/'directory-details'/(r['directory_id']+'.json.gz'))
            assert d.norm(r['city']) in d.norm(entry['locality'])
            evidence=detail['evidence'];url=entry['directory_url'];basis=dict(directory_name=entry['name'],locality=entry['locality'])
        else:
            geo=d.load(d.RUN/'geography-evidence'/(r['slug']+'.json.gz'))
            assert geo['city']==r['city'] and geo['country_code']==r['country_code']
            evidence=geo['evidence'];url=evidence['url'];basis=geo
        assert evidence['status']==200
        reviewed.append(dict(name=name,institution_id=institution['id'],city=r['city'],country=r['country_code'],source_url=url,evidence=evidence,basis=basis))
    d.save(folder/'geography-reviewed.json',reviewed)
    apply_reviewed(phase,reviewed)


def apply_reviewed(phase,reviewed,expected_institutions=None):
    folder=d.RUN/phase
    assert not (folder/'geography-applied.json').exists()
    assert d.load(d.RUN/'cloud-sql-backup.json')['status']=='SUCCESSFUL'
    ids=[x['institution_id'] for x in reviewed]
    with d.connect(True) as db,db.transaction():
        db.execute("SELECT set_config('artline.actor_user_id',%s,true)",(d.ACTOR,))
        db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
        before={x['v']['id']:x['v'] for x in db.execute('SELECT to_jsonb(i) v FROM institutions i WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(ids,))}
        assert len(before)==len(ids)
        if expected_institutions is not None:assert before==expected_institutions,'Concurrent institution drift'
        d.save(d.BACKUP/phase/'geography-before.json.gz',before)
        countries={x['code']:x for x in db.execute('SELECT * FROM countries WHERE code=ANY(%s)',(sorted({x['country'] for x in reviewed}),))}
        d.save(d.BACKUP/phase/'geography-countries-before.json.gz',countries)
        for code in sorted({x['country'] for x in reviewed}-set(countries)):
            definition=d.load(d.RUN/'country-registry.json')[code]
            assert definition['record']['code']==code and definition['evidence']['status']==200
            d.batch_insert(db,'countries',[definition['record']])
        applied=[];preserved=[]
        for row in reviewed:
            institution=before[row['institution_id']]
            assert institution['status']!='archived'
            if institution['place_id']:
                place=db.execute('SELECT country_code FROM places WHERE id=%s',(institution['place_id'],)).fetchone()
                assert place['country_code']==row['country']
                preserved.append(institution['id']);continue
            assert db.execute("SELECT EXISTS(SELECT 1 FROM artworks WHERE current_institution_id=%s AND status<>'archived') yes",(institution['id'],)).fetchone()['yes']
            matches=list(db.execute('SELECT id::text FROM places WHERE country_code=%s AND normalized_name=%s',(row['country'],d.norm(row['city']))))
            assert len(matches)<=1,('Ambiguous city identity',row['city'])
            pid=matches[0]['id'] if matches else d.uid('place/'+row['country']+'/'+d.norm(row['city']))
            if not matches:d.batch_insert(db,'places',[dict(id=pid,name=row['city'],normalized_name=d.norm(row['city']),country_code=row['country'])])
            sid=d.uid('source/geography/'+institution['id'])
            if not db.execute('SELECT id FROM sources WHERE id=%s',(sid,)).fetchone():
                d.batch_insert(db,'sources',[dict(id=sid,slug=d.OP+'-geo-'+institution['id'],name=row['name']+' — institution geography evidence',source_type='collection_page',base_url=row['source_url'],adapter_key=d.OP)])
            db.execute('UPDATE institutions SET place_id=%s,updated_at=now() WHERE id=%s AND place_id IS NULL',(pid,institution['id']))
            d.batch_insert(db,'citations',[dict(id=d.uid('institution-geography/'+institution['id']),entity_type='institution',entity_id=institution['id'],field_name='country_city_location',source_id=sid,source_url=row['source_url'],evidence_note=json.dumps(row,ensure_ascii=False),retrieved_at=row['evidence']['retrieved_at'],created_by=d.ACTOR)])
            applied.append(dict(id=institution['id'],name=institution['name'],place_id=pid,city=row['city'],country=row['country']))
        after=list(db.execute('SELECT i.id::text,i.name,p.name city,p.country_code FROM institutions i JOIN places p ON p.id=i.place_id WHERE i.id=ANY(%s::uuid[])',(ids,)))
        assert len(after)==len(ids)
    d.save(folder/'geography-applied.json',dict(at=d.now(),applied=applied,preserved=preserved,after=after,local_database_changes=0))
    print(json.dumps(dict(phase=phase,cities_linked=len(applied),existing_places_preserved=len(preserved))))


if __name__=='__main__':run(sys.argv[1])
