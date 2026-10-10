#!/usr/bin/env python3
"""Review explicit object-map cities and alternate titles in captured ArCo pages."""
import argparse,collections,gzip,importlib.util,json,re
from pathlib import Path
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('priority',Path(__file__).with_name('museum-1-10-priority-20261007.py'))
p=importlib.util.module_from_spec(s);s.loader.exec_module(p)
c=p.c
old=c.module('priority_arco_base','minimum-100-arco-native-20261006.py')
a=old.a


def native(raw,candidate):
    f=a.fields(raw);authority=candidate['scope']['authority'];discovery=candidate['index_row']
    key=discovery['work'].removeprefix('https://w3id.org/arco/resource/')
    if f.get('CODICE DI CATALOGO NAZIONALE')!=key.rsplit('/',1)[-1]:return None,'native_id_conflict'
    if not f['title']or not f['date']:return None,'missing_native_title_or_creation_date'
    dates=a.numeric_date(f['date'])
    if not dates or dates!=a.numeric_date(discovery['date']):return None,'index_native_creation_date_conflict'
    kind=f.get('OGGETTO')
    if kind not in old.TYPES or kind!=discovery['type']:return None,'native_type_or_component_requires_review'
    suffix=authority['source_institution_uri'].removeprefix('https://w3id.org/arco/resource/')
    if len(f.get('museum_links',[]))!=1 or not f['museum_links'][0].rstrip('/').endswith('/'+suffix):return None,'native_museum_identity_conflict'
    if c.norm(f.get('LUOGO DI CONSERVAZIONE'))not in {c.norm(v)for v in authority['source_names']}:return None,'native_museum_name_conflict'
    soup=BeautifulSoup(raw,'html.parser');maps=[]
    for script in soup.find_all('script'):
        match=re.search(r'var addressPoints\s*=\s*(\[.*?\]);',script.get_text(),re.S)
        if match:maps.extend(json.loads(match[1]))
    if maps and any(x.get('typeOfRes')!='/'+key for x in maps):return None,'native_object_label_identity_requires_review'
    # Some source pages omit the visible address but explicitly give the same
    # object's municipality in their map payload. Preserve the absent address.
    address=' '.join((f.get('INDIRIZZO')or'').split());city=' '.join(authority['catalogue_city'].split())
    map_cities={c.norm(v)for x in maps for v in x.get('site_comune',[])}
    expected_city=c.norm(re.sub(r'\s*\([A-Z]{2}\)\s*$','',city))
    if address:
        if city not in address:return None,'native_museum_city_conflict'
        city_basis='explicit_native_address'
    elif map_cities=={expected_city}:city_basis='explicit_same_object_map_municipality'
    else:return None,'native_museum_city_conflict'
    if map_cities and map_cities!={expected_city}:return None,'native_address_map_city_conflict'
    legal=c.norm(f.get('CONDIZIONE GIURIDICA'))
    if legal not in {'proprieta stato','proprieta ente pubblico territoriale','proprieta ente pubblico non territoriale','proprieta ente religioso cattolico','detenzione stato','detenzione ente pubblico territoriale','detenzione ente pubblico non territoriale'}:return None,'native_custody_requires_review'
    narrative=' '.join(v for k,v in f.items()if isinstance(v,str)and k not in ['title','date'])
    if re.search(r'\b(deposito|prestito|comodato|rubat\w*|furt\w*|dispers\w*|restitu\w*|privat\w*)\b',c.norm(narrative)):return None,'qualified_or_historical_custody_requires_review'
    if re.search(r'inventario.*corrisponde.{0,40}altro|campi.{0,40}andrebbero.{0,40}omess',c.norm(narrative)):return None,'publisher_flags_incorrect_inventory_or_fields'
    labels={v for x in maps for v in x.get('site_label',[])+x.get('cis_label',[])}
    if maps:
        # The payload may repeat plain alternative titles beside one cataloguing
        # label. Keep every label; require a single explicit object-category label.
        typed={v for v in labels if re.search(r'\((?:dipinto|disegno|stampa|acquerello)(?:[,)]|\s)',v)}
        if len(typed)!=1:return None,'native_object_label_ambiguity'
        label=next(iter(typed))
        if not re.search(r'\('+re.escape(kind)+r'(?:, opera isolata)?\)',label):return None,'native_ensemble_or_component_requires_review'
    else:
        canonical=soup.find('meta',property='og:url')
        if not canonical or re.sub(r'^https?://','',canonical.get('content',''))!='catalogo.cultura.gov.it/detail/'+key:return None,'native_canonical_identity_requires_review'
        label=None
    if re.search(r'\b(serie|insieme|scomparto|frammento|pendant|ciclo|bozzett[oi] per)\b',' '.join(labels)or f['title'],re.I):return None,'native_version_requires_review'
    if re.search(r'\b(serie|scomparti|polittico|smembrat\w*|framment\w*|pendant|undici|dodici)\b',c.norm(f.get('NOTIZIE STORICO CRITICHE'))):return None,'native_narrative_object_relationship_requires_review'
    creator=f.get('ATTRIBUZIONI')or f.get('AMBITO CULTURALE')or None
    qualifiers={q.strip()for q in re.findall(r'\(([^()]*(?:attribuit|bottega|scuola|ambito|cerchia|seguace|maniera|copia|copista)[^()]*)\)',' '.join(labels),re.I)}
    missing=sorted(q for q in qualifiers if creator and c.norm(q)not in c.norm(creator))
    if missing:creator+='; '+'; '.join(missing)
    facts=dict(title=f['title'],creator_label=creator,first=dates[0],last=dates[1],date_precision=dates[2],date_display=f['date'],work_type=old.TYPES[kind],
        medium=f.get('MATERIA E TECNICA')or None,dimensions=f.get('MISURE')or None,accession=f.get("NUMERO D'INVENTARIO")or None,
        source_url='https://catalogo.cultura.gov.it/detail/'+key,
        holding_basis='Official Italian national catalogue identifies the exact individual object, named museum URI and municipality through the visible address or the same object’s explicit map municipality. Original category, alternate source titles and attribution qualifications retained. Catalogue-recorded custody only; no legal ownership or current-display claim.')
    return dict(facts=facts,native_fields=f,object_label=label,all_object_labels=sorted(labels),city_evidence=city_basis),None


def research(wave):
    museums,_=p.snapshot();seen=set();candidates=[]
    for path in sorted(old.RUN.glob('*/selection.json.gz')):
        for candidate in c.load(path)['candidates']:
            iid=candidate['museum']['id'];uri=candidate['index_row']['work']
            if iid not in p.BASE or iid not in museums or uri in seen:continue
            seen.add(uri);candidates.append(dict(candidate,museum=museums[iid]))
    c.save(p.ROOT/wave/'selected-cached-objects.json.gz',candidates)
    ready=[];held=[]
    for num,candidate in enumerate(candidates,1):
        uri=candidate['index_row']['work'];key=uri.removeprefix('https://w3id.org/arco/resource/')
        url='https://catalogo.cultura.gov.it/detail/'+key
        path=old.RUN/'pages'/(c.d.sha(url.encode())+'.json')
        if not path.exists():held.append(dict(museum_id=candidate['museum']['id'],source_record_id=key,reason='native_page_not_previously_captured'));continue
        saved=c.load(path);rc=saved['receipt'];raw=gzip.decompress((c.ROOT/saved['body_path']).read_bytes());assert c.d.sha(raw)==rc['sha256']
        if rc['status']!=200:held.append(dict(museum_id=candidate['museum']['id'],source_record_id=key,reason='native_page_not_successful'));continue
        parsed,reason=native(raw,candidate)
        if reason:held.append(dict(museum_id=candidate['museum']['id'],source_record_id=key,reason=reason));continue
        ready.append(dict(artwork_id=c.d.uid('arco/'+key),slug=c.OP+'-arco-native-'+key.rsplit('/',1)[-1],source_record_id=key,provider='arco-native-priority',origin='verified_native_object',
            museum=candidate['museum'],facts=parsed['facts'],source_receipt=rc,body_path=saved['body_path'],raw_source_record=dict(candidate=candidate,**{k:v for k,v in parsed.items()if k!='facts'})))
        if num%200==0:print('Reviewed cached primary object pages',num,'/',len(candidates),'ready',len(ready),flush=True)
    c.prepare_wave(wave,ready,held)
    print('Held:',dict(collections.Counter(x['reason']for x in held)),flush=True)


ORIGINAL_CHECK=c.check_body
def check_body(row,cache):
    if row['provider']!='arco-native-priority':return ORIGINAL_CHECK(row,cache)
    rc=row['source_receipt'];raw=gzip.decompress((c.ROOT/row['body_path']).read_bytes())
    assert c.d.sha(raw)==rc['sha256']and rc['status']==200 and rc['url']==row['facts']['source_url']
    source=row['raw_source_record'];candidate=source['candidate'];parsed,reason=native(raw,candidate)
    assert not reason and parsed['facts']==row['facts']
    for key in ['native_fields','object_label','all_object_labels','city_evidence']:assert parsed[key]==source[key]
    ir=candidate['index_receipt'];indexraw=gzip.decompress((c.ROOT/candidate['index_body_path']).read_bytes())
    assert c.d.sha(indexraw)==ir['sha256']and ir['status']==200
    rows=[{k:v['value']for k,v in x.items()}for x in json.loads(indexraw)['results']['bindings']]
    assert candidate['index_row']in rows and candidate['index_row']['work']=='https://w3id.org/arco/resource/'+row['source_record_id']


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('phase',choices=['research','plan','apply']);ap.add_argument('--wave',required=True);args=ap.parse_args()
    assert args.wave.startswith('priority-1-10-')
    if args.phase=='research':research(args.wave)
    else:
        c.d.TARGET_FIELD='linked';c.d.DEFAULT_CONFIDENCE=0.9;c.d.SOURCE_NAME='Low-count museums: verified Italian national catalogue objects';c.d.SOURCE_BASE_URL='https://catalogo.cultura.gov.it/'
        c.d.CONFIDENCE_BASIS='Exact national object ID, museum URI/name and source address or explicit same-object map municipality. Original labels and date bounds preserved. Catalogue custody, not display or legal ownership. Editorial assessment 0.90, not calibrated probability.'
        c.check_body=check_body;c.delivery(args.phase,args.wave)
