#!/usr/bin/env python3
"""Bounded Spain research. Immutable evidence; metadata selection precedes images."""
import argparse, collections, importlib.util, json, re, time
from pathlib import Path
from urllib.parse import urlencode, urlparse
import psycopg
from psycopg.rows import dict_row
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'docs/research/spain-deep-20260916'
def module(name, filename):
    s=importlib.util.spec_from_file_location(name,ROOT/'ops'/filename);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
w=module('spain_wiki','research-wikimedia-catalogues.py');w.RUN=RUN/'wikimedia'
m=module('spain_commons','overnight-commons-images.py');core=m.core
# This read-only catalogue snapshot tolerates replica lag, but still obeys
# maxlag errors and HTTP Retry-After. No editing endpoint is used.
_fetch=w.fetch
def read_fetch(url):
    if urlparse(url).hostname=='www.wikidata.org':url=url.replace('maxlag=5','maxlag=30')
    return _fetch(url)
w.fetch=read_fetch

PRIORITIES='''Bartolomé Bermejo|Jaume Huguet|Bernat Martorell|Lluís Dalmau|Lluís Borrassà|Pere Serra|Jaume Serra|Ferrer Bassa|Joan Reixach|Fernando Gallego|Diego de la Cruz|Nicolás Francés|Pedro Berruguete|Juan de Flandes|Alejo Fernández|Fernando Yáñez de la Almedina|Vicente Juan Masip|Vicente Macip|Alonso Sánchez Coello|Luis de Morales|Juan Correa de Vivar|Hernando de los Llanos|Juan Fernández Navarrete|Juan Pantoja de la Cruz|Francisco Ribalta|Juan Ribalta|Juan Bautista Maíno|Luis Tristán|Francisco Pacheco|Juan de Roelas|Francisco Herrera the Elder|Francisco Herrera the Younger|Alonso Cano|Antonio del Castillo y Saavedra|Francisco de Zurbarán|Jusepe de Ribera|Diego Velázquez|Bartolomé Esteban Murillo|Juan de Valdés Leal|Juan de Pareja|Francisco Rizi|Juan Rizi|Juan Carreño de Miranda|Claudio Coello|José Antolínez|Antonio de Pereda|Juan de Arellano|Tomás Hiepes|Juan de Espinosa|Juan van der Hamen|Juan Sánchez Cotán|Francisco Collantes|Luis Meléndez|Luis Paret y Alcázar|Francisco Bayeu y Subías|Ramón Bayeu|Mariano Salvador Maella|Antonio González Velázquez|Francisco Goya|Agustín Esteve|Vicente López Portaña|José de Madrazo|Federico de Madrazo|Luis de Madrazo|Raimundo de Madrazo y Garreta|Antonio María Esquivel|Valeriano Bécquer|Leonardo Alenza|Eugenio Lucas Velázquez|Genaro Pérez Villaamil|Carlos de Haes|Martín Rico y Ortega|Marià Fortuny|Eduardo Rosales|Antonio Gisbert|Francisco Pradilla Ortiz|José Casado del Alisal|José Jiménez Aranda|José Villegas Cordero|Ignacio Pinazo Camarlench|Joaquín Sorolla|Ignacio Zuloaga|Julio Romero de Torres|Enrique Simonet|Cecilio Pla|Aureliano de Beruete|Darío de Regoyos|Valentín de Zubiaurre|Ramón de Zubiaurre|Gustavo de Maeztu|Ramon Casas|Santiago Rusiñol|Isidre Nonell|Joaquim Mir|Joaquim Sunyer|Hermenegildo Anglada Camarasa|Eliseu Meifrèn|Modest Urgell|Dionís Baixeras|Josep Maria Sert|Lluïsa Vidal|María Luisa de la Riva|Julia Alcayde|Elena Brockmann|Alejandrina Gessler|Fernanda Francés y Arribas|Emilia Menassade|María Roësset Mosquera|María Blanchard|Maruja Mallo|Ángeles Santos|Delhy Tejero|Margarita Manso|Remedios Varo|Juan Gris|Joaquín Torres García|Óscar Domínguez|José Gutiérrez Solana|Benjamín Palencia|Daniel Vázquez Díaz|Francisco Bores|Esteban Vicente|Pablo Picasso|Joan Miró|Salvador Dalí'''.split('|')

def save(name,data):core.save_new(RUN/name,data)
def load(name):return json.loads((RUN/name).read_text())
def api(params):return w.fetch('https://www.wikidata.org/w/api.php?'+urlencode(dict(params,format='json',maxlag=5)))
def log(*xs):print(core.now(),*xs,flush=True)

def inventory():
    with psycopg.connect('postgresql://localhost/artline',row_factory=dict_row,options='-c default_transaction_read_only=on -c statement_timeout=90000') as db:
        artists=db.execute("""SELECT a.id::text,a.slug,a.display_name,a.normalized_name,a.birth_year,a.death_year,a.status,
          ARRAY(SELECT external_id FROM external_identifiers e WHERE e.entity_type='artist' AND e.entity_id=a.id AND e.scheme='wikidata') qids,
          ARRAY(SELECT alias FROM artist_aliases x WHERE x.artist_id=a.id) aliases
          FROM artists a WHERE a.status<>'archived'""").fetchall()
        ids=[a['id'] for a in load('artist-coverage.json')]
        works=db.execute("""WITH selected AS MATERIALIZED (SELECT DISTINCT artwork_id FROM artwork_artists WHERE artist_id=ANY(%s::uuid[]))
          SELECT a.id::text artwork_id,a.slug,a.title,a.alternate_title,a.normalized_title,a.accession_number,
          a.creation_year_start,a.creation_year_end,a.date_precision,a.date_display,a.work_type,a.status,a.revision,a.primary_media_id::text,
          a.current_institution_id::text,i.slug institution_slug,i.name institution_name,i.website_url,i.wikidata_id institution_qid,
          ARRAY(SELECT external_id FROM external_identifiers e WHERE e.entity_type='artwork' AND e.entity_id=a.id AND e.scheme='wikidata') qids,
          coalesce((SELECT jsonb_agg(jsonb_build_object('id',ar.id,'name',ar.display_name,'death',ar.death_year,'qid',(SELECT external_id FROM external_identifiers e WHERE e.entity_type='artist' AND e.entity_id=ar.id AND scheme='wikidata' LIMIT 1))) FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=a.id),'[]') creators,
          ARRAY(SELECT source_url FROM citations c WHERE c.entity_type='artwork' AND c.entity_id=a.id) source_urls
          FROM selected s JOIN artworks a ON a.id=s.artwork_id LEFT JOIN institutions i ON i.id=a.current_institution_id
          WHERE a.status<>'archived'""",(ids,)).fetchall()
    save('all-artist-identities.json',artists);save('spanish-work-inventory.json',works)
    log('Inventory',len(artists),'artist identities;',len(works),'Spain-associated works')

def discover(corrected=False):
    existing=load('all-artist-identities.json');resolved=[];held=[]
    corrections=load('reviewed-artist-disambiguation.json')['identities'] if corrected else {}
    for name in PRIORITIES+['El Greco']:
        path=RUN/'artist-discovery'/(core.sha(name.encode())[:20]+'.json')
        if path.exists():result=json.loads(path.read_text())
        else:
            exact=[a for a in existing if w.norm(name) in {w.norm(a['display_name']),*[w.norm(s) for s in a['aliases']]} and len(a['qids'])==1]
            if len(exact)==1:
                result={'name':name,'qid':exact[0]['qids'][0],'basis':'existing exact catalogue identity'}
            else:
                data,receipt=api({'action':'wbsearchentities','search':name,'language':'en','uselang':'en','limit':5,'type':'item'})
                result={'name':name,'candidates':data.get('search',[]),'receipt':receipt}
                candidates=[x for x in data.get('search',[]) if re.search('paint|artist',x.get('description',''),re.I)]
                if len(candidates)==1:result.update(qid=candidates[0]['id'],basis='unique painter/artist search result; authority validation follows')
            core.save_new(path,result)
        if name in corrections:result=dict(result,qid=corrections[name],basis='Individually disambiguated authority; original search evidence retained')
        (resolved if result.get('qid') else held).append(result)
        log('Artist identity',name,result.get('qid','manual disambiguation'))
    entities,receipts=w.entities(sorted({x['qid'] for x in resolved}));valid=[]
    for x in resolved:
        e=entities[x['qid']]
        if m.ids(e,'P31')!={'Q5'} or not any(w.norm(x['name'])==w.norm(s) for s in w.labels(e)):
            held.append(dict(x,reason='Exact source alias/person verification required'));continue
        x.update(entity=e,receipt=receipts[x['qid']]);valid.append(x)
    suffix='-corrected' if corrected else ''
    save('priority-artists'+suffix+'.json',{'artists':valid,'held':held,'selection':'Named priority gaps across periods and regional schools, plus women and modern artists. Association is research scope, not an inferred nationality.'})
    allworks={};discoveries=[]
    for x in valid:
        q=x['qid'];path=RUN/'work-discovery'/(q+'.json')
        if path.exists():record=json.loads(path.read_text())
        else:
            query=f'haswbstatement:P170={q} haswbstatement:P31=Q3305213 haswbstatement:P195'
            data,receipt=api({'action':'query','list':'search','srsearch':query,'srnamespace':0,'srlimit':24,'srprop':''})
            record={'artist':x['name'],'qid':q,'query':query,'records':data.get('query',{}).get('search',[]),'total':data.get('query',{}).get('searchinfo',{}).get('totalhits'),'receipt':receipt,'cap':24}
            core.save_new(path,record)
        discoveries.append(record)
        for row in record['records']:allworks.setdefault(row['title'],[]).append(q)
        log('Metadata discovery',x['name'],len(record['records']))
    save('work-discovery-index'+suffix+'.json',{'artists':discoveries,'works':allworks})

def discover_corrected():discover(True)

def research():
    discovered=load('work-discovery-index-corrected.json');artists={x['qid']:x for x in load('priority-artists-corrected.json')['artists']}
    raw,receipts=w.entities(sorted(discovered['works']));museum_ids=set();property_ids=set()
    for e in raw.values():
        museum_ids.update(m.ids(e,'P195'));property_ids.update(k for k,v in e.get('claims',{}).items() if any(c.get('mainsnak',{}).get('datatype')=='external-id' for c in v))
    museums,museum_receipts=w.entities(sorted(museum_ids));props,_=w.entities(sorted(property_ids))
    save('museum-authorities.json',{'entities':museums,'receipts':museum_receipts});save('property-authorities.json',props)
    existing={q:x for x in load('spanish-work-inventory.json') for q in x['qids']};records=[];held=[]
    for q,e in raw.items():
        cs=w.claims(e,'P170');hs=[c for c in w.claims(e,'P195') if 'P582' not in c.get('qualifiers',{})];d=w.date(e)
        if e.get('id')!=q:why='Redirected identity'
        elif not m.ids(e,'P31')&m.PAINTED:why='Not a supported painting type'
        elif len(cs)!=1 or set(cs[0].get('qualifiers',{}))-{'P7452'}:why='Missing, multiple or qualified attribution'
        elif w.value(cs[0]).get('id') not in artists:why='Different creator authority'
        elif len(hs)!=1:why='Missing, multiple or historic institution claim'
        elif d['first'] is not None and not d['eligible']:why='Known date outside scope'
        else:why=None
        if why:held.append({'qid':q,'reason':why});continue
        cq=w.value(cs[0])['id'];mq=w.value(hs[0])['id'];me=museums[mq];ae=artists[cq]['entity']
        urls=[]
        for prop,pd in props.items():
            for fmt in m.values(pd,'P1630'):
                if isinstance(fmt,str) and fmt.startswith(('https://','http://')):
                    for val in m.values(e,prop):
                        if isinstance(val,str):urls.append({'property':prop,'id':val,'url':fmt.replace('$1',val)})
        urls.extend({'property':'P973','url':s} for s in m.values(e,'P973') if isinstance(s,str))
        acc=list(dict.fromkeys(v for v in w.values(e,'P217') if isinstance(v,str)))
        records.append({'qid':q,'title':w.label(e),'titles':w.labels(e),'creator_qid':cq,'creator_name':w.label(ae),'creator_names':w.labels(ae),'birth':w.year(ae,'P569'),'death':w.year(ae,'P570'),'creator_countries':sorted(m.ids(ae,'P27')),'creator_gender':sorted(m.ids(ae,'P21')),'institution_qid':mq,'institution_name':w.label(me),'institution_websites':m.values(me,'P856'),'date':d,'accession':acc[0] if len(acc)==1 else None,'accessions':acc,'image_names':m.values(e,'P18'),'object_urls':urls,'entity':e,'receipt':receipts[q],'creator_entity':ae,'creator_receipt':artists[cq]['receipt'],'existing':existing.get(q)})
    # Bounded selection: breadth first, at most 10 records per named priority creator.
    groups=collections.defaultdict(list)
    for x in records:groups[x['creator_qid']].append(x)
    selected=[]
    for q,rows in groups.items():
        rows.sort(key=lambda x:(bool(x['existing'] and x['existing']['primary_media_id']),not bool(x['object_urls']),not x['date']['eligible'],not bool(x['image_names']),int(x['qid'][1:])))
        selected.extend(rows[:10])
        held.extend({'qid':x['qid'],'reason':'Outside bounded ten-work artist selection'} for x in rows[10:])
    save('selected-metadata.json',{'records':selected,'held':held,'discovered':len(raw),'creator_count':len(groups),'selected':len(selected),'unknown_dates':sum(not x['date']['eligible'] for x in selected)})
    log('Selected',len(selected),'works by',len(groups),'artists; held',len(held))

def primary():
    rows=load('selected-metadata-final-v2.json')['records'];out=[];unavailable={}
    for x in rows:
        path=RUN/'primary-records'/(x['qid']+'.json')
        if path.exists():out.append(json.loads(path.read_text()));continue
        sites={(urlparse(s).hostname or '').removeprefix('www.') for s in x['institution_websites']}
        urls=[]
        for u in x['object_urls']:
            host=(urlparse(u['url']).hostname or '').removeprefix('www.')
            if host and (any(host==s or host.endswith('.'+s) for s in sites if s) or host in {'museodelprado.es','museunacional.cat','museoreinasofia.es','museothyssen.org','metmuseum.org','artic.edu','clevelandart.org','nga.gov','nationalgallery.org.uk','hispanicsociety.emuseum.com','colecciones.uv.es','ceres.mcu.es','ceres.mecd.es','collections.louvre.fr'}):urls.append(u['url'])
        result={'qid':x['qid'],'title':x['title'],'artist':x['creator_name'],'candidates':urls,'captures':[],'errors':[]}
        for url in list(dict.fromkeys(urls))[:1]:
            key=core.sha(url.encode());p=RUN/'primary-captures'/(key+'.html');rp=p.with_suffix('.receipt.json')
            try:
                if p.exists():raw=p.read_bytes();receipt=json.loads(rp.read_text())
                else:
                    if urlparse(url).hostname in unavailable:raise ValueError(unavailable[urlparse(url).hostname])
                    time.sleep(1.1);resp=w.SESSION.get(url,timeout=(12,35));resp.raise_for_status();raw=resp.content
                    if len(raw)>12_000_000:raise ValueError('Oversize museum response')
                    receipt={'url':url,'final_url':resp.url,'retrieved_at':core.now(),'sha256':core.sha(raw),'bytes':len(raw),'status':resp.status_code};core.save_new(p,raw);core.save_new(rp,receipt)
                soup=BeautifulSoup(raw,'html.parser')
                for node in soup(['script','style','nav','footer','header']):node.decompose()
                text=soup.get_text(' ',strip=True)
                result['captures'].append({'receipt':receipt,'page_title':soup.title.get_text(' ',strip=True) if soup.title else '', 'text':text,'accession_present':bool(x['accession'] and x['accession'] in text)})
            except Exception as exc:
                if isinstance(exc,w.requests.HTTPError) and exc.response.status_code in (403,429):unavailable[urlparse(url).hostname]='Public site access/rate response respected; direct captures deferred after HTTP '+str(exc.response.status_code)
                result['errors'].append({'url':url,'error':str(exc)[:250]})
        core.save_new(path,result);out.append(result);log('Official source captures',x['qid'],len(result['captures']),x['creator_name'])
    save('primary-capture-index.json',{'records':out,'captured_objects':sum(bool(x['captures']) for x in out),'policy':'Captures are evidence, not automatic validation of facts or image rights.'})

def native():
    # Directly checked Reina Sofia catalogue records omitted by the secondary
    # discovery index. Museum-native identities are never presented as QIDs.
    inputs=[('AD07401','Autorretrato de cuerpo entero',1912,'Q19502553','autorretrato-de-cuerpo-entero'),('AD10745','Autorretrato',1937,'Q5801792','autorretrato-9'),('AS00904','Labradora de Toro (Mujer con guindas)',1946,'Q5801792','labradora-de-toro-mujer-con-guindas'),('AS01203','Composición abstracta',1954,'Q5801792','composicion-abstracta-2')]
    artists={a['qid']:a for a in load('priority-artists-corrected.json')['artists']};records=[]
    for accession,title,year,cq,slug in inputs:
        url='https://www.museoreinasofia.es/colecciones/obra/'+slug+'/';key=core.sha(url.encode());path=RUN/'primary-captures'/(key+'.html');rp=path.with_suffix('.receipt.json')
        if path.exists():raw=path.read_bytes();receipt=json.loads(rp.read_text())
        else:
            time.sleep(1.1);res=w.SESSION.get(url,timeout=(12,45));res.raise_for_status();raw=res.content;receipt={'url':url,'final_url':res.url,'sha256':core.sha(raw),'bytes':len(raw),'retrieved_at':core.now(),'status':res.status_code};core.save_new(path,raw);core.save_new(rp,receipt)
        soup=BeautifulSoup(raw,'html.parser');text=soup.get_text(' ',strip=True)
        assert accession in text and str(year) in text and w.norm(title) in w.norm(text) and 'Óleo' in text
        ae=artists[cq]['entity'];q='reina-'+accession.lower();name=w.label(ae)
        assert ('Tejero' in text if cq=='Q5801792' else 'Mosquera' in text)
        records.append({'qid':q,'source_scheme':'reina-sofia-object','source_record_id':accession,'source_url':url,'title':title,'titles':[title],'creator_qid':cq,'creator_name':name,'creator_names':w.labels(ae),'birth':w.year(ae,'P569'),'death':w.year(ae,'P570'),'creator_countries':sorted(m.ids(ae,'P27')),'creator_gender':sorted(m.ids(ae,'P21')),'institution_qid':'Q460889','institution_name':'Museo Nacional Centro de Arte Reina Sofía','institution_websites':['https://www.museoreinasofia.es/'],'date':{'first':year,'last':year,'precision':'exact','display':str(year),'eligible':True},'accession':accession,'accessions':[accession],'image_names':[],'object_urls':[{'property':'native','id':accession,'url':url}],'entity':None,'receipt':receipt,'creator_entity':ae,'creator_receipt':artists[cq]['receipt'],'existing':None,'native_primary_validation':{'url':url,'accession':accession,'title':title,'year':year,'creator':name,'medium':'Oil painting','source_sha256':receipt['sha256'],'no_current_display_claim':True}})
        log('Direct museum gap confirmed',accession,title)
    save('primary-native-selection.json',records)

def finalize():
    data=load('selected-metadata.json');extra=load('primary-native-selection.json');institutions=load('all-institutions.json');museums=load('museum-authorities.json')['entities']
    known=set(w.MAPPING.values())|{i['wikidata_id'] for i in institutions if i['wikidata_id']}
    museum_words=r'\b(?:museum|museo|museu|musée|gallery|galerie|galería|museen|pinacoteca|pinakothek)\b'
    eligible=[];outside=[]
    for x in data['records']:
        q=x['institution_qid'];name=x['institution_name']
        if q in known or re.search(museum_words,name,re.I) and not re.search(r'private|auction|sotheby|christie',name,re.I):eligible.append(x)
        else:outside.append({'qid':x['qid'],'institution_qid':q,'institution_name':name,'reason':'No independently established museum connection in this bounded pass; retain research only'})
    data=dict(data,records=eligible+extra,native_primary_additions=len(extra),museum_scope_held=outside);data['selected']=len(data['records']);save('selected-metadata-final.json',data);log('Final selection',data['selected'],'museum-scope holds',len(outside))

def activity():
    artists=load('priority-artists-corrected.json')['artists'];ids=set().union(*(m.ids(x['entity'],'P937') for x in artists));entities,receipts=w.entities(sorted(ids));out={}
    for x in artists:
        locations=[{'qid':q,'name':w.label(entities[q]),'receipt':receipts[q]} for q in sorted(m.ids(x['entity'],'P937')) if q=='Q29' or m.ids(entities[q],'P17')=={'Q29'}]
        if locations:out[x['qid']]={'source':'https://www.wikidata.org/wiki/'+x['qid'],'relationship':'active','locations':locations,'basis':'Explicit source work-location statement cross-checked with independently captured place-country authority. Does not assign citizenship or replace other affiliations.'}
    save('spanish-activity-evidence.json',out);log('Documented activity in Spain',len(out),'artists')

def titles():
    data=load('selected-metadata-final.json');missing=[x['qid'] for x in data['records'] if x['title']==x['qid']];out={}
    for start in range(0,len(missing),20):
        part=missing[start:start+20];response,receipt=api({'action':'wbgetentities','ids':'|'.join(part),'props':'labels|aliases|claims','languages':'en|mul|es|ca|gl|eu|fr|de|it|pt'})
        for q,e in response['entities'].items():
            core.save_new(RUN/'enriched-title-entities'/(q+'.json'),{'entity':e,'receipt':receipt});out[q]={'entity':e,'receipt':receipt}
    for x in data['records']:
        if x['qid'] not in out:continue
        item=out[x['qid']];e=item['entity'];assert e['claims']==x['entity']['claims'],'Artwork facts changed during title enrichment'
        if w.label(e)==x['qid']:
            x.update(title='Title not recorded'+(' (inventory '+x['accession']+')' if x['accession'] else ''),titles=[],title_unknown=True,entity=e,receipt=item['receipt'],title_enriched=True)
        else:x.update(title=w.label(e),titles=w.labels(e),entity=e,receipt=item['receipt'],title_enriched=True)
    save('selected-metadata-final-v2.json',data);log('Source-language titles resolved',len(missing))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['inventory','discover','discover_corrected','research','primary','native','finalize','activity','titles']);a=p.parse_args();globals()[a.phase]()
