#!/usr/bin/env python3
"""Import a pinned selection of fresh Met records using existing catalogue tables.

No artwork is published. Object identifiers, creator authorities, institution
accessions, titles and redirects are checked independently in each database.
"""
import argparse, collections, importlib.util, json, re, shutil, unicodedata
from pathlib import Path
import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('met_research', ROOT/'ops/research-overnight-met-selection.py')
research = importlib.util.module_from_spec(spec); spec.loader.exec_module(research)
core = research.core
SOURCE = 'overnight-met-selected-primary-20260915'
SCHEMES = ['met-object', 'european-met-the-met-object']

def norm(value):
    return ' '.join(re.findall(r'\w+', unicodedata.normalize('NFKD', str(value or '')).casefold()))

def snapshot(db, records, institution_slug='the-met', schemes=None, artist_scheme='wikidata'):
    """Read bounded artist/institution slices; never use a global artwork CTE."""
    schemes=schemes or SCHEMES
    institutions = db.execute("SELECT id::text FROM institutions WHERE slug=%s AND status<>'archived'",(institution_slug,)).fetchall()
    assert len(institutions) == 1, 'Museum institution absent or ambiguous'
    iid = institutions[0]['id']
    qids = sorted({c['artist_qid'] for c in records})
    people = db.execute("""SELECT a.id::text,a.slug,a.status,e.external_id qid FROM artists a
      JOIN external_identifiers e ON e.entity_type='artist' AND e.entity_id=a.id
      WHERE e.scheme=%s AND e.external_id=ANY(%s)""", (artist_scheme,qids)).fetchall()
    artists = collections.defaultdict(list)
    for row in people: artists[row['qid']].append(row)
    artist_ids = [r['id'] for r in people]
    works = db.execute("""SELECT a.id::text,a.slug,a.title,a.status,a.accession_number,a.current_institution_id::text,
        a.creation_year_start,a.creation_year_end,a.date_precision,a.date_display,a.work_type,
        array(SELECT aa.artist_id::text FROM artwork_artists aa WHERE aa.artwork_id=a.id) artist_ids,
        EXISTS(SELECT 1 FROM artwork_location_assertions la WHERE la.artwork_id=a.id AND la.institution_id=%s) museum_holding
      FROM artworks a WHERE a.current_institution_id=%s OR a.id IN
        (SELECT la.artwork_id FROM artwork_location_assertions la WHERE la.institution_id=%s) OR a.id IN
        (SELECT aa.artwork_id FROM artwork_artists aa WHERE aa.artist_id=ANY(%s::uuid[]))""", (iid,iid,iid,artist_ids)).fetchall()
    identifiers = db.execute("""SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers
      WHERE entity_type='artwork' AND (scheme=ANY(%s) OR (scheme='wikidata' AND external_id=ANY(%s)) OR canonical_url=ANY(%s))""",
      (schemes,[c['qid'] for c in records if c.get('qid')],[c['page'] for c in records])).fetchall()
    redirects = db.execute("""SELECT old_slug,entity_id::text FROM slug_redirects WHERE entity_type='artwork'
      AND (old_slug=ANY(%s) OR entity_id=ANY(%s::uuid[]))""", ([c['slug'] for c in records],[c['artwork_id'] for c in records])).fetchall()
    return {'institution_id':iid,'artists':dict(artists),'works':works,'identifiers':identifiers,'redirects':redirects,'schemes':schemes}

def conflicts(records, state, title_collision_review=None):
    ids = {r['id']:r for r in state['works']}; by_accession=collections.defaultdict(set); by_title=collections.defaultdict(set)
    # All artworks in this scoped snapshot were independently checked for holding
    # below. Artist-title collisions are held even when their museum is unknown.
    for w in state['works']:
        if (w['current_institution_id']==state['institution_id'] or w.get('museum_holding')) and w['accession_number']:
            by_accession[norm(w['accession_number'])].add(w['id'])
        for aid in w['artist_ids']: by_title[(aid,norm(w['title']))].add(w['id'])
    keys=collections.defaultdict(set); urls=collections.defaultdict(set)
    for e in state['identifiers']:
        keys[(e['scheme'],e['external_id'])].add(e['entity_id'])
        if e['canonical_url']:urls[e['canonical_url']].add(e['entity_id'])
    redirects={r['old_slug'] for r in state['redirects']}|{r['entity_id'] for r in state['redirects']}
    accepted=[];held=[];seen_accessions=set();seen_titles=collections.defaultdict(list)
    for c in records:
        aid=c['artwork_id'];reason=None;people=state['artists'].get(c['artist_qid'],[])
        if len(people)!=1 or people[0]['status']=='archived' or people[0]['slug']!=c['artist_slug']:reason='Creator authority absent, archived or different'
        elif c['slug'] in redirects or aid in redirects:reason='Artwork redirect requires reconciliation'
        else:
            artist_id=people[0]['id'];acc=norm(c['accession_number']);title_key=(artist_id,norm(c['title']))
            old=ids.get(aid)
            if old:
                fields=('slug','title','accession_number','creation_year_start','creation_year_end','date_precision','date_display','work_type')
                if old['status']!='review' or old['current_institution_id']!=state['institution_id'] or any(old[k]!=c[k] for k in fields) or old['artist_ids']!=[artist_id]:reason='Existing deterministic row differs from pinned source'
            other=set(urls[c['page']])
            for scheme in state.get('schemes',SCHEMES):other.update(keys[(scheme,c['external_id'])])
            if c.get('qid'):other.update(keys[('wikidata',c['qid'])])
            if other-{aid}:reason='Existing source identifier or source cross-reference requires review'
            elif by_accession[acc]-{aid} or (not old and acc in seen_accessions):reason='Museum accession already represented; physical-object review required'
            elif by_title[title_key]-{aid} or (not old and title_key in seen_titles):
                collisions=[ids[key] for key in by_title[title_key]-{aid}]
                prior=seen_titles[title_key] if not old else []
                if title_collision_review is None or not title_collision_review(c,collisions,prior,state):reason='Same-artist title already represented; version or duplicate review required'
            if not reason:
                accepted.append(dict(c,target_artist_id=artist_id,already_present=bool(old)))
                seen_accessions.add(acc);seen_titles[title_key].append(c)
        if reason:held.append({'artwork_id':aid,'source_object_id':c['external_id'],'reason':reason})
    return accepted,held

def build(run, reference, limit):
    if (run/'plan.json').exists():return json.loads((run/'plan.json').read_text())
    leads={r['object']['Object ID']:r for r in json.loads((reference/'source-candidates.json').read_text())}
    rows=[]
    for path in (reference/'verified').glob('*.json'):
        c=json.loads(path.read_text());fresh=research.verify(leads[c['external_id']],c['object'])
        assert all(c[k]==v for k,v in fresh.items()), 'Source verification changed before planning'
        rows.append(c)
    rows.sort(key=lambda c:(not c['popular'],c['work_type']!='painting',c['artist'],int(c['external_id'])))
    with psycopg.connect('postgres://localhost/artline',row_factory=dict_row,options='-c default_transaction_read_only=on') as db:
        state=snapshot(db,rows);selected,held=conflicts(rows,state)
    selected=[c for c in selected if not c['already_present']]
    if limit:selected=selected[:limit]
    for c in selected:
        for key in ('target_artist_id','already_present'):c.pop(key,None)
        c['target_ids']={'local':c['artwork_id']}
    backup=Path.home()/'Library/Application Support/Artline/backups/overnight-images-20260915'/run.name
    core.save_new(backup/('local-selection-preimages-'+core.sha(core.encode(state))[:16]+'.json'),state)
    data={'at':core.now(),'records':selected,'held':held,'source_root':str(reference.relative_to(ROOT) if reference.is_absolute() else reference),
          'policy':'Fresh official Met records; museum ID, creator authority, dates, type, ownership and explicit CC0 eligibility verified. New records remain in review. Shared artwork Wikidata references are evidence only, never invented physical-object keys.'}
    core.save_new(run/'plan.json',data);core.save_new(run/'plan-manifest.json',{'sha256':core.sha((run/'plan.json').read_bytes()),'count':len(selected)})
    print('Met plan',len(selected),'popular',sum(c['popular'] for c in selected),'types',dict(collections.Counter(c['work_type'] for c in selected)),'held',len(held),flush=True)
    return data

def apply(run,target,limit):
    data=json.loads((run/'plan.json').read_text());assert core.sha((run/'plan.json').read_bytes())==json.loads((run/'plan-manifest.json').read_text())['sha256']
    records=data['records'][:limit] if limit else data['records'];dsn='postgres://localhost/artline' if target=='local' else core.cloud_dsn()
    if not records:raise SystemExit('No selected records')
    out=[];backup=Path.home()/'Library/Application Support/Artline/backups/overnight-images-20260915'/run.name
    with psycopg.connect(dsn,autocommit=True,row_factory=dict_row) as db:
        state=snapshot(db,records);selected,held=conflicts(records,state)
        preflight=backup/(target+'-import-preflight.json')
        if not preflight.exists():core.save_new(preflight,{'at':core.now(),'state':state,'held':held})
        if held:raise SystemExit('Target identity conflicts; import held for review: '+str(len(held)))
        iid=state['institution_id']
        with db.transaction():
            db.execute("INSERT INTO sources(slug,name,source_type,base_url,terms_url) VALUES(%s,'The Metropolitan Museum of Art: selected independently verified works','museum_api','https://collectionapi.metmuseum.org',%s) ON CONFLICT(slug) DO NOTHING",(SOURCE,research.CC0))
            sid=db.execute('SELECT id FROM sources WHERE slug=%s',(SOURCE,)).fetchone()['id']
        for start in range(0,len(selected),25):
            group=selected[start:start+25]
            with db.transaction():
                db.execute('SELECT pg_advisory_xact_lock(559220260915)')
                # Native object identifiers have a database uniqueness constraint.
                # Per-batch rechecks cover concurrent edits after the initial audit.
                active=[c for c in group if not c['already_present']]
                if active:
                    collisions=db.execute("""SELECT e.entity_id FROM external_identifiers e WHERE e.entity_type='artwork'
                      AND ((e.scheme=ANY(%s) AND e.external_id=ANY(%s)) OR e.canonical_url=ANY(%s))""",(SCHEMES,[c['external_id'] for c in active],[c['page'] for c in active])).fetchall()
                    assert not collisions,'Museum identifier appeared during import'
                with db.pipeline():
                    for c in group:
                        if c['already_present']:out.append({'artwork_id':c['artwork_id'],'outcome':'already_present'});continue
                        o=c['object'];checked=c['metadata_capture']['retrieved_at'];aid=c['artwork_id'];page=c['page']
                        db.execute("""INSERT INTO artworks(id,slug,title,normalized_title,date_display,creation_year_start,creation_year_end,date_precision,work_type,medium_text,dimensions_text,current_institution_id,accession_number,status,research_candidate,created_by,updated_by)
                          VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'review',true,%s,%s)""",(aid,c['slug'],c['title'],norm(c['title']),c['date_display'],c['creation_year_start'],c['creation_year_end'],c['date_precision'],c['work_type'],o.get('medium'),o.get('dimensions'),iid,c['accession_number'],core.ACTOR,core.ACTOR))
                        db.execute("INSERT INTO artwork_artists(artwork_id,artist_id,attribution_role,attribution_note) VALUES(%s,%s,'primary','Exact unqualified museum object-to-creator authority; existing artist Wikidata identity confirmed.')",(aid,c['target_artist_id']))
                        db.execute("INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at) VALUES('artwork',%s,'met-object',%s,%s,%s,%s)",(aid,c['external_id'],page,sid,checked))
                        db.execute("INSERT INTO artwork_location_assertions(artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state) VALUES(%s,'holding',%s,'collection',%s,%s,%s,%s,'accepted')",(aid,iid,sid,page,'Official Met repository, accession '+c['accession_number']+', and acquisition credit support the holding. Loans excluded; no current display claim.',checked))
                        evidence={'source_fields':{k:o.get(k) for k in ('objectID','objectURL','title','objectDate','objectBeginDate','objectEndDate','objectName','classification','medium','dimensions','accessionNumber','repository','creditLine','artistDisplayName','artistWikidata_URL','artistPrefix','artistSuffix','constituents','objectWikidata_URL')},'metadata_capture':c['metadata_capture'],'metadata_license':research.CC0,'date_review':'Original source wording and uncertainty retained; normalized bounds are source-provided, never creator lifespan.'}
                        db.execute("INSERT INTO citations(entity_type,entity_id,source_id,field_name,source_record_id,source_url,evidence_note,retrieved_at,created_by) VALUES('artwork',%s,%s,'official_object_identity',%s,%s,%s,%s,%s)",(aid,sid,c['external_id'],page,json.dumps(evidence,ensure_ascii=False),checked,core.ACTOR))
                        out.append({'artwork_id':aid,'outcome':'inserted'})
            print(core.now(),target,'Met metadata',len(out),'of',len(selected),flush=True)
        verified=db.execute("SELECT count(*) n,count(*) FILTER(WHERE status='review' AND published_at IS NULL AND research_candidate AND artline_has_selection_evidence(id)) ok FROM artworks WHERE id=ANY(%s::uuid[])",([c['artwork_id'] for c in records],)).fetchone()
        assert verified['n']==verified['ok']==len(records)
        path=run/(target+'-metadata-verified'+('-canary' if limit else '')+'.json')
        if not path.exists():core.save_new(path,{'at':core.now(),'counts':verified,'records':out})
        print(target,'verified',verified,flush=True)
    if target=='local' and not limit:
        candidates=[];reference=ROOT/data['source_root']
        for c in records:
            image_candidate={k:c[k] for k in ('artwork_id','slug','title','date_display','creation_year_start','creation_year_end','work_type','scheme','external_id','artist','popular','provider','page','target_ids')}
            candidates.append(image_candidate)
            url='https://collectionapi.metmuseum.org/public/collection/v1/objects/'+c['external_id'];key=core.sha(url.encode())
            for suffix in ('.json','.receipt.json'):
                source=reference/'fresh-api'/(key+suffix);dest=run/'metadata/met'/(key+suffix)
                core.save_new(dest,source.read_bytes())
        core.save_new(run/'candidates.json',{'created_at':data['at'],'candidates':candidates,'production_metadata_pending':True})
        core.save_new(run/'backups.json',(run.parent/'backups.json').read_bytes())

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['plan','apply']);p.add_argument('--run',type=Path,required=True);p.add_argument('--reference',type=Path);p.add_argument('--limit',type=int,default=0);p.add_argument('--target',choices=['local','cloud'],default='local');a=p.parse_args();a.run.mkdir(parents=True,exist_ok=True)
    if a.phase=='plan':build(a.run,a.reference or a.run,a.limit)
    else:apply(a.run,a.target,a.limit)
