#!/usr/bin/env python3
"""Enrich uniquely matched existing research candidates from official FSG records.

The supplied catalogue is only an identity lead. All final facts and media are
independently reproducible from the current Smithsonian museum record.
"""
import argparse,collections,importlib.util,json
from pathlib import Path
import psycopg
from psycopg.rows import dict_row
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('fsg_import',ROOT/'ops/import-overnight-fsg-selection.py');imp=importlib.util.module_from_spec(s);s.loader.exec_module(imp);fsg=imp.fsg;core=fsg.core
SOURCE='overnight-fsg-reconciled-primary-20260915'

def rows_for(db,artist_ids):
    return db.execute("""SELECT to_jsonb(a) artwork,
       ARRAY(SELECT aa.artist_id::text FROM artwork_artists aa WHERE aa.artwork_id=a.id) artist_ids,
       ARRAY(SELECT aa.attribution_role FROM artwork_artists aa WHERE aa.artwork_id=a.id) roles,
       ARRAY(SELECT e.external_id FROM external_identifiers e WHERE e.entity_type='artwork' AND e.entity_id=a.id) identifiers,
       EXISTS(SELECT 1 FROM artwork_location_assertions la WHERE la.artwork_id=a.id AND la.review_state='accepted' AND la.superseded_by IS NULL) accepted_location,
       ARRAY(SELECT r.raw_json FROM research_artwork_links l JOIN research_records r ON (r.snapshot_id,r.source_key,r.record_kind,r.source_record_id)=(l.snapshot_id,l.source_key,l.record_kind,l.research_record_id) WHERE l.artwork_id=a.id) research
       FROM artworks a JOIN (SELECT DISTINCT artwork_id FROM artwork_artists WHERE artist_id=ANY(%s::uuid[])) wanted ON wanted.artwork_id=a.id""",(artist_ids,)).fetchall()

def verify_existing(c,row):
    a=row['artwork']
    if a['status']!='review' or not a['research_candidate'] or a['published_at'] is not None:raise ValueError('Existing editorial state differs')
    if a['work_type']!='unknown' or a['primary_media_id'] or a['accession_number'] or a['current_institution_id'] or row['identifiers'] or row['accepted_location']:raise ValueError('Existing object already has independent facts requiring reconciliation')
    if row['artist_ids']!=[c['artist_id']] or row['roles']!=['primary']:raise ValueError('Existing creator identity differs')
    if a['title']!=c['title'] or (a['creation_year_start'],a['creation_year_end'])!=(c['creation_year_start'],c['creation_year_end']):raise ValueError('Existing title or creation interval differs')
    if fsg.norm(a['date_display'].removeprefix('Unverified date: '))!=fsg.norm(c['date_display']):raise ValueError('Supplied creation date differs from official object')
    if a['medium_text'] or a['dimensions_text'] or a['creation_place_display']:raise ValueError('Existing descriptive facts require separate review')
    if len(row['research'])!=1:raise ValueError('Existing research provenance is not unique')
    cells=row['research'][0].get('csv',{}).get('cells',[])
    if len(cells)!=6 or cells[1]!=c['title'] or fsg.norm(cells[2])!=fsg.norm(c['date_display']) or cells[3]!='National Museum of Asian Art':raise ValueError('Supplied candidate does not identify this museum and date')
    names={fsg.norm(v) for v in fsg.creator_variants(cells[0])}
    if not names&{fsg.norm(v) for v in [c['artist']]+c['aliases']}:raise ValueError('Supplied creator differs')

def plan(run,reference):
    if (run/'plan.json').exists():return json.loads((run/'plan.json').read_text())
    leads=json.loads((reference/'source-leads.json').read_text());held_ids={h['source_object_id'] for h in json.loads((reference/'plan.json').read_text())['held']};candidates=[imp.candidate(c) for c in leads if c['source_object_id'] in held_ids]
    # Count all objects in this museum, including records without selected images,
    # before treating any creator/title as a unique physical-object lead.
    names=collections.defaultdict(set)
    for c in candidates:
        for name in [c['artist']]+c['aliases']:names[fsg.norm(name)].add(c['artist_id'])
    source_keys=collections.defaultdict(set)
    for path in (reference/'metadata').glob('*.txt'):
        raw=path.read_bytes();receipt=json.loads(path.with_suffix('.receipt.json').read_text());assert core.sha(raw)==receipt['sha256']
        for line in raw.splitlines():
            o=json.loads(line);ft=o['content'].get('freetext',{});dn=o['content']['descriptiveNonRepeating'];artists=fsg.fields(ft,'name','Artist')
            if len(artists)!=1:continue
            try:variants=fsg.creator_variants(artists[0])
            except ValueError:continue
            matches=set().union(*(names[fsg.norm(v)] for v in variants))
            for aid in matches:source_keys[(aid,fsg.norm(dn.get('title',{}).get('content','')))].add(dn.get('record_ID'))
    with fsg.ro('postgres://localhost/artline') as db:
        rows=rows_for(db,sorted({c['artist_id'] for c in candidates}));iid=db.execute('SELECT id::text FROM institutions WHERE slug=%s',(fsg.SLUG,)).fetchone()['id']
    by_key=collections.defaultdict(list)
    for row in rows:
        for aid in row['artist_ids']:by_key[(aid,fsg.norm(row['artwork']['title']))].append(row)
    selected=[];held=[]
    for c in candidates:
        try:
            key=(c['artist_id'],fsg.norm(c['title']))
            if len(source_keys[key])!=1:raise ValueError('Multiple museum objects share this creator/title')
            hits=by_key[key]
            if len(hits)!=1:raise ValueError('Multiple or absent existing catalogue objects')
            row=hits[0];verify_existing(c,row);old=row['artwork'];c.update(artwork_id=old['id'],slug=old['slug'],target_ids={'local':old['id']},institution_ids={'local':iid},previous_revision=old['revision'],previous_record=row)
            selected.append(c)
        except ValueError as exc:held.append({'source_object_id':c['external_id'],'reason':str(exc)})
    backup=Path.home()/'Library/Application Support/Artline/backups/overnight-images-20260915'/run.name
    core.save_new(backup/'local-selection-preimages.json',[c['previous_record'] for c in selected])
    data={'at':core.now(),'records':selected,'held':held,'policy':'Unique creator/title across the full authoritative museum export; unique existing candidate; supplied museum/date/creator agree. Only independently sourced fields and exact CC0 media become current catalogue facts. Existing artwork IDs and in-review status are preserved.'}
    core.save_new(run/'plan.json',data);core.save_new(run/'plan-manifest.json',{'sha256':core.sha((run/'plan.json').read_bytes()),'count':len(selected)})
    print('FSG existing candidates to verify',len(selected),'popular',sum(c['popular'] for c in selected),'held',dict(collections.Counter(h['reason'] for h in held)),flush=True);return data

def apply(run,target):
    data=json.loads((run/'plan.json').read_text());assert core.sha((run/'plan.json').read_bytes())==json.loads((run/'plan-manifest.json').read_text())['sha256'];records=data['records'];dsn='postgres://localhost/artline' if target=='local' else core.cloud_dsn()
    backup=Path.home()/'Library/Application Support/Artline/backups/overnight-images-20260915'/run.name;out=[]
    with psycopg.connect(dsn,autocommit=True,row_factory=dict_row) as db:
        people=db.execute("SELECT a.id::text,a.slug,e.external_id qid FROM external_identifiers e JOIN artists a ON a.id=e.entity_id WHERE e.entity_type='artist' AND e.scheme='wikidata' AND e.external_id=ANY(%s) AND a.status<>'archived'",(sorted({c['artist_qid'] for c in records}),)).fetchall();pi=collections.defaultdict(list)
        for person in people:pi[person['qid']].append(person)
        iid=db.execute('SELECT id::text FROM institutions WHERE slug=%s',(fsg.SLUG,)).fetchone()['id']
        # Historical supplied candidates and some artists have different UUIDs
        # across targets. Match documented authorities/slugs, never assume UUID parity.
        target_rows=db.execute('SELECT id::text,slug FROM artworks WHERE slug=ANY(%s)',([c['slug'] for c in records],)).fetchall();by_slug=collections.defaultdict(list)
        for row in target_rows:by_slug[row['slug']].append(row)
        mapped=[]
        for c in records:
            assert len(pi[c['artist_qid']])==1 and pi[c['artist_qid']][0]['slug']==c['artist_slug'],'Creator authority or slug differs'
            assert len(by_slug[c['slug']])==1,'Existing candidate slug absent or ambiguous'
            mapped.append(dict(c,artwork_id=by_slug[c['slug']][0]['id'],artist_id=pi[c['artist_qid']][0]['id'],local_artwork_id=c['artwork_id']))
        records=mapped
        snapshot=rows_for(db,sorted({c['artist_id'] for c in records}));index={r['artwork']['id']:r for r in snapshot};preimages=[index[c['artwork_id']] for c in records]
        path=backup/(target+'-apply-preimages.json')
        if not path.exists():core.save_new(path,preimages)
        with db.transaction():
            db.execute("INSERT INTO sources(slug,name,source_type,base_url,terms_url) VALUES(%s,'National Museum of Asian Art: independently verified existing candidates','museum_api','https://asia.si.edu/',%s) ON CONFLICT(slug) DO NOTHING",(SOURCE,fsg.CC0));sid=db.execute('SELECT id FROM sources WHERE slug=%s',(SOURCE,)).fetchone()['id']
        for start in range(0,len(records),20):
            group=records[start:start+20]
            with db.transaction():
                db.execute('SELECT pg_advisory_xact_lock(559220260915)')
                current={r['id']:r for r in db.execute('SELECT id::text,revision,work_type,current_institution_id::text,accession_number,title,date_display,creation_year_start,creation_year_end,date_precision FROM artworks WHERE id=ANY(%s::uuid[]) FOR UPDATE',([c['artwork_id'] for c in group],)).fetchall()}
                for c in group:
                    aid=c['artwork_id'];a=current[aid];fsg.source_match(c,c['raw']['object'])
                    already=db.execute("SELECT entity_id::text FROM external_identifiers WHERE entity_type='artwork' AND scheme='fsg-object' AND external_id=%s",(c['external_id'],)).fetchall()
                    if already:
                        assert len(already)==1 and already[0]['entity_id']==aid and a['current_institution_id']==iid and all(a[k]==c[k] for k in ('accession_number','title','date_display','creation_year_start','creation_year_end','date_precision','work_type'))
                        out.append({'artwork_id':aid,'outcome':'already_verified'});continue
                    verify_existing(c,index[aid]);assert a['revision']==index[aid]['artwork']['revision'],'Concurrent artwork edit requires new review'
                    assert not db.execute('SELECT 1 FROM artworks WHERE current_institution_id=%s AND accession_number=%s',(iid,c['accession_number'])).fetchone()
                    assert not db.execute("SELECT 1 FROM external_identifiers WHERE entity_type='artwork' AND (entity_id=%s OR canonical_url=%s)",(aid,c['page'])).fetchone()
                    assert not db.execute("SELECT 1 FROM slug_redirects WHERE entity_type='artwork' AND (old_slug=%s OR entity_id=%s)",(c['slug'],aid)).fetchone()
                    with db.pipeline():
                        db.execute("UPDATE artworks SET date_display=%s,creation_year_start=%s,creation_year_end=%s,date_precision=%s,work_type=%s,medium_text=%s,dimensions_text=%s,creation_place_display=%s,current_institution_id=%s,accession_number=%s,revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s",(c['date_display'],c['creation_year_start'],c['creation_year_end'],c['date_precision'],c['work_type'],c['medium_text'],c['dimensions_text'],c['creation_place_display'],iid,c['accession_number'],core.ACTOR,aid))
                        db.execute("INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at) VALUES('artwork',%s,'fsg-object',%s,%s,%s,%s)",(aid,c['external_id'],c['page'],sid,c['checked_at']))
                        db.execute("INSERT INTO artwork_location_assertions(artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state) VALUES(%s,'holding',%s,'collection',%s,%s,%s,%s,'accepted')",(aid,iid,sid,c['page'],'Official Smithsonian record and accession '+c['accession_number']+' establish museum holding. No current display claim.',c['checked_at']))
                        evidence={'official_record':c['raw']['object'],'metadata_capture':c['raw']['metadata_capture'],'metadata_license':fsg.CC0,'reconciliation':'Existing supplied creator, title, date and museum lead uniquely to this accessioned object in the complete current museum export. Current catalogue facts are independently supported by the official record; review status remains unchanged.'}
                        db.execute("INSERT INTO citations(entity_type,entity_id,source_id,field_name,source_record_id,source_url,evidence_note,retrieved_at,created_by) VALUES('artwork',%s,%s,'official_object_identity',%s,%s,%s,%s,%s)",(aid,sid,c['external_id'],c['page'],json.dumps(evidence,ensure_ascii=False),c['checked_at'],core.ACTOR))
                    out.append({'artwork_id':aid,'outcome':'verified_existing'})
            print(core.now(),target,'FSG existing metadata',len(out),'of',len(records),flush=True)
        checked=db.execute("SELECT count(*) n,count(*) FILTER(WHERE status='review' AND published_at IS NULL AND research_candidate AND artline_has_selection_evidence(id)) ok FROM artworks WHERE id=ANY(%s::uuid[])",([c['artwork_id'] for c in records],)).fetchone();assert checked['n']==checked['ok']==len(records)
        path=run/(target+'-metadata-verified.json')
        if not path.exists():core.save_new(path,{'at':core.now(),'counts':checked,'records':out})
    if target=='local':
        images=[]
        for c in records:
            image={k:v for k,v in c.items() if k not in ('previous_record','previous_revision')};images.append(image);core.save_new(run/'selected/night-fsg'/(c['artwork_id']+'.json'),image)
        core.save_new(run/'candidates.json',{'created_at':data['at'],'candidates':images,'production_metadata_pending':True})
        for name in ('institution.html','institution.receipt.json'):core.save_new(run/name,(run.parent/'fsg'/name).read_bytes())
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['plan','apply']);p.add_argument('--run',type=Path,required=True);p.add_argument('--reference',type=Path);p.add_argument('--target',choices=['local','cloud'],default='local');a=p.parse_args();a.run.mkdir(parents=True,exist_ok=True)
    if a.phase=='plan':plan(a.run,a.reference or a.run.parent/'fsg')
    else:apply(a.run,a.target)
