#!/usr/bin/env python3
"""Selected source captions only; no database writes or image downloads."""
import importlib.util
import re
import sys
import concurrent.futures
from pathlib import Path

s = importlib.util.spec_from_file_location('research', Path(__file__).with_name('switzerland-southern-cone-research-20261011.py'))
r = importlib.util.module_from_spec(s)
s.loader.exec_module(r)


def fact(provider, museum, key, url, title, creator, date, medium, dimensions, inventory, kind, receipt, raw, **extra):
    years = [int(x) for x in re.findall(r'(?<!\d)(1[0-9]{3}|20[0-9]{2})(?!\d)', date)]
    return dict(provider=provider, museum=museum, source_id=key, source_url=url,
                title=title, creator_label=creator, date_display=date,
                year_start=min(years) if years else None, year_end=max(years) if years else None,
                date_decision=('after_cutoff' if min(years)>1970 else 'date_review' if max(years)>1970 else 'eligible') if years else 'date_review',
                medium=medium, dimensions=dimensions, accession_number=inventory,
                source_type=kind, evidence=receipt, raw=raw, **extra)


def swiss():
    museum = "Museo Comunale d'Arte Moderna di Ascona"
    records = []
    for path, collection in [('collezione-comune-di-ascona','CCA'),('fondazione-marianne-werefkin','FMW'),('fondo-anna-iduna-zehnder','AIZ')]:
        url = 'https://www.museoascona.ch/it/collezioni/'+path
        soup, receipt = r.page(url)
        # Each gallery caption is a single source text node, with literal separators.
        captions = [str(x).strip() for x in soup.find_all(string=True) if ' | ' in str(x) and (' cm' in str(x))]
        assert len(captions) == {'CCA':7,'FMW':8,'AIZ':4}[collection], (collection, captions)
        for caption in captions:
            fields = [x.strip() for x in caption.split('|')]
            if collection == 'FMW':
                fields.insert(0, 'Marianne Werefkin')
            creator, title, date, medium, dimensions = fields[:5]
            inventory = fields[5] if len(fields)>5 else None
            key = inventory or 'zehnder-'+r.b.sha(caption.encode())[:16]
            record = fact('swiss-ascona',museum,key,url,title,creator,date,medium,dimensions,inventory,'painting',receipt,
                          dict(caption=caption,collection=collection,
                               custody_note='Fondazione Marianne Werefkin collection at the municipal museum; foundation identity preserved, no transfer of ownership asserted.' if collection=='FMW' else 'Municipal collection/fund documented by the museum'))
            if collection=='FMW':
                record['verified_artist_id']='2968aa72-b97a-4ec2-b2f9-698084699245'
            if creator=='Albert Kohler':
                record.update(creator_link_hold=True, creator_identity_note='Gallery caption says Albert Kohler; body says Alfred Kohler. Original caption retained; personal identity unresolved.')
            if creator=='Alexej Jawlensky':
                record['verified_artist_id']='12a8f102-6089-4c8b-829a-52c137c2f467'
            records.append(record)
    url='https://allerheiligen.ch/museum/sammlung/kunst/'
    soup, receipt = r.page(url)
    source_text=soup.get_text(' ',strip=True)
    museum='Museum zu Allerheiligen Schaffhausen'
    selections=[
        ('A1772','Der Holzfäller','Ferdinand Hodler','1910','Öl auf Leinwand','128 x 105 cm','painting','Depositum Sturzenegger-Stiftung'),
        ('B5924','Selbstporträt','Tobias Stimmer','um 1563','Kreide, Tusche und Aquarell auf Papier','19,7 x 15 cm','drawing','Depositum Peyer’sche Tobias Stimmer-Stiftung'),
        ('A1077','Bildnis Tobias Holländer von Berau, Schaffhauser Bürgermeister (1683-1695)','Daniel Savoye','1686','Öl auf Leinwand','17,5 x 99 cm','painting',None),
        ('P119','Ruhender Herkules (Allegorie auf die Schweiz)','Alexander Trippel','1775','Gips','87 cm','sculpture',None),
        ('B6218','Vue de la chûte du Rhin / près de Schaffouse','Johann Ludwig (Louis) Bleuler','um 1840','Gouache mit Weisshöhung auf Papier','42,3 x 58,2 cm','painting',None),
        ('A 556','Selbstbildnis mit Rosen','Ferdinand Hodler','1914','Öl auf Leinwand','43 x 39 cm','painting',None),
    ]
    for inventory,title,creator,date,medium,dimensions,kind,custody in selections:
        for value in [inventory,title,creator,date,medium,dimensions]:
            assert value in source_text, value
        records.append(fact('swiss-allerheiligen',museum,inventory,url,title,creator,date,medium,dimensions,inventory,kind,receipt,
                       dict(custody_note=custody,source_caption=next(str(x).strip() for x in soup.find_all(string=True) if inventory in str(x)),
                            dimensions_note='Dimensions retained literally; apparent source anomaly in A1077 not silently corrected.' if inventory=='A1077' else None)))
    r.b.save(r.RUN/'CH-followup/source-records.json.gz',records)
    print('Selected source records',len(records))


def argentina():
    records=[]
    gaps=[]
    base='https://museopettoruti.icpba.gba.gob.ar/coleccion/obras-destacadas-de-todos-los-tiempos'
    urls=[]
    for number in range(5):
        soup,_=r.page(base+('?page='+str(number) if number else ''))
        for a in soup.select('main a[href]'):
            if '/obras/' in a['href']:
                url=r.urljoin(base,a['href'])
                if url not in urls:urls.append(url)
    def pettoruti(url):
        soup,receipt=r.page(url)
        article=soup.select_one('article.node--type-obras')
        assert article
        fields={r.text(x.select_one('.field__label')):r.text(x.select_one('.field__items') or x.select_one('.field__item')) for x in article.select('.field--label-inline')}
        title=r.text(article.select_one('.field--name-title'))
        alt=article.select_one('.field--name-field-image img')['alt']
        inv=re.search(r'Inv\.\s*([^/]+)',alt)
        inv=inv.group(1).strip() if inv else None
        source_type={'pintura':'painting','grabado':'print','dibujo':'drawing','escultura':'sculpture'}.get(fields.get('Objeto','').lower(),'unknown')
        return fact('argentina-pettoruti','Museo Provincial de Bellas Artes Emilio Pettoruti',url.rsplit('/',1)[-1],url,title,fields.get('Autor'),fields.get('Año') or 'Date unknown',
                    ' sobre '.join(x for x in [fields.get('Técnica'),fields.get('Soporte')] if x) or None,fields.get('Medidas'),inv,source_type,receipt,
                    dict(fields=fields,image_alt=alt,selection='Museum-selected highlights'),
                    creator_link_hold=bool(re.search(r'atribu|an[oó]nim',fields.get('Autor',''),re.I)))
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        records.extend(pool.map(pettoruti,urls))
    index='https://www.malba.org.ar/coleccion/'
    soup,_=r.page(index)
    urls=list(dict.fromkeys(r.urljoin(index,a['href']) for a in soup.select('a[href]') if 'coleccion.malba.org.ar/' in a['href'] and ('/Detail/objects/' in a['href'] or '/abaporu/' in a['href'])))
    def malba(url):
        soup,receipt=r.page(url)
        fields={r.text(x.select_one('.item_label')):r.text(x.select_one('.item_value')) for x in soup.select('.stack_item') if x.select_one('.item_label')}
        if not (fields.get('Título') and fields.get('N° de inventario')):
            gaps.append(dict(url=url,evidence=receipt,reason='Linked page lacks current object title/inventory fields; not converted into an artwork.'))
            return None
        credit=fields.get('Línea de crédito','')
        return fact('argentina-malba','Museo de Arte Latinoamericano de Buenos Aires (Malba)',fields['N° de inventario'],url,fields['Título'],r.text(soup.select_one('.main_author')),fields.get('Año') or 'Date unknown',fields.get('Técnica'),fields.get('Medidas'),fields['N° de inventario'],'painting',receipt,dict(fields=fields,selection='Museum-selected highlights'),credit=credit,
                    editorial_hold=None if 'Colección Malba.' in credit else 'Private Costantini collection/other ownership label: do not equate with museum collection without custody evidence.')
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        records.extend(x for x in pool.map(malba,urls) if x)
    r.b.save(r.RUN/'AR-wave1/source-records.json.gz',records)
    r.b.save(r.RUN/'AR-wave1/source-gaps.json',gaps)
    for x in records:print(x['museum'],x['source_id'],x['title'],x['creator_label'],x['date_display'],x.get('credit',''),flush=True)


def uruguay():
    selected=r.b.load(r.RUN/'UY/mnav-selected-metadata.json.gz')
    records=[];held=[]
    for x in selected['records']:
        if not x['ID'].isdigit() or x['TEC']=='Documento':
            held.append(dict(record=x,reason='Archival document: associated person is not necessarily its maker. Not imported as an artwork.'))
            continue
        medium=x['TEC']
        kind='drawing' if 'lápiz' in medium.lower() or 'dibujo' in medium.lower() else 'painting' if any(t in medium.lower() for t in ['óleo','acrílico','gouache']) else 'watercolor' if 'acuarela' in medium.lower() else 'print' if 'monocopia' in medium.lower() else 'unknown'
        records.append(fact('uruguay-mnav','Museo Nacional de Artes Visuales',x['ID'],'https://acervo.mnav.gub.uy/obras.php?q=ni:'+x['ID'],x['TITULO'],x['creator'],x['REALIZ'],medium,
                            ' x '.join(x[k].strip() for k in ['ALTO','ANCHO','PROF'] if x[k].strip())+' cm',x['ID'],kind,selected['evidence'],
                            dict(source_row=x,selection='Bounded dated works from the museum inventory, currently assigned to MNAV rather than another institution; EXHIBICION retained only as source evidence.'),native_image_url=x['IMAGEN']))
    for key,title,year,dimensions in [('28692','Emigración',1932,'58,5 x 79 cm'),('11839','La primera disputa',1932,'47x 62cm')]:
        url='https://www.museofigari.gub.uy/innovaportal/v/'+key+'/20/mecweb/'+('pedro-figari-emigracion' if key=='28692' else 'pedro-figari:-la-primera-disputa')+'?contid=10752'
        soup,receipt=r.page(url);text=r.text(soup.select_one('#colder'))
        for value in [title,str(year),dimensions]:assert value in text
        records.append(fact('uruguay-figari','Museo Figari',key,url,title,'Pedro Figari',str(year),'Óleo sobre cartón',dimensions,None,'painting',receipt,
                            dict(selection='Museum collection focus entry',source_text=text,
                                 dimensions_note='Emigración: detail caption gives 58,5 x 79 cm; index typo 19 cm retained as conflicting evidence, not accepted.' if key=='28692' else None)))
    r.b.save(r.RUN/'UY-wave1/source-records.json.gz',records)
    r.b.save(r.RUN/'UY-wave1/source-gaps.json',held)
    print('Uruguay records',len(records),'held archival objects',len(held))


def argentina_neuquen():
    names={'SÍVORI EDUARDO':'Eduardo Sívori','SCHIAFFINO EDUARDO':'Eduardo Schiaffino','PUEYRREDÓN PRILIDIANO':'Prilidiano Pueyrredón',
           'MALHARRO MARTIN':'Martín Malharro','GÓMEZ CORNET RAMÓN':'Ramón Gómez Cornet','GARCIA DEL MOLINO FERNANDO':'Fernando García del Molino',
           'GARCÍA DEL MOLINO FERNANDO':'Fernando García del Molino','FIGARI PEDRO':'Pedro Figari','FADER FERNANDO':'Fernando Fader',
           'BUTLER HORACIO':'Horacio Butler','BERNI ANTONIO':'Antonio Berni','BARRADAS RAFAEL':'Rafael Barradas'}
    records=[]
    for path in sorted((r.RUN/'AR/neuquen-selected').glob('*.json.gz')):
        x=r.b.load(path);soup=r.BeautifulSoup(x['html'],'html.parser')
        title=r.text(soup.select_one('h3.elementor-heading-title'))
        assert title
        match=re.search(r',\s*((?:1\d{3})(?:\s*[-–]\s*1\d{3})?)$',title)
        date=match.group(1) if match else 'Date unknown'
        if match:title=title[:match.start()]
        fields={}
        for p in soup.select('.elementor-widget-text-editor p'):
            text=r.text(p)
            if ':' in text:
                key,value=text.split(':',1);fields[key.strip()]=value.strip()
        medium=fields['Técnica'];dimensions=fields['Medidas']
        kind='drawing' if fields.get('Disciplina')=='Dibujo' else 'watercolor' if 'acuarela' in medium else 'painting'
        row=fact('argentina-neuquen','Museo Nacional de Bellas Artes Neuquén',soup.select_one('[data-elementor-post-type="portfolio"]')['data-elementor-id'],x['url'],
                 title,names[x['creator']],date,medium,dimensions,None,kind,x['evidence'],
                 dict(source_creator_label=x['creator'],caption_fields=fields,dimensions_note='Units are not explicit in the object caption; none invented.',
                      custody_note='Native Neuquén collection catalogue. National collection ownership is separate from Neuquén custody; no ownership transfer or current-display assertion.',
                      source_title_and_date=r.text(soup.select_one('h3.elementor-heading-title'))))
        if row['date_decision']=='date_review' and row['year_end']:
            row['editorial_hold']='Native creation/modification span crosses 1970; resolve original and later version dates before catalogue addition.'
        records.append(row)
    assert len(records)==21
    r.b.save(r.RUN/'AR-wave2/source-records.json.gz',records)
    print('Neuquén source objects',len(records))


def uruguay_blanes():
    records=[]
    groups=[('juan-manuel-blanes','Juan Manuel Blanes',[
        ('Aurora','Date unknown','28 x 23 cm','óleo sobre cartón'),
        ('Crepúsculo','Date unknown','24 x 28 cm','óleo sobre cartón'),
        ('Atardecer','Date unknown','48 x 40 cm','óleo s/tela'),
        ('Amanecer','Date unknown','48 x 40 cm','óleo s/tela'),
        ('Escena campestre','circa 1870-1880','80 x 118 cm','óleo sobre tela'),
        ('La cautiva','circa 1879','104.5 x 80 cm','óleo sobre tela'),
        ('Retrato de Clara García de Zúñiga','1857','50.5 x 42 cm','Óleo sobre tela'),
        ('La taba','circa 1878','30 x 39 cm','Óleo sobre tela'),
        ('Los dos caminos','Date unknown','61 x 90 cm','Óleo sobre tela')]),
        ('carmelo-de-arzadun','Carmelo de Arzadun',[
        ('Salida de luna','1945','51 x 70 cm','óleo sobre madera'),
        ('Corral y luna','s/f','62 x 50 cm','óleo sobre madera'),
        ('Las Flores','s/f','38.5 x 60.5 cm','óleo sobre cartón'),
        ('Rue Rossiere','s/f','105.5 x 69 cm','óleo sobre cartón'),
        ('Rue de Nevers','s/f','103,5 x 69 cm','óleo sobre cartón'),
        ('Tiempo gris','1941','92 x 72 cm','óleo sobre tela'),
        ('Paisaje urbano','1940','80 x 54 cm','óleo sobre madera')])]
    for slug,creator,objects in groups:
        url='https://blanes.montevideo.gub.uy/exposiciones/coleccion/la-coleccion-del-museo-blanes/pinacoteca/'+slug
        soup,receipt=r.page(url);text=r.text(soup)
        for title,date,dimensions,medium in objects:
            for value in [title,dimensions,medium]:assert value in text,value
            if date not in ['s/f','Date unknown']:assert date in text
            records.append(fact('uruguay-blanes','Museo de Bellas Artes Juan Manuel Blanes',slug+'-'+r.b.sha((title+'|'+dimensions).encode())[:16],url,
                                title,creator,date,medium,dimensions,None,'painting',receipt,
                                dict(selection='Individually captioned object on museum acervo page; biographical mentions excluded.',
                                     caption=dict(title=title,date=date,dimensions=dimensions,medium=medium),
                                     dedup_note='La cautiva repeats in the gallery caption and lower page; selected once.' if title=='La cautiva' else None)))
    r.b.save(r.RUN/'UY-wave2/source-records.json.gz',records)
    r.b.save(r.RUN/'UY-wave2/source-gaps.json',[
        dict(title='Juramento de los Treinta y Tres Orientales',reason='Caption explicitly identifies MNAV collection and display at Blanes since 1976. Do not treat that as Blanes ownership or a fresh display assertion.'),
        dict(creator='Pedro Figari',reason='Collection page gallery lacks individual titles/dates; no paintings invented from biography or unnamed slides.')])
    print('Blanes captioned objects',len(records))


def paraguay_jesuit():
    url='https://museo.upsanignacio.edu.py/recursos_java/coleccion.js'
    raw,receipt=r.b.capture(url)
    assert receipt['status']==200
    records=[]
    for key,title,html in re.findall(r'"([\w-]+)":\s*\{\s*title:\s*"([^"]+)",\s*spanish:\s*`(.*?)`',raw.decode(),re.S):
        if key=='reloj-solar':
            continue  # Date, maker and object materials not yet reviewed.
        soup=r.BeautifulSoup(html,'html.parser');caption=r.text(soup.select_one('p'))
        creator=('Atribuido a José Brasanelli' if key=='san-antonio' else
                 'Escultor anónimo de las Misiones Jesuíticas Guaraníes' if 'Escultor anónimo' in caption else None)
        century=re.search(r'Siglo (XVIII|XVII)',caption)
        date=century.group(0) if century else 'Date unknown'
        medium=('Madera dorada y policromada' if 'Madera dorada y policromada' in caption else
                'Madera policromada' if 'Madera policromada' in caption else 'Madera tallada y policromada')
        records.append(fact('paraguay-jesuit','Museo Diocesano de Arte Jesuítico-Guaraní de San Ignacio Guazú',key,
                            'https://museo.upsanignacio.edu.py/coleccion.html',title,creator,date,medium,None,None,'sculpture',receipt,
                            dict(caption=caption,collection_model_key=key,caption_script_url=url,
                                 date_note='Maker activity dates and saint biography dates are not artwork creation dates. Century remains explicit, without an invented exact year.'),creator_link_hold=True))
    assert len(records)==5
    r.b.save(r.RUN/'PY-wave1/source-records-supplement-jesuit.json.gz',records)
    print('Jesuit-Guaraní source records',len(records))


def paraguay():
    records=[]
    url='https://www.museodeartesacro.com/coleccion-permanente'
    soup,receipt=r.page(url)
    for card in soup.select('a[onclick*="mostrarDetalleGeneral"]'):
        key=re.search(r"mostrarDetalleGeneral\('([0-9]+)'\)",card['onclick']).group(1)
        caption=r.text(card)
        date='Finales del Siglo XVIII' if 'Finales del Siglo XVIII' in caption else 'Siglo XVIII'
        assert date in caption
        details=r.text(card.select_one('div[style*="height"]'))
        records.append(fact('paraguay-sacro','Museo de Arte Sacro',key,url,r.text(card.select_one('h5')),None,date,
                            details.replace(date,'').strip(),None,None,'sculpture',receipt,
                            dict(caption=caption,origin='Paraguay',creator_note='Individual maker not supplied; no named artist or workshop inferred.',
                                 date_note='Source century and late-century qualifier retained; no exact year or narrower interval invented.'),
                            native_image_url=card.select_one('img')['src']))
    assert len(records)==6
    url='https://cultura.gov.py/2016/05/valiosos-cuadros-en-el-museo-casa-de-la-independencia-aguardan-la-visita-de-los-ciudadanos/'
    soup,receipt=r.page(url);text=r.text(soup)
    for subject in ['Pedro Juan Caballero','Fulgencio Yegros','Dr. José Gaspar Rodríguez de Francia','Mauricio José Troche','Antonio Tomás Yegros','Vicente Ignacio Iturbe']:
        assert subject in text and 'Pablo Alborno' in text and '1911' in text
        records.append(fact('paraguay-casa','Museo Casa de la Independencia','alborno-1911-'+r.b.sha(subject.encode())[:12],url,
                            'Retrato de '+subject,'Pablo Alborno','1911','Óleo',None,None,'painting',receipt,
                            dict(subject=subject,title_note='Descriptive title based on the ministry article; no formal catalogue title supplied.',
                                 custody_note='Government museum director documents the six portraits, transferred from Gabinete Civil for the 2014 restoration; article dated 13 May 2016. Historical custody, not a fresh display assertion.',
                                 evidence_date='2016-05-13')))
    for key,title,creator,phrase in [('bestard-intimacion','Intimación al gobernador Bernardo de Velasco','Jaime Bestard','intimación al entonces Gobernador Bernardo de Velasco'),
                                     ('coimbra-recepcion','La recepción a Fulgencio Yegros','Gil Coimbra','La recepción a Fulgencio Yegros')]:
        assert creator in text and phrase in text
        records.append(fact('paraguay-casa','Museo Casa de la Independencia',key,url,title,creator,'Date unknown',None,None,None,'painting',receipt,
                            dict(title_note='Title/subject wording from the ministry article.',custody_note='Documented museum custody in 2016; no current display claim. Exact date, support and dimensions unknown.',evidence_date='2016-05-13')))
    r.b.save(r.RUN/'PY-wave1/source-records.json.gz',records)
    r.b.save(r.RUN/'PY-wave1/source-gaps.json',[
        dict(source_url=url,reason='Guillermo Da Re passage repeats a sitter and ambiguously describes two works; no object identities invented.'),
        dict(source_url='https://www.museodeartesacro.com/coleccion-permanente',reason='Sculpture photography is not licensed for reuse by the source; metadata selected, native images remain unattached.')])
    print('Paraguay source records',len(records))


if __name__=='__main__':
    globals()[sys.argv[1] if len(sys.argv)>1 else 'swiss']()
