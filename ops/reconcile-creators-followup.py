#!/usr/bin/env python3
"""Evidence-backed links to existing painters; no name-only identity merges."""
import argparse
import collections
import importlib.util
import json
from pathlib import Path
from psycopg.types.json import Jsonb


def module(name, path):
    spec=importlib.util.spec_from_file_location(name,path)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result


ROOT=Path(__file__).resolve().parent.parent
r=module('wiki_research',ROOT/'ops/research-wikimedia-catalogues.py')
old=module('old_reconciliation',ROOT/'ops/reconcile-artwork-creators.py')
names=module('name_policy',ROOT/'ops/plan-expanded-round2.py')
RUN=ROOT/'docs/research/creator-reconciliation-followup-20260913'
BACKUPS=Path('/Users/vadimdulub/Library/Application Support/Artline/backups/creator-reconciliation-followup-20260913')
FIELD='creator_identity_reconciled_20260913'
ACTOR='local-european-research'
SOURCE_SLUG='creator-reconciliation-followup-20260913'
SOURCE_NAME='Creator identity reconciliation — official museums and Wikidata'


def read(name):return json.loads((RUN/name).read_text())
def save(name,value):r.core.save_new(RUN/name,value)


class Matcher:
    def __init__(self, artists, redirects=None):
        self.artists={a['id']:a for a in artists};self.ids=collections.defaultdict(set);self.names=collections.defaultdict(set)
        self.redirects=redirects or {}
        for a in artists:
            for ident in a['authorities']:
                value=self.redirects.get(ident['id'],ident['id']) if ident['scheme']=='wikidata' else ident['id']
                self.ids[(ident['scheme'],str(value))].add(a['id'])
            for label in [a['display_name'],*a['aliases']]:self.names[names.namekey(label)].add(a['id'])

    def match(self,painter,source,labels=()):
        if old.QUALIFIED.search(painter.get('name','')):return None,'qualified_or_anonymous_creator'
        if painter.get('role','').lower() not in ('','artist','painter','kunstner','maler'):return None,'creator_role_requires_review'
        if all(painter.get(k) is not None for k in ('birth','death')) and not 0<=painter['death']-painter['birth']<=125:return None,'implausible_source_lifespan'
        direct=set()
        for scheme,value in [(source+'-person',painter.get('source_id')),('wikidata',painter.get('wikidata'))]:
            if value:direct.update(self.ids.get((scheme,str(self.redirects.get(value,value) if scheme=='wikidata' else value)),set()))
        candidates=set().union(*(self.names.get(names.namekey(x),set()) for x in [painter['name'],painter.get('sort_name',''),*labels] if x))
        def compatible(a):
            return a['status']!='archived' and a['entity_type']=='person' and not any(painter.get(k) is not None and a[k+'_year'] is not None and painter[k]!=a[k+'_year'] for k in ('birth','death'))
        if direct:
            if len(direct)!=1:return None,'conflicting_authority_ids'
            artist=self.artists[next(iter(direct))]
            if not compatible(artist):return None,'authority_biography_conflict'
            basis='exact_source_person_or_wikidata_identifier'
        else:
            good=[self.artists[x] for x in candidates if compatible(self.artists[x]) and all(painter.get(k) is not None and painter[k]==self.artists[x][k+'_year'] for k in ('birth','death'))]
            if len(good)!=1:return None,'ambiguous_identity' if len(good)>1 else 'no_identity_with_corroborating_closed_lifespan'
            artist=good[0];basis='documented_name_variant_and_both_lifespan_boundaries'
            qid=painter.get('wikidata')
            existing={self.redirects.get(x['id'],x['id']) for x in artist['authorities'] if x['scheme']=='wikidata'}
            if qid and existing and qid not in existing:return None,'existing_wikidata_conflict'
        return {'artist':artist,'basis':basis},None


def plan():
    assert not (RUN/'plan.json').exists(),'Plan is immutable'
    pending={x['id']:x for x in read('unlinked-artworks.json')}
    redirects={e['redirects']['from']:e['redirects']['to'] for e in read('guercino-redirect.json')['data']['entities'].values() if e.get('redirects')}
    matcher=Matcher(read('artists.json'),redirects)
    originals={x['id']:x for x in read('unlinked-original-identities.json')}
    accepted={};holds=[]

    def consider(work,painter,source,evidence,labels=(),source_guard=None,context=None,state='needs_review',review=None,note=''):
        check={'painter':painter,'context':context,'state':state,'review':review or {},'note':note,'precision':work['date_precision'],'first':work['creation_year_start'],'last':work['creation_year_end'],'type':work['work_type']}
        reason=old.blocked(check)
        match=None
        if not reason:match,reason=matcher.match(painter,source,labels)
        if not reason:
            artist=match['artist'];first,last=work['creation_year_start'],work['creation_year_end']
            if (last is not None and artist['birth_year'] is not None and last<artist['birth_year']) or (first is not None and artist['death_year'] is not None and first>artist['death_year']):reason='artwork_outside_painter_lifetime'
        if reason:
            holds.append({'artwork_id':work['id'],'slug':work['slug'],'source':source,'painter':painter['name'],'reason':reason});return
        entry={'before':work,'artist':match['artist'],'basis':match['basis'],'painter':painter,'source':source,'evidence':evidence,'source_guard':source_guard,'original':originals.get(work['id'])}
        if work['id'] in accepted:
            assert accepted[work['id']]['artist']['id']==entry['artist']['id'],'Conflicting sources for one creator'
            return
        accepted[work['id']]=entry

    for work in read('wikimedia-unlinked.json'):
        qid=work['slug'].replace('wikimedia-artwork-q','Q');path=r.RUN/'ready'/(qid+'.json')
        rec=json.loads(path.read_text())['record'];ce=rec['creator_entity']
        painter={'name':rec['creator_label'],'wikidata':rec['creator_qid'],'birth':r.year(ce,'P569'),'death':r.year(ce,'P570'),'role':'artist'}
        evidence={'object_url':'https://www.wikidata.org/wiki/'+qid,'object_id':qid,'creator_url':'https://www.wikidata.org/wiki/'+(rec['creator_qid'] or qid),'entity_receipt':rec['entity_receipt'],'creator_receipt':rec['creator_receipt'],'prepared_record_path':str(path.relative_to(ROOT)),'prepared_record_sha256':r.core.sha(path.read_bytes())}
        consider(work,painter,'wikidata',evidence,r.labels(ce))
    museum_facts=read('museum-creator-facts.json')
    for fact in museum_facts:
        work=pending[fact['id']]
        consider(work,fact['painter'],fact['source_kind'],{'object_url':fact['object_url'],'research_record_id':fact['research_record_id'],'facts_sha256':fact['facts_sha256']},source_guard=fact,context=fact['context'],state=fact['state'],review=fact['review_evidence'],note=fact['note'])
    # Reuse exact object matches from the previous official-source research,
    # restricted to original CSV identities still unresolved in the live DB.
    path=ROOT/'docs/research/expanded-round15-20260913/new-source-matches.json'
    matches=json.loads(path.read_text());checksum=r.core.sha(path.read_bytes())
    previously_resolved={x['id'] for x in museum_facts}
    for oid,original in originals.items():
        if oid in accepted or oid in previously_resolved:continue
        options=matches.get(original['research_record_id'],{})
        if len(options)!=1:continue
        fact=next(iter(options.values()));work=pending[oid];painter=fact['painter']
        if names.namekey(original['cells'][0]) not in {names.namekey(painter['name']),names.namekey(painter.get('sort_name',''))}:
            holds.append({'artwork_id':oid,'slug':work['slug'],'source':fact['source'],'reason':'original_creator_label_mismatch'});continue
        consider(work,painter,fact['source'],{'object_url':fact['object_url'],'object_id':fact['object_id'],'source_receipts':fact['evidence'],'match_file':str(path.relative_to(ROOT)),'match_file_sha256':checksum,'research_record_id':original['research_record_id']},context=fact.get('object_context'))
    entries=sorted(accepted.values(),key=lambda x:x['before']['slug'])
    save('holds.json',holds);save('plan.json',entries)
    manifest={'at':r.core.now(),'sha256':r.core.sha((RUN/'plan.json').read_bytes()),'audited_unlinked_artworks':len(pending),'links':len(entries),'existing_painters':len({x['artist']['id'] for x in entries}),'sources':dict(collections.Counter(x['source'] for x in entries)),'held_reasons':dict(collections.Counter(x['reason'] for x in holds)),'redirects':redirects,'museum_scope':'New museums and collections are included; no institution-based restriction on creator reconciliation.'}
    save('manifest.json',manifest);print(json.dumps(manifest,indent=2),flush=True)


def load_plan():
    manifest=read('manifest.json');raw=(RUN/'plan.json').read_bytes()
    assert r.core.sha(raw)==manifest['sha256'],'Changed plan'
    entries=json.loads(raw);assert len(entries)==manifest['links']
    return manifest,entries


def selected_rows(db,entries,lock=False):
    rows=db.execute('SELECT to_jsonb(a) AS row FROM artworks a WHERE slug=ANY(%s)'+(' FOR UPDATE' if lock else ''),([e['before']['slug'] for e in entries],)).fetchall()
    assert len(rows)==len(entries),'Missing artwork in target'
    return {x['row']['slug']:x['row'] for x in rows}


def artist_rows(db,entries):
    rows=db.execute('''SELECT to_jsonb(a) AS row,
      coalesce((SELECT jsonb_agg(alias) FROM artist_aliases WHERE artist_id=a.id),'[]') aliases,
      coalesce((SELECT jsonb_agg(jsonb_build_object('scheme',scheme,'id',external_id)) FROM external_identifiers WHERE entity_type='artist' AND entity_id=a.id),'[]') authorities
      FROM artists a WHERE slug=ANY(%s)''',(list({e['artist']['slug'] for e in entries}),)).fetchall()
    assert len(rows)==len({e['artist']['slug'] for e in entries}),'Missing target painter'
    return {x['row']['slug']:x for x in rows}


def guards(db,entries,works,artists,check_links=True):
    for entry in entries:
        before=entry['before'];now=works[before['slug']];artist=artists[entry['artist']['slug']]
        for key in ('title','unlinked_creator_label','creation_year_start','creation_year_end','date_precision','work_type','research_candidate','status'):
            assert now[key]==before[key],(before['slug'],'artwork changed',key)
        assert now['status']=='review' and now['published_at'] is None
        for key in ('display_name','normalized_name','birth_year','death_year','status','entity_type'):
            assert artist['row'][key]==entry['artist'][key],(entry['artist']['slug'],'painter changed',key)
        assert set(entry['artist']['aliases'])<=set(artist['aliases']),'Painter alias evidence changed'
        assert {(x['scheme'],x['id']) for x in entry['artist']['authorities']}<={(x['scheme'],x['id']) for x in artist['authorities']},'Painter authority evidence changed'
    if check_links:
        assert not db.execute('SELECT 1 FROM artwork_artists WHERE artwork_id=ANY(%s::uuid[]) LIMIT 1',([x['id'] for x in works.values()],)).fetchone(),'Artwork already linked'
    originals=[e['original'] for e in entries if e['original']]
    if originals:
        rows=db.execute('''SELECT w.slug,l.research_record_id,l.entry_sha256,rr.raw_json#>'{csv,cells}' AS cells
          FROM research_artwork_links l JOIN artworks w ON w.id=l.artwork_id
          JOIN research_records rr ON rr.snapshot_id=l.snapshot_id AND rr.source_key=l.source_key AND rr.record_kind=l.record_kind AND rr.source_record_id=l.research_record_id
          WHERE l.research_record_id=ANY(%s) AND l.disposition='created' ''',([x['research_record_id'] for x in originals],)).fetchall()
        assert len(rows)==len(originals)
        actual={x['research_record_id']:x for x in rows}
        for original in originals:
            assert actual[original['research_record_id']]=={k:original[k] for k in ('slug','research_record_id','entry_sha256','cells')},'Original CSV identity changed'
    facts=[e['source_guard'] for e in entries if e['source_guard']]
    if facts:
        rows=db.execute('SELECT research_record_id,source_kind,state,note,facts_sha256,facts_json->\'painter\' painter,facts_json->\'object_context\' context,review_evidence,object_url FROM research_resolutions WHERE research_record_id=ANY(%s)',([x['research_record_id'] for x in facts],)).fetchall()
        assert len(rows)==len(facts);actual={x['research_record_id']:x for x in rows}
        for fact in facts:
            assert actual[fact['research_record_id']]=={k:v for k,v in fact.items() if k not in ('id','slug')},'Official-source attribution evidence changed'
    wiki=[e for e in entries if e['source']=='wikidata']
    if wiki:
        rows=db.execute("SELECT a.slug,e.external_id FROM artworks a JOIN external_identifiers e ON e.entity_type='artwork' AND e.entity_id=a.id AND e.scheme='wikidata' WHERE a.slug=ANY(%s)",([x['before']['slug'] for x in wiki],)).fetchall()
        assert {x['slug']:x['external_id'] for x in rows}=={x['before']['slug']:x['evidence']['object_id'] for x in wiki}


def preflight(target):
    manifest,entries=load_plan();works={};artists={}
    with r.base.connect(target=='production') as db,db.transaction():
        db.execute('SET TRANSACTION READ ONLY');db.execute("SET LOCAL statement_timeout='120s'")
        for offset in range(0,len(entries),100):
            batch=entries[offset:offset+100];w=selected_rows(db,batch);a=artist_rows(db,batch);guards(db,batch,w,a);works.update(w);artists.update(a)
        prior_citations=db.execute("SELECT count(*) AS n FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND field_name=%s",([x['id'] for x in works.values()],FIELD)).fetchone()['n'];assert prior_citations==0
        counts=db.execute("SELECT (SELECT count(*) FROM artworks) artworks,(SELECT count(*) FROM artists) artists,(SELECT count(*) FROM artworks w WHERE w.unlinked_creator_label IS NOT NULL AND w.status='review' AND NOT EXISTS(SELECT 1 FROM artwork_artists aa WHERE aa.artwork_id=w.id)) unlinked").fetchone()
    BACKUPS.mkdir(parents=True,exist_ok=True)
    snapshot={'at':r.core.now(),'target':target,'plan_sha256':manifest['sha256'],'works':works,'artists':artists,'counts':counts}
    r.core.save_new(BACKUPS/(target+'-preimages.json'),snapshot)
    save(target+'-preflight.json',{'at':r.core.now(),'plan_sha256':manifest['sha256'],'works':len(works),'painters':len(artists),'counts':counts,'preimages_sha256':r.core.sha((BACKUPS/(target+'-preimages.json')).read_bytes())})
    print(target,'preflight passed',len(works),'artworks',len(artists),'painters',flush=True)


def apply(target):
    manifest,entries=load_plan()
    assert (BACKUPS/'local-backup-receipt.json').exists()
    assert json.loads((BACKUPS/'production-backup-receipt.json').read_text())['status']=='SUCCESSFUL'
    for name in ('local','production'):assert read(name+'-preflight.json')['plan_sha256']==manifest['sha256']
    with r.base.connect(target=='production') as db:
        with db.transaction():
            db.execute("INSERT INTO sources(slug,name,source_type,base_url) VALUES(%s,%s,'authority_data','https://www.wikidata.org/') ON CONFLICT(slug) DO NOTHING",(SOURCE_SLUG,SOURCE_NAME))
            sid=db.execute("SELECT id FROM sources WHERE slug=%s",(SOURCE_SLUG,)).fetchone()['id']
        for offset in range(0,len(entries),100):
            batch=entries[offset:offset+100];receipt=RUN/'applied'/target/f'batch-{offset//100+1:03d}.json'
            if receipt.exists():continue
            with db.transaction():
                db.execute('SET TRANSACTION ISOLATION LEVEL SERIALIZABLE');db.execute("SET LOCAL statement_timeout='90s'");db.execute("SET LOCAL lock_timeout='10s'")
                db.execute('SELECT pg_advisory_xact_lock(2026090959)');db.execute('SELECT pg_advisory_xact_lock(559220260914)')
                works=selected_rows(db,batch,lock=True);artists=artist_rows(db,batch)
                existing=db.execute('SELECT entity_id::text FROM citations WHERE entity_type=\'artwork\' AND field_name=%s AND entity_id=ANY(%s::uuid[])',(FIELD,[x['id'] for x in works.values()])).fetchall()
                assert not existing,'Committed batch missing receipt: verify before resuming'
                guards(db,batch,works,artists)
                updates=[];outcomes=[]
                with db.pipeline():
                    for entry in batch:
                        work=works[entry['before']['slug']];artist=artists[entry['artist']['slug']]['row'];aid=work['id'];pid=artist['id']
                        note='Creator reconciled by '+entry['basis']+'. Original object-level creator label: '+entry['before']['unlinked_creator_label']+'. Source evidence and plan retained for editorial review.'
                        r.base.insert(db,'artwork_artists',dict(artwork_id=aid,artist_id=pid,attribution_role='primary',attribution_note=note))
                        updates.append(db.execute('UPDATE artworks SET unlinked_creator_label=NULL,revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s AND unlinked_creator_label=%s',(ACTOR,aid,entry['before']['unlinked_creator_label'])))
                        evidence={'identity_basis':entry['basis'],'original_creator_label':entry['before']['unlinked_creator_label'],'source_painter':entry['painter'],'source_evidence':entry['evidence'],'plan_sha256':manifest['sha256'],'artist_slug':artist['slug']}
                        r.base.insert(db,'citations',dict(entity_type='artwork',entity_id=aid,field_name=FIELD,source_id=sid,source_record_id=entry['evidence'].get('object_id') or entry['evidence']['research_record_id'],source_url=entry['evidence']['object_url'],evidence_note=json.dumps(evidence,ensure_ascii=False,sort_keys=True),retrieved_at=r.core.now(),created_by=ACTOR))
                        outcomes.append({'slug':work['slug'],'artwork_id':aid,'artist_id':pid,'artist_slug':artist['slug'],'source':entry['source']})
                assert all(x.rowcount==1 for x in updates)
            r.core.save_new(receipt,{'at':r.core.now(),'plan_sha256':manifest['sha256'],'outcomes':outcomes})
            print(target,'linked batch',offset//100+1,len(outcomes),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['plan','preflight','apply']);parser.add_argument('--target',choices=['local','production']);args=parser.parse_args()
    if args.phase=='plan':plan()
    elif args.phase=='preflight':preflight(args.target)
    else:apply(args.target)
