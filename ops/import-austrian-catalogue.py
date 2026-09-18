#!/usr/bin/env python3
"""Pinned, idempotent Austrian collection research import using existing schema.

Museum geography, object evidence and creator citizenship are separate facts.
Existing editorial metadata and images are preserved. No current display claims.
"""
import argparse,collections,importlib.util,json,re,uuid
from pathlib import Path
import psycopg
from psycopg.rows import dict_row
s=importlib.util.spec_from_file_location('research',Path(__file__).with_name('research-austrian-wikimedia.py'));research=importlib.util.module_from_spec(s);s.loader.exec_module(research)
s=importlib.util.spec_from_file_location('match',Path(__file__).with_name('apply-wikimedia-catalogues.py'));match=importlib.util.module_from_spec(s);s.loader.exec_module(match)
r=research.r;m=research.m;core=m.core
SOURCE='austrian-collections-research-20260916';CC0='https://creativecommons.org/publicdomain/zero/1.0/'
MUSEUMS={
 'Q303139':('belvedere','Q1741'), 'Q95569':('kunsthistorisches-museum','Q1741'),
 'Q371908':('wikimedia-museum-q371908','Q1741'), 'Q414219':('wikimedia-museum-q414219','Q1741'),
 'Q505873':('wikimedia-museum-q505873','Q1741'), 'Q59435':('wikimedia-museum-q59435','Q1741'),
 'Q686531':('wikimedia-museum-q686531','Q41329'), 'Q1979511':('neue-galerie-graz','Q13298'),
 'Q2436253':('tyrolean-state-museum-ferdinandeum','Q1735'), 'Q2215920':('salzburg-museum','Q34713'),
 'Q2011578':('upper-austrian-state-museum','Q41329')}

def uid(key):return str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.local/austria/'+key))
def load(p):return json.loads(p.read_text())
def connect(target,ro=False):return psycopg.connect('postgres://localhost/artline' if target=='local' else core.cloud_dsn(),autocommit=True,row_factory=dict_row,options='-c statement_timeout=90000'+(' -c default_transaction_read_only=on' if ro else ''))

def validate_record(x):
    e=x['entity']; assert e['id']==x['qid'] and m.ids(e,'P31')&m.PAINTED,'Painting classification not established'
    cs=r.claims(e,'P170');assert len(cs)==1 and not cs[0].get('qualifiers') and r.value(cs[0])['id']==x['creator_qid'],'Creator attribution requires review'
    hs=[c for c in r.claims(e,'P195') if 'P582' not in c.get('qualifiers',{})];assert len(hs)==1 and r.value(hs[0])['id']==x['institution_qid'],'Current collection statement differs'
    assert m.ids(x['creator_entity'],'P31')=={'Q5'},'Creator requires non-person attribution support'
    assert x['date']['first'] is None or 1000<=x['date']['first']<=x['date']['last']<=1970,'Creation date outside scope'
    assert x['title'] and x['title']!=x['qid'] and x['creator_label']!=x['creator_qid']

def artist_plan(x,artists,countries):
    cq=x['creator_qid'];exact=[a for a in artists if cq in a['qids']]
    if len(exact)>1:raise ValueError('Multiple existing creator authorities')
    names={r.norm(n) for n in x['creator_names']};same=[a for a in artists if r.norm(a['display_name']) in names]
    row=exact[0] if exact else None
    if row and row['status']=='archived':raise ValueError('Archived artist preserved')
    if not row and same:
        compatible=[a for a in same if not a['qids'] and a['birth_year']==x['creator_birth'] is not None and a['death_year']==x['creator_death'] is not None and a['status']!='archived']
        if len(compatible)!=1:raise ValueError('Existing named creator needs manual authority reconciliation')
        row=compatible[0]
    birth,death=x['creator_birth'],x['creator_death'];first,last=birth,death;basis='life'
    if row is None and (birth is None or death is None):
        if not x['date']['eligible']:raise ValueError('Creator lacks life dates and documented dated activity')
        first,last=x['date']['first'],x['date']['last'];basis='activity'
    if row is None and not 1000<=first<=last<=2026:raise ValueError('Creator timeline requires editorial review')
    codes=[]
    for q in x['creator_countries']:
        if q not in countries:continue  # Keep an unverified country mapping unresolved.
        ce=countries[q]['entity'];iso=m.values(ce,'P297')
        # Only extant country authorities with one source ISO code. Never map
        # a dissolved empire or historic birthplace to a modern nationality.
        if len(iso)==1 and re.fullmatch('[A-Z]{2}',iso[0]) and not m.values(ce,'P576'):codes.append({'code':iso[0],'qid':q,'source_url':'https://www.wikidata.org/wiki/'+cq,'country_url':'https://www.wikidata.org/wiki/'+q})
    return {'id':row['id'] if row else uid('artist/'+cq),'slug':row['slug'] if row else 'austrian-research-painter-'+cq.lower(),'qid':cq,'new':row is None,'match':'authority' if exact else 'exact_name_and_lifespan' if row else 'new_authority','name':row['display_name'] if row else x['creator_label'],'birth':birth,'death':death,'first':first,'last':last,'basis':basis,'countries':codes,'preimage':row}

def plan(run):
    path=run/'metadata-plan.json'
    if path.exists():return load(path)
    source=run/'metadata-input.json';data=load(source);museums=load(run/'wikimedia/museum-entities.json');cities=load(run/'wikimedia/verified-city-entities.json');country_path=run/'wikimedia/country-authorities.json';countries=load(country_path) if country_path.exists() else {};out={'at':core.now(),'source_sha256':core.sha(source.read_bytes()),'targets':{},'country_authorities_available':bool(countries),'policy':'Existing fields and images preserved; all new records in review; no on-view assertion; independently sourced facts only.'}
    for target in ('local','cloud'):
        states=[];holds=[];institutions={};artist_states={}
        with connect(target,True) as db:
            ii=db.execute('SELECT i.id::text,i.slug,i.name,i.wikidata_id,i.place_id::text,i.website_url,i.status,p.country_code FROM institutions i LEFT JOIN places p ON p.id=i.place_id WHERE i.wikidata_id=ANY(%s) OR i.slug=ANY(%s)',(list(MUSEUMS),[v[0] for v in MUSEUMS.values()]+['academy-fine-arts-vienna-paintings-gallery'])).fetchall()
            for q,(slug,cityq) in MUSEUMS.items():
                assert m.ids(museums[q],'P17')=={'Q40'}
                city=cities[cityq]['entity'];assert m.ids(city,'P17')=={'Q40'}
                old=[i for i in ii if i['wikidata_id']==q or i['slug']==slug];assert len(old)<=1,'Ambiguous museum authority'
                old=old[0] if old else None
                if old:assert old['status']!='archived' and old['country_code'] in (None,'AT') and old['wikidata_id'] in (None,q)
                pp=db.execute("SELECT id::text,name,country_code,wikidata_id FROM places WHERE wikidata_id=%s OR (country_code='AT' AND lower(name)=ANY(%s))",(cityq,[n.lower() for n in r.labels(city)])).fetchall()
                exact=[p for p in pp if p['wikidata_id']==cityq];place=(exact or pp)
                assert len(place)<=1,'Ambiguous city identity';place=place[0] if place else None
                related=[old['id']] if old else []
                if q=='Q414219':related.extend(i['id'] for i in ii if i['slug']=='academy-fine-arts-vienna-paintings-gallery')
                sites=m.values(museums[q],'P856');website=old['website_url'] if old and old['website_url'] else (sites[0] if sites else None)
                institutions[q]={'id':old['id'] if old else uid('museum/'+q),'slug':slug,'name':old['name'] if old else r.label(museums[q]),'qid':q,'website_url':website,'new':old is None,'preimage':old,'related_ids':related,'city_qid':cityq,'city_name':r.label(city),'place_id':place['id'] if place else uid('place/'+cityq),'new_place':place is None,'place_preimage':place}
            allq=[x['qid'] for x in data['records']];creatorq=list({x['creator_qid'] for x in data['records']});names=list({r.norm(n) for x in data['records'] for n in x['creator_names']})
            artists=db.execute("SELECT a.id::text,a.slug,a.display_name,a.birth_year,a.death_year,a.status,ARRAY(SELECT external_id FROM external_identifiers e WHERE e.entity_type='artist' AND e.entity_id=a.id AND e.scheme='wikidata') qids FROM artists a WHERE a.normalized_name=ANY(%s) OR a.id IN(SELECT entity_id FROM external_identifiers WHERE entity_type='artist' AND scheme='wikidata' AND external_id=ANY(%s))",(names,creatorq)).fetchall()
            ids=[i['id'] for i in ii];works=db.execute("""WITH selected AS MATERIALIZED (SELECT id FROM artworks WHERE current_institution_id=ANY(%s::uuid[]) UNION SELECT entity_id FROM external_identifiers WHERE entity_type='artwork' AND scheme='wikidata' AND external_id=ANY(%s))
              SELECT a.id::text,a.slug,a.title,a.alternate_title,a.accession_number,a.current_institution_id::text,a.creation_year_start,a.creation_year_end,a.date_precision,a.date_display,a.work_type,a.status,a.revision,a.primary_media_id::text,
              ARRAY(SELECT external_id FROM external_identifiers e WHERE e.entity_type='artwork' AND e.entity_id=a.id AND e.scheme='wikidata') qids,
              ARRAY(SELECT ar.display_name FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=a.id) creator_names,
              ARRAY(SELECT e.external_id FROM artwork_artists aa JOIN external_identifiers e ON e.entity_type='artist' AND e.entity_id=aa.artist_id AND e.scheme='wikidata' WHERE aa.artwork_id=a.id) creator_qids
              FROM selected s JOIN artworks a ON a.id=s.id""",(ids,allq)).fetchall()
            accession_counts=collections.Counter((x['institution_qid'],match.accession_key(x['accession'])) for x in data['records'] if x['accession'])
            for x in data['records']:
                try:
                    validate_record(x);inst=institutions[x['institution_qid']]
                    if not inst['website_url']:raise ValueError('Museum current official website requires reconciliation')
                    if x['accession'] and accession_counts[(x['institution_qid'],match.accession_key(x['accession']))]>1:raise ValueError('Multiple source objects share institutional accession')
                    exact=[w for w in works if x['qid'] in w['qids']];assert len(exact)<=1,'Multiple existing object authorities'
                    peers=[w for w in works if w['current_institution_id'] in inst['related_ids']]
                    old,reason=match.choose_existing(x,peers)
                    if reason:raise ValueError(reason)
                    if exact:
                        if exact[0]['current_institution_id'] not in inst['related_ids']:raise ValueError('Existing authority has another institutional context')
                        if old and old['id']!=exact[0]['id']:raise ValueError('Authority and accession identify different existing artworks')
                        old=exact[0]
                    if old:
                        if old['status']=='archived':raise ValueError('Archived artwork preserved')
                        if old['qids'] and old['qids']!=[x['qid']]:raise ValueError('Existing object has a different authority')
                        if old['creator_qids'] and x['creator_qid'] not in old['creator_qids']:raise ValueError('Existing creator conflicts')
                        if old['accession_number'] and x['accession'] and match.accession_key(old['accession_number'])!=match.accession_key(x['accession']):raise ValueError('Existing accession conflicts')
                    cq=x['creator_qid']
                    if cq not in artist_states:artist_states[cq]=artist_plan(x,artists,countries)
                    author=artist_states[cq]
                    # Cross-institution same-title works need distinct object evidence.
                    if old is None:
                        clashes=db.execute("SELECT a.id::text,a.current_institution_id::text,a.accession_number,ARRAY(SELECT external_id FROM external_identifiers e WHERE e.entity_type='artwork' AND e.entity_id=a.id AND e.scheme='wikidata') qids FROM artworks a JOIN artwork_artists aa ON aa.artwork_id=a.id WHERE aa.artist_id=%s AND (lower(a.title)=ANY(%s) OR lower(a.alternate_title)=ANY(%s)) AND a.status<>'archived'",(author['id'],match.title_lookup_variants(x['titles']),match.title_lookup_variants(x['titles']))).fetchall()
                        if any(not (w['accession_number'] and x['accession'] and w['current_institution_id']!=inst['id'] and w['qids'] and x['qid'] not in w['qids']) for w in clashes):raise ValueError('Same creator/title requires distinct physical-object review')
                    states.append({'qid':x['qid'],'artwork_id':old['id'] if old else uid('work/'+x['qid']),'slug':old['slug'] if old else 'austrian-research-artwork-'+x['qid'].lower(),'action':'existing' if old else 'new','institution_id':old['current_institution_id'] if old else inst['id'],'artist_qid':cq,'artist_id':author['id'],'existing':old})
                except (AssertionError,ValueError) as exc:holds.append({'qid':x['qid'],'reason':str(exc)})
            # Different discovered QIDs must never select one existing work twice.
            duplicateids={aid for aid,n in collections.Counter(s['artwork_id'] for s in states).items() if n>1}
            for st in states:
                if st['artwork_id'] in duplicateids:holds.append({'qid':st['qid'],'reason':'Multiple source identities match the same catalogue artwork'})
            states=[st for st in states if st['artwork_id'] not in duplicateids]
            active_artists={st['artist_qid'] for st in states};artist_states={q:v for q,v in artist_states.items() if q in active_artists}
            out['targets'][target]={'records':states,'held':holds,'institutions':institutions,'artists':artist_states}
            backup=Path.home()/'Library/Application Support/Artline/backups'/run.name
            core.save_new(backup/(target+'-research-row-preimages.json'),{'institutions':ii,'artists':artists,'artworks':works})
            print(target,'Planned',len(states),dict(collections.Counter(s['action'] for s in states)),'new painters',sum(a['new'] for a in artist_states.values()),'held',len(holds),dict(collections.Counter(h['reason'] for h in holds)),flush=True)
    core.save_new(path,out);core.save_new(run/'metadata-plan-manifest.json',{'sha256':core.sha(path.read_bytes()),'at':core.now()});return out

def citation(db,typ,eid,field,sid,q,url,evidence,at):
    if not db.execute('SELECT 1 FROM citations WHERE entity_type=%s AND entity_id=%s AND field_name=%s AND source_id=%s',(typ,eid,field,sid)).fetchone():
        db.execute('INSERT INTO citations(entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)',(typ,eid,field,sid,q,url,json.dumps(evidence,ensure_ascii=False),at,core.ACTOR))

def authority(db,typ,eid,q,sid,at):
    rows=db.execute("SELECT entity_id::text FROM external_identifiers WHERE entity_type=%s AND scheme='wikidata' AND external_id=%s",(typ,q)).fetchall()
    if rows:assert len(rows)==1 and rows[0]['entity_id']==eid,'Concurrent authority conflict'
    else:db.execute("INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at) VALUES(%s,%s,'wikidata',%s,%s,%s,%s)",(typ,eid,q,'https://www.wikidata.org/wiki/'+q,sid,at))

def apply(run,target,limit=0):
    backups=load(run/'backups.json');assert backups['cloud']['status']=='SUCCESSFUL' and backups['local']['archive_directory_validated'] and Path(backups['local']['path']).stat().st_size==backups['local']['bytes'],'Verified backups required'
    raw=(run/'metadata-plan.json').read_bytes();assert core.sha(raw)==load(run/'metadata-plan-manifest.json')['sha256'];plan=load(run/'metadata-plan.json');assert core.sha((run/'metadata-input.json').read_bytes())==plan['source_sha256']
    facts={x['qid']:x for x in load(run/'metadata-input.json')['records']};t=plan['targets'][target];states=t['records'][:limit] if limit else t['records'];stats=collections.Counter();sid=uid('source/'+SOURCE)
    with connect(target) as db:
        with db.transaction(),db.pipeline():
            db.execute("INSERT INTO sources(id,slug,name,source_type,base_url,terms_url) VALUES(%s,%s,'Austrian museum collections: independent authority research','authority_data','https://www.wikidata.org/','https://www.wikidata.org/wiki/Wikidata:Licensing') ON CONFLICT(slug) DO NOTHING",(sid,SOURCE))
            assert str(db.execute('SELECT id FROM sources WHERE slug=%s',(SOURCE,)).fetchone()['id'])==sid
            for q,i in t['institutions'].items():
                if not any(facts[s['qid']]['institution_qid']==q for s in states):continue
                if i['new_place']:
                    db.execute('INSERT INTO places(id,name,normalized_name,country_code,wikidata_id) VALUES(%s,%s,%s,\'AT\',%s) ON CONFLICT(id) DO NOTHING',(i['place_id'],i['city_name'],r.norm(i['city_name']),i['city_qid']))
                place=db.execute('SELECT country_code FROM places WHERE id=%s',(i['place_id'],)).fetchone();assert place and place['country_code']=='AT'
                if i['new']:
                    db.execute("INSERT INTO institutions(id,slug,name,normalized_name,place_id,website_url,wikidata_id,kind,status) VALUES(%s,%s,%s,%s,%s,%s,%s,'museum','review') ON CONFLICT(id) DO NOTHING",(i['id'],i['slug'],i['name'],r.norm(i['name']),i['place_id'],i['website_url'],q))
                current=db.execute('SELECT id::text,wikidata_id,place_id::text FROM institutions WHERE id=%s FOR UPDATE',(i['id'],)).fetchone();assert current and current['wikidata_id'] in (None,q)
                if current['place_id'] is None:db.execute('UPDATE institutions SET place_id=%s,updated_at=now() WHERE id=%s',(i['place_id'],i['id']))
                if current['wikidata_id'] is None:db.execute('UPDATE institutions SET wikidata_id=%s,updated_at=now() WHERE id=%s',(q,i['id']))
                citation(db,'institution',i['id'],'institution_country',sid,q,'https://www.wikidata.org/wiki/'+q,{'country':'AT','country_authority':'Q40','city_authority':i['city_qid'],'official_website':i['website_url'],'metadata_license':CC0,'scope':'Institution geography only; no painter nationality or current display inference'},plan['at'])
                db.execute('INSERT INTO source_institutions(source_id,institution_id) VALUES(%s,%s) ON CONFLICT DO NOTHING',(sid,i['id']))
        for st in states:
            q=st['qid'];x=facts[q];validate_record(x);aid=st['artwork_id'];ap=t['artists'][st['artist_qid']];receipt=run/'metadata-applied'/target/(q+'.json')
            with db.transaction(),db.pipeline():
                db.execute("SET LOCAL lock_timeout='5s'");db.execute('SELECT pg_advisory_xact_lock(559220260916)')
                done=db.execute("SELECT 1 FROM citations WHERE entity_type='artwork' AND entity_id=%s AND source_id=%s AND field_name='austrian_museum_identity'",(aid,sid)).fetchone()
                if done:stats['already_applied']+=1;continue
                ar=db.execute('SELECT id::text,status FROM artists WHERE id=%s',(ap['id'],)).fetchone();newartist=False
                if not ar:
                    assert ap['new'];assert not db.execute('SELECT 1 FROM artists WHERE normalized_name=%s',(r.norm(ap['name']),)).fetchone(),'Concurrent named artist collision'
                    db.execute("INSERT INTO artists(id,slug,display_name,sort_name,normalized_name,entity_type,birth_year,death_year,timeline_start_year,timeline_end_year,timeline_display,timeline_basis,active_start_year,active_end_year,activity_display,status,created_by,updated_by) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'review',%s,%s)",(ap['id'],ap['slug'],ap['name'],ap['name'],r.norm(ap['name']),ap.get('entity_type','person'),ap['birth'],ap['death'],ap['first'],ap['last'],str(ap['first'])+'–'+str(ap['last']),ap['basis'],ap['first'] if ap['basis']=='activity' else None,ap['last'] if ap['basis']=='activity' else None,('Documented artwork: '+str(ap['first'])+'–'+str(ap['last'])) if ap['basis']=='activity' else None,core.ACTOR,core.ACTOR));newartist=True
                else:assert ar['status']!='archived'
                authority(db,'artist',ap['id'],ap['qid'],sid,x['creator_capture']['retrieved_at'])
                citation(db,'artist',ap['id'],'authority_identity_and_dates',sid,ap['qid'],x['creator_capture']['source_url'],{'source_sha256':x['creator_capture']['evidence_sha256'],'metadata_license':CC0,'birth_year':ap['birth'],'death_year':ap['death'],'timeline_basis':ap['basis'],'note':'Existing artist dates are preserved. Activity dates are documented artwork dates, not invented life dates.'},x['creator_capture']['retrieved_at'])
                for c in ap['countries']:
                    db.execute("INSERT INTO artist_countries(artist_id,country_code,relationship_type,is_primary,note) SELECT %s,%s,'citizenship',false,%s WHERE EXISTS(SELECT 1 FROM countries WHERE code=%s) ON CONFLICT DO NOTHING",(ap['id'],c['code'],'Explicit Wikidata P27 country '+c['qid']+'; '+c['source_url']+'. Museum location is independent.',c['code']))
                if ap['countries']:citation(db,'artist',ap['id'],'source_country_citizenship',sid,ap['qid'],x['creator_capture']['source_url'],{'countries':ap['countries'],'metadata_license':CC0},x['creator_capture']['retrieved_at'])
                current=db.execute('SELECT id::text,slug,status,revision,current_institution_id::text FROM artworks WHERE id=%s FOR UPDATE',(aid,)).fetchone()
                if st['action']=='new':
                    assert not current,'Unexpected existing artwork without research citation'
                    assert not db.execute("SELECT 1 FROM external_identifiers WHERE entity_type='artwork' AND scheme='wikidata' AND external_id=%s",(q,)).fetchone(),'Concurrent object authority'
                    if x['accession']:assert not db.execute('SELECT 1 FROM artworks WHERE current_institution_id=%s AND accession_number=%s',(st['institution_id'],x['accession'])).fetchone(),'Concurrent institutional accession'
                    d=x['date'];db.execute("INSERT INTO artworks(id,slug,title,normalized_title,alternate_title,date_display,creation_year_start,creation_year_end,date_precision,work_type,current_institution_id,accession_number,status,research_candidate,created_by,updated_by) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,'painting',%s,%s,'review',true,%s,%s)",(aid,st['slug'],x['title'],r.norm(x['title']),next((a for a in x['titles'] if a!=x['title']),None),d['display'],d['first'],d['last'],d['precision'],st['institution_id'],x['accession'],core.ACTOR,core.ACTOR))
                    db.execute("INSERT INTO artwork_artists(artwork_id,artist_id,attribution_role,attribution_note) VALUES(%s,%s,'primary','Unqualified source creator authority; full evidence retained for editorial review.')",(aid,ap['id']))
                    db.execute("INSERT INTO artwork_location_assertions(artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state) VALUES(%s,'holding',%s,'collection',%s,%s,'Current non-expired Wikidata P195 institutional collection statement. A documented museum connection, not an on-view assertion.',%s,'accepted')",(aid,st['institution_id'],sid,x['entity_capture']['source_url'],x['entity_capture']['retrieved_at']))
                else:
                    assert current and all(current[k]==st['existing'][k] for k in ('slug','status','revision','current_institution_id')),'Existing artwork changed since review'
                authority(db,'artwork',aid,q,sid,x['entity_capture']['retrieved_at'])
                citation(db,'artwork',aid,'austrian_museum_identity',sid,q,x['entity_capture']['source_url'],{'source_sha256':x['entity_capture']['evidence_sha256'],'metadata_license':CC0,'title':x['title'],'artist_authority':x['creator_qid'],'date':x['date'],'object_type':'painting','museum_authority':x['institution_qid'],'museum_country':'AT','accession':x['accession'],'image_status':'Separately verified licence required; this metadata import does not grant image reuse rights.'},x['entity_capture']['retrieved_at'])
                if x.get('primary_wien'):
                    native=x['primary_wien'];citation(db,'artwork',aid,'official_object_identity',sid,native['object_id'],native['url'],{'facts':native['facts'],'maker':native['makers'],'source_sha256':native['capture']['sha256'],'metadata_terms':'https://sammlung.wienmuseum.at/ueber-uns/','scope':'Factual catalogue fields only; no authored description imported.'},native['capture']['retrieved_at'])
            result={'at':core.now(),'artwork_id':aid,'qid':q,'action':st['action'],'new_artist':newartist,'target':target,'status':'review' if st['action']=='new' else st['existing']['status']};core.save_new(receipt,result);stats[st['action']]+=1;stats['new_artists']+=int(newartist)
            if sum(stats[k] for k in ('new','existing','already_applied'))%25==0:print(core.now(),target,dict(stats),flush=True)
    core.save_new(run/(target+'-metadata-result'+('-canary' if limit else '')+'.json'),{'at':core.now(),'counts':dict(stats)});print(target,dict(stats),flush=True)

def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['plan','apply']);p.add_argument('--run',type=Path,required=True);p.add_argument('--target',choices=['local','cloud']);p.add_argument('--limit',type=int,default=0);a=p.parse_args();plan(a.run) if a.command=='plan' else apply(a.run,a.target,a.limit)
if __name__=='__main__':main()
