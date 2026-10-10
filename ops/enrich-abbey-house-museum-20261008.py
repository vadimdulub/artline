#!/usr/bin/env python3
"""Selected Abbey House Museum research and evidence-preserving enrichment."""
import argparse, collections, concurrent.futures, gzip, hashlib, importlib.util, json, re, uuid, subprocess
from pathlib import Path
from urllib.parse import urlencode, quote
from bs4 import BeautifulSoup
from psycopg.types.json import Jsonb
from psycopg import sql

ROOT=Path(__file__).resolve().parents[1]
def module(name,filename):
    spec=importlib.util.spec_from_file_location(name,ROOT/'ops'/filename)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
q=module('abbey_connection','research-production-wikiart-images-20261006.py')
h=module('abbey_capture','research-havre-rouen-cyprus-20261006.py')
OP='abbey-house-museum-20261008';RUN=ROOT/'docs/research'/OP
BACKUP=Path.home()/'Library/Application Support/Artline/backups'/OP
ARCHIVE=Path.home()/'Library/Application Support/Artline/source-images'/OP
h.RUN=RUN;q.r.RUN=RUN
IID='e444f120-1389-5e14-935c-ea581b8b29f8';QID='Q4664027'
load=h.load;save=h.save;capture=h.capture;connect=q.r.connect;now=h.now;norm=h.norm
ACTOR='local-european-research'
def uid(value):return str(uuid.uuid5(uuid.NAMESPACE_URL,OP+'/'+value))
def snapshot(db,ids):return module('abbey_snapshot','promote-local-image-recovery-20261008.py').snapshot(db,ids)
def pin(path):return dict(path=str(path.relative_to(ROOT)),sha256=h.sha(path.read_bytes()))
def values(entity,prop):return [x['mainsnak'].get('datavalue',{}).get('value')for x in entity['claims'].get(prop,[])if x.get('rank')!='deprecated']

def discovery():
    query='''SELECT DISTINCT ?item ?itemLabel ?creator ?creatorLabel ?date ?inventory ?artuk WHERE {
      ?item wdt:P195 wd:Q4664027 .
      OPTIONAL {?item wdt:P170 ?creator} OPTIONAL {?item wdt:P571 ?date}
      OPTIONAL {?item wdt:P217 ?inventory} OPTIONAL {?item wdt:P4704 ?artuk}
      SERVICE wikibase:label {bd:serviceParam wikibase:language "en".}
    } LIMIT 200'''
    urls={
      'official':'https://museumsandgalleries.leeds.gov.uk/abbey-house-museum-trlc',
      'artuk-venue':'https://artuk.org/visit/venues/abbey-house-museum-leeds-museums-and-galleries-4869',
      'commons-category':'https://commons.wikimedia.org/w/api.php?'+urlencode(dict(action='query',list='categorymembers',cmtitle='Category:Abbey House Museum',cmlimit=100,format='json')),
      'wikidata-collection':'https://query.wikidata.org/sparql?'+urlencode(dict(query=query,format='json')),
      'museum-entity':'https://www.wikidata.org/wiki/Special:EntityData/Q4664027.json',
    }
    for tag,url in urls.items():
        dest=RUN/'discovery'/(tag+'.json')
        if dest.exists():continue
        raw,rc=capture(url)
        try:body=json.loads(raw)
        except ValueError:
            soup=BeautifulSoup(raw,'html.parser');body=dict(text=soup.get_text(' ',strip=True),links=[dict(label=a.get_text(' ',strip=True),url=a['href'])for a in soup.select('a[href]')])
        save(dest,dict(receipt=rc,data=body))
        print(tag,rc['status'],len(raw),flush=True)
        if tag=='wikidata-collection' and rc['status']==200:
            for item in body.get('results',{}).get('bindings',[]):print(json.dumps({k:v['value']for k,v in item.items()},ensure_ascii=False),flush=True)

def entities():
    bindings=load(RUN/'discovery/wikidata-collection.json')['data']['results']['bindings']
    ids=sorted({b['item']['value'].rsplit('/',1)[1]for b in bindings})
    for qid in ids:
        path=RUN/'entities'/(qid+'.json')
        if path.exists():continue
        raw,rc=capture('https://www.wikidata.org/wiki/Special:EntityData/'+qid+'.json')
        assert rc['status']==200
        entity=json.loads(raw)['entities'][qid]
        save(path,dict(entity=entity,receipt=rc))
        def val(p):return [x['mainsnak'].get('datavalue',{}).get('value')for x in entity['claims'].get(p,[])]
        print(qid,entity.get('labels',{}).get('en',{}).get('value'),json.dumps({p:val(p)for p in ['P170','P2093','P571','P1367','P4704','P217']}),flush=True)

def mds_probe():
    urls={
      'mds-museum':'https://museumdata.uk/object-search/?'+urlencode({'q':'"LEEAG.PA.1927.0805"'}),
      'harding-official':'https://museumsandgalleries.leeds.gov.uk/blog-colonel-harding-s-alterations-to-abbey-house-tk9c',
    }
    for tag,url in urls.items():
        dest=RUN/'discovery'/(tag+'.json')
        if dest.exists():continue
        raw,rc=capture(url);soup=BeautifulSoup(raw,'html.parser')
        save(dest,dict(receipt=rc,text=soup.get_text(' ',strip=True),links=[dict(label=a.get_text(' ',strip=True),url=a['href'])for a in soup.select('a[href]')]))
        print(tag,rc['status'],soup.get_text(' ',strip=True)[:3500],flush=True)

def details():
    names=[];accs=[];qids=[];urls=[];records=[]
    for path in sorted((RUN/'entities').glob('*.json')):
        d=load(path);e=d['entity'];c=e['claims']
        def vals(p):return [x['mainsnak'].get('datavalue',{}).get('value')for x in c.get(p,[])if x.get('rank')!='deprecated']
        title=e['labels']['en']['value'];desc=e['descriptions']['en']['value']
        label=desc.split('painting by ',1)[1].split(', Abbey House Museum',1)[0]
        refs=sorted({sn['datavalue']['value']for claims in c.values()for claim in claims for ref in claim.get('references',[])for sn in ref.get('snaks',{}).get('P854',[])if sn.get('snaktype')=='value'})
        strings={k:vals(k)for k in c if any(isinstance(v,str)for v in vals(k))}
        record=dict(qid=e['id'],title=title,creator_label=label,creator_qids=[v['id']for v in vals('P170')if isinstance(v,dict)],inventories=vals('P217'),source_urls=refs,dates=c.get('P571',[]),strings=strings,receipt=d['receipt'])
        records.append(record);accs+=record['inventories'];qids+=record['creator_qids'];urls+=refs
        names.append(re.sub(r'\s*\([^)]*\)','',label).strip())
        print(e['id'],label,'refs',refs,'dates',json.dumps(c.get('P571',[]),ensure_ascii=False)[:800],flush=True)
    save(RUN/'source-records.json',records)
    with connect('production')as db:
        exact=db.execute("SELECT to_jsonb(a) artwork FROM artworks a WHERE accession_number=ANY(%s) OR normalized_title=ANY(%s)",(accs,[norm(x['title'])for x in records])).fetchall()
        authority=db.execute("SELECT DISTINCT ar.id FROM artists ar LEFT JOIN external_identifiers e ON e.entity_type='artist' AND e.entity_id=ar.id WHERE (e.scheme='wikidata' AND e.external_id=ANY(%s)) OR ar.normalized_name=ANY(%s)",(qids,[norm(x)for x in names])).fetchall()
        artist_ids=[x['id']for x in authority]
        artists=db.execute("SELECT to_jsonb(ar) artist,coalesce((SELECT jsonb_agg(to_jsonb(e)) FROM external_identifiers e WHERE e.entity_type='artist' AND e.entity_id=ar.id),'[]') identifiers FROM artists ar WHERE id=ANY(%s::uuid[])",(artist_ids,)).fetchall()
        creator_works=db.execute('SELECT DISTINCT a.id FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id WHERE aa.artist_id=ANY(%s::uuid[]) AND (a.normalized_title=ANY(%s) OR a.title ILIKE %s)',(artist_ids,[norm(x['title'])for x in records],'%Kirkstall%')).fetchall()
        ids=sorted({str(x['artwork']['id'])for x in exact}|{str(x['id'])for x in creator_works})
        states=module('abbey_state','promote-local-image-recovery-20261008.py').snapshot(db,ids)
        source_matches=db.execute("SELECT entity_id::text,source_url url FROM citations WHERE entity_type='artwork' AND source_url=ANY(%s) UNION SELECT entity_id::text,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND canonical_url=ANY(%s)",(urls,urls)).fetchall()
    save(RUN/'identity-discovery.json',dict(at=now(),states=states,artists=artists,source_matches=source_matches))
    print('Database title/accession/creator candidates',len(states),'artist identities',len(artists),'source matches',len(source_matches),flush=True)

def mds_collection():
    url='https://museumdata.uk/object-search/?'+urlencode({'q':'Kirkstall','collection[]':'Abbey House Museum'})
    raw,rc=capture(url);soup=BeautifulSoup(raw,'html.parser')
    save(RUN/'discovery/mds-collection.json',dict(receipt=rc,text=soup.get_text(' ',strip=True),links=[dict(label=a.get_text(' ',strip=True),url=a['href'])for a in soup.select('a[href]')]))
    print(rc['status'],soup.get_text(' ',strip=True)[:4500],flush=True)

def commons_metadata():
    for d in load(RUN/'source-records.json'):
        if d['creator_label'].startswith(('British','unknown')):continue
        e=load(RUN/'entities'/(d['qid']+'.json'))['entity']
        files=[x['mainsnak']['datavalue']['value']for x in e['claims'].get('P18',[])]
        if not files:continue
        filename=files[0];url='https://commons.wikimedia.org/w/api.php?'+urlencode(dict(action='query',titles='File:'+filename,prop='imageinfo',iiprop='url|size|sha1|extmetadata',format='json'))
        raw,rc=capture(url);assert rc['status']==200
        body=json.loads(raw);page=next(iter(body['query']['pages'].values()));assert 'missing'not in page
        save(RUN/'commons'/(d['qid']+'.json'),dict(qid=d['qid'],filename=filename,page=page,receipt=rc))
        info=page['imageinfo'][0]
        print(d['qid'],filename,{k:info['extmetadata'].get(k,{}).get('value')for k in ['LicenseShortName','LicenseUrl','Copyrighted','Artist','ImageDescription','Credit']},flush=True)

def prepare():
    assert not(RUN/'plan.json.gz').exists()
    records=load(RUN/'source-records.json');discovery=load(RUN/'identity-discovery.json')
    selected=[];held=[];crosswalk={'Q119710580':'3d5daa34-3906-5a4f-ad29-03bde21d52e7','Q119760365':'f414b1b7-f1f0-54b6-be2c-c049f2fd0f99','Q119020478':'70c184b3-85c0-572c-8a77-35c6790d71ed'}
    evidence=[pin(RUN/'source-records.json'),pin(RUN/'identity-discovery.json'),pin(RUN/'version-comparison.json'),pin(RUN/'williams-comparison-reference.json'),pin(RUN/'discovery/williams-wikiart.json')]
    for r in records:
        if r['creator_label'].startswith(('British','unknown')):
            held.append(dict(qid=r['qid'],title=r['title'],reason='Anonymous or school attribution retained in discovery; outside this selected named-creator expansion.'));continue
        qid=r['qid'];entity=load(RUN/'entities'/(qid+'.json'))['entity'];evidence.append(pin(RUN/'entities'/(qid+'.json')))
        assert {x['id']for x in values(entity,'P195')}=={QID}
        assert values(entity,'P31')==[dict(**values(entity,'P31')[0])] and values(entity,'P31')[0]['id']=='Q3305213'
        assert len(r['inventories'])==1
        artuk=values(entity,'P1679');assert len(artuk)==1
        creator_strings=[v['datavalue']['value']for claim in entity['claims'].get('P4765',[])for v in claim.get('qualifiers',{}).get('P2093',[])if v.get('snaktype')=='value']
        source_creator=creator_strings[0]if creator_strings else r['creator_label']
        dates=[v for v in r['dates']if v.get('rank')!='deprecated']
        first=last=None;precision='unknown';date='Creation date under review'
        if dates:
            assert len(dates)==1;claim=dates[0];v=claim['mainsnak']['datavalue']['value'];assert v['precision']==9 and v['before']==v['after']==0
            first=last=int(v['time'][1:5]);assert last<=1970
            qualifiers={k:[s.get('datavalue',{}).get('value')for s in ss]for k,ss in claim.get('qualifiers',{}).items()}
            if qualifiers:
                assert set(qualifiers)=={'P1480'}and len(qualifiers['P1480'])==1 and qualifiers['P1480'][0]['id']=='Q5727902'
                precision='circa';date='c. '+str(first)
            else:precision='exact';date=str(first)
        source_qids=r['creator_qids'];matches=[]
        for item in discovery['artists']:
            artist=item['artist'];aqids={v['external_id']for v in item['identifiers']if v['scheme']=='wikidata'}
            by_id=bool(set(source_qids)&aqids)
            by_name=not source_qids and re.sub(r'\s*\([^)]*\)','',r['creator_label']).strip()==artist['display_name']
            if by_id or by_name:matches.append(item)
        assert len(matches)<=1
        artist=matches[0]if matches else None
        materials={x['id']for x in values(entity,'P186')};medium='oil on canvas'if materials=={'Q296955','Q12321255'}else None
        height=values(entity,'P2048');width=values(entity,'P2049');dimensions=None
        if len(height)==len(width)==1 and height[0]['unit']==width[0]['unit']=='http://www.wikidata.org/entity/Q174728':dimensions=height[0]['amount'].lstrip('+')+' × '+width[0]['amount'].lstrip('+')+' cm'
        aid=crosswalk.get(qid,uid('artwork/'+qid));before=discovery['states'].get(aid)
        uncertainty=[]
        if precision=='unknown':uncertainty.append('Source has no creation date. Retain unknown years and review classification; no date inferred from creator or accession.')
        if qid=='Q119020478':uncertainty.append('Existing creator authority is William Williams (1727–1791), whereas the museum-derived source says William Williams of Norwich (1727–1797). The visually identical painting and its 1793 date establish object identity; existing creator link retained for separate authority reconciliation.')
        if qid=='Q119942544':uncertainty.append('Source creator lifespan 1856–1927 differs from existing authority birth year 1850. Exact Wikidata creator identity agrees. Source label preserved; artist biography not rewritten.')
        selected.append(dict(qid=qid,artwork_id=aid,action='enrich'if before else'create',title=r['title'],accession=r['inventories'][0],artuk_id=artuk[0],source_url='https://www.wikidata.org/wiki/'+qid,artuk_url='https://artuk.org/discover/artworks/'+artuk[0],creator_label=source_creator,artist=artist,role='attributed_to'if'attributed to'in source_creator else'primary',first=first,last=last,precision=precision,date_display=date,work_type='painting',medium=medium,dimensions=dimensions,receipt=r['receipt'],confidence=0.99 if qid=='Q119020478'else 0.9,confidence_basis='Explicit Abbey House Museum collection claim, exact accession, source title and Art UK object identifier; creator label retained. WikiArt/Art UK visual composition comparison also confirms the existing 1793 painting.'if qid=='Q119020478'else'Explicit Abbey House Museum collection claim with exact accession and linked Art UK object reference; no inference from subject or a Leeds-wide collection.',uncertainty=uncertainty))
    assert len(selected)==18 and len(held)==8
    with connect('production')as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        allids=[x['artwork_id']for x in selected];before=snapshot(db,allids)
        for row in selected:
            expected=discovery['states'].get(row['artwork_id']);assert before.get(row['artwork_id'])==expected
            if expected:
                a=expected['artwork'];assert a['status']=='review'and a['published_at']is None and a['current_institution_id']in (None,IID)
                assert norm(a['title'])==norm(row['title'])
                assert not a['accession_number']or a['accession_number']==row['accession']
                assert all(x['institution_id']==IID for x in expected['holdings']if x['claim_type']=='holding'and x['review_state']=='accepted'and x['superseded_by']is None)
            row['before']=expected
            row['add_holding']=not expected or not any(x['claim_type']=='holding'and x['review_state']=='accepted'and x['superseded_by']is None for x in expected['holdings'])
            row['updates']={}
            if expected:
                for field,key in [('accession_number','accession'),('medium_text','medium'),('dimensions_text','dimensions')]:
                    if a.get(field)is None and row[key]is not None:row['updates'][field]=row[key]
        expected={x['qid']:x['artwork_id']for x in selected}
        exact=db.execute("SELECT scheme,external_id,entity_id::text FROM external_identifiers WHERE entity_type='artwork' AND ((scheme='wikidata' AND external_id=ANY(%s)) OR external_id=ANY(%s) OR (scheme ~* 'art.?uk' AND external_id=ANY(%s)))",(list(expected),[x['artuk_id']for x in selected],[x['artuk_id'].rsplit('-',1)[1]for x in selected])).fetchall()
        for x in exact:
            row=next(r for r in selected if x['external_id']in (r['qid'],r['artuk_id'],r['artuk_id'].rsplit('-',1)[1]));assert x['entity_id']==row['artwork_id'],'Conflicting source identifier'
        museum=db.execute('SELECT to_jsonb(i) record FROM institutions i WHERE id=%s',(IID,)).fetchone()['record']
        query='SELECT id FROM artworks WHERE current_institution_id=%s AND status<>%s ORDER BY id LIMIT 100'
        query_plan=db.execute('EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) '+query,(IID,'archived')).fetchone()
    plan=dict(at=now(),authorization='User: see Abbey House Museum add more artworks and connect existing ones; go ahead. Production continuation of prior delivery.',records=selected,held=held,museum=museum,evidence=evidence,source_identity_matches=exact,query_plan=query_plan,metadata_source_limitation='Art UK venue HTTP 403; actual captures are Wikidata statements and Commons metadata, with original Art UK references preserved. Museum Data Service searches returned no matches. No claim of a fresh direct Art UK catalogue fetch.',policy='Selected named-creator additions remain review, including unknown dates. Preserve source qualifications, existing creator assignments, images, dates and publication. Museum holdings are not current display.')
    save(RUN/'plan.json.gz',plan);save(RUN/'plan-pin.json',pin(RUN/'plan.json.gz'));save(BACKUP/'plan-and-preimages.json.gz',plan)
    print(json.dumps(dict(selected=len(selected),new=sum(x['action']=='create'for x in selected),existing=sum(x['action']=='enrich'for x in selected),new_holdings=sum(x['add_holding']for x in selected),held=len(held),unknown_dates=sum(x['precision']=='unknown'for x in selected))),flush=True)

def pinned():
    p=RUN/'plan.json.gz';digest=load(RUN/'plan-pin.json')['sha256'];assert h.sha(p.read_bytes())==digest;data=load(p)
    for ref in data['evidence']:assert h.sha((ROOT/ref['path']).read_bytes())==ref['sha256']
    return data,digest

def backup():
    dest=RUN/'cloud-sql-backup.json';assert not dest.exists()
    raw=subprocess.check_output(['gcloud','sql','backups','create','--instance=artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--description=Before Abbey House Museum 18 artwork enrichment 20261008','--format=json'],text=True)
    result=json.loads(raw);save(BACKUP/'cloud-sql-backup-create.json',result)
    print(json.dumps(result),flush=True)

def backup_verify():
    raw=subprocess.check_output(['gcloud','sql','backups','list','--instance=artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--limit=15','--format=json'],text=True)
    rows=json.loads(raw);matches=[r for r in rows if r.get('description')=='Before Abbey House Museum 18 artwork enrichment 20261008']
    assert len(matches)==1 and matches[0]['status']=='SUCCESSFUL'
    save(RUN/'cloud-sql-backup.json',matches[0]);save(BACKUP/'cloud-sql-backup.json',matches[0]);print('Successful backup',matches[0]['id'],flush=True)

def insert(db,table,row):
    db.execute(sql.SQL('INSERT INTO {} ({}) VALUES ({})').format(sql.Identifier(table),sql.SQL(',').join(map(sql.Identifier,row)),sql.SQL(',').join(sql.Placeholder()for _ in row)),list(row.values()))

def check_after(db,plan):
    ids=[r['artwork_id']for r in plan['records']];after=snapshot(db,ids);assert len(after)==len(ids)
    for r in plan['records']:
        x=after[r['artwork_id']];a=x['artwork'];assert a['status']=='review'and a['published_at']is None and a['current_institution_id']==IID
        assert a['accession_number']==r['accession']
        holdings=[x for x in x['holdings']if x['claim_type']=='holding'and x['review_state']=='accepted'and x['superseded_by']is None]
        assert len(holdings)==1 and holdings[0]['institution_id']==IID and holdings[0]['display_state']is None
        external={(e['scheme'],e['external_id'])for e in x['identifiers']}
        assert ('wikidata',r['qid'])in external and ('artuk-artwork',r['artuk_id'])in external
        old=r['before']
        if old:
            allowed={'revision','updated_by','updated_at','current_institution_id'}|set(r['updates'])
            assert {k:v for k,v in a.items()if k not in allowed}=={k:v for k,v in old['artwork'].items()if k not in allowed}
            for field,value in r['updates'].items():assert a[field]==value
            assert a['revision']==old['artwork']['revision']+1
            assert x['creators']==old['creators']and x['attachments']==old['attachments']
            for key in ['identifiers','holdings']:
                existing={v['id']:v for v in x[key]};assert all(existing[v['id']]==v for v in old[key])
        else:
            assert a['title']==r['title']and a['normalized_title']==norm(r['title'])
            assert (a['creation_year_start'],a['creation_year_end'],a['date_precision'],a['date_display'])==(r['first'],r['last'],r['precision'],r['date_display'])
            assert a['medium_text']==r['medium']and a['dimensions_text']==r['dimensions']and a['work_type']=='painting'
            assert a['research_candidate'] and a['primary_media_id']is None and not x['attachments']
            if r['artist']:
                assert len(x['creators'])==1 and x['creators'][0]['artist_id']==r['artist']['artist']['id']and x['creators'][0]['attribution_role']==r['role']
                assert a['unlinked_creator_label']is None
            else:assert not x['creators']and a['unlinked_creator_label']==r['creator_label']
    citations=db.execute("SELECT entity_id::text,evidence_note FROM citations WHERE source_id=%s AND field_name='abbey_house_reconciliation_20261008'",(uid('source'),)).fetchall()
    assert len(citations)==len(ids)and {x['entity_id']for x in citations}==set(ids)
    for x in citations:assert json.loads(x['evidence_note'])['plan_sha256']==load(RUN/'plan-pin.json')['sha256']
    return after

def apply():
    plan,digest=pinned();assert not(RUN/'applied.json').exists();backup=load(RUN/'cloud-sql-backup.json');assert backup['status']=='SUCCESSFUL'
    rows=plan['records'];ids=[r['artwork_id']for r in rows];sid=uid('source')
    with connect('production',readonly=False)as db,db.transaction():
        db.execute('SET LOCAL lock_timeout=10000');db.execute('SELECT pg_advisory_xact_lock(hashtext(%s))',(OP,))
        db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(ids,)).fetchall()
        current=snapshot(db,ids);assert current=={r['artwork_id']:r['before']for r in rows if r['before']},'Concurrent artwork or relationship drift'
        institution=db.execute('SELECT to_jsonb(i) record FROM institutions i WHERE id=%s FOR SHARE',(IID,)).fetchone()['record'];assert institution==plan['museum']
        artists={r['artist']['artist']['id']:r['artist']['artist']for r in rows if r['artist']}
        actual={x['record']['id']:x['record']for x in db.execute('SELECT to_jsonb(a) record FROM artists a WHERE id=ANY(%s::uuid[]) ORDER BY id FOR SHARE',(list(artists),))};assert actual==artists
        mapping={r['qid']:r['artwork_id']for r in rows};mapping.update({r['artuk_id']:r['artwork_id']for r in rows})
        for e in db.execute("SELECT scheme,external_id,entity_id::text FROM external_identifiers WHERE entity_type='artwork' AND ((scheme='wikidata' AND external_id=ANY(%s)) OR external_id=ANY(%s)) FOR SHARE",([r['qid']for r in rows],[r['artuk_id']for r in rows])):assert mapping[e['external_id']]==e['entity_id']
        save(BACKUP/'locked-preimages.json.gz',dict(at=now(),plan_sha256=digest,artworks=current,institution=institution,artists=actual))
        insert(db,'sources',dict(id=sid,slug=OP,name='Abbey House Museum: Wikidata/Art UK object reconciliation, 8 October 2026',source_type='authority_data',base_url='https://www.wikidata.org/',adapter_key=OP))
        for r in rows:
            aid=r['artwork_id'];old=r['before']
            if old:
                changes={**r['updates'], 'revision':old['artwork']['revision']+1,'updated_by':ACTOR}
                db.execute(sql.SQL('UPDATE artworks SET {},updated_at=now() WHERE id=%s').format(sql.SQL(',').join(sql.SQL('{}=%s').format(sql.Identifier(k))for k in changes)),list(changes.values())+[aid])
            else:
                row=dict(id=aid,slug=OP+'-'+r['qid'].lower(),title=r['title'],normalized_title=norm(r['title']),date_display=r['date_display'],creation_year_start=r['first'],creation_year_end=r['last'],date_precision=r['precision'],work_type='painting',medium_text=r['medium'],dimensions_text=r['dimensions'],accession_number=r['accession'],status='review',research_candidate=True,unlinked_creator_label=None if r['artist']else r['creator_label'],created_by=ACTOR,updated_by=ACTOR)
                insert(db,'artworks',row)
                if r['artist']:
                    link=dict(artwork_id=aid,artist_id=r['artist']['artist']['id'],attribution_role=r['role'],representative_order=1,attribution_note='Source creator label: '+r['creator_label']+'. Explicit authority/name concordance retained in reconciliation citation. '+r['source_url'])
                    insert(db,'artwork_artists',link)
                    insert(db,'audit_log',dict(actor_user_id=ACTOR,action='insert',entity_type='artwork_creator_link',entity_id=aid,after_json=Jsonb(link)))
            for scheme,external,url in [('wikidata',r['qid'],r['source_url']),('artuk-artwork',r['artuk_id'],r['artuk_url'])]:
                existing=db.execute("SELECT entity_id::text FROM external_identifiers WHERE scheme=%s AND external_id=%s",(scheme,external)).fetchone()
                if existing:assert existing['entity_id']==aid
                else:
                    link=dict(id=uid('identifier/'+scheme+'/'+external),entity_type='artwork',entity_id=aid,scheme=scheme,external_id=external,canonical_url=url,source_id=sid,retrieved_at=r['receipt']['retrieved_at'])
                    insert(db,'external_identifiers',link);insert(db,'audit_log',dict(actor_user_id=ACTOR,action='insert',entity_type='external_identifier',entity_id=link['id'],after_json=Jsonb(link)))
            note={k:v for k,v in r.items()if k not in ['before','artist']};note.update(plan_sha256=digest,actual_source='Wikidata structured data with preserved Art UK references; direct Art UK access unavailable.',publication='Artwork remains review; no current-display assertion.',confidence_interpretation='Editorial assessment, not a calibrated probability.')
            insert(db,'citations',dict(id=uid('citation/'+r['qid']),entity_type='artwork',entity_id=aid,field_name='abbey_house_reconciliation_20261008',source_id=sid,source_record_id=r['qid'],source_url=r['source_url'],evidence_note=json.dumps(note,ensure_ascii=False),retrieved_at=r['receipt']['retrieved_at'],created_by=ACTOR))
            if r['add_holding']:
                insert(db,'artwork_location_assertions',dict(id=uid('holding/'+r['qid']),artwork_id=aid,claim_type='holding',institution_id=IID,context='collection',source_id=sid,source_url=r['source_url'],evidence_note=json.dumps(dict(confidence=r['confidence'],basis=r['confidence_basis'],accession=r['accession'],artuk_reference=r['artuk_url'],source_sha256=r['receipt']['sha256'],uncertainty=r['uncertainty'],scope='Documented collection holding; no claim of current display.'),ensure_ascii=False),checked_at=r['receipt']['retrieved_at'],review_state='accepted'))
        after=check_after(db,plan)
        save(BACKUP/'transaction-after.json.gz',dict(at=now(),plan_sha256=digest,artworks=after))
    receipt=dict(at=now(),plan_sha256=digest,target='production',new_artworks=sum(r['action']=='create'for r in rows),existing_new_museum_links=sum(bool(r['before'])and r['add_holding']for r in rows),existing_enriched=sum(bool(r['before'])for r in rows),new_painter_links=sum(r['action']=='create'and bool(r['artist'])for r in rows),total_selected=len(rows),new_holding_assertions=sum(r['add_holding']for r in rows),source_identifiers_verified=len(rows)*2,held=plan['held'],catalogue_review_and_images_preserved=True,local_database_changed=False,artwork_ids=ids)
    save(RUN/'applied.json',receipt);print(json.dumps({k:v for k,v in receipt.items()if k not in ['held','artwork_ids']}),flush=True)

def verify():
    plan,digest=pinned();applied=load(RUN/'applied.json');assert applied['plan_sha256']==digest
    with connect('production')as db:
        after=check_after(db,plan)
        count=db.execute("SELECT count(*) total,count(primary_media_id) images FROM artworks WHERE current_institution_id=%s AND status<>'archived'",(IID,)).fetchone()
        assert count['total']==len(plan['records'])
        unaffected=load(RUN/'identity-discovery.json')['states'];ids=[aid for aid in unaffected if aid not in after]
        assert snapshot(db,ids)=={aid:unaffected[aid]for aid in ids},'Unrelated title/version candidates changed'
    checks=[]
    for row in plan['records']:
        url='https://artlines.org/api/backend/v1/museums/'+plan['museum']['slug']+'/works/'+row['artwork_id']
        response=q.r.requests.get(url,timeout=(15,45));body=response.json()if response.status_code==200 else{}
        expected_media=None
        if row['before']and row['before']['artwork']['primary_media_id']:
            expected_media=next(x['media']['storage_path']for x in load(RUN/'version-comparison.json')['media']if x['media']['id']==row['before']['artwork']['primary_media_id'])
        checks.append(dict(artwork_id=row['artwork_id'],url=url,status=response.status_code,actual_title=body.get('title'),actual_media=body.get('media_url'),verified=response.status_code==200 and body.get('title')==row['title']and body.get('media_url')==expected_media))
    result=dict(at=now(),database_records_verified=len(after),museum_counts=count,api_checks=checks,api_verified=sum(x['verified']for x in checks),unrelated_records_unchanged=len(ids),existing_images_and_creators_preserved=True,publication_preserved=True,source_identity_verified=True,local_database_changed=False)
    save(RUN/'verification.json',result);print(json.dumps({k:v for k,v in result.items()if k!='api_checks'}),flush=True);assert all(x['verified']for x in checks)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase');a=p.parse_args();globals()[a.phase]()
