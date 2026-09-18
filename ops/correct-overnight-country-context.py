#!/usr/bin/env python3
"""Correct two individually reviewed legacy Russian catalogue classifications.

Only this overnight run's new RU relations are replaced. Original source
citations, names, dates, artworks and review status remain intact.
"""
import argparse,importlib.util,json
from pathlib import Path
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('g',Path(__file__).with_name('review-overnight-country-gaps.py'));g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
m=g.m;CORE=m.m.core;RUN=m.x.BASE/'country-context-corrections';SOURCE='overnight-country-context-correction-20260913'

def capture(url,needles):
    path=RUN/'primary-captures'/(CORE.sha(url.encode())+'.html');raw=path.read_bytes();receipt=json.loads(path.with_suffix('.receipt.json').read_text());assert CORE.sha(raw)==receipt['sha256']
    text=BeautifulSoup(raw,'html.parser').get_text(' ',strip=True)
    for needle in needles:assert needle in text,(url,needle)
    return dict(url=url,receipt=receipt,reviewed_facts=needles)

def plan():
    registries,receipts=g.c.museum_rows();nga=registries['nga-constituent']
    evidence=[dict(slug='mikhail-gordeevich-deregus-nga-3913',person_id='3913',country='UA',primary=capture('https://www.nga.gov/artists/3913-mikhail-gordeevich-deregus',['Mikhail Gordeevich Deregus','Ukrainian, born 1904']),context='The exact NGA person record display biography identifies Ukrainian affiliation. Its structured nationality field says Russian. The current NGA artist page independently corroborates the display biography; the legacy structured value is retained in source evidence but no longer used as a cultural classification.'),dict(slug='ahdona-prano-skirutite-nga-3071',person_id='3071',country='LT',primary=capture('https://www.vle.lt/straipsnis/aldona-skirutyte/',['Aldona Skirutytė','lietuvių grafikė']),identity=[capture('https://www.webumenia.sk/autor/9395',['Aldona Skirutytė','Aldona Prano Skirutite','17.05.1932']),capture('https://plus-legacy.cobiss.net/cobiss/si/sl/bib/sikra/46493697',['Skirutyte, Aldona Prano, 1932-'])],context='Individually reviewed identity: NGA Ahdona Prano Skirutite, born 1932, is the documented Aldona Prano Skirutite alias of Aldona Skirutytė. Rare full surname and patronymic, same birth year, museum creator authority aliases and contemporary exhibition catalogue corroborate the name typo. The Lithuanian national encyclopedia explicitly identifies a Lithuanian graphic artist. Original NGA spelling and numeric date fields are preserved; no new Wikidata identifier or exclusive citizenship assertion is made.')]
    baseline={r['row']['slug']:r for r in json.loads((m.x.BASE/'local-artists-baseline.json').read_text())}
    for e in evidence:
        rec=nga[e['person_id']];assert rec['nationality']=='Russian' and not baseline[e['slug']]['countries'];e['nga_record']=rec['raw'];e['nga_receipt']=receipts['nga-constituent']
    targets={}
    for target in ('local','production'):
        with m.m.r.base.connect(target=='production') as db,db.transaction():
            db.execute('SET TRANSACTION READ ONLY');rows=g.c.selected(db,[{'artist':{'slug':e['slug']}} for e in evidence])
            for e in evidence:
                a=rows[e['slug']];assert a['row']['status']=='review' and a['row']['published_at'] is None
                assert {'scheme':'nga-constituent','id':e['person_id']} in a['authorities']
                assert len(a['countries'])==1 and a['countries'][0]['country_code']=='RU' and a['countries'][0]['relationship_type']=='cultural_affiliation'
                assert a['countries'][0]['note'].startswith("nga-constituent source records nationality 'Russian'. Exact source person ID "+e['person_id']+'.')
                assert db.execute("SELECT 1 FROM citations c JOIN sources s ON s.id=c.source_id WHERE c.entity_type='artist' AND c.entity_id=%s AND s.slug='overnight-country-review-20260913'",(a['row']['id'],)).fetchone()
        targets[target]=rows;CORE.save_new(m.BACKUPS/('country-context-'+target+'-preimages.json'),rows)
    for e in evidence:assert g.signature(targets['local'][e['slug']])==g.signature(targets['production'][e['slug']])
    path=RUN/'correction-plan.json';CORE.save_new(path,dict(at=CORE.now(),evidence=evidence,targets=targets));CORE.save_new(RUN/'correction-manifest.json',dict(at=CORE.now(),plan_sha256=CORE.sha(path.read_bytes()),reviewed_corrections=2));print('Country context plan 2',flush=True)

def apply():
    raw=(RUN/'correction-plan.json').read_bytes();pin=json.loads((RUN/'correction-manifest.json').read_text())['plan_sha256'];assert CORE.sha(raw)==pin;data=json.loads(raw)
    for target in ('local','production'):
        dest=RUN/('correction-'+target+'-verified.json')
        if dest.exists():continue
        with m.m.r.base.connect(target=='production') as db:
            with db.transaction():
                db.execute('SELECT pg_advisory_xact_lock(559220260914)');sid=m.m.source(db,SOURCE,'Primary-source review of historical country label conflicts','authority_data','https://www.nga.gov/')
                for e in data['evidence']:
                    old=data['targets'][target][e['slug']];a=db.execute('SELECT to_jsonb(a) row FROM artists a WHERE id=%s FOR UPDATE',(old['row']['id'],)).fetchone()['row']
                    done=db.execute("SELECT 1 FROM citations WHERE entity_type='artist' AND entity_id=%s AND source_id=%s AND field_name='geography' AND evidence_note LIKE %s",(a['id'],sid,'%'+pin+'%')).fetchone()
                    if done:continue
                    assert a==old['row'];countries=[r['row'] for r in db.execute('SELECT to_jsonb(c) row FROM artist_countries c WHERE artist_id=%s',(a['id'],)).fetchall()];assert countries==old['countries']
                    assert db.execute("DELETE FROM artist_countries WHERE artist_id=%s AND country_code='RU' AND relationship_type='cultural_affiliation' AND note=%s",(a['id'],old['countries'][0]['note'])).rowcount==1
                    db.execute("INSERT INTO artist_countries(artist_id,country_code,relationship_type,is_primary,note) VALUES(%s,%s,'cultural_affiliation',false,%s)",(a['id'],e['country'],e['context']))
                    db.execute("UPDATE artists SET geography_review_state='classified',revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s",(m.m.ACTOR,a['id']))
                    m.m.r.base.insert(db,'citations',dict(entity_type='artist',entity_id=a['id'],source_id=sid,field_name='geography',source_record_id=e['person_id'],source_url=e['primary']['url'],retrieved_at=e['primary']['receipt']['retrieved_at'],created_by=m.m.ACTOR,evidence_note=json.dumps(dict(plan_sha256=pin,evidence=e,superseded_relation=old['countries'][0],preservation='Original museum source citation retained; original artist spelling, timeline and review status preserved.'),ensure_ascii=False)))
            checked=[]
            with db.transaction():
                db.execute('SET TRANSACTION READ ONLY')
                for e in data['evidence']:
                    old=data['targets'][target][e['slug']];a=db.execute('SELECT to_jsonb(a) row FROM artists a WHERE id=%s',(old['row']['id'],)).fetchone()['row'];ignored={'geography_review_state','revision','updated_at','updated_by'}
                    assert {k:v for k,v in a.items() if k not in ignored}=={k:v for k,v in old['row'].items() if k not in ignored}
                    countries=db.execute('SELECT country_code FROM artist_countries WHERE artist_id=%s',(a['id'],)).fetchall();assert countries==[{'country_code':e['country']}]
                    checked.append(dict(slug=e['slug'],country=e['country'],status=a['status']))
        CORE.save_new(dest,dict(at=CORE.now(),plan_sha256=pin,verified=checked));print(target,'country context corrections verified',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['plan','apply']);a=p.parse_args();globals()[a.command]()
