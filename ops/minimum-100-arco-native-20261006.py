#!/usr/bin/env python3
"""Selected official Italian object pages; no image downloads or local DB writes."""
import argparse, collections, gzip, importlib.util, json, re, threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from bs4 import BeautifulSoup

spec=importlib.util.spec_from_file_location('minimum_campaign',Path(__file__).with_name('all-museums-minimum-100-20261006.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
a=c.module('minimum_arco','museum-expansion-arco-20261006.py')
RUN=c.RUN/'arco';a.RUN=RUN
INDEX=c.ROOT/'docs/research/museum-expansion-20261006/arco/rechecks/qualified-index-06/index-review-summary.json.gz'
TYPES={'dipinto':'painting','disegno':'drawing','stampa':'print','acquerello':'watercolor'}
SOURCE_STOP=threading.Event()


def native(raw,candidate):
    f=a.fields(raw);scope=candidate['scope'];authority=scope['authority'];discovery=candidate['index_row']
    uri=discovery['work'];key=uri.removeprefix('https://w3id.org/arco/resource/')
    if f.get('CODICE DI CATALOGO NAZIONALE')!=key.rsplit('/',1)[-1]:return None,'native_id_conflict'
    if not f['title'] or not f['date']:return None,'missing_native_title_or_creation_date'
    dates=a.numeric_date(f['date'])
    if not dates or dates!=a.numeric_date(discovery['date']):return None,'index_native_creation_date_conflict'
    kind=f.get('OGGETTO')
    if kind not in TYPES or kind!=discovery['type']:return None,'native_type_or_component_requires_review'
    suffix=authority['source_institution_uri'].removeprefix('https://w3id.org/arco/resource/')
    if len(f.get('museum_links',[]))!=1 or not f['museum_links'][0].rstrip('/').endswith('/'+suffix):return None,'native_museum_identity_conflict'
    if c.norm(f.get('LUOGO DI CONSERVAZIONE')) not in {c.norm(v)for v in authority['source_names']}:return None,'native_museum_name_conflict'
    if ' '.join(authority['catalogue_city'].split()) not in ' '.join((f.get('INDIRIZZO')or '').split()):return None,'native_museum_city_conflict'
    legal=c.norm(f.get('CONDIZIONE GIURIDICA'))
    if legal not in {'proprieta stato','proprieta ente pubblico territoriale','proprieta ente pubblico non territoriale','proprieta ente religioso cattolico','detenzione stato','detenzione ente pubblico territoriale','detenzione ente pubblico non territoriale'}:return None,'native_custody_requires_review'
    narrative=' '.join(v for k,v in f.items()if isinstance(v,str)and k not in ['title','date'])
    if re.search(r'\b(deposito|prestito|comodato|rubat\w*|furt\w*|dispers\w*|restitu\w*|privat\w*)\b',c.norm(narrative)):return None,'qualified_or_historical_custody_requires_review'
    if re.search(r'inventario.*corrisponde.{0,40}altro|campi.{0,40}andrebbero.{0,40}omess',c.norm(narrative)):return None,'publisher_flags_incorrect_inventory_or_fields'
    # The object's own embedded label preserves cataloguing category and
    # attribution qualifiers which the visible creator field can omit.
    soup=BeautifulSoup(raw,'html.parser');maps=[]
    for script in soup.find_all('script'):
        match=re.search(r'var addressPoints\s*=\s*(\[.*?\]);',script.get_text(),re.S)
        if match:maps.extend(json.loads(match[1]))
    if maps:
        if any(x.get('typeOfRes')!='/'+key for x in maps):return None,'native_object_label_identity_requires_review'
        labels={v for x in maps for v in x.get('site_label',[])+x.get('cis_label',[])}
        if len(labels)!=1:return None,'native_object_label_ambiguity'
        label=next(iter(labels))
        if not re.search(r'\('+re.escape(kind)+r'(?:, opera isolata)?\)',label):return None,'native_ensemble_or_component_requires_review'
    else:
        # Older catalogue pages have no map when object coordinates are absent.
        # National object ID, explicit museum URI/name/city and canonical URL
        # still establish identity. Do not invent a missing object-category label.
        canonical=soup.find('meta',property='og:url')
        if not canonical or re.sub(r'^https?://','',canonical.get('content',''))!='catalogo.cultura.gov.it/detail/'+key:return None,'native_canonical_identity_requires_review'
        label=None
    if re.search(r'\b(serie|insieme|scomparto|frammento|pendant|ciclo|bozzett[oi] per)\b',label or f['title'],re.I):return None,'native_version_requires_review'
    if re.search(r'\b(serie|scomparti|polittico|smembrat\w*|framment\w*|pendant|undici|dodici)\b',c.norm(f.get('NOTIZIE STORICO CRITICHE'))):return None,'native_narrative_object_relationship_requires_review'
    creator=f.get('ATTRIBUZIONI')or f.get('AMBITO CULTURALE')or None
    qualifiers={q.strip()for q in re.findall(r'\(([^()]*(?:attribuit|bottega|scuola|ambito|cerchia|seguace|maniera|copia|copista)[^()]*)\)',label or '',re.I)}
    missing=sorted(q for q in qualifiers if creator and c.norm(q)not in c.norm(creator))
    if missing:creator+='; '+'; '.join(missing)
    # ALTRE ATTRIBUZIONI is historical research, never a definite creator.
    facts=dict(title=f['title'],creator_label=creator,first=dates[0],last=dates[1],date_precision=dates[2],date_display=f['date'],
        work_type=TYPES[kind],medium=f.get('MATERIA E TECNICA')or None,dimensions=f.get('MISURE')or None,
        accession=f.get("NUMERO D'INVENTARIO")or None,source_url='https://catalogo.cultura.gov.it/detail/'+key,
        holding_basis='Official Italian national catalogue object page explicitly names the reviewed museum URI, name and city. Native national ID, creation date, original object-category label and attribution qualifications retained. Missing category qualifications remain unknown. Catalogue-recorded custody only; no current display or independent legal ownership claim.')
    return dict(facts=facts,native_fields=f,object_label=label),None


def selection(pass_name,museum_limit,page_limit):
    dest=RUN/pass_name/'selection.json.gz'
    if dest.exists():return c.load(dest)
    index=c.load(INDEX);grouped=collections.defaultdict(list);authority_ids=collections.defaultdict(set)
    for scope in a.scopes():authority_ids[(scope['authority']['source_institution_uri'],scope['authority']['catalogue_city'])].add(scope['museum']['id'])
    holds=[]
    for review in index['reviews']:
        iid=review['museum']['id']
        if iid not in c.BASE:continue
        if len(authority_ids[(review['authority']['source_institution_uri'],review['authority']['catalogue_city'])])!=1:
            holds.append(dict(museum_id=iid,reason='duplicate_museum_authorities_require_reconciliation'));continue
        if not review.get('body_path'):continue
        raw=gzip.decompress((c.ROOT/review['body_path']).read_bytes())
        assert c.d.sha(raw)==review['source_receipt']['sha256']and review['source_receipt']['status']==200
        actual=[{k:v['value']for k,v in row.items()}for row in json.loads(raw)['results']['bindings']]
        for row in review.get('candidate_source_ids',[]):
            assert row in actual
            if row['type']not in TYPES or not a.numeric_date(row['date']):continue
            grouped[iid].append(dict(index_row=row,scope=dict(museum=review['museum'],authority=review['authority']),
                index_receipt=review['source_receipt'],index_body_path=review['body_path']))
    with c.d.connect()as db:
        institutions={x['v']['id']:x['v']for x in db.execute('SELECT to_jsonb(i) v FROM institutions i WHERE id=ANY(%s::uuid[])',(list(grouped),))}
        counts={x['id']:x for x in db.execute("SELECT i.id::text,count(a.id) linked,count(a.id)FILTER(WHERE artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision)='eligible')eligible FROM institutions i LEFT JOIN artworks a ON a.current_institution_id=i.id AND a.status<>'archived' WHERE i.id=ANY(%s::uuid[])GROUP BY i.id",(list(grouped),))}
        sourceids={r['key']for r in db.execute("SELECT split_part(canonical_url,'/detail/',2)key FROM external_identifiers WHERE entity_type='artwork'AND canonical_url LIKE '%%catalogo.%%/detail/%%' UNION SELECT split_part(source_url,'/detail/',2) FROM citations WHERE entity_type='artwork'AND source_url LIKE '%%catalogo.%%/detail/%%'")}
    selected=[];museums=[];researched=set()
    for previous in RUN.glob('*/selection.json.gz'):
        if previous==dest:continue
        researched.update(x['index_row']['work']for x in c.load(previous)['candidates'])
    order=sorted(grouped,key=lambda iid:-(len(grouped[iid])/max(1,100-counts[iid]['linked'])))
    for iid in order:
        if counts[iid]['linked']>=100:continue
        if len(museums)>=museum_limit or len(selected)>=page_limit:break
        rows=[];seen=set();bound=min(180,max(12,(100-counts[iid]['linked'])*2+10))
        for row in grouped[iid]:
            key=row['index_row']['work'].removeprefix('https://w3id.org/arco/resource/')
            if key in seen or key in sourceids or row['index_row']['work']in researched:continue
            seen.add(key);rows.append(dict(row,museum=institutions[iid]))
            if len(rows)>=bound or len(selected)+len(rows)>=page_limit:break
        if rows:selected.extend(rows);museums.append(dict(museum=institutions[iid],before=counts[iid],selected=len(rows),source_candidates=len(grouped[iid])))
    value=dict(at=c.d.now(),candidates=selected,museums=museums,held=holds,page_bound=page_limit,museum_bound=museum_limit)
    c.save(dest,value);return value


def one(candidate):
    uri=candidate['index_row']['work'];key=uri.removeprefix('https://w3id.org/arco/resource/')
    if SOURCE_STOP.is_set():return None,dict(source_record_id=key,museum_id=candidate['museum']['id'],reason='source_paused_after_access_response')
    try:raw,saved=a.page(uri)
    except Exception as exc:
        if re.search(r'HTTP (403|429)',str(exc)):SOURCE_STOP.set()
        return None,dict(source_record_id=key,museum_id=candidate['museum']['id'],reason='native_page_request_failed',error=type(exc).__name__+': '+str(exc)[:250])
    parsed,reason=native(raw,candidate)
    if reason:return None,dict(source_record_id=key,museum_id=candidate['museum']['id'],reason=reason,source_receipt=saved['receipt'],body_path=saved['body_path'])
    return dict(artwork_id=c.d.uid('arco/'+key),slug=c.OP+'-arco-native-'+key.rsplit('/',1)[-1],source_record_id=key,
        provider='arco-native',origin='verified_native_object',museum=candidate['museum'],facts=parsed['facts'],source_receipt=saved['receipt'],
        body_path=saved['body_path'],raw_source_record=dict(candidate=candidate,native_fields=parsed['native_fields'],object_label=parsed['object_label'])),None


def research(pass_name,museum_limit,page_limit):
    selected=selection(pass_name,museum_limit,page_limit);ready=[];held=list(selected['held'])
    # Two concurrent metadata requests; the source helper waits before each.
    with ThreadPoolExecutor(max_workers=2)as pool:
        for n,(row,hold)in enumerate(pool.map(one,selected['candidates']),1):
            if row:ready.append(row)
            if hold:held.append(hold)
            if n%10==0:print(pass_name,n,'/',len(selected['candidates']),'ready',len(ready),'held',len(held),flush=True)
    c.prepare_wave(pass_name,ready,held)


ORIGINAL_CHECK=c.check_body
def check_body(row,cache):
    if row['provider']!='arco-native':return ORIGINAL_CHECK(row,cache)
    rc=row['source_receipt'];raw=gzip.decompress((c.ROOT/row['body_path']).read_bytes())
    assert c.d.sha(raw)==rc['sha256']and rc['status']==200 and rc['url']==row['facts']['source_url']
    candidate=row['raw_source_record']['candidate'];parsed,reason=native(raw,candidate)
    assert not reason and parsed['facts']==row['facts']and parsed['native_fields']==row['raw_source_record']['native_fields']and parsed['object_label']==row['raw_source_record']['object_label']
    ir=candidate['index_receipt'];indexraw=gzip.decompress((c.ROOT/candidate['index_body_path']).read_bytes())
    assert c.d.sha(indexraw)==ir['sha256']and ir['status']==200
    rows=[{k:v['value']for k,v in x.items()}for x in json.loads(indexraw)['results']['bindings']]
    assert candidate['index_row']in rows and candidate['index_row']['work']=='https://w3id.org/arco/resource/'+row['source_record_id']


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['research','plan','apply']);p.add_argument('--wave',required=True);p.add_argument('--museums',type=int,default=10);p.add_argument('--pages',type=int,default=350);args=p.parse_args()
    if args.phase=='research':research(args.wave,args.museums,args.pages)
    else:
        c.d.TARGET_FIELD='linked';c.d.DEFAULT_CONFIDENCE=0.9;c.d.SOURCE_BASE_URL='https://catalogo.cultura.gov.it/'
        c.d.CONFIDENCE_BASIS='Exact official national object ID, explicit museum URI/name/city, original title/date and catalogue creator/custody labels. Missing map or category data remains unknown. Documented custody does not assert legal ownership or current display. Editorial assessment, not a calibrated probability.'
        c.check_body=check_body;c.delivery(args.phase,args.wave)
