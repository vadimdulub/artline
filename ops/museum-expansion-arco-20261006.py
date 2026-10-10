#!/usr/bin/env python3
"""Bounded Italian national catalogue research for underfilled Artline museums.

Read-only discovery; query each reviewed institution URI AND city. Source
graphs and creation qualifiers, not quota, decide whether an addition is ready.
"""
import argparse
import collections
import csv
import gzip
import hashlib
import importlib.util
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
from urllib.parse import unquote

import requests
from bs4 import BeautifulSoup

spec=importlib.util.spec_from_file_location('campaign',Path(__file__).with_name('museum-expansion-20261006.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
RUN=m.RUN/'arco'
ENDPOINT='https://dati.beniculturali.it/sparql'
REQUEST_METHOD='POST'
CAPTURE_ATTEMPT='initial'
DC='http://purl.org/dc/elements/1.1/'
LOC='https://w3id.org/arco/ontology/location/'
CD='https://w3id.org/arco/ontology/context-description/'
DD='https://w3id.org/arco/ontology/denotative-description/'
CORE='https://w3id.org/arco/ontology/core/'
LABEL='http://www.w3.org/2000/01/rdf-schema#label'
PREFIX='''PREFIX dc: <http://purl.org/dc/elements/1.1/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX loc: <https://w3id.org/arco/ontology/location/>
PREFIX cd: <https://w3id.org/arco/ontology/context-description/>
PREFIX dd: <https://w3id.org/arco/ontology/denotative-description/>
PREFIX core: <https://w3id.org/arco/ontology/core/>
PREFIX cat: <https://w3id.org/arco/ontology/catalogue/>
'''
GRAPH_LINKS={LOC+'hasTimeIndexedTypedLocation',LOC+'hasCulturalPropertyAddress',CD+'hasAuthorshipAttribution',CD+'hasInventorySituation',CD+'hasLegalSituation',CD+'hasDating',LOC+'hasCulturalInstituteOrSite','https://w3id.org/arco/ontology/catalogue/isDescribedByCatalogueRecord'}


def capture(query,prefixes=True):
    query=(PREFIX if prefixes else '')+query
    # Successful legacy responses remain usable and retain their original URL.
    # New endpoint attempts get distinct evidence paths, including failures.
    legacy_keys=[hashlib.sha256(query.encode()).hexdigest()]
    legacy_keys.extend(hashlib.sha256((endpoint+'\n'+query).encode()).hexdigest()
        for endpoint in ['https://dati.cultura.gov.it/sparql','https://dati.beniculturali.it/sparql'])
    request_key=REQUEST_METHOD+'\n'+ENDPOINT+'\n'
    key=hashlib.sha256((request_key+query).encode()).hexdigest()
    dest=RUN/'captures'/(key+'.json.gz')
    if not dest.exists():
        for legacy_key in legacy_keys:
            legacy=RUN/'captures'/(legacy_key+'.json.gz')
            if legacy.exists():dest=legacy;break
    if dest.exists():
        saved=m.load(dest);body=gzip.decompress((m.ROOT/saved['body_path']).read_bytes())
        assert hashlib.sha256(body).hexdigest()==saved['receipt']['sha256']
        assert saved['receipt']['status']==200
        return saved
    receipt_path=RUN/'captures'/(key+'.receipt.json')
    if receipt_path.exists():
        # A failed HTTP response is evidence too. A later named pass may make
        # one separate attempt, but can never replace the failed response.
        prior=m.load(receipt_path)
        assert prior['status']!=200,'Successful source receipt without parsed capture requires review'
        key=hashlib.sha256((request_key+CAPTURE_ATTEMPT+'\n'+query).encode()).hexdigest()
        dest=RUN/'captures'/(key+'.json.gz')
        receipt_path=RUN/'captures'/(key+'.receipt.json')
        if dest.exists():
            saved=m.load(dest);raw=gzip.decompress((m.ROOT/saved['body_path']).read_bytes())
            assert saved['receipt']['status']==200 and hashlib.sha256(raw).hexdigest()==saved['receipt']['sha256']
            return saved
        if receipt_path.exists():raise requests.HTTPError('Retained source HTTP failure in this named pass: '+str(m.load(receipt_path)['status']))
    time.sleep(0.6)
    payload={'query':query,'format':'application/sparql-results+json'}
    assert REQUEST_METHOD in {'GET','POST'}
    request=requests.get if REQUEST_METHOD=='GET' else requests.post
    arguments={'params':payload} if REQUEST_METHOD=='GET' else {'data':payload}
    with request(ENDPOINT,**arguments,
        headers={'User-Agent':'ArtlineMuseumResearch/1.0 (bounded official metadata; no images)'},timeout=(15,80),stream=True) as response:
        raw=b''
        for part in response.iter_content(65536):
            raw+=part
            if len(raw)>12_000_000:raise ValueError('Source response exceeds metadata bound')
        receipt=dict(url=ENDPOINT,final_url=response.url,method=REQUEST_METHOD,request_form=payload,status=response.status_code,retrieved_at=m.now(),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
        bodypath=RUN/'captures'/(key+'.body.gz');bodypath.parent.mkdir(parents=True,exist_ok=True)
        if not bodypath.exists():bodypath.write_bytes(gzip.compress(raw,mtime=0))
        m.save(RUN/'captures'/(key+'.receipt.json'),receipt)
        response.raise_for_status()
    data=json.loads(raw)
    rows=[{k:v['value'] for k,v in row.items()} for row in data['results']['bindings']]
    saved=dict(query=query,receipt=receipt,body_path=str(bodypath.relative_to(m.ROOT)),rows=rows)
    m.save(dest,saved)
    return saved


def scopes():
    return m.load(m.RUN/'arco-research-roster.json')['scopes']


def discovery(scope):
    a=scope['authority'];uri=a['source_institution_uri'];city=a['catalogue_city']
    assert re.fullmatch(r'https://w3id.org/arco/resource/[A-Za-z0-9_/-]+',uri)
    # Bound the result before any object enrichment. All creation dates are
    # preserved here; their full graph is required for eligibility decisions.
    return capture('''SELECT DISTINCT ?work ?type ?date ?title WHERE {
      ?work loc:hasCulturalInstituteOrSite <'''+uri+'''>; dc:coverage '''+json.dumps(city)+'''; dc:type ?type; dc:date ?date .
      FILTER(?type IN ("dipinto","disegno","stampa","acquerello"))
      OPTIONAL { ?work cd:title ?title }
    } ORDER BY ?work LIMIT 601''')


def graphs(uris):
    assert 1<=len(uris)<=15
    assert all(re.fullmatch(r'https://w3id.org/arco/resource/[A-Za-z0-9_/-]+',u) for u in uris)
    for path in (RUN/'captures').glob('*.json.gz'):
        cached=m.load(path)
        if '?link ?s' in cached['query'] and cached['rows'] and 'root' in cached['rows'][0] and set(uris)<={r['root'] for r in cached['rows']}:
            raw=gzip.decompress((m.ROOT/cached['body_path']).read_bytes())
            assert hashlib.sha256(raw).hexdigest()==cached['receipt']['sha256']
            return dict(cached,rows=[r for r in cached['rows'] if r['root'] in uris])
    key=hashlib.sha256('\n'.join(uris).encode()).hexdigest();dest=RUN/'graph-bundles-v2'/(key+'.json.gz')
    if dest.exists():return m.load(dest)
    # Separate exact subject lookups avoid the endpoint's broad join plan.
    # Every original response remains a separate capture, never a fake response.
    ids=' '.join('<'+u+'>' for u in uris)
    roots=capture('SELECT DISTINCT ?root ?s ?p ?o WHERE { VALUES ?root { '+ids+' } ?root ?p ?o . BIND(?root AS ?s) } LIMIT 10001')
    assert len(roots['rows'])<10001
    children={r['o'] for r in roots['rows'] if r['p'] in {LOC+'hasTimeIndexedTypedLocation',CD+'hasInventorySituation'}}
    museums={r['o'] for r in roots['rows'] if r['p']==LOC+'hasCulturalInstituteOrSite'}
    assert all(re.fullmatch(r'https://w3id.org/arco/resource/[A-Za-z0-9_/-]+',u) for u in children|museums)
    child_ids=' '.join('<'+u+'>' for u in sorted(children));museum_ids=' '.join('<'+u+'>' for u in sorted(museums))
    child=capture('SELECT DISTINCT ?s ?p ?o WHERE { VALUES ?s { '+child_ids+' } ?s ?p ?o } LIMIT 10001')
    labels=capture('SELECT DISTINCT ?s ?p ?o WHERE { VALUES ?s { '+museum_ids+' } ?s rdfs:label ?o . BIND(rdfs:label AS ?p) } LIMIT 1001')
    assert len(child['rows'])<10001
    assert len(labels['rows'])<1001
    rows=join_graph_components(roots['rows'],child['rows']+labels['rows'])
    components=[dict(role=role,receipt=c['receipt'],body_path=c['body_path']) for role,c in [('objects',roots),('linked_nodes',child),('museum_labels',labels)]]
    bundle=dict(rows=rows,receipt=roots['receipt'],body_path=roots['body_path'],components=components)
    m.save(dest,bundle);return bundle


def join_graph_components(roots,children):
    rows=list(roots)
    for uri in sorted({r['root'] for r in roots}):
        linked={r['o'] for r in roots if r['root']==uri and r['s']==uri and r['p'] in GRAPH_LINKS}
        rows.extend(dict(root=uri,**r) for r in children if r['s'] in linked)
    return rows


def subject_query(uri):
    assert re.fullmatch(r'https://w3id.org/arco/resource/[A-Za-z0-9_/-]+',uri)
    return 'SELECT ?p ?o WHERE { <'+uri+'> ?p ?o } LIMIT 500'


def join_subject_components(components):
    """Reconstruct exact-subject responses; never infer an uncaptured triple."""
    roots=[];children=[];seen=set()
    for component,values in components:
        subject=component['subject'];role=component['role']
        assert subject not in seen and role in {'object_subject','linked_subject'}
        seen.add(subject)
        assert component['receipt']['request_form']['query']==subject_query(subject)
        assert len(values)<500 and all(set(v)=={'p','o'} for v in values)
        if role=='object_subject':roots.extend(dict(root=subject,s=subject,**v) for v in values)
        else:children.extend(dict(s=subject,**v) for v in values)
    linked={r['o'] for r in roots if r['p'] in GRAPH_LINKS}
    assert {r['s'] for r in children}<=linked
    return join_graph_components(roots,children)


def subject_graphs(uris):
    """Optional recovery route: bounded GETs for individual RDF subjects."""
    assert 1<=len(uris)<=15 and len(set(uris))==len(uris)
    key=hashlib.sha256('\n'.join(uris).encode()).hexdigest()
    prior=RUN/'graph-bundles-v2'/(key+'.json.gz')
    if prior.exists():return m.load(prior)
    dest=RUN/'graph-bundles-subjects-v1'/(key+'.json.gz')
    if dest.exists():return m.load(dest)
    parts=[]
    def read(subject,role):
        result=capture(subject_query(subject),prefixes=False)
        assert len(result['rows'])<500
        component=dict(role=role,subject=subject,receipt=result['receipt'],body_path=result['body_path'])
        parts.append((component,result['rows']))
        return result['rows']
    roots=[]
    for uri in uris:roots.extend(read(uri,'object_subject'))
    linked={r['o'] for r in roots if r['p'] in {LOC+'hasTimeIndexedTypedLocation',CD+'hasInventorySituation',LOC+'hasCulturalInstituteOrSite'}}
    for uri in sorted(linked):read(uri,'linked_subject')
    rows=join_subject_components(parts);components=[c for c,_ in parts]
    bundle=dict(rows=rows,components=components,receipt=components[0]['receipt'],body_path=components[0]['body_path'])
    m.save(dest,bundle);return bundle


def page(uri):
    key=uri.removeprefix('https://w3id.org/arco/resource/')
    assert re.fullmatch(r'[A-Za-z0-9_/-]+',key)
    url='https://catalogo.cultura.gov.it/detail/'+key
    digest=hashlib.sha256(url.encode()).hexdigest();dest=RUN/'pages'/(digest+'.json')
    if dest.exists():
        saved=m.load(dest);raw=gzip.decompress((m.ROOT/saved['body_path']).read_bytes())
        assert hashlib.sha256(raw).hexdigest()==saved['receipt']['sha256']
        assert saved['receipt']['status']==200
        return raw,saved
    time.sleep(0.8)
    with requests.get(url,timeout=(15,35),headers={'User-Agent':'ArtlineMuseumResearch/1.0 (selected catalogue metadata)'},stream=True) as response:
        raw=b''
        for chunk in response.iter_content(65536):
            raw+=chunk
            if len(raw)>3_000_000:raise ValueError('Object HTML exceeds bound')
        rc=dict(url=url,final_url=response.url,retrieved_at=m.now(),status=response.status_code,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
    body=RUN/'pages'/(digest+'.html.gz');body.parent.mkdir(parents=True,exist_ok=True)
    if not body.exists():body.write_bytes(gzip.compress(raw,mtime=0))
    saved=dict(receipt=rc,body_path=str(body.relative_to(m.ROOT)));m.save(dest,saved)
    if rc['status']!=200:raise ValueError('Object source HTTP '+str(rc['status']))
    return raw,saved


def page_probe(uri):
    raw,saved=page(uri);soup=BeautifulSoup(raw,'html.parser')
    for tag in soup.find_all(['h1','h2','h3']):
        if tag.get_text(' ',strip=True):print(str(tag)[:700])
    for text in ['OGGETTO','MATERIA','ATTRIBUZIONI','CODICE DI CATALOGO','1835']:
        for node in soup.find_all(string=re.compile(text,re.I))[:3]:print(str(node.parent.parent)[:1200])


def fields(raw):
    soup=BeautifulSoup(raw,'html.parser');result={}
    for li in soup.select('li.d-flex'):
        label=li.select_one('span.label');value=li.select_one('span.campo')
        if label and value:
            key=label.get_text(' ',strip=True)
            assert key not in result,'Repeated catalogue field'
            result[key]=value.get_text(' ',strip=True)
            if key=='LUOGO DI CONSERVAZIONE':result['museum_links']=[a['href'] for a in value.select('a[href]')]
    title=soup.select_one('h2.title-opera');date=soup.select_one('.desc-opera > span')
    result['title']=title.get_text(' ',strip=True) if title else None
    result['date']=date.get_text(' ',strip=True) if date else None
    return result


def numeric_date(value):
    value=' '.join((value or '').split()).casefold()
    match=re.fullmatch(r'(\d{3,4})\s*[-–]\s*(\d{3,4})',value)
    precision=None
    if match:
        first,last=map(int,match.groups())
    elif re.fullmatch(r'\d{3,4}',value):first=last=int(value)
    else:
        # Preserve explicitly bounded after/before dates without tightening
        # the publisher's endpoints to invented calendar years.
        bounded=re.fullmatch(r'post\s+(\d{3,4})\s*[-–]\s*ante\s+(\d{3,4})',value)
        if not bounded:bounded=re.fullmatch(r'(\d{3,4})\s+post\s*[-–]\s*(\d{3,4})\s+ante',value)
        if bounded:
            first,last=map(int,bounded.groups())
            if first>=last:return None
            precision='range'
        else:
            parts=re.split(r'\s*[-–]\s*',value)
            if len(parts) not in [1,2]:return None
            parsed=[];approximate=False
            for part in parts:
                term=re.fullmatch(r'(?:(ca\.?)\s*)?(\d{3,4})(?:\s*(ca\.?))?',part)
                if not term or (term[1] and term[3]):return None
                parsed.append(int(term[2]));approximate|=bool(term[1] or term[3])
            if not approximate:return None
            first,last=parsed[0],parsed[-1]
            # An approximate boundary exactly at the cutoff needs editorial
            # dating evidence rather than automatic pre-1971 classification.
            if last==1970:return None
            precision='circa' if first==last else 'circa_range'
    if not 100<=first<=last<=1970:return None
    return first,last,precision or ('exact' if first==last else 'range')


def graph_map(rows,uri):
    graph=collections.defaultdict(lambda:collections.defaultdict(set))
    for r in rows:
        assert r['root']==uri
        graph[r['s']][r['p']].add(r['o'])
    return graph


def graph_check(rows,uri,scope):
    graph=graph_map(rows,uri);root=graph[uri];authority=scope['authority']
    kinds=root[DC+'type'];dates=root[DC+'date'];cities=root[DC+'coverage']
    if len(kinds)!=1 or not kinds<={'dipinto','disegno','stampa','acquerello'}:return 'ambiguous_or_unsupported_type'
    if len(dates)!=1 or not numeric_date(next(iter(dates))):return 'creation_date_requires_review'
    if cities!={authority['catalogue_city']}:return 'catalogue_city_conflict'
    current=[u for u in root[LOC+'hasTimeIndexedTypedLocation'] if LOC+'CurrentPhysicalLocation' in graph[u][LOC+'hasLocationType']]
    if len(current)!=1 or graph[current[0]][LOC+'hasCulturalInstituteOrSite']!={authority['source_institution_uri']}:return 'no_unique_current_museum_custody'
    names={m.norm(n) for n in graph[authority['source_institution_uri']][LABEL]}
    if not names & {m.norm(n) for n in authority['source_names']}:return 'museum_label_changed'
    rights=root[DC+'rights'];allowed={'proprieta stato','proprieta ente pubblico territoriale','proprieta ente pubblico non territoriale','proprieta ente religioso cattolico'}
    if not rights or not all(m.norm(v) in allowed for v in rights):return 'legal_status_requires_review'
    custody=' '.join(root[DC+'description']|rights|graph[current[0]][CORE+'specifications'])
    if re.search(r'\b(deposito|prestito|rubat\w*|furt\w*|dispers\w*|restitu\w*|privat\w*)\b',m.norm(custody)):return 'custody_qualification_requires_review'
    if any(values for key,values in root.items() if key.endswith(('/isPartOf','/hasPart'))):return 'component_or_ensemble_requires_review'
    if any(re.search(r'insieme|serie|complesso|scomparto|elemento|pendant',v,re.I) for key,values in root.items() if key.endswith('/hasCulturalPropertyCataloguingCategory') for v in values):return 'series_or_component_requires_review'
    if len(root[CD+'hasDating'])!=1:return 'multiple_creation_phases_require_review'
    return None


def facts(rows,uri,scope,html_fields):
    reason=graph_check(rows,uri,scope)
    if reason:return None,reason
    graph=graph_map(rows,uri);root=graph[uri];f=html_fields
    if not f['title'] or not f['date']:return None,'missing_object_title_or_creation_date'
    dates=numeric_date(f['date'])
    if dates is None:return None,'object_creation_qualification_or_cutoff_review'
    if dates!=numeric_date(next(iter(root[DC+'date']))):return None,'html_graph_creation_conflict'
    if f.get('CODICE DI CATALOGO NAZIONALE') not in root['https://w3id.org/arco/ontology/arco/uniqueIdentifier']:
        return None,'html_graph_catalogue_identifier_conflict'
    museum_suffix=scope['authority']['source_institution_uri'].removeprefix('https://w3id.org/arco/resource/')
    if not any(u.rstrip('/').endswith('/'+museum_suffix) for u in f.get('museum_links',[])):return None,'html_museum_identity_conflict'
    if m.norm(f.get('LUOGO DI CONSERVAZIONE')) not in {m.norm(v) for v in scope['authority']['source_names']}:return None,'html_museum_label_conflict'
    if ' '.join(scope['authority']['catalogue_city'].split()) not in ' '.join((f.get('INDIRIZZO') or '').split()):return None,'html_museum_city_conflict'
    kind=next(iter(root[DC+'type']))
    if not (f.get('OGGETTO')==kind or f.get('OGGETTO')==kind+' (frammento)'):return None,'html_object_type_or_components_require_review'
    if m.norm(f.get('CONDIZIONE GIURIDICA')) not in {m.norm(v) for v in root[DC+'rights']}:return None,'html_graph_legal_status_conflict'
    title_keys={m.norm(v) for v in root[CD+'title']|root[CD+'subject']}
    # The official page joins a named title and its subject with a full stop.
    # Require both literal parts from this same object; no fuzzy title match.
    title_keys.update(m.norm(title+'. '+subject) for title in root[CD+'title'] for subject in root[CD+'subject'])
    if m.norm(f['title']) not in title_keys:return None,'html_graph_title_conflict'
    inventory=set().union(*(graph[u][CD+'inventoryIdentifier'] for u in root[CD+'hasInventorySituation'])) if root[CD+'hasInventorySituation'] else set()
    inventory|=root['https://w3id.org/arco/ontology/arco-lite/alternativeInventoryNumber']
    creator=f.get('ATTRIBUZIONI') or f.get('AMBITO CULTURALE') or None
    # Qualifiers can be absent from the HTML attribution field but present in
    # this object's own label. Preserve them; never use shared agent labels.
    qualifiers={q.strip() for label in root[LABEL] for q in re.findall(r'\(([^()]*(?:attribuit|bottega|scuola|ambito|cerchia|seguace|maniera|copia|copista)[^()]*)\)',label,re.I)}
    missing_qualifiers=sorted(q for q in qualifiers if creator and q not in creator)
    if missing_qualifiers:creator+='; '+ '; '.join(missing_qualifiers)
    return dict(title=f['title'],creator_label=creator,first=dates[0],last=dates[1],date_precision=dates[2],date_display=f['date'],
        work_type={'dipinto':'painting','disegno':'drawing','stampa':'print','acquerello':'watercolor'}[kind],
        medium=f.get('MATERIA E TECNICA') or None,dimensions=f.get('MISURE') or None,accession='; '.join(sorted(inventory)) or None,
        source_url='https://catalogo.cultura.gov.it/detail/'+uri.removeprefix('https://w3id.org/arco/resource/'),
        holding_basis='Italian national catalogue: object-specific HTML and unique current-location graph agree on the reviewed museum and city. Catalogue-recorded custody only; no fresh observation, public display, or legal ownership transfer is asserted.'),None


def existing(museum_id):
    with m.connect() as db:
        urls={row['source_url'].rstrip('/') for row in db.execute("SELECT DISTINCT source_url FROM citations WHERE entity_type='artwork' AND source_url LIKE '%/detail/%'")}
        urls.update(row['canonical_url'].rstrip('/') for row in db.execute("SELECT canonical_url FROM external_identifiers WHERE entity_type='artwork' AND canonical_url LIKE '%/detail/%'"))
        identifiers={u.split('/detail/',1)[1] for u in urls}
        data=db.execute('''WITH selected AS MATERIALIZED (
            SELECT id FROM artworks WHERE current_institution_id=%s
            UNION SELECT artwork_id FROM artwork_location_assertions WHERE institution_id=%s AND superseded_by IS NULL
            ) SELECT a.id::text,a.title,a.alternate_title,a.accession_number FROM selected s JOIN artworks a ON a.id=s.id''',(museum_id,museum_id)).fetchall()
        titles={m.norm(r[k]) for r in data for k in ['title','alternate_title'] if r[k]}
        inventories=set().union(*(m.acc(r['accession_number']) for r in data)) if data else set()
        stats=db.execute('''SELECT count(*) works,count(*) FILTER(WHERE artline_creation_scope(creation_year_start,creation_year_end,date_precision)='eligible') eligible FROM artworks WHERE current_institution_id=%s AND status<>'archived' ''',(museum_id,)).fetchone()
    return identifiers,titles,inventories,stats


def research(slug,pass_name='initial'):
    assert re.fullmatch(r'[a-z0-9-]+',pass_name)
    result_root=RUN if pass_name=='initial' else RUN/'rechecks'/pass_name
    dest=result_root/'museums'/(slug+'.json.gz')
    if dest.exists():print(slug,'research already retained',flush=True);return
    selected_scopes=[s for s in scopes() if s['museum']['slug']==slug]
    assert selected_scopes
    museum=selected_scopes[0]['museum'];known,titles,inventories,before=existing(museum['id'])
    goal=max(0,200-before['eligible']);ready=[];held=[];index_receipts=[];inspected=0;seen=set();source_failures=0;consecutive_failures=0
    for scope in selected_scopes:
        if len(ready)>=goal or inspected>=400 or consecutive_failures>=3:break
        try:result=discovery(scope)
        except requests.RequestException as exc:
            source_failures+=1;consecutive_failures+=1
            held.append(dict(scope=scope,reason='source_index_request_failed',error=type(exc).__name__))
            continue
        index_receipts.append(dict(scope=scope,source_receipt=result['receipt'],rows=len(result['rows']),bounded=len(result['rows'])==601))
        candidates=[];by_id=collections.defaultdict(list)
        for row in result['rows']:by_id[row['work']].append(row)
        for uri,rows in by_id.items():
            if uri in seen:continue
            seen.add(uri)
            key=uri.removeprefix('https://w3id.org/arco/resource/')
            if key in known:continue
            if len(rows)!=1 or not numeric_date(rows[0]['date']):
                held.append(dict(uri=uri,reason='discovery_date_or_identity_requires_review'));continue
            candidates.append(uri)
        for offset in range(0,len(candidates),5):
            if len(ready)>=goal or inspected>=400 or consecutive_failures>=3:break
            uris=candidates[offset:offset+5]
            try:captured=graphs(uris)
            except requests.RequestException as exc:
                source_failures+=1;consecutive_failures+=1
                held.extend(dict(uri=uri,reason='source_graph_request_failed',error=type(exc).__name__) for uri in uris)
                print(slug,'graph source failure',source_failures,flush=True);continue
            consecutive_failures=0
            assert len(captured['rows'])<20001,'Graph batch exceeds bound'
            grouped=collections.defaultdict(list)
            for row in captured['rows']:grouped[row['root']].append(row)
            assert set(grouped)==set(uris)
            for uri in uris:
                if len(ready)>=goal or inspected>=400:break
                inspected+=1;triples=grouped[uri];reason=graph_check(triples,uri,scope)
                g=graph_map(triples,uri);root=g[uri]
                source_titles=root[CD+'title']|root[CD+'subject']
                source_inventory=set().union(*(g[u][CD+'inventoryIdentifier'] for u in root[CD+'hasInventorySituation'])) if root[CD+'hasInventorySituation'] else set()
                if not reason and any(m.norm(t) in titles for t in source_titles):reason='existing_or_selected_museum_title_requires_review'
                if not reason and any(m.acc(v)&inventories for v in source_inventory):reason='existing_or_selected_inventory_requires_review'
                if reason:
                    held.append(dict(uri=uri,reason=reason,source_receipt=captured['receipt']));continue
                try:raw,object_capture=page(uri)
                except (requests.RequestException,ValueError) as exc:
                    source_failures+=1;consecutive_failures+=1;held.append(dict(uri=uri,reason='object_page_request_failed',error=type(exc).__name__+': '+str(exc)[:200]))
                    if consecutive_failures>=3:break
                    continue
                consecutive_failures=0
                object_fields=fields(raw);f,reason=facts(triples,uri,scope,object_fields)
                if reason:
                    held.append(dict(uri=uri,reason=reason,object_fields=object_fields,source_receipt=object_capture['receipt']));continue
                record=dict(source_record_id=uri.removeprefix('https://w3id.org/arco/resource/'),museum=museum,facts=f,
                    raw_source_record=dict(uri=uri,graph=triples,scope=scope,object_fields=object_fields,graph_receipt=captured['receipt'],graph_body_path=captured['body_path']),
                    source_receipt=object_capture['receipt'],body_path=object_capture['body_path'])
                if captured.get('components'):record['raw_source_record']['graph_components']=captured['components']
                ready.append(record);titles.add(m.norm(f['title']));inventories.update(m.acc(f['accession']))
            print(slug,'ready',len(ready),'/',goal,'graphs reviewed',inspected,flush=True)
            progress=result_root/'progress'/(slug+f'-{inspected:04d}.json.gz')
            if not progress.exists():m.save(progress,dict(museum=museum,before=before,records=ready,held=held,index_scopes=index_receipts,graphs_reviewed=inspected,partial=True))
    m.save(dest,dict(at=m.now(),museum=museum,before=before,records=ready,held=held,index_scopes=index_receipts,graphs_reviewed=inspected,
        research_status='partial_source_failure' if source_failures else 'bounded_pass_complete',source_failures=source_failures,
        scope_limit='At most 601 index rows per known institution/city scope and 400 new object graphs per museum; stop at 200 eligible works. Incomplete indexes are not collection-completeness claims.'))
    print('Completed',slug,'new',len(ready),'held',len(held),flush=True)


def run(start,count,pass_name='initial'):
    museums={s['museum']['slug']:s['museum'] for s in scopes()}
    ordered=sorted(museums.values(),key=lambda r:(r['works']>=100,-r['works'],r['slug']))
    for museum in ordered[start:start+count]:research(museum['slug'],pass_name)


def validate_record(record,raw):
    original=record['raw_source_record'];uri=original['uri'];scope=original['scope']
    assert scope['museum']['id']==record['museum']['id']
    assert any(s['museum']['id']==record['museum']['id'] and s['authority']==scope['authority'] for s in scopes())
    def read_capture(c):
        body=gzip.decompress((m.ROOT/c['body_path']).read_bytes())
        assert c['receipt']['status']==200 and hashlib.sha256(body).hexdigest()==c['receipt']['sha256']
        return [{k:v['value'] for k,v in row.items()} for row in json.loads(body)['results']['bindings']]
    if original.get('graph_components'):
        components=original['graph_components']
        if any(c['role']=='object_subject' for c in components):
            joined=join_subject_components([(c,read_capture(c)) for c in components])
        else:
            parts={c['role']:read_capture(c) for c in components}
            joined=join_graph_components(parts['objects'],parts['linked_nodes']+parts.get('museum_labels',[]))
        triples=[r for r in joined if r['root']==uri]
    else:
        triples=[r for r in read_capture(dict(receipt=original['graph_receipt'],body_path=original['graph_body_path'])) if r['root']==uri]
    assert triples==original['graph']
    parsed=fields(raw);assert parsed==original['object_fields']
    result,reason=facts(triples,uri,scope,parsed)
    assert not reason,reason
    assert record['source_receipt']['url']==result['source_url']
    return result


def assemble(batch,slugs,pass_name='initial'):
    assert re.fullmatch(r'arco-\d{3}',batch)
    records=[];held=[];museum_summaries=[]
    for slug in slugs:
        result_root=RUN if pass_name=='initial' else RUN/'rechecks'/pass_name
        result=m.load(result_root/'museums'/(slug+'.json.gz'))
        held.extend(result['held']);museum_summaries.append({k:result[k] for k in ['museum','before','graphs_reviewed','research_status','source_failures']})
        for row in result['records']:
            body=gzip.decompress((m.ROOT/row['body_path']).read_bytes())
            assert hashlib.sha256(body).hexdigest()==row['source_receipt']['sha256']
            row['facts']=validate_record(row,body)
            records.append(row)
    repeated={key for key,n in collections.Counter(r['source_record_id'] for r in records).items() if n>1}
    for r in records:
        if r['source_record_id'] in repeated:held.append(dict(uri=r['raw_source_record']['uri'],reason='cross_museum_source_identity_requires_review'))
    records=[r for r in records if r['source_record_id'] not in repeated]
    assert records
    plan=dict(at=m.now(),records=records,held=held,museum_summaries=museum_summaries,
        policy='Object-specific Italian national catalogue pages plus current-location source graphs. Every artwork remains review-only. Source date bounds, anonymous/qualified creator labels and missing inventory preserved. No images, display observations or invented authority profiles.')
    path=m.RUN/(batch+'-current-plan.json.gz');m.save(path,plan)
    print(json.dumps(dict(batch=batch,ready=len(records),museums=len(slugs),plan_sha256=hashlib.sha256(path.read_bytes()).hexdigest())),flush=True)


def discover_all(pass_name='initial'):
    """Bounded first-page metadata review for every queued Italian museum."""
    roster=scopes()
    with m.connect() as db:
        known={r['source_url'].rstrip('/').split('/detail/',1)[1] for r in db.execute("SELECT DISTINCT source_url FROM citations WHERE entity_type='artwork' AND source_url LIKE '%/detail/%'")}
        known.update(r['canonical_url'].rstrip('/').split('/detail/',1)[1] for r in db.execute("SELECT canonical_url FROM external_identifiers WHERE entity_type='artwork' AND canonical_url LIKE '%/detail/%'"))
    def one(scope):
        a=scope['authority'];key=hashlib.sha256((a['source_institution_uri']+'|'+a['catalogue_city']).encode()).hexdigest()
        result_root=RUN if pass_name=='initial' else RUN/'rechecks'/pass_name
        dest=result_root/'index-reviews'/(key+'.json.gz')
        if dest.exists():return m.load(dest)
        prior=RUN/'index-reviews'/(key+'.json.gz')
        if pass_name!='initial' and prior.exists() and m.load(prior)['status']=='bounded_primary_index_reviewed':return m.load(prior)
        row=dict(museum=scope['museum'],authority=a,at=m.now())
        try:
            result=discovery(scope);by_id=collections.defaultdict(list)
            for v in result['rows']:by_id[v['work']].append(v)
            new=[];existing_count=0;dates_held=0
            for uri,objects in by_id.items():
                if uri.removeprefix('https://w3id.org/arco/resource/') in known:existing_count+=1;continue
                if len(objects)!=1 or not numeric_date(objects[0]['date']):dates_held+=1;continue
                new.append(objects[0])
            row.update(source_receipt=result['receipt'],body_path=result['body_path'],rows=len(result['rows']),distinct_source_ids=len(by_id),
                page_capped=len(result['rows'])==601,existing_source_ids=existing_count,source_date_or_identity_holds=dates_held,
                candidate_source_ids=new,candidate_count=len(new),status='bounded_primary_index_reviewed',
                limitation='Candidates require object-specific creation, attribution, institution/city, custody and duplicate checks. This bounded page does not prove collection completeness.')
        except (requests.RequestException,ValueError,AssertionError) as exc:
            row.update(status='source_failure',error=type(exc).__name__+': '+str(exc)[:350])
        m.save(dest,row);return row
    results=[]
    # Two independent, read-only bounded source queries at a time. No images.
    with ThreadPoolExecutor(max_workers=2) as pool:
        jobs=[pool.submit(one,s) for s in roster]
        for job in as_completed(jobs):
            row=job.result();results.append(row)
            if len(results)%10==0 or row['status']=='source_failure':print('Italian museum scopes reviewed',len(results),'/',len(roster),'; latest',row['museum']['slug'],row.get('candidate_count'),row['status'],flush=True)
    summary=dict(at=m.now(),scopes=len(results),distinct_museums=len({r['museum']['id'] for r in results}),successful_scopes=sum(r['status']=='bounded_primary_index_reviewed' for r in results),source_failures=sum(r['status']=='source_failure' for r in results),
        candidate_source_ids=len({v['work'] for r in results for v in r.get('candidate_source_ids',[])}),reviews=sorted(results,key=lambda r:(r['museum']['slug'],r['authority']['source_institution_uri'])))
    result_root=RUN if pass_name=='initial' else RUN/'rechecks'/pass_name
    m.save(result_root/'index-review-summary.json.gz',summary);print('Italian scope review finished:',{k:v for k,v in summary.items() if k!='reviews'},flush=True)


def reassess_index(from_pass,pass_name):
    """Re-evaluate preserved bounded indexes without another source download."""
    assert from_pass!=pass_name
    source_root=RUN if from_pass=='initial' else RUN/'rechecks'/from_pass
    destination=RUN if pass_name=='initial' else RUN/'rechecks'/pass_name
    previous=m.load(source_root/'index-review-summary.json.gz')
    with m.connect() as db:
        known={r['source_url'].rstrip('/').split('/detail/',1)[1] for r in db.execute("SELECT DISTINCT source_url FROM citations WHERE entity_type='artwork' AND source_url LIKE '%/detail/%'")}
        known.update(r['canonical_url'].rstrip('/').split('/detail/',1)[1] for r in db.execute("SELECT canonical_url FROM external_identifiers WHERE entity_type='artwork' AND canonical_url LIKE '%/detail/%'"))
    reviews=[]
    for prior in previous['reviews']:
        row=dict(prior,at=m.now(),reassessment_of=str((source_root/'index-review-summary.json.gz').relative_to(m.ROOT)),
            reassessment_policy='Source-explicit finite dates, bounded post/ante intervals, and circa qualifiers retained; no new HTTP capture. All candidates still require full object and custody checks.')
        if prior['status']=='bounded_primary_index_reviewed':
            body=gzip.decompress((m.ROOT/prior['body_path']).read_bytes())
            assert prior['source_receipt']['status']==200
            assert hashlib.sha256(body).hexdigest()==prior['source_receipt']['sha256']
            values=[{k:v['value'] for k,v in item.items()} for item in json.loads(body)['results']['bindings']]
            assert len(values)==prior['rows']
            grouped=collections.defaultdict(list)
            for item in values:grouped[item['work']].append(item)
            new=[];existing_count=0;holds=0
            for uri,objects in grouped.items():
                if uri.removeprefix('https://w3id.org/arco/resource/') in known:existing_count+=1;continue
                if len(objects)!=1 or not numeric_date(objects[0]['date']):holds+=1;continue
                new.append(objects[0])
            row.update(existing_source_ids=existing_count,source_date_or_identity_holds=holds,candidate_source_ids=new,candidate_count=len(new))
        key=hashlib.sha256((row['authority']['source_institution_uri']+'|'+row['authority']['catalogue_city']).encode()).hexdigest()
        m.save(destination/'index-reviews'/(key+'.json.gz'),row);reviews.append(row)
    summary=dict(at=m.now(),scopes=len(reviews),distinct_museums=len({r['museum']['id'] for r in reviews}),
        successful_scopes=sum(r['status']=='bounded_primary_index_reviewed' for r in reviews),source_failures=sum(r['status']=='source_failure' for r in reviews),
        candidate_source_ids=len({v['work'] for r in reviews for v in r.get('candidate_source_ids',[])}),reviews=reviews)
    m.save(destination/'index-review-summary.json.gz',summary)
    print(json.dumps({k:v for k,v in summary.items() if k!='reviews'}),flush=True)


def export_index(pass_name,label):
    result_root=RUN if pass_name=='initial' else RUN/'rechecks'/pass_name
    summary=m.load(result_root/'index-review-summary.json.gz')
    with m.connect() as db:
        known={r['source_url'].rstrip('/').split('/detail/',1)[1] for r in db.execute("SELECT DISTINCT source_url FROM citations WHERE entity_type='artwork' AND source_url LIKE '%/detail/%'")}
        known.update(r['canonical_url'].rstrip('/').split('/detail/',1)[1] for r in db.execute("SELECT canonical_url FROM external_identifiers WHERE entity_type='artwork' AND canonical_url LIKE '%/detail/%'"))
    candidates=collections.defaultdict(list)
    for review in summary['reviews']:
        for row in review.get('candidate_source_ids',[]):candidates[row['work']].append((review,row))
    rows=[];held=[];already_known=0
    for uri,items in sorted(candidates.items()):
        key=uri.removeprefix('https://w3id.org/arco/resource/')
        if key in known:already_known+=1;continue
        if len({r['museum']['id'] for r,_ in items})!=1:
            held.append(dict(uri=uri,reason='multiple_museum_scopes_require_identity_review',museum_slugs=sorted({r['museum']['slug'] for r,_ in items})));continue
        review,item=items[0]
        rows.append(dict(museum=review['museum']['name'],museum_slug=review['museum']['slug'],catalogue_city=review['authority']['catalogue_city'],
            source_record_id=key,source_title=item.get('title',''),source_creation_range=item['date'],source_type=item['type'],
            source_url='https://catalogo.cultura.gov.it/detail/'+key,status='candidate_requires_object_custody_and_duplicate_checks'))
    destination=RUN/('source-candidates-'+label+'.csv')
    with destination.open('x',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    out=dict(at=m.now(),source_scopes=summary['scopes'],museum_targets=summary['distinct_museums'],source_failures=summary['source_failures'],
        index_candidates=summary['candidate_source_ids'],already_catalogued_at_export=already_known,queued=len(rows),
        candidate_museums=len({r['museum_slug'] for r in rows}),held_cross_museum=len(held),held=held,
        csv=str(destination.relative_to(m.ROOT)),scope='Research queue only. These are unseen primary index identities, not approved artwork facts or new database records. No quota or source-date index value bypasses object-level checks.')
    m.save(RUN/('source-candidate-summary-'+label+'.json'),out)
    print(json.dumps({k:v for k,v in out.items() if k not in ['held','scope']}),flush=True)


def probe(slug):
    scope=next(v for v in scopes() if v['museum']['slug']==slug)
    result=discovery(scope)
    print(json.dumps(dict(museum=scope['museum']['name'],rows=len(result['rows']),sample=result['rows'][:8]),ensure_ascii=False),flush=True)
    uris=list(dict.fromkeys(r['work'] for r in result['rows']))[:3]
    if uris:
        data=graphs(uris);m.save(RUN/'probe.json',dict(scope=scope,index=result,graphs=data))
        for r in data['rows']:
            if r['root']==uris[0] and (r['s']!=r['root'] and ('Dating/' in r['s'] or '/Event/' in r['s'] or 'TimeInterval/' in r['s']) or r['p'] in [DC+'date',CD+'title',LABEL]):
                print(json.dumps(r,ensure_ascii=False),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=['probe','page-probe','research','run','assemble','discover-all','reassess-index','export-index'])
    parser.add_argument('--slug',default='arco-museum-7126033f30f76a37666f')
    parser.add_argument('--start',type=int,default=0);parser.add_argument('--count',type=int,default=10)
    parser.add_argument('--batch',default='arco-001');parser.add_argument('--slugs',nargs='+')
    parser.add_argument('--pass-name',default='initial')
    parser.add_argument('--from-pass',default='ministry-endpoint')
    args=parser.parse_args()
    assert re.fullmatch(r'[a-z0-9-]+',args.pass_name)
    assert re.fullmatch(r'[a-z0-9-]+',args.from_pass)
    CAPTURE_ATTEMPT=args.pass_name
    if args.command=='probe':probe(args.slug)
    elif args.command=='page-probe':page_probe('https://w3id.org/arco/resource/HistoricOrArtisticProperty/1100034601')
    elif args.command=='research':research(args.slug,args.pass_name)
    elif args.command=='run':run(args.start,args.count,args.pass_name)
    elif args.command=='discover-all':discover_all(args.pass_name)
    elif args.command=='reassess-index':reassess_index(args.from_pass,args.pass_name)
    elif args.command=='export-index':export_index(args.pass_name,args.batch)
    else:
        assert args.slugs
        assemble(args.batch,args.slugs,args.pass_name)
