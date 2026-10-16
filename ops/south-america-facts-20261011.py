#!/usr/bin/env python3
"""Normalize exact native object fields with explicit date/version holds."""
import argparse,collections,importlib.util,re
from pathlib import Path
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('sources',Path(__file__).with_name('south-america-sources-20261011.py'));src=importlib.util.module_from_spec(s);s.loader.exec_module(src);c=src.c;d=c.d
f=c.module('source_facts','switzerland-southern-cone-facts-20261011.py')
def txt(n):return n.get_text(' ',strip=True) if n else ''
def kind(value):
    v=d.norm(value)
    for pattern,term in [('acuarela','watercolor'),('aquarela','watercolor'),('fotograf','photograph'),('escultur','sculpture'),('escultoric','sculpture'),('grabado','print'),('gravura','print'),('grafica','print'),('dibujo','drawing'),('desenho','drawing'),('pintura','painting'),('pictorica','painting'),('textil','textile')]:
        if pattern in v:return term
    return 'unknown'
def date_bounds(value):
    explicit=src.bounds(value)
    if explicit:return explicit
    # Explicit old centuries are bounded source dates, never artist lifespans.
    roman={'XV':15,'XVI':16,'XVII':17,'XVIII':18,'XIX':19}
    match=re.fullmatch(r'(?:(?:siglo|siglos|s\.)\s*)?(XVIII|XVII|XVI|XIX|XV)(?:\s*[-–/]\s*(XVIII|XVII|XVI|XIX|XV))?',value.strip(),re.I)
    if match:
        low=roman[match[1].upper()];high=roman[(match[2] or match[1]).upper()]
        if low<=high:return ((low-1)*100+1,high*100)
    return None

def parse(country,x,p):
    url=x['index']['url'];rc=x['evidence'];fields={};extra={}
    if country=='BR':
        box=p.select_one('.collection-info-box');assert box,'Missing MASP object box'
        for li in box.select('li'):
            label=li.select_one('h5')
            if label:fields[txt(label).rstrip(':')]=txt(li).removeprefix(txt(label)).strip()
        title=fields.get('Título');creator=fields.get('Autor');date=fields.get('Data da obra','');medium=fields.get('Técnica');dimensions=fields.get('Dimensões');inv=fields.get('Número de inventário');typ=fields.get('Designação','')
        museum='Museu de Arte de São Paulo Assis Chateaubriand (MASP)';provider='brazil-masp';ident=url.rsplit('/',1)[-1]
        extra['credit']=fields.get('Aquisição');extra['image_gap']='Native image reuse has separate photographer/artist conditions. Approved exact-match image source required.'
    elif country=='CL':
        box=p.select_one('article');assert box
        for node in box.select('.field'):
            label=node.find('div',class_='field-label',recursive=False);value=node.find('div',class_='field-item',recursive=False) or node.find('div',class_='field-items',recursive=False)
            if label and value:fields[txt(label)]=txt(value)
        objs=box.select_one('.field--name-object');parts=objs.find_all('div',attrs={'item-value':True},recursive=False) if objs else []
        if len(parts)!=1:return None,'Multiple catalogued object components require physical-object review'
        for node in objs.select('.js-form-item'):
            label=node.select_one('label');value=node.select_one('.field-item')
            if label and value:fields[txt(label)]=txt(value)
        creator_nodes=objs.select('.creator-name-item');creator='; '.join(txt(z) for z in creator_nodes)
        title=fields.get('Título');date=fields.get('Fecha de creación','');medium=fields.get('Técnica / Material');dimensions=fields.get('Dimensiones');inv=fields.get('Nº de inventario');typ=fields.get('Objeto','');museum=fields.get('Institución');provider='chile-surdoc';ident=fields.get('Número de registro')
        assert ident==url.rsplit('/',1)[-1]
        if re.search(r'\b(reverso|anverso|frente y|fragmento)\b',title or '',re.I):return None,'Reverse/front/component view requires object-version reconciliation'
        if any(v in fields.get('Ubicación','').lower() for v in ['restituido','robado']):return None,'Object no longer in documented custody'
        if fields.get('Forma de ingreso')=='Comodato':return None,'Loan custody requires separate holding review'
        extra['image_gap']='Native SURDOC photograph has no explicit commercial reuse grant established; exact approved source matching remains separate.'
    elif country=='PE':
        for node in p.select('.detailField'):
            label=node.select_one('.detailFieldLabel');value=node.select_one('.detailFieldValue')
            if label and value:fields[txt(label)]=txt(value)
        title=txt(p.select_one('h1'));creator=fields.get('Artista');date=fields.get('FECHA','');medium=fields.get('TÉCNICA');dimensions=fields.get('MEDIDAS');inv=fields.get('CÓDIGO');typ=fields.get('CLASIFICACIÓN','');museum='Museo de Arte de Lima';provider='peru-mali';ident=re.search(r'/objects/(\d+)/',url)[1]
        names=p.select('.peopleField .detailFieldValue a');extra['creator_name_for_reconciliation']='; '.join(txt(n) for n in names)
        extra['credit']=fields.get('LÍNEA DE CRÉDITO');extra['image_gap']='Museum object page offers a reproduction but an explicit reuse grant has not been established.'
    else:
        for node in p.select('.hit-visible-fields-containers .field-container'):
            fields[txt(node.select_one('.label-field'))]=txt(node.select_one('.value-field'))
        date=fields.get('Fecha de creación','');dimensions=fields.get('Dimensiones');ident=url.rsplit('/',1)[-1]
        if country=='CO':
            title=txt(p.select_one('.hit-teaser-title'));typ=fields.get('Denominación','');title=title.removesuffix(' - '+typ)
            creator=fields.get('Artista');medium=fields.get('Técnica y material');inv=fields.get('Número de registro');museum='Banco de la República — Colección de Arte';provider='colombia-banrep'
            extra['raw_holding_basis']='Official bank collection record; institution is the collection authority, not a claim to a particular display venue. Museum venues and current reserve/display text are retained only as source metadata.'
            extra['image_gap']='Native reproduction is CC BY-NC-ND or otherwise reserved; commercial image reuse requires independent approved exact source.'
        else:
            title=fields.get('Título');typ=fields.get('Tipo de objeto','');creator=fields.get('Autor');medium=fields.get('Material') or fields.get('Técnica');inv=fields.get('Código del bien');museum=fields.get('Museo');provider='ecuador-national'
            extra['image_gap']='Native national catalogue reproduction lacks a verified per-image reuse grant.'
    if not title or not museum or not ident or not inv:return None,'Missing title, institution, native ID or inventory; fields not invented'
    bounds=date_bounds(date)
    if not bounds:return None,'Creation date is unknown, open-ended, conflicting, after 1970, or crosses the cutoff; source date retained for review'
    kt=kind(typ)
    if kt=='unknown':return None,'Source classification outside selected painting/drawing/print/sculpture/photo/textile types'
    if not creator:creator=None
    row=f.fact(provider,museum,ident,url,title,creator,date,medium,dimensions,inv,kt,rc,dict(source_fields=fields,index=x['index'],source_context=extra.pop('raw_holding_basis',None),date_basis='Exact native creation field; explicit bounded centuries converted to their conventional range. No biographical, acquisition or photography date substituted.'),creator_link_hold=True,**extra)
    row.update(year_start=bounds[0],year_end=bounds[1],date_decision='eligible',country_code=country)
    # Only explicit unqualified names can link; original labels are always retained.
    if creator and not re.search(r'\?|an[oó]nim|desconoc|atribu|taller|escuela|copia|estilo|seg[uú]n|after|school|workshop|atribu[ií]d',creator,re.I):
        if country in ['BR','CO']:row['creator_name_for_reconciliation']=creator
        elif country=='CL' and len(creator_nodes)==1:
            anchor=creator_nodes[0].select_one('a[href^="/administration/dictionary/"]')
            if anchor:row['creator_name_for_reconciliation']=txt(anchor)
    return row,None

def produce(country,version):
    tag={'BR':'masp','CL':'surdoc','CO':'skin','EC':'skin','PE':'mali'}[country];records=[];held=[]
    for path in sorted((c.RUN/country/tag/'objects').glob('*.json.gz')):
        x=d.load(path);url=x['index']['url']
        if x.get('error'):held.append(dict(url=url,reason=x['error']));continue
        raw,rc=c.capture(url);assert rc['sha256']==x['evidence']['sha256'];p=BeautifulSoup(raw,'html.parser')
        try:row,reason=parse(country,x,p)
        except Exception as e:row=None;reason='Parser review: '+str(e)
        if row:records.append(row)
        else:held.append(dict(url=url,reason=reason,source_text=x['text']))
    names=collections.defaultdict(set)
    with d.connect() as db:
        for row in db.execute("SELECT id::text,display_name name FROM artists WHERE status<>'archived' UNION SELECT a.id::text,al.alias FROM artists a JOIN artist_aliases al ON al.artist_id=a.id WHERE a.status<>'archived'"):names[d.norm(row['name'])].add(row['id'])
    for row in records:
        name=row.get('creator_name_for_reconciliation')
        if name and len(names[d.norm(name)])==1:row['verified_artist_id']=next(iter(names[d.norm(name)]))
    d.save(c.RUN/country/(version+'-facts.json.gz'),dict(records=records,held=held));print(country,'eligible',len(records),'held',len(held),'linked',sum(bool(r.get('verified_artist_id')) for r in records),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('country');p.add_argument('version');a=p.parse_args();produce(a.country,a.version)
