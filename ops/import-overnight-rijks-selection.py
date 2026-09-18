#!/usr/bin/env python3
"""Select exact licensed Rijks paintings, then import their independent metadata."""
import argparse,collections,concurrent.futures,importlib.util,json,re,time
from pathlib import Path
import psycopg
from psycopg.rows import dict_row
ROOT=Path(__file__).resolve().parents[1]
def module(name,file):
    s=importlib.util.spec_from_file_location(name,ROOT/'ops'/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
rijks=module('rijks_selection_adapter','overnight-rijks-images.py');guard=module('rijks_import_guard','import-overnight-met-selection.py');core=rijks.core
SOURCE='overnight-rijks-selected-primary-20260915';INSTITUTION='rijksmuseum'

def prepare(run,deadline):
    rows=[json.loads(p.read_text()) for p in (run/'verified').glob('*.json')];rows.sort(key=lambda c:(not c['popular'],c['artist'],c['title']))
    with rijks.ro('postgres://localhost/artline') as db:
        authorities=db.execute("SELECT entity_id::text,scheme,external_id FROM external_identifiers WHERE entity_type='artist' AND entity_id=ANY(%s::uuid[]) AND scheme IN ('wikidata','rijks-person')",(list({c['artist_id'] for c in rows}),)).fetchall()
    by_artist=collections.defaultdict(dict)
    for a in authorities:by_artist[a['entity_id']][a['scheme']]=a['external_id']
    expected_persons=collections.defaultdict(set)
    for c in rows:expected_persons[c['artist_id']].update(c['rijks_people'])
    def stripe(items):
        f=core.Fetcher(run/'metadata/night-rijks');counts=collections.Counter()
        for c in items:
            if time.time()>=deadline:return counts
            dest=run/'rights-verified'/(c['external_id']+'.json');held=run/'image-selection-held'/(c['external_id']+'.json')
            if dest.exists() or held.exists():continue
            try:
                authority=by_artist[c['artist_id']];qid=authority.get('wikidata');pid=c['rijks_people'][0]
                if not qid:raise ValueError('Existing creator Wikidata authority missing')
                if len(expected_persons[c['artist_id']])!=1:raise ValueError('Multiple museum person IDs need authority reconciliation')
                if authority.get('rijks-person') not in (None,pid):raise ValueError('Existing museum person authority conflicts')
                if not authority.get('rijks-person') and qid not in c['artist_qids']:raise ValueError('New museum creator relation lacks exact authority equivalence')
                if c['artist_qids'] and c['artist_qids']!=[qid]:raise ValueError('Museum creator Wikidata equivalence conflicts')
                years=[int(v) for v in re.findall(r'\d{4}',c['date_display'])]
                if c['date_precision'] in ('exact','range') and (min(years),max(years))!=(c['creation_year_start'],c['creation_year_end']):raise ValueError('Textual and structured creation dates conflict')
                if c['date_precision'] in ('circa','circa_range') and not c['creation_year_start']<=min(years)<=max(years)<=c['creation_year_end']:raise ValueError('Approximate source date outside normalized interval')
                url='https://data.rijksmuseum.nl/'+c['external_id']+'?_profile=la-framed';key=core.sha(url.encode())
                for suffix in ('.json','.receipt.json'):
                    source=run/'fresh-api'/(key+suffix);target=f.cache/(key+suffix)
                    if not target.exists():core.save_new(target,source.read_bytes())
                im=rijks.image_record(c,f,{},{} )
                if not im:raise ValueError('Exact image lacks an approved reusable rights statement')
                qids={x.get('id','').rstrip('/').rsplit('/',1)[-1] for x in c['object'].get('equivalent',[]) if 'wikidata.org/' in x.get('id','')}
                if len(qids)>1:raise ValueError('Multiple object cross-references require identity review')
                im.update(artist_qid=qid,qid=next(iter(qids),None),source_metadata_capture=c['metadata_capture'],artist_slug=c['artist_slug'],artist_slugs=[c['artist_slug']],alternate_title='; '.join(c['alternate_titles']) or None)
                core.save_new(dest,im);counts['rights_verified']+=1
            except ValueError as exc:core.save_new(held,{'at':core.now(),'source_object_id':c['external_id'],'reason':str(exc)});counts['held']+=1
            except Exception as exc:
                with core.LOCK:
                    with (run/'image-selection-errors.jsonl').open('a') as out:out.write(json.dumps({'at':core.now(),'source_object_id':c['external_id'],'error':str(exc)[:250]})+'\n')
                counts['retryable_error']+=1
            if sum(counts.values())%25==0:print(core.now(),'Rijks metadata/rights',dict(counts),flush=True)
        return counts
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:results=[job.result() for job in [pool.submit(stripe,rows[n::3]) for n in range(3)]]
    print(core.now(),'Rijks image selection complete',dict(sum(results,collections.Counter())),flush=True)

def plan(run):
    if (run/'plan.json').exists():return json.loads((run/'plan.json').read_text())
    rows=[json.loads(p.read_text()) for p in (run/'rights-verified').glob('*.json')];rows.sort(key=lambda c:(not c['popular'],c['artist'],c['title']))
    with rijks.ro('postgres://localhost/artline') as db:state=guard.snapshot(db,rows,INSTITUTION,['rijks-object','european-rijks-object']);selected,held=guard.conflicts(rows,state)
    selected=[c for c in selected if not c['already_present']]
    for c in selected:
        for key in ('target_artist_id','already_present'):c.pop(key,None)
        c['institution_ids']={'local':state['institution_id']}
    backup=Path.home()/'Library/Application Support/Artline/backups/overnight-images-20260915'/run.name;core.save_new(backup/'local-selection-preimages.json',state)
    data={'at':core.now(),'records':selected,'held':held,'policy':'Official Linked Art object/creator/date metadata and EDM institution/primary-image/PDM evidence. Exact authority and accession duplicate checks. Existing schema; all artworks remain research candidates in review.'}
    core.save_new(run/'plan.json',data);core.save_new(run/'plan-manifest.json',{'sha256':core.sha((run/'plan.json').read_bytes()),'count':len(selected)});print('Rijks selected',len(selected),'popular',sum(c['popular'] for c in selected),'held',len(held),flush=True);return data

def apply(run,target):
    data=json.loads((run/'plan.json').read_text());assert core.sha((run/'plan.json').read_bytes())==json.loads((run/'plan-manifest.json').read_text())['sha256'];records=data['records'];dsn='postgres://localhost/artline' if target=='local' else core.cloud_dsn();out=[]
    backup=Path.home()/'Library/Application Support/Artline/backups/overnight-images-20260915'/run.name
    with psycopg.connect(dsn,autocommit=True,row_factory=dict_row) as db:
        state=guard.snapshot(db,records,INSTITUTION,['rijks-object','european-rijks-object']);selected,held=guard.conflicts(records,state);iid=state['institution_id']
        before=backup/(target+'-import-preflight.json')
        if not before.exists():core.save_new(before,{'at':core.now(),'state':state,'held':held})
        if held:raise SystemExit('Target identity conflicts; review required: '+str(len(held)))
        with db.transaction():
            db.execute("INSERT INTO sources(slug,name,source_type,base_url,terms_url) VALUES(%s,'Rijksmuseum: independently verified selected paintings','museum_api','https://data.rijksmuseum.nl/',%s) ON CONFLICT(slug) DO NOTHING",(SOURCE,rijks.CC0));sid=db.execute('SELECT id FROM sources WHERE slug=%s',(SOURCE,)).fetchone()['id']
        for start in range(0,len(selected),20):
            with db.transaction():
                db.execute('SELECT pg_advisory_xact_lock(559220260915)')
                for c in selected[start:start+20]:
                    rijks.source_match(c,c['raw']['object']);assert core.rijks_edm(c['raw']['edm']['edm_document'],c['external_id'],c['accession_number'])
                    if c['already_present']:out.append({'artwork_id':c['artwork_id'],'outcome':'already_present'});continue
                    aid=c['artwork_id'];artist=c['target_artist_id'];pid=c['rijks_people'][0];checked=c['checked_at']
                    authorities=db.execute("SELECT entity_id::text,external_id FROM external_identifiers WHERE entity_type='artist' AND scheme='rijks-person' AND (entity_id=%s OR external_id=%s)",(artist,pid)).fetchall()
                    if authorities:assert len(authorities)==1 and authorities[0]['entity_id']==artist and authorities[0]['external_id']==pid
                    else:
                        assert c['artist_qid'] in c['artist_qids']
                        db.execute("INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at) VALUES('artist',%s,'rijks-person',%s,%s,%s,%s)",(artist,pid,'https://id.rijksmuseum.nl/'+pid,sid,checked))
                        db.execute("INSERT INTO citations(entity_type,entity_id,source_id,field_name,source_record_id,source_url,evidence_note,retrieved_at) VALUES('artist',%s,%s,'museum_creator_authority',%s,%s,%s,%s)",(artist,sid,pid,c['page'],'Official object production explicitly links Rijksmuseum person '+pid+' to existing Wikidata authority '+c['artist_qid']+'. No biography or nationality change.',checked))
                    assert not db.execute("SELECT 1 FROM external_identifiers WHERE entity_type='artwork' AND ((scheme='rijks-object' AND external_id=%s) OR canonical_url=%s)",(c['external_id'],c['page'])).fetchone()
                    assert not db.execute('SELECT 1 FROM artworks WHERE current_institution_id=%s AND accession_number=%s',(iid,c['accession_number'])).fetchone()
                    with db.pipeline():
                        db.execute("INSERT INTO artworks(id,slug,title,alternate_title,normalized_title,date_display,creation_year_start,creation_year_end,date_precision,work_type,current_institution_id,accession_number,status,research_candidate,created_by,updated_by) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,'painting',%s,%s,'review',true,%s,%s)",(aid,c['slug'],c['title'],c['alternate_title'],guard.norm(c['title']),c['date_display'],c['creation_year_start'],c['creation_year_end'],c['date_precision'],iid,c['accession_number'],core.ACTOR,core.ACTOR))
                        db.execute("INSERT INTO artwork_artists(artwork_id,artist_id,attribution_role,attribution_note) VALUES(%s,%s,'primary','Exact unqualified museum person identity and existing painter authority verified.')",(aid,artist))
                        db.execute("INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at) VALUES('artwork',%s,'rijks-object',%s,%s,%s,%s)",(aid,c['external_id'],c['page'],sid,checked))
                        db.execute("INSERT INTO artwork_location_assertions(artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state) VALUES(%s,'holding',%s,'collection',%s,%s,%s,%s,'accepted')",(aid,iid,sid,c['page'],'Official Rijksmuseum object and EDM collection provider identify accession '+c['accession_number']+'. Holding only; no current display claim.',checked))
                        evidence={'source_object':c['raw']['object'],'edm_document':c['raw']['edm']['edm_document'],'metadata_capture':c['source_metadata_capture'],'metadata_license':rijks.CC0,'creation_note':'Original source date text and independently corroborated bounds retained; no lifespan-derived dates.'}
                        db.execute("INSERT INTO citations(entity_type,entity_id,source_id,field_name,source_record_id,source_url,evidence_note,retrieved_at,created_by) VALUES('artwork',%s,%s,'official_object_identity',%s,%s,%s,%s,%s)",(aid,sid,c['external_id'],c['page'],json.dumps(evidence,ensure_ascii=False),checked,core.ACTOR))
                    out.append({'artwork_id':aid,'outcome':'inserted'})
            print(core.now(),target,'Rijks metadata',len(out),'of',len(selected),flush=True)
        verified=db.execute("SELECT count(*) n,count(*) FILTER(WHERE status='review' AND published_at IS NULL AND research_candidate AND artline_has_selection_evidence(id)) ok FROM artworks WHERE id=ANY(%s::uuid[])",([c['artwork_id'] for c in records],)).fetchone();assert verified['n']==verified['ok']==len(records)
        dest=run/(target+'-metadata-verified.json')
        if not dest.exists():core.save_new(dest,{'at':core.now(),'counts':verified,'records':out})
    if target=='local':
        for c in records:core.save_new(run/'selected/night-rijks'/(c['artwork_id']+'.json'),c)
        core.save_new(run/'candidates.json',{'created_at':data['at'],'candidates':records,'production_metadata_pending':True})
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['prepare','plan','apply']);p.add_argument('--run',type=Path,required=True);p.add_argument('--deadline',type=float,default=1789530401);p.add_argument('--target',choices=['local','cloud'],default='local');a=p.parse_args()
    if a.phase=='prepare':prepare(a.run,a.deadline)
    elif a.phase=='plan':plan(a.run)
    else:apply(a.run,a.target)
