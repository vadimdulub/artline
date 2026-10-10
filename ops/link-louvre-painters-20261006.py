#!/usr/bin/env python3
"""Evidence-backed Louvre painter links; production only, preserving review."""
import argparse, collections, copy, functools, gzip, importlib.util, json, re, time, uuid
from pathlib import Path
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from psycopg.types.json import Jsonb

ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('louvre_round2',ROOT/'ops/resolve-louvre-wikiart-round2-20261006.py')
n=importlib.util.module_from_spec(s);s.loader.exec_module(n)
d=n.d;r=n.r;q=n.q
OLD=ROOT/'docs/research/louvre-wikiart-20261006'
THIRD=ROOT/'docs/research/louvre-wikiart-round3-20261006'
RUN=ROOT/'docs/research/louvre-painter-links-20261006'
r.RUN=RUN;r.PORT=55467
BACKUP=Path.home()/'Library/Application Support/Artline/backups'/RUN.name
ACTOR='local-european-research'

def ident(value):return str(uuid.uuid5(uuid.NAMESPACE_URL,RUN.name+'/'+value))
def records():return r.load(RUN/'production-artworks.json.gz')
def labels():return {x['artwork_id']:x for x in r.load(OLD/'artwork-image-results.json')}
def candidate_records():
    rows=r.load(RUN/'authority-candidates.json');extra=RUN/'additional-authority-candidates.json'
    return rows+(r.load(extra)if extra.exists()else[])
def profile_proposals():
    pointer=RUN/'profile-proposals-pointer.txt'
    return r.load(Path(pointer.read_text()))if pointer.exists()else r.load(RUN/'profile-proposals.json')
def creator_authority(qid):
    return next((p for p in [RUN/'creator-authorities'/(qid+'.json'),THIRD/'creator-authorities'/(qid+'.json')]if p.exists()),None)
def reviewed():
    pointer=RUN/'review-pointer.txt'
    if pointer.exists():return r.load(Path(pointer.read_text()))
    return {'accepted':r.load(RUN/'reviewed-links.json'),'held':r.load(RUN/'review-held.json'),'profiles':r.load(RUN/'profile-matches.json'),'profile_holds':r.load(RUN/'profile-holds.json')}

def audit():
    q.snapshot();works=records();old=labels();names=set();qids=set()
    for row in works:
        w=row['artwork'];prior=old.get(w['id'],{})
        names.update(prior.get('creator_labels',[]))
        if w.get('unlinked_creator_label'):names.add(w['unlinked_creator_label'])
        for lab in prior.get('label_evidence',[]):
            if lab.get('creator'):qids.add(lab['creator'].rsplit('/',1)[-1])
            if lab.get('creatorName'):names.add(lab['creatorName'])
    for qid in qids:
        path=THIRD/'creator-authorities'/(qid+'.json')
        if path.exists():
            entity=r.load(path);names.update(x['value']for x in entity.get('labels',{}).values())
            names.update(x['value']for xs in entity.get('aliases',{}).values()for x in xs)
    linked={a['id']for w in works for a in w['artists']}
    normalized=sorted({r.norm(re.sub(r'\([^)]*\)','',x).strip())for x in names})
    with r.connect('production')as db:
        query='''SELECT DISTINCT a.id FROM artists a WHERE a.status<>'archived' AND
          (a.id=ANY(%s::uuid[]) OR a.normalized_name=ANY(%s) OR a.id IN
           (SELECT artist_id FROM artist_aliases WHERE normalized_alias=ANY(%s)) OR a.id IN
           (SELECT entity_id FROM external_identifiers WHERE entity_type='artist' AND scheme='wikidata' AND external_id=ANY(%s)))'''
        params=(sorted(linked),normalized,normalized,sorted(qids))
        r.save(RUN/'artist-lookup-plan.json',db.execute('EXPLAIN (FORMAT JSON) '+query,params).fetchone())
        ids=[str(x['id'])for x in db.execute(query,params).fetchall()]
        rows=db.execute('''SELECT to_jsonb(a) artist,
          COALESCE((SELECT jsonb_agg(to_jsonb(e) ORDER BY e.scheme) FROM external_identifiers e WHERE e.entity_type='artist' AND e.entity_id=a.id),'[]') identifiers,
          COALESCE((SELECT jsonb_agg(to_jsonb(al) ORDER BY al.id) FROM artist_aliases al WHERE al.artist_id=a.id),'[]') aliases,
          COALESCE((SELECT jsonb_agg(to_jsonb(c) ORDER BY c.id) FROM citations c WHERE c.entity_type='artist' AND c.entity_id=a.id),'[]') citations
          FROM artists a WHERE a.id=ANY(%s::uuid[]) ORDER BY a.id''',(ids,)).fetchall()
        schemes=db.execute("SELECT scheme,count(*) n FROM external_identifiers WHERE entity_type='artist' AND scheme ILIKE '%%wikiart%%' GROUP BY scheme ORDER BY scheme").fetchall()
    r.save_gz(RUN/'scoped-artists.json.gz',rows)
    summary={'at':r.now(),'artworks':len(works),'unlinked':sum(not x['artists']for x in works),'scoped_artists':len(rows),'object_creator_qids':len(qids),'wikiart_schemes':schemes}
    r.save(RUN/'audit.json',summary);print(json.dumps(summary),flush=True)

def inspect():
    old=labels();artists=r.load(RUN/'scoped-artists.json.gz');byqid=collections.defaultdict(list)
    for a in artists:
        for e in a['identifiers']:
            if e['scheme']=='wikidata':byqid[e['external_id']].append(a)
    stats=collections.Counter();examples=collections.defaultdict(list);candidates=[]
    for row in records():
        w=row['artwork']
        if row['artists']:continue
        primary=n.traits(row);prior=old.get(w['id'],{})
        ls=[l for l in prior.get('label_evidence',[])if primary and l.get('joconde')==primary['reference']]
        qs={l['creator'].rsplit('/',1)[-1]for l in ls if l.get('creator')}
        match=[a for qid in qs for a in byqid[qid]]
        status='unique_existing_authority'if len(qs)==1 and len(match)==1 else 'multiple_creators_or_artists'if len(qs)>1 or len(match)>1 else 'authority_not_in_catalogue'if qs else 'no_exact_object_creator'
        stats[status]+=1
        if len(examples[status])<20:examples[status].append([w['id'],w['unlinked_creator_label'],w['title'],sorted(qs)])
        if status=='unique_existing_authority':candidates.append({'artwork_id':w['id'],'before':w,'artist':match[0],'creator_qid':next(iter(qs)),'labels':ls,'primary_object':primary})
    r.save(RUN/'authority-candidates.json',candidates);r.save(RUN/'authority-inspection.json',{'counts':dict(stats),'examples':dict(examples)})
    print(json.dumps({'counts':dict(stats),'examples':dict(examples)},ensure_ascii=False),flush=True)

@functools.lru_cache(maxsize=3000)
def primary_row(path,reference):
    value=r.load(ROOT/path);rows=value.get('data',[])if isinstance(value,dict)else value
    found=[x for x in rows if str(x.get('Reference')or x.get('reference'))==reference]
    assert len(found)==1,(path,reference)
    return found[0]

def profiles():
    artists={x['artist']['id']:x for x in r.load(RUN/'scoped-artists.json.gz')}
    works={x['artwork']['id']:x for x in records()}
    candidates=candidate_records();byartist=collections.defaultdict(list)
    for x in candidates:byartist[x['artist']['artist']['id']].append(x)
    maps={}
    for folder in [ROOT/'docs/research/louvre-wikiart-round2-20261006',THIRD]:
        maps.update({x['artwork_id']:x for x in r.load(folder/'artist-map-v2.json')['records']})
    previous=q.r.RUN;q.r.RUN=OLD
    oldplan=q.load_artist_plan();q.r.RUN=previous
    oldmap={x['artwork_id']:x for x in oldplan['records']}
    sources={};proposals=[]
    for pid,items in byartist.items():
        a=artists[pid];qid=items[0]['creator_qid'];urls=collections.defaultdict(set)
        for e in a['identifiers']:
            if e['scheme']=='wikiart-artist':urls[e['canonical_url']or'https://www.wikiart.org/en/'+e['external_id']].add('existing_catalogue_identifier')
        ap=creator_authority(qid)
        if ap:
            for slug in r.load(ap)['claims'].get('P6002',[]):urls['https://www.wikiart.org/en/'+slug].add('exact_wikidata_P6002')
        for x in items:
            aid=x['artwork_id']
            for src in maps.get(aid,{}).get('sources',[]):urls[src['url']].add('prior_creator_discovery')
            for url in oldmap.get(aid,{}).get('artist_urls',[]):urls[url].add('prior_creator_discovery')
            media=works[aid].get('media')or{};url=media.get('source_page_url')or''
            if url.startswith('https://www.wikiart.org/'):
                path=urlparse(url).path.split('/')
                if len(path)>=4:urls['https://www.wikiart.org/en/'+path[2]].add('attached_same_work_source')
        proposals.append({'artist_id':pid,'creator_qid':qid,'name':a['artist']['display_name'],'artwork_ids':[x['artwork_id']for x in items],'sources':[{'url':u,'basis':sorted(b)}for u,b in sorted(urls.items())]})
        for u in urls:sources[u]=True
    path=RUN/'profile-proposal-versions'/(r.sha(d.core.encode(proposals))+'.json');r.save(path,proposals)
    (RUN/'profile-proposals-pointer.txt').write_text(str(path))
    print('Scoped WikiArt painter profiles',len(sources),'for',len(byartist),'candidate painters',flush=True)
    for i,url in enumerate(sorted(sources),1):
        dest=RUN/'profiles'/(r.sha(url.encode())+'.json')
        if dest.exists():continue
        raw,rc=q.capture(url,'profile-captures');soup=BeautifulSoup(raw,'html.parser')
        heading=soup.select_one('h1');page_name=heading.get_text(' ',strip=True)if heading else ''
        all_names=[page_name]+[x.get_text(' ',strip=True)for x in soup.select('h2')]
        qids=sorted(set(re.findall(r'(?:www\.)?wikidata\.org/(?:wiki/)?(Q\d+)',raw.decode())))
        dates={}
        for prop in ['birthDate','deathDate']:
            el=soup.select_one('[itemprop="'+prop+'"]')
            if el:dates[prop]=el.get('content')or el.get('datetime')or el.get_text(' ',strip=True)
        r.save(dest,{'url':url,'page_name':page_name,'names':all_names,'wikidata_ids':qids,'dates':dates,'receipt':rc,'status':rc['status']})
        if i%25==0:print('Painter profiles checked',i,'of',len(sources),flush=True)

@functools.lru_cache(maxsize=1)
def official_objects():
    result={};arks=collections.defaultdict(set)
    base=ROOT/'docs/research/artwork-locations-20261004'
    for p in (base/'louvre-joconde-crosswalk-20261005c').glob('*.json.gz'):
        value=r.load(p)
        if 'data'not in value:continue
        for x in value['data']:
            if x.get('ark'):arks[x['joconde']].add(x['ark'])
    for ref,values in arks.items():
        if len(values)!=1:continue
        path=base/'louvre-objects-20261005c'/(next(iter(values))+'.json.gz')
        if path.exists():
            value=r.load(path)
            if value.get('object'):result[ref]={'object':value['object'],'receipt':value['source_receipt'],'evidence_path':str(path.relative_to(ROOT))}
    for folder in [THIRD/'object-comparisons',THIRD/'object-comparisons-03']:
        for p in folder.glob('*.json'):
            value=r.load(p);result[value['primary_object']['reference']]={'object':value['museum'],'receipt':value['official_receipt'],'evidence_path':str(p.relative_to(ROOT))}
    return result

def review():
    artists={x['artist']['id']:x for x in r.load(RUN/'scoped-artists.json.gz')}
    canonical={x['url']:x['canonical_url']for x in r.load(RUN/'profile-canonical-urls.json')}if (RUN/'profile-canonical-urls.json').exists()else{}
    links={};profile_holds=[]
    for proposal in profile_proposals():
        a=artists[proposal['artist_id']];qid=proposal['creator_qid']
        names=[a['artist']['display_name']]+[x['alias']for x in a['aliases']]
        authority=creator_authority(qid)
        if authority:
            entity=r.load(authority);names += [x['value']for x in entity.get('labels',{}).values()]
            names += [x['value']for xs in entity.get('aliases',{}).values()for x in xs]
        matched=[]
        for src in proposal['sources']:
            path=RUN/'profiles'/(r.sha(src['url'].encode())+'.json')
            if not path.exists():continue
            profile=r.load(path)
            if profile['status']!=200 or not profile['page_name']:continue
            if profile['wikidata_ids'] and qid not in profile['wikidata_ids']:continue
            authority_slugs=r.load(authority)['claims'].get('P6002',[])if authority else[]
            exact=qid in profile['wikidata_ids'] or urlparse(src['url']).path.split('/')[2]in authority_slugs or 'exact_wikidata_P6002'in src['basis'] or 'existing_catalogue_identifier'in src['basis']
            if not exact and q.namekey(profile['page_name'])not in {q.namekey(x)for x in names}:continue
            # Closed lifespan boundaries corroborate names and identify homonyms.
            conflict=False
            for key,prop in [('birth_year','birthDate'),('death_year','deathDate')]:
                years=re.findall(r'\b(1\d{3}|20\d{2})\b',profile['dates'].get(prop,''))
                if years and a['artist'][key]is not None and int(years[-1])!=a['artist'][key]:conflict=True
            if conflict and not exact:continue
            url=canonical.get(src['url'],src['url']);assert urlparse(url).hostname=='www.wikiart.org'
            matched.append({**src,'url':url,'observed_url':src['url'],'profile_evidence':str(path.relative_to(ROOT)),'profile_name':profile['page_name'],'profile_receipt':profile['receipt'],'creator_authority_evidence':str(authority.relative_to(ROOT))if authority else None,'lifespan_discrepancy_preserved':conflict,'identity_basis':'exact_creator_authority'if exact else'exact_full_creator_name_or_documented_alias','source_slug':urlparse(url).path.split('/')[2]})
        unique={x['source_slug']:x for x in matched}
        if len(unique)==1:links[proposal['artist_id']]=next(iter(unique.values()))
        else:profile_holds.append({**proposal,'reason':'No unique corroborated WikiArt painter profile','matched':list(unique.values())})
    accepted=[];held=[]
    for x in candidate_records():
        pid=x['artist']['artist']['id'];w=x['before'];pr=x['primary_object'];primary=primary_row(pr['evidence_path'],pr['reference'])
        reason=None
        if pid not in links:reason='No unique corroborated WikiArt painter profile'
        elif w['status']!='review' or w['published_at']is not None:reason='Record is not an unpublished review record'
        elif q.namekey(primary.get('Auteur'))!=q.namekey(w.get('unlinked_creator_label')):reason='Museum author label differs from supplied creator label'
        # Qualified labels and copied originals require role-specific review.
        fields={k:primary.get(k)for k in ['Auteur','Precisions_sur_l_auteur','Ancienne_attribution','Genese','Periode_de_l_original_copie']}
        qualifier_text=q.norm(' '.join(str(v or'')for k,v in fields.items()if k!='Ancienne_attribution'))
        if not reason and re.search(r'\b(?:attribue|attribution|atelier|ecole|entourage|suiveur|apres|copie|copy|workshop|circle|follower|anonyme|anonymous|inconnu)\b',qualifier_text):reason='Qualified attribution or copied-original evidence requires individual role review'
        if not reason and fields['Ancienne_attribution']:reason='Historical attribution changes require individual role review'
        official=official_objects().get(pr['reference'])
        if not reason and official:
            creators=[c for c in official['object'].get('creator',[])if c.get('attributionLevel')=='Attribution actuelle'and c.get('wikidata')]
            exact=[c for c in creators if c['wikidata']==x['creator_qid']]
            if len(exact)!=1 or len(creators)!=1:reason='Current Louvre creator differs or has multiple named creators'
            elif any(exact[0].get(k)for k in ['linkType','authenticationType','doubt']):reason='Current Louvre creator attribution is qualified'
        p=x['artist']['artist']
        if not reason and ((w['creation_year_end']is not None and p['birth_year']is not None and w['creation_year_end']<p['birth_year'])or(w['creation_year_start']is not None and p['death_year']is not None and w['creation_year_start']>p['death_year'])):reason='Artwork creation range lies outside documented creator lifespan'
        if reason:held.append({'artwork_id':x['artwork_id'],'title':w['title'],'creator':w['unlinked_creator_label'],'reason':reason,'source_attribution_fields':fields})
        else:accepted.append({**x,'wikiart':links[pid],'source_attribution_fields':fields,'current_louvre_attribution_evidence':official,'identity_basis':x.get('additional_existing_artist_match')or'Exact Louvre/Joconde object creator authority agrees with existing painter Wikidata identity and verified WikiArt profile'})
    value={'profiles':links,'profile_holds':profile_holds,'accepted':accepted,'held':held}
    path=RUN/'review-versions'/(r.sha(d.core.encode(value))+'.json');r.save(path,value)
    (RUN/'review-pointer.txt').write_text(str(path))
    print(json.dumps({'accepted_artwork_links':len(accepted),'unique_painters':len({x['artist']['artist']['id']for x in accepted}),'verified_profiles':len(links),'holds':dict(collections.Counter(x['reason']for x in held))}),flush=True)

def artist_rows(db,ids):
    return {x['artist']['id']:x for x in db.execute('''SELECT to_jsonb(a) artist,
      COALESCE((SELECT jsonb_agg(to_jsonb(e) ORDER BY e.scheme) FROM external_identifiers e WHERE e.entity_type='artist' AND e.entity_id=a.id),'[]') identifiers,
      COALESCE((SELECT jsonb_agg(to_jsonb(c) ORDER BY c.id) FROM citations c WHERE c.entity_type='artist' AND c.entity_id=a.id),'[]') citations
      FROM artists a WHERE a.id=ANY(%s::uuid[]) ORDER BY a.id''',(ids,)).fetchall()}

def plan():
    rows=reviewed()['accepted'];ready=[];held=[];before={}
    ids=[x['artwork_id']for x in rows];pids=sorted({x['artist']['artist']['id']for x in rows})
    with r.connect('production')as db:
        assert db.execute('SELECT current_database() name').fetchone()['name']=='artline'
        assert db.execute('SELECT 1 FROM editor_accounts WHERE user_id=%s',(ACTOR,)).fetchone()
        for start in range(0,len(ids),200):before.update(d.live_records(db,ids[start:start+200]))
        painters=artist_rows(db,pids)
        slugs=sorted({x['wikiart']['source_slug']for x in rows})
        existing={x['external_id']:x for x in db.execute("SELECT * FROM external_identifiers WHERE scheme='wikiart-artist' AND external_id=ANY(%s)",(slugs,)).fetchall()}
        for x in rows:
            aid=x['artwork_id'];pid=x['artist']['artist']['id'];source=x['wikiart'];current=before[aid];painter=painters[pid];reason=None
            if current['artwork']!=x['before']or current['creators']:reason='Artwork changed or already linked since snapshot'
            elif any(painter['artist'][k]!=x['artist']['artist'][k]for k in ['id','slug','display_name','birth_year','death_year','entity_type','status']):reason='Painter identity changed since snapshot'
            elif source['source_slug']in existing and str(existing[source['source_slug']]['entity_id'])!=pid:reason='WikiArt identifier belongs to another existing painter record'
            elif any(e['scheme']=='wikiart-artist'and e['external_id']!=source['source_slug']for e in painter['identifiers']):reason='Painter already has a different WikiArt identifier'
            if reason:held.append({'artwork_id':aid,'painter':painter['artist']['display_name'],'reason':reason});continue
            ready.append({**x,'artist':{'artist':painter['artist'],'identifiers':painter['identifiers']}})
    pids={x['artist']['artist']['id']for x in ready}
    value={'operation':RUN.name,'target':'production','selected':ready,'held':held,
      'before':{x['artwork_id']:before[x['artwork_id']]for x in ready},'painters_before':{pid:painters[pid]for pid in sorted(pids)}}
    digest=r.sha(d.core.encode(value));path=RUN/'plans'/(digest+'.json');r.save(path,value)
    r.save_gz(BACKUP/(digest+'-before.json.gz'),value);(RUN/'plan-pointer.txt').write_text(str(path))
    print(json.dumps({'ready_links':len(ready),'painters':len(pids),'new_wikiart_identifiers':sum(not any(e['scheme']=='wikiart-artist'for e in painters[pid]['identifiers'])for pid in pids),'holds':held,'plan_sha256':digest}),flush=True)

def load_plan():return r.load(Path((RUN/'plan-pointer.txt').read_text()))

def apply():
    plan=load_plan();digest=r.sha(d.core.encode(plan));assert r.load(BACKUP/(digest+'-before.json.gz'))==plan
    selected=plan['selected'];source_id=ident('source');completed=0
    with r.connect('production',readonly=False)as db:
        for start in range(0,len(selected),75):
            batch=selected[start:start+75];receipt=RUN/'applied'/f'{start//75+1:03d}.json'
            if receipt.exists():completed+=len(batch);continue
            ids=[x['artwork_id']for x in batch];pids=sorted({x['artist']['artist']['id']for x in batch});source_rows=[]
            with db.transaction():
                db.execute("SET LOCAL lock_timeout='5s'");db.execute('SELECT pg_advisory_xact_lock(202610062)')
                db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(ids,)).fetchall()
                db.execute('SELECT id FROM artists WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(pids,)).fetchall()
                current=d.live_records(db,ids);painters=artist_rows(db,pids)
                assert all(current[aid]==plan['before'][aid]for aid in ids),'Artwork changed after pinned backup'
                assert all(painters[pid]['artist']==plan['painters_before'][pid]['artist']for pid in pids),'Painter changed after pinned backup'
                db.execute("INSERT INTO sources(id,slug,name,source_type,base_url)VALUES(%s,%s,'Louvre painter identity and WikiArt profile links','authority_data','https://www.wikiart.org/')ON CONFLICT(id) DO NOTHING",(source_id,RUN.name))
                for pid in pids:
                    x=next(x for x in batch if x['artist']['artist']['id']==pid);wiki=x['wikiart'];eid=ident('wikiart/'+pid)
                    existing=db.execute("SELECT * FROM external_identifiers WHERE scheme='wikiart-artist' AND(external_id=%s OR(entity_type='artist'AND entity_id=%s))",(wiki['source_slug'],pid)).fetchall()
                    if existing:
                        assert len(existing)==1 and str(existing[0]['entity_id'])==pid and existing[0]['external_id']==wiki['source_slug']
                    else:
                        row=db.execute("INSERT INTO external_identifiers(id,entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at)VALUES(%s,'artist',%s,'wikiart-artist',%s,%s,%s,%s)RETURNING to_jsonb(external_identifiers) row",(eid,pid,wiki['source_slug'],wiki['url'],source_id,wiki['profile_receipt']['retrieved_at'])).fetchone()['row']
                        db.execute("INSERT INTO audit_log(actor_user_id,action,entity_type,entity_id,request_id,before_json,after_json)VALUES(%s,'insert','external_identifier',%s,%s,NULL,%s)",(ACTOR,eid,RUN.name,Jsonb(row)));source_rows.append(row)
                    evidence={'operation':RUN.name,'plan_sha256':digest,'creator_qid':x['creator_qid'],'identity_basis':wiki['identity_basis'],'profile_evidence':wiki['profile_evidence'],'profile_receipt':wiki['profile_receipt'],'artist_fields_preserved':True}
                    db.execute("INSERT INTO citations(id,entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by)VALUES(%s,'artist',%s,'wikiart_profile_identity',%s,%s,%s,%s,%s,%s)ON CONFLICT(id)DO NOTHING",(ident('artist-citation/'+pid),pid,source_id,wiki['source_slug'],wiki['url'],json.dumps(evidence,ensure_ascii=False),wiki['profile_receipt']['retrieved_at'],ACTOR))
                checks=[]
                with db.pipeline():
                    for x in batch:
                        aid=x['artwork_id'];pid=x['artist']['artist']['id'];wiki=x['wikiart'];label=x['before']['unlinked_creator_label']
                        note=x['identity_basis']+'. Original creator label: '+label+'. Review retained.'
                        checks.append(db.execute("INSERT INTO artwork_artists(artwork_id,artist_id,attribution_role,attribution_note)VALUES(%s,%s,'primary',%s)",(aid,pid,note)))
                        checks.append(db.execute("UPDATE artworks SET unlinked_creator_label=NULL,revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s AND status='review'AND primary_media_id IS NOT DISTINCT FROM %s::uuid AND unlinked_creator_label=%s",(ACTOR,aid,x['before']['primary_media_id'],label)))
                        evidence={'operation':RUN.name,'plan_sha256':digest,'original_creator_label':label,'artist_id':pid,'creator_qid':x['creator_qid'],'identity_basis':x['identity_basis'],'primary_object':x['primary_object'],'object_creator_labels':x['labels'],'source_attribution_fields':x['source_attribution_fields'],'current_louvre_attribution_evidence':x['current_louvre_attribution_evidence'],'wikiart_profile':wiki,'review_status_preserved':True}
                        db.execute("INSERT INTO citations(id,entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by)VALUES(%s,'artwork',%s,'creator_identity_link',%s,%s,%s,%s,%s,%s)",(ident('artwork-citation/'+aid),aid,source_id,x['primary_object']['reference'],x['primary_object']['source_url'],json.dumps(evidence,ensure_ascii=False),wiki['profile_receipt']['retrieved_at'],ACTOR))
                        link={'artwork_id':aid,'artist_id':pid,'attribution_role':'primary','representative_order':None,'attribution_note':note}
                        db.execute("INSERT INTO audit_log(actor_user_id,action,entity_type,entity_id,request_id,before_json,after_json)VALUES(%s,'insert','artwork_creator_link',%s,%s,NULL,%s)",(ACTOR,aid,RUN.name,Jsonb(link)))
                assert all(c.rowcount==1 for c in checks)
                after=d.live_records(db,ids)
                for x in batch:
                    aid=x['artwork_id'];w=after[aid]['artwork'];before=x['before'];allowed={'unlinked_creator_label','revision','updated_at','updated_by'}
                    assert {k:v for k,v in w.items()if k not in allowed}=={k:v for k,v in before.items()if k not in allowed}
                    assert w['unlinked_creator_label']is None and w['revision']==before['revision']+1 and w['status']=='review'
                    assert len(after[aid]['creators'])==1 and after[aid]['creators'][0]['artist_id']==x['artist']['artist']['id']
            r.save_gz(BACKUP/'after'/f'{start//75+1:03d}.json.gz',after)
            r.save(receipt,{'at':r.now(),'plan_sha256':digest,'artwork_ids':ids,'new_source_identifiers':source_rows})
            completed+=len(batch);print('Production painter links',completed,'/',len(selected),flush=True)

def verify():
    plan=load_plan();items=plan['selected'];ids=[x['artwork_id']for x in items]
    pids=sorted(plan['painters_before']);current={};digest=r.sha(d.core.encode(plan))
    with r.connect('production')as db:
        for start in range(0,len(ids),200):current.update(d.live_records(db,ids[start:start+200]))
        painters=artist_rows(db,pids)
        audits=db.execute("SELECT entity_id::text,entity_type,before_json,after_json FROM audit_log WHERE entity_id=ANY(%s::uuid[]) AND entity_type IN ('artwork','artwork_creator_link')",(ids,)).fetchall()
        artwork_audits={x['entity_id']for x in audits if x['entity_type']=='artwork'and x['before_json']==plan['before'][x['entity_id']]['artwork']and x['after_json']==current[x['entity_id']]['artwork']}
        link_audits={x['entity_id']for x in audits if x['entity_type']=='artwork_creator_link'and x['before_json']is None and x['after_json']in current[x['entity_id']]['creators']}
        for x in items:
            aid=x['artwork_id'];before=plan['before'][aid];after=current[aid];w=after['artwork'];allowed={'unlinked_creator_label','revision','updated_at','updated_by'}
            assert {k:v for k,v in w.items()if k not in allowed}=={k:v for k,v in before['artwork'].items()if k not in allowed}
            assert w['unlinked_creator_label']is None and w['revision']==before['artwork']['revision']+1
            assert w['status']=='review'and w['published_at']is None
            assert len(after['creators'])==1 and after['creators'][0]['artist_id']==x['artist']['artist']['id']and after['creators'][0]['attribution_role']=='primary'
            assert before['attachments']==after['attachments']and all(c in after['citations']for c in before['citations'])
            c=next(c for c in after['citations']if c['id']==ident('artwork-citation/'+aid));e=json.loads(c['evidence_note'])
            assert e['original_creator_label']==before['artwork']['unlinked_creator_label']and e['plan_sha256']==digest and e['artist_id']==x['artist']['artist']['id']
            assert aid in artwork_audits and aid in link_audits
        new_identifiers=0
        for pid,painter in painters.items():
            before=plan['painters_before'][pid];assert painter['artist']==before['artist']
            assert all(e in painter['identifiers']for e in before['identifiers'])and all(c in painter['citations']for c in before['citations'])
            item=next(x for x in items if x['artist']['artist']['id']==pid)
            links=[e for e in painter['identifiers']if e['scheme']=='wikiart-artist'];assert len(links)==1 and links[0]['external_id']==item['wikiart']['source_slug']
            assert any(c['id']==ident('artist-citation/'+pid)and c['source_url']==item['wikiart']['url']for c in painter['citations'])
            new_identifiers+=not any(e['scheme']=='wikiart-artist'for e in before['identifiers'])
        museum=items[0]['before']['current_institution_id']
        totals=db.execute('''SELECT count(*) artworks,count(primary_media_id) illustrated,
          count(*)FILTER(WHERE EXISTS(SELECT 1 FROM artwork_artists aa WHERE aa.artwork_id=a.id)) linked,
          count(*)FILTER(WHERE NOT EXISTS(SELECT 1 FROM artwork_artists aa WHERE aa.artwork_id=a.id)) unlinked,
          count(*)FILTER(WHERE status='review') in_review FROM artworks a WHERE current_institution_id=%s''',(museum,)).fetchone()
    for start in range(0,len(items),75):
        backup=r.load(BACKUP/'after'/f'{start//75+1:03d}.json.gz')
        assert all(backup[x['artwork_id']]==current[x['artwork_id']]for x in items[start:start+75])
    print('Production verified',len(items),'artwork links and',len(pids),'painter profiles',flush=True)
    samples=items[::max(1,len(items)//12)][:12];api=[]
    for x in samples:
        url='https://artlines.org/api/backend/v1/museums/musee-du-louvre/works/'+x['artwork_id']
        for attempt in range(3):
            response=r.requests.get(url,timeout=(15,45))
            if response.status_code in (500,502,503,504)and attempt<2:
                time.sleep(2+attempt);continue
            response.raise_for_status();break
        body=response.json();assert body['id']==x['artwork_id']and body['unlinked_creator_label']is None and body['status']=='review'
        assert any(a['id']==x['artist']['artist']['id']and a['role']=='primary'for a in body['artists'])
        assert body['date_display']==x['before']['date_display']and body['creation_year_start']==x['before']['creation_year_start']and body['creation_year_end']==x['before']['creation_year_end']
        old=next(w for w in records()if w['artwork']['id']==x['artwork_id']);assert body['media_url']==((old.get('media')or{}).get('storage_path'))
        api.append({'url':url,'status':response.status_code,'artwork_id':x['artwork_id'],'artist_id':x['artist']['artist']['id'],'checked_at':r.now()})
    r.save(RUN/'production-api-checks.json',api)
    summary={'verified_at':r.now(),'target':'production','artworks_linked':len(items),'painters_linked':len(pids),'new_wikiart_profile_identifiers':new_identifiers,'existing_wikiart_profiles_reused':len(pids)-new_identifiers,
      'artwork_audits_verified':len(artwork_audits),'creator_link_audits_verified':len(link_audits),'live_api_checks':len(api),'louvre_totals':totals,'images_dates_holdings_and_review_preserved':True,'artist_rows_preserved':True,
      'plan_sha256':digest,'backup_directory':str(BACKUP)}
    r.save(RUN/'verification.json',summary);print(json.dumps(summary),flush=True)

def report():
    plan=load_plan();v=r.load(RUN/'verification.json');assert v['plan_sha256']==r.sha(d.core.encode(plan))
    linked={x['artwork_id']:x for x in plan['selected']};painters={};held={x['artwork_id']:x for x in reviewed()['held']}
    held.update({x['artwork_id']:x for x in plan['held']});candidates={x['artwork_id']for x in candidate_records()}
    original={x['artwork_id']:x for x in r.load(RUN/'authority-candidates.json')};outcomes=[];counts=collections.Counter()
    for row in records():
        if row['artists']:continue
        aid=row['artwork']['id']
        if aid in linked:status='Linked to verified existing painter and WikiArt profile'
        elif aid in held:status=held[aid]['reason']
        elif aid not in candidates:status='No unambiguous existing painter identity established in this pass'
        else:status='Further creator identity review required'
        counts[status]+=1;outcomes.append({'artwork_id':aid,'title':row['artwork']['title'],'original_creator_label':row['artwork']['unlinked_creator_label'],'outcome':status,
          'artist_id':linked[aid]['artist']['artist']['id']if aid in linked else None,'wikiart_url':linked[aid]['wikiart']['url']if aid in linked else None,'review_detail':held.get(aid)})
    assert len(outcomes)==2337 and counts['Linked to verified existing painter and WikiArt profile']==v['artworks_linked']
    r.save(RUN/'record-outcomes.json',outcomes)
    for x in plan['selected']:
        p=x['artist']['artist'];entry=painters.setdefault(p['id'],{'artist':p,'wikiart':x['wikiart'],'artwork_ids':[]});entry['artwork_ids'].append(x['artwork_id'])
    r.save(RUN/'linked-painters.json',list(painters.values()))
    def cell(x):return str(x).replace('|','\\|').replace('\n',' ')
    lines=['# Louvre painter links — 6 October 2026','',
      f"**Linked {v['artworks_linked']:,} existing Louvre artworks to {v['painters_linked']:,} verified painter records in production.** Added {v['new_wikiart_profile_identifiers']} WikiArt profile identifiers and reused {v['existing_wikiart_profiles_reused']} existing references. Verified {v['verified_at']}.",'',
      f"Louvre now has **{v['louvre_totals']['linked']:,} artworks with painter links** and **{v['louvre_totals']['unlinked']:,} without a resolved painter link**, out of {v['louvre_totals']['artworks']:,}. All {v['artworks_linked']:,} changed artworks remain unpublished review records. Image coverage remains {v['louvre_totals']['illustrated']:,}; this pass linked painters and did not add images.",'',
      'Selected identities combine exact Louvre/Joconde object references, documented creator authorities, existing catalogue painter identities and live WikiArt profiles. Additional existing-name matches require both museum lifespan years to agree. Qualified, conflicting and historical attributions remain held. Canonical WikiArt URLs reconcile profile aliases; exact authority identifiers can establish identity despite source lifespan discrepancies, which remain documented without rewriting painter dates.','',
      'Original creator labels are preserved in citations, link notes, full backups and audit records. Existing artwork images, dates, holdings, types and review/publication state are unchanged. Existing painter rows are unchanged; no new painters or artworks were created. The Jan Both WikiArt identifier already belongs to a different existing painter record, so those two links remain held for duplicate reconciliation. Giovanni di Paolo/Panini and Andrea di Bartolo/del Castagno were kept separate.','',
      f"Verified all {v['artwork_audits_verified']} artwork audit entries, {v['creator_link_audits_verified']} relationship audit entries, all {v['painters_linked']} painter references, and {v['live_api_checks']} live museum API responses. Target queries were scoped by institution and selected IDs; query plans and source capture checksums are archived.",'',
      '[Production verification](verification.json) · [All 2,337 initial unlinked-record outcomes](record-outcomes.json) · [Linked painters](linked-painters.json) · [Preflight evidence checks](preflight-evidence-checks.json)','',
      f"Backup: `{BACKUP}`. Plan SHA-256: `{v['plan_sha256']}`.",'',
      '## Outcomes','','| Outcome | Records |','| --- | ---: |']
    lines += [f'| {cell(k)} | {n:,} |'for k,n in counts.items()]
    lines += ['', '## Painters linked','','| Painter | Artwork links | WikiArt | Catalogue |','| --- | ---: | --- | --- |']
    for p in sorted(painters.values(),key=lambda p:p['artist']['display_name'].casefold()):
        lines.append(f"| {cell(p['artist']['display_name'])} | {len(p['artwork_ids'])} | [Profile]({p['wikiart']['url']}) | [Painter](https://artlines.org/artists/{p['artist']['slug']}) |")
    lines += ['', '## Artwork links','','| Artwork | Original creator label | Linked painter |','| --- | --- | --- |']
    lines += [f"| {cell(x['before']['title'])} · `{x['artwork_id']}` | {cell(x['before']['unlinked_creator_label'])} | [{cell(x['artist']['artist']['display_name'])}]({x['wikiart']['url']}) |"for x in plan['selected']]
    r.save(RUN/'README.md',('\n'.join(lines)+'\n').encode())
    main=ROOT/'docs/louvre-wikiart-reconciliation-20261006.md';body=main.read_text()
    heading='## Painter-link continuation — 6 October 2026'
    if heading not in body:
        insert=f"{heading}\n\nLinked **{v['artworks_linked']:,} Louvre artworks to {v['painters_linked']} existing painters** in production, adding **{v['new_wikiart_profile_identifiers']} WikiArt profile references**. All changed artworks remain in review; original creator labels, images, dates and holdings are preserved in evidence and audit history. **{v['louvre_totals']['linked']:,} / {v['louvre_totals']['artworks']:,} artworks now have painter links; {v['louvre_totals']['unlinked']:,} remain without one.** Image coverage remains {v['louvre_totals']['illustrated']:,}. [Painter-link report and evidence](research/louvre-painter-links-20261006/README.md).\n\n"
        body=body.replace('## Latest unresolved outcomes',insert+'## Latest unresolved outcomes',1);main.write_text(body)
    print(json.dumps({'verification':v,'outcomes':dict(counts)}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['audit','inspect','profiles','review','plan','apply','verify','report']);a=p.parse_args();globals()[a.command]()
