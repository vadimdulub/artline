#!/usr/bin/env python3
"""Normalize captured object-level evidence; preserve qualifications and gaps."""
import argparse,collections,re
import base64
from urllib.parse import urlsplit,parse_qs
import importlib.util
from pathlib import Path
from bs4 import BeautifulSoup
spec=importlib.util.spec_from_file_location('campaign',Path(__file__).with_name('switzerland-southern-cone-1000-20261011.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
d=c.d;RUN=c.RUN
f=c.module('facts','switzerland-southern-cone-facts-20261011.py')

def text(node):return node.get_text(' ',strip=True) if node else ''

def basel():
    records=[];held=[]
    order={x['oid']:n for n,x in enumerate(d.load(RUN/'CH/metadata-selection.json.gz')['records'])}
    for p in sorted((RUN/'CH/objects').glob('*.json.gz'),key=lambda p:order[p.name.split('.')[0]]):
        x=d.load(p);item=x.get('item');reason=x.get('error')
        if not item:held.append(dict(id=x['index']['oid'],reason=reason));continue
        title=c.label(item,'ObjListTitleTxt');date=c.label(item,'ObjDetailDateTxt');bounds=c.date_bounds(date)
        rights=c.label(item,'ObjDetailRightsTxt');credit=c.label(item,'ObjDetailCreditlineTxt')
        images=[v for v in item.get('Carousel',[]) if v.get('def') and v.get('mime')=='image/jpeg']
        acc=c.label(item,'ObjDetailNumberTxt');creator=c.label(item,'ObjListArtistTxt')
        types=x['index'].get('ObjSearchClassificationVoc_de_ss',[])
        if not bounds:reason='Native detailed date is not an explicit image-eligible date/range'
        elif len(images)!=1:reason='Default image identity is not unique'
        elif 'gemeinfrei' not in c.label(images[0],'description').lower():reason='Selected reproduction lacks a per-image public-domain label'
        elif 'Kunstmuseum Basel' not in credit or re.search('Leihgabe|Depositum|Privatbesitz|Dauerleih',credit,re.I):reason='Loan/private custody or missing collection credit requires separate review'
        elif item.get('ObjDetailObjectARef',{}).get('Items') or item.get('ObjDetailObjectBRef',{}).get('Items'):reason='Related object/component records need physical-object review'
        elif re.search(r'\b(verso|rückseite|Rückseiten|Vorderseite und Rückseite)\b',title,re.I):reason='Reverse/paired view may duplicate one physical artwork'
        elif not set(types)&{'Bild','Zeichnung','Druckgrafik','Plastik','Fotografie'}:reason='Catalogue unit outside selected fine-art types'
        if reason:held.append(dict(id=item['Id'],title=title,inventory=acc,reason=reason));continue
        kind=next((v for k,v in [('Druckgrafik','print'),('Zeichnung','drawing'),('Bild','painting'),('Plastik','sculpture'),('Fotografie','photograph')] if k in types),'unknown')
        r=f.fact('swiss-basel','Kunstmuseum Basel',str(item['Id']),x['evidence']['url'],title,creator,date,
            c.label(item,'ObjDetailMaterialTechniqueTxt'),c.label(item,'ObjDetailDimensionTxt'),acc,kind,x['evidence'],dict(native=item,index=x['index']),
            credit=credit,creator_link_hold=True,creator_identity_note='Full original creator wording, including uncertain attribution and regional anonymous labels, retained. Explicit unique links are resolved separately.',
            image_url=c.BASEL+'/'+images[0]['full'],image_license_url=x['evidence']['url'],
            image_rights_label=c.label(images[0],'description'),image_rights_status='public_domain',image_identity_confidence=.99,
            image_identity_basis='The single default reproduction is directly bound to this native object ID and inventory, and has its own public-domain rights label. The complete source frame is retained.',
            image_original_credit=rights)
        r.update(year_start=bounds[0],year_end=bounds[1],date_decision='eligible')
        persons=item.get('ReferenceValues',{}).get('ObjDetailPersonRef',[])
        if len(persons)==1 and not re.search(r'\?|:|zugeschrieben|Umkreis|Werkstatt|Nachfolger|nach |Kopie|Schule|Anonym|Unbekannt|vermut|wahrscheinlich',creator,re.I):
            r['creator_name_for_reconciliation']=c.label(persons[0].get('Captions',{}),'PerTileCaption1Txt')
        records.append(r)
    return records,held

def uruguay():
    inventory=d.load(RUN/'UY/inventory-obras.json.gz');people=d.load(RUN/'UY/inventory-artistas.json.gz')
    makers={x['NRO']:x for x in people['rows']};records=[];held=[]
    for x in inventory['rows']:
        bounds=c.date_bounds(x['REALIZ'])
        reasons=[]
        if x['UBICACION']!='Museo Nacional de Artes Visuales':reasons.append('Native location is not MNAV; custody/holding requires separate review')
        if not bounds:reasons.append('No explicit creation year or bounded range within the selected image date scope through 1955')
        if not x['ID'].isdigit():reasons.append('No numeric native inventory ID')
        if x['TEC']=='Documento':reasons.append('Document outside the selected fine-art batch')
        if reasons:
            held.append(dict(id=x['ID'],title=x['TITULO'],reason='; '.join(reasons),source_row=x));continue
        maker=makers.get(x['NAUTOR']);assert maker
        creator=maker['NOMAPE'];medium=x['TEC'];ml=medium.lower()
        kind='drawing' if 'lápiz' in ml or 'dibujo' in ml else 'painting' if any(t in ml for t in ['óleo','acrílico','gouache']) else 'watercolor' if 'acuarela' in ml else 'print' if any(t in ml for t in ['monocopia','litografía','grabado','xilografía','aguafuerte']) else 'sculpture' if any(t in ml for t in ['bronce','mármol','escultura','yeso']) else 'unknown'
        r=f.fact('uruguay-mnav','Museo Nacional de Artes Visuales',x['ID'],'https://acervo.mnav.gub.uy/obras.php?q=ni:'+x['ID'],x['TITULO'],creator,x['REALIZ'],medium,
            ' x '.join(x[k].strip() for k in ['ALTO','ANCHO','PROF'] if x[k].strip())+' cm',x['ID'],kind,inventory['evidence'],
            dict(source_row=x,creator_row=maker,creator_evidence=people['evidence'],scope='Exact museum inventory, explicitly located at MNAV. Exhibition flag is historical metadata, not a fresh display claim.'),
            native_image_url=x['IMAGEN'],image_gap='The public metadata feed provides an image link but does not itself license the reproduction. Approved image-source matching remains separate.')
        r.update(year_start=bounds[0],year_end=bounds[1],date_decision='eligible');records.append(r)
    return records,held

def argentina():
    records=[];held=[]
    for path in sorted((RUN/'AR/objects').glob('*.json.gz')):
        x=d.load(path)
        if x.get('error'):held.append(dict(url=x['index']['url'],reason=x['error']));continue
        soup=BeautifulSoup(x['html'],'html.parser');root=soup.select_one('[data-elementor-post-type="portfolio"]')
        caption=text(soup.select_one('h3.elementor-heading-title'));creator=text(soup.select_one('h1')) or x['index']['title']
        match=re.search(r',\s*((?:1\d{3})(?:\s*[-–]\s*1\d{3})?)$',caption)
        date=match.group(1) if match else 'Date unknown';title=caption[:match.start()] if match else caption
        fields={}
        for p in soup.select('.elementor-widget-text-editor p'):
            value=text(p)
            if ':' in value:key,val=value.split(':',1);fields[key.strip()]=val.strip()
        if not root or not title or not fields.get('Técnica'):
            held.append(dict(url=x['index']['url'],reason='Missing distinct native object caption'));continue
        medium=fields['Técnica'];disc=fields.get('Disciplina','').lower()
        kind='drawing' if disc=='dibujo' else 'watercolor' if 'acuarela' in medium.lower() else 'print' if 'grabado' in disc else 'sculpture' if 'escultura' in disc else 'painting' if disc=='pintura' else 'unknown'
        row=f.fact('argentina-neuquen','Museo Nacional de Bellas Artes Neuquén',root['data-elementor-id'],x['index']['url'],title,creator,date,medium,fields.get('Medidas'),None,kind,x['evidence'],
            dict(source_creator_label=creator,caption_fields=fields,source_title_and_date=caption,custody_note='National collection held at the Neuquén venue; no ownership transfer or current-display claim.',dimensions_note='Units are not explicit in the caption; none invented.'),
            creator_link_hold=True,image_gap='Native reproduction has no explicit reuse grant in the object caption. Requires an approved exact-match image source.')
        if row['date_decision']!='eligible':held.append(dict(record=row,reason='Select explicitly dated works through 1970 for this additional batch'));continue
        records.append(row)
    return records,held

def paraguay():
    selections=[
        ('PASAJE DE GIL BLAS','JOSÉ MORENO CARBONERO','1890','Óleo sobre tela','62 x 97 cm'),
        ('RETRATO DE JUAN SILVANO GODOY','TEÓFILO CASTILLO','1901','Óleo sobre tela','80 x 110 cm'),
        ('CABEZA DE MUJER','FRANCISCO PABLO MICCHETTI','1880','Óleo sobre tabla','29 x 16 cm'),
        ('UNA MARITORNES','HENRI TANOUX','1892','Óleo sobre tela','56 x 38 cm'),
        ('ENTRADA A LA TUMBA DE GARIBALDI','ALFREDO BERISSO','1902','Óleo sobre tabla','52 x 42 cm'),
        ('LA MUERTE DEL REY CANDAULES','PAUL LUIS BOUCHARD','1882','Óleo sobre tela','235 x 185 cm'),
        ('NIÑA AL PIANO','ALEJANDRO COURTINES','1882','Óleo sobre tela','155 x 101 cm'),
        ('RETRATO DE SEÑORA','JUAN LUNA Y NOVICIO','1887','Óleo sobre tela','100 x 67 cm'),
        ('CABEZA DE JOVEN','RAFAEL MONTESINOS','1880','Óleo sobre tela','45 x 55 cms'),
        ('CABEZA DE VIEJO','RAFAEL HIDALGO','1904','Óleo sobre tela','59 x 49 cms'),
        ('AGUADORAS','RUBENS SANTORO','1900','Óleo sobre tela','38 x 23 cms'),
        ('EL TÚNEL','MASSIMO D´AZEGLIO','hacia 1850','Óleo sobre tela','21 x 80 cm'),
        ('CABEZA DE MUJER','AUGUST JOHANN HOLMBERG','1889','Óleo sobre tabla','23 x 16,5 cm'),
        ('ORLY','PRIMALDO MÓNACO','1931','Óleo sobre tela','70 x 50 cms'),
        ('LA SALAMANCA','JULIO MORNET','1900','Óleo sobre tela','57 x 100 cm'),
    ]
    records=[];pages=[d.load(p) for p in (RUN/'PY/objects').glob('*.json.gz')]
    for title,creator,date,medium,dimensions in selections:
        matches=[p for p in pages if p.get('text') and all(v in p['text'] for v in [title,creator,date,medium,dimensions])]
        assert len(matches)==1,(title,creator,len(matches))
        x=matches[0];assert 'ROBADA' not in x['text']
        ident=base64.b64decode(parse_qs(urlsplit(x['evidence']['url']).query)['PqwoiflUYTeslk'][0]).decode();assert ident.isdigit()
        row=f.fact('paraguay-mnba-portal','Museo Nacional de Bellas Artes de Asunción',ident,x['evidence']['url'],title,creator,date,medium,dimensions,None,'painting',x['evidence'],
            dict(source_text=x['text'],source_caption=dict(title=title,creator=creator,date=date,medium=medium,dimensions=dimensions),
                source_context='Museum collection catalogue reproduced by Portal Guaraní. The source identifies the MNBA and curator Lotte Schulz/2003 catalogue, or documents the museum display in June 2011. Current display is not inferred.',
                historical_holding_note='The 2002 theft is independently checked; pages expressly marked stolen are excluded. Archival holdings evidence remains dated.',
                creator_note='Original printed creator label retained. Biographical lifespan text is neither imported nor used as a creation date.'),
            source_provider_name='MNBA Asunción collection catalogue — reproduced by Portal Guaraní',creator_link_hold=True,
            holding_confidence=.91,holding_basis='Object-level museum catalogue caption with title, creator, dimensions and date, reproduced by Portal Guaraní; explicit MNBA collection. Government confirms the institution. Historical holdings evidence, not current display.',
            image_gap='Portal Guaraní reserves reproduction rights; source images are not attached without an independent approved exact-match source.')
        if creator=='JUAN LUNA Y NOVICIO':row['raw']['fresh_holding_corroboration']=d.load(RUN/'PY/luna-2026.json.gz')
        if date.startswith('hacia'):row['date_display']='circa 1850';row['raw']['original_date_display']=date
        records.append(row)
    return records,[dict(url=p.get('evidence',{}).get('url'),reason='Not in selected dated batch; stolen work, unknown date, source/lifespan ambiguity or separate follow-up',source_text=p.get('text')) for p in pages if not any(r['source_url']==p.get('evidence',{}).get('url') for r in records)]

def rietberg():
    original=d.load(c.SWISS/'CH/rietberg-open-objects.json.gz')
    # Capture/reuse the publisher's exact metadata and separate image-rights grant.
    _,receipt=c.capture(original['evidence']['url'])
    policy=d.load(c.SWISS/'CH/native-discovery/rietberg-open.json')
    _,policy_receipt=c.capture(policy['evidence']['url'])
    assert 'Die Bilder stehen in der Public Domain' in policy['text']
    entries=d.load(c.SWISS/'CH/rietberg-zip-directory.json')
    filenames=collections.defaultdict(list)
    clean=lambda s:re.sub(r'[^a-z0-9]','',s.lower())
    for e in entries:
        if e['name'].startswith('Bilder Kunstwerke/') and e['size']:
            filenames[clean(e['name'].split('/')[-1].rsplit('.',1)[0])].append(e)
    inventories=[x['Inventarnummer'].split('.Obj.')[-1].replace('_',' ') for x in original['data']]
    records=[];held=[]
    for x,acc in zip(original['data'],inventories):
        key=clean(acc);matches=filenames[key];reason=None;dates=x['Datierung']
        if len(matches)!=1:reason='No unique exact inventory-named image file'
        elif any(clean(a)!=key and clean(a).startswith(key) and re.fullmatch(r'[a-z]',clean(a)[len(key):]) for a in inventories):reason='Album/ensemble parent excluded; distinct catalogued leaves can be selected separately'
        elif len(dates)!=1:reason='Multiple manufacturing-date statements require individual resolution'
        else:
            dt=dates[0];display=dt['Date_Label'];explicit=re.search(r'(?:datiert|dat\.|um)\s*(1\d{3})(?!\d)',display,re.I)
            if re.search(r'oder später|Kopie|nach ',display,re.I):reason='Open-ended dating or later-copy possibility'
            elif explicit:lo=hi=int(explicit.group(1))
            elif re.fullmatch(r'1\d{3}',dt['Date_Exakt'] or ''):lo=hi=int(dt['Date_Exakt'])
            elif re.fullmatch(r'1\d{3}',dt['Date_Von'] or '') and re.fullmatch(r'1\d{3}',dt['Date_Bis'] or ''):lo,hi=int(dt['Date_Von']),int(dt['Date_Bis'])
            else:reason='No explicit dated year or bounded native creation range'
            if not reason and not(1000<=lo<=hi<=1955):reason='Outside existing image date scope'
        if reason:held.append(dict(id=x['ID'],inventory=acc,reason=reason,dates=dates));continue
        titles=[v['Titel'].strip() for v in x['Titel_Bezeichnungen'] if v.get('Titel_Typ')=='Titel/Untertitel DE' and v.get('Titel','').strip()]
        if not titles:held.append(dict(id=x['ID'],inventory=acc,reason='No explicit object title'));continue
        makers=[m for m in x['Urheber*innen'] if m['UrheberIn_von'] in ['', 'Malerei','Kalligrafie']]
        if not makers:held.append(dict(id=x['ID'],inventory=acc,reason='Only collector seal or later inscription makers; artwork maker unresolved'));continue
        labels=[]
        for m in makers:
            label=m['UrheberIn_Label'].strip()
            if m['Zuschreibung'] not in ['','eindeutig']:label=m['Zuschreibung']+': '+label
            if m['UrheberIn_von']:label+=' ('+m['UrheberIn_von']+')'
            labels.append(label)
        dimensions=[]
        for dim in x['Masse']:
            value=' x '.join(str(dim[k]) for k in ['Masse_Hohe','Masse_Breite'] if dim.get(k))
            if value:dimensions.append(dim['Masse_Typ']+': '+value+' '+str(dim.get('Masse_Einheit','')))
        r=f.fact('swiss-rietberg','Museum Rietberg',x['ID'],receipt['url'],titles[0],'; '.join(labels),display,x['Material_Technik'],'; '.join(dimensions),acc,
            'calligraphy' if 'Kalligrafie' in x['Objekttyp'] else 'painting',receipt,
            dict(native=x,date_basis='Explicit dated year in native label takes precedence over broad search bounds; otherwise the supplied bounded native range is retained without inventing a precise year.',
                catalogue_unit='Exact source inventory; album leaves are explicitly titled and inventoried objects. Ensemble parents are excluded from this selection, preventing parent-plus-component inflation.'),
            creator_link_hold=True,image_url='https://data.stadt-zuerich.ch/dataset/mrz_drenowatz_sammlung/download/mrz_drenowatz_sammlung_bilder.zip#'+matches[0]['name'],
            image_license_url=policy_receipt['url'],image_rights_label='Museum Rietberg open data: image files public domain',image_rights_status='public_domain',
            image_identity_confidence=.99,image_identity_basis='Exact source inventory-named member of the museum-released archive. Visual review must distinguish complete artworks from seals/details before attachment.',
            image_original_credit='Foto: Rainer Wolfensberger / Museum Rietberg',image_archive_member=matches[0],image_policy_receipt=policy_receipt)
        r.update(year_start=lo,year_end=hi,date_decision='eligible');records.append(r)
    return records,held

def produce(country,tag):
    records,held={'CH':basel,'AR':argentina,'UY':uruguay,'PY':paraguay,'RIETBERG':rietberg}[country]()
    # Resolve only explicitly unqualified native person identities against unique
    # existing names/aliases. Qualified wording never becomes a primary artist link.
    names=collections.defaultdict(set)
    with d.connect() as db:
        for x in db.execute("SELECT id::text,display_name name FROM artists WHERE status<>'archived' UNION SELECT a.id::text,al.alias FROM artists a JOIN artist_aliases al ON al.artist_id=a.id WHERE a.status<>'archived'"):
            names[d.norm(x['name'])].add(x['id'])
    for r in records:
        label=r.get('creator_name_for_reconciliation')
        if country=='UY' and not re.search(r'\?|atribu|anónim|desconoc|taller|escuela|copia|después',r['creator_label'],re.I):label=r['creator_label']
        if label and len(names[d.norm(label)])==1:r['verified_artist_id']=next(iter(names[d.norm(label)]))
    d.save(RUN/country/(tag+'-facts.json.gz'),dict(records=records,held=held))
    print(country,'eligible facts',len(records),'held',len(held),'linked',sum(bool(r.get('verified_artist_id')) for r in records),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('country',choices=['CH','AR','UY','PY','RIETBERG']);p.add_argument('tag');a=p.parse_args();produce(a.country,a.tag)
