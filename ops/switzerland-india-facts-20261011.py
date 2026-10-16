#!/usr/bin/env python3
"""Selected museum objects, with source fields kept separate from interpretation."""
import argparse
import collections
import importlib.util
import json
import re
from pathlib import Path
from urllib.parse import urljoin

spec = importlib.util.spec_from_file_location('campaign', Path(__file__).with_name('switzerland-india-museums-20261011.py'))
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)
m, RUN = c.m, c.RUN

REGISTRY = {
    'solothurn': ('Kunstmuseum Solothurn', 'wikimedia-museum-q683163', 'https://www.kunstmuseum-so.ch', '602', 'Solothurn'),
    'langmatt': ('Museum Langmatt Sidney and Jenny Brown Foundation', 'wikimedia-museum-q1341595', 'https://www.langmatt.ch', '47', 'Baden'),
    'luzern': ('Kunstmuseum Luzern', 'wikimedia-museum-q1792543', 'https://www.kunstmuseumluzern.ch', '373', 'Luzern'),
    'stgallen': ('St. Gallen Museum of Art', 'wikimedia-museum-q1792552', 'https://www.kunstmuseumsg.ch', '532', 'St. Gallen'),
    'chaux': ('Musée des Beaux-Arts de La Chaux-de-Fonds, La Chaux-de-Fonds, Switzerland', 'museum-source-96f34529ae890f4fd5c4', 'https://www.mbac.ch', '153', 'La Chaux-de-Fonds'),
    'rietberg': ('Museum Rietberg', 'museum-rietberg', 'https://rietberg.ch', '762', 'Zürich'),
    'rosengart': ('Museum Sammlung Rosengart', 'museum-sammlung-rosengart', 'https://www.rosengart.ch', '874', 'Luzern'),
    'olten': ('Kunstmuseum Olten', 'kunstmuseum-olten', 'https://kunstmuseumolten.ch', '459', 'Olten'),
    'locle': ('Musée des beaux-arts du Locle', 'musee-des-beaux-arts-du-locle', 'https://www.mbal.ch', '355', 'Le Locle'),
    'neuchatel': ("Musée d’art et d’histoire de Neuchâtel", 'musee-art-histoire-neuchatel', 'https://www.mahn.ch', '434', 'Neuchâtel'),
    'chur': ('Bündner Kunstmuseum Chur', 'bundner-kunstmuseum-chur', 'https://kunstmuseum.gr.ch', '157', 'Chur'),
    'masi': ('Museo d’arte della Svizzera italiana', 'museo-arte-svizzera-italiana', 'https://www.masilugano.ch', '365', 'Lugano'),
    'fribourg': ("Musée d’art et d’histoire Fribourg", 'musee-art-histoire-fribourg', 'https://www.fr.ch/mahf', '211', 'Fribourg'),
    'jenisch': ('Musée Jenisch Vevey', 'musee-jenisch-vevey', 'https://museejenisch.ch', '681', 'Vevey'),
}


def clean(s):
    return re.sub(r'\s+', ' ', s.replace('\xad', '').replace('\u200b', '')).strip()


def bounds(display):
    # Only source creation fields, never years extracted from biographies or provenance.
    text = clean(display).lower()
    match = re.fullmatch(r'(?:um |vers |ca\. |circa )?(\d{4})(?:[/–−-](\d{2,4}))?', text)
    if match:
        lo = int(match[1]); end = match[2]
        hi = int(end) if end and len(end) == 4 else (lo // 100 * 100 + int(end) if end else lo)
        if hi < lo:
            return None, None, 'date_review'
        return lo, hi, 'eligible' if hi <= 1970 else ('after_cutoff' if lo > 1970 else 'date_review')
    match = re.fullmatch(r'(\d{1,2})\. (?:jahrhundert|jh\.)', text)
    if match:
        lo, hi = (int(match[1])-1)*100+1, int(match[1])*100
        return lo, hi, 'eligible' if hi <= 1970 else 'date_review'
    return None, None, 'date_review'


def page(key):
    discovery = m.load(RUN/'CH/native-discovery'/(key+'.json'))
    p, rc = c.source(discovery['url'])
    return p, rc, discovery['url']


def add(rows, museum, native_id, title, creator, date, receipt, url, snippet,
        medium=None, dimensions=None, accession=None, work_type='unknown', culture=None, **extra):
    assert clean(title) in clean(snippet), ('Title missing from selected source context', title)
    lo, hi, decision = bounds(date)
    r = dict(provider='swiss-'+museum, museum=REGISTRY[museum][0], source_id=str(native_id),
             source_url=url, title=clean(title), creator_label=clean(creator) if creator else None,
             date_display=clean(date), year_start=lo, year_end=hi, date_decision=decision,
             medium=medium, dimensions=dimensions, accession_number=accession,
             source_type=work_type, culture=culture, evidence=receipt,
             raw={'selected_source_context': clean(snippet), 'directory_id': REGISTRY[museum][3]},
             selection_basis='Small documented collection selection for nationwide breadth; no display assertion',
             **extra)
    if not creator or re.search(r'unbekannt|unbekannter|meister|zugeschrieben|nach |attribu|anonymous|unknown', creator, re.I):
        r['creator_link_hold'] = True
    rows.append(r)


def first_wave():
    rows = []
    p, rc, u = page('solothurn-holbein')
    add(rows, 'solothurn', '27478', 'Solothurner Madonna', 'Hans Holbein (der Jüngere)', '1522', rc, u,
        p.select_one('.text').get_text(' ', strip=True), 'Öl auf Lindenholz', '143.5 × 102 × 3.7 cm', 'A I 134', 'painting')

    p, rc, u = page('langmatt')
    for a in p.select('a[title]'):
        match = re.fullmatch(r'([^,]+), «(.+)», (.+)', a.get('title', ''))
        if not match or len([x for x in rows if x['provider']=='swiss-langmatt']) >= 5:
            continue
        creator, title, date = match.groups()
        img = a.find('img'); alt = img.get('alt', '') if img else ''
        snippet = a['title']+' '+alt
        target = urljoin(u, a['href']); detail, detail_rc = c.source(target)
        # Index captions resolve adjacent-work navigation on detail pages.
        add(rows, 'langmatt', target.split('/sammlung/', 1)[1], title, creator.title(), date, rc, u,
            snippet, work_type='painting', object_url=target, object_evidence=detail_rc,
            raw_caption=alt)

    p, rc, u = page('rosengart')
    for item in p.select('.map-texte p')[:5]:
        fields = [clean(x) for x in item.get_text('\n', strip=True).splitlines() if clean(x)]
        assert len(fields)==3, fields
        creator, title, date = fields
        title = title.strip('«,»'); creator = creator.rstrip(',')
        add(rows, 'rosengart', m.sha((creator+'/'+title).encode())[:20], title, creator, date, rc, u,
            item.get_text(' ', strip=True))

    p, _, base = page('luzern')
    selected = ['206', '570', '4276', '455', '2274']
    for native_id in selected:
        url = base+'?werke-detail='+native_id
        obj, rc = c.source(url)
        italic = obj.find('i')
        assert italic, url
        caption = italic.parent
        fields = [clean(x) for x in caption.get_text('\n', strip=True).splitlines() if clean(x)]
        assert len(fields)==3, fields
        text = (obj.find('main') or obj).get_text('\n', strip=True)
        lines = [clean(x) for x in text.splitlines() if clean(x)]
        i = lines.index(fields[2]); medium, dimensions = lines[i+1:i+3]
        acc = next((x.split('Inv.-Nr.',1)[1].strip() for x in lines if 'Inv.-Nr.' in x), None)
        add(rows, 'luzern', native_id, fields[1], fields[0], fields[2], rc, url,
            text, medium, dimensions, acc, 'painting', credit='; '.join(lines[i+3: i+8]))

    for native_id in ['2005-100', '2005-101', '2005-102', '2005-103', '2005-104']:
        url = 'https://rietberg.ch/en/collections/'+native_id
        obj, rc = c.source(url)
        title = obj.find('h1').get_text(' ', strip=True)
        facts = {dt.get_text(' ', strip=True): dt.find_next_sibling('dd').get_text(' ', strip=True)
                 for dt in obj.select('dl dt') if dt.find_next_sibling('dd')}
        assert facts.get('Inventory number') == native_id.replace('-', '.'), facts
        add(rows, 'rietberg', native_id, title, facts.get('Artist/Creator'), facts.get('Date', 'Date unknown'),
            rc, url, obj.get_text(' ', strip=True), facts.get('Material and technique'), facts.get('Dimensions'),
            facts['Inventory number'], 'drawing', facts.get('Style/Culture'),
            credit=facts.get('Credit line'), native_fields=facts)

    p, rc, u = page('stgallen')
    # First-class anonymous Greek/Russian icon coverage: inventory distinguishes versions.
    icons = {
        'G 2013.67': ('Christus Pantokrator', 'Griechenland', '19. Jahrhundert', 'Eitempera auf Holz', '41,5 × 34 cm'),
        'G 2013.104': ('Synaxis der Engel', 'Russland', 'Anfang 18. Jahrhundert', 'Eitempera auf Holz, Metallnimbus', '31,3 × 27 cm'),
        'G 2013.119': ('Die Heilige Dreifaltigkeit (alttestamentlicher Typ), Mitteltafel eines Triptychons', 'Griechenland', '18. Jahrhundert', 'Eitempera auf Holz', '19 × 11 cm'),
        'G 2013.103': ('Erzengel Michael und Gabriel', 'Russland', '19. Jahrhundert', 'Eitempera auf Holz', '38,5 × 31 cm'),
        'G 2013.28': ('Gottesmutter von Kasan', 'Rumänien [od. Westukraine?]', '18. Jahrhundert', 'Tempera auf Holz', '35 × 36,6 cm'),
    }
    for acc, (title, culture, date, medium, dimensions) in icons.items():
        caption = next(x.get_text(' ', strip=True) for x in p.select('figcaption') if re.search(re.escape(acc)+r'(?:\D|$)', x.get_text(' ', strip=True)))
        add(rows, 'stgallen', acc, title, None, date, rc, u, caption, medium, dimensions, acc, 'painting', culture,
            attribution_basis='Native icon catalogue gives cultural origin but no named creator')

    p, rc, u = page('olten')
    selections = [
        ('Di.B-41', 'Selbstbildnis als junger Mann', 'Martin Disteli', 'um 1832', 'Feder über Bleistift, Aquarell, auf Papier', '9.5 × 8.3 cm', 'drawing'),
        ('1861.B85 / Di.Z-5', 'Gestörtes Liebesabenteuer (Zölibat), Entwurf für ein Agitationstaschentuch', 'Martin Disteli', 'um 1834', 'Feder und Aquarell über Bleistift auf Papier', '37 × 37.2 cm', 'drawing'),
        ('Di.H-10', 'Hugis Sturz auf dem Rottalgletscher', 'Martin Disteli', '1830', 'Feder über Bleistift, Aquarell und Gold auf Velin', '13 × 10.5 cm', 'drawing'),
        ('1972.26', 'Kirchenraum Paris', 'Otto Morach', '1912', 'Öl auf Leinwand', '81 × 60 cm', 'painting'),
        ('1967.17', 'Selbstbildnis', 'Otto Morach', '1915', 'Öl auf Jute', '31.5 × 41 cm', 'painting'),
    ]
    for acc, title, creator, date, medium, dimensions, kind in selections:
        caption = next(x.get_text(' ', strip=True) for x in p.select('figcaption') if 'Inv. '+acc in x.get_text(' ', strip=True))
        add(rows, 'olten', acc, title, creator, date, rc, u, caption, medium, dimensions, acc, kind)

    p, rc, u = page('locle')
    for item in p.select('.more-info'):
        fields = [clean(x) for x in item.get_text('\n', strip=True).splitlines() if clean(x)]
        if len(fields)!=3 or len([x for x in rows if x['provider']=='swiss-locle'])>=5:
            continue
        creator, title, date = fields
        if bounds(date)[2]=='after_cutoff' or title in ['Olympia', 'Sans titre']:
            continue
        creator = re.sub(r'\s*\([^)]*\)$', '', creator)
        add(rows, 'locle', m.sha((creator+'/'+title).encode())[:20], title, creator, date, rc, u,
            item.get_text(' ', strip=True))

    p, rc, u = page('chaux-junod')
    for node in p.select('figcaption')[:5]:
        caption = clean(node.get_text(' ', strip=True))
        match = re.match(r'(.+?), «(.+)», ([\d–−\-]+) (Huile .+), ([\d., ×x]+ cm)', caption)
        assert match, caption
        creator, title, date, medium, dimensions = match.groups()
        add(rows, 'chaux', m.sha((creator+'/'+title).encode())[:20], title, creator, date, rc, u,
            caption, medium, dimensions, work_type='painting')

    p, rc, u = page('neuchatel-paintings')
    for img in p.select('img[alt]'):
        alt = img.get('alt', '')
        match = re.fullmatch(r'(.+?) \([\d–-]+\), (.+), (\d{4})\. (AP \d+)', alt)
        if not match or len([x for x in rows if x['provider']=='swiss-neuchatel'])>=5:
            continue
        creator, title, date, accession = match.groups()
        if int(date)>1970:
            continue
        add(rows, 'neuchatel', accession, title, creator, date, rc, u, alt, accession=accession,
            work_type='painting')

    p, rc, u = page('chur-kauffmann')
    add(rows, 'chur', 'self-portrait-minerva', 'Selbstbildnis mit der Büste der Minerva', 'Angelika Kauffmann',
        'Date unknown', rc, u, p.get_text(' ', strip=True), work_type='painting')

    assert len({(x['provider'],x['source_id']) for x in rows})==len(rows)
    m.save(RUN/'CH-wave1/source-records.json.gz', rows)
    registry = {name: dict(slug=slug, website=website, directory_id=directory_id, city=city, country_code='CH')
                for name, slug, website, directory_id, city in REGISTRY.values()}
    m.save(RUN/'institution-registry.json', registry)
    print(json.dumps({'records':len(rows),'museums':dict(collections.Counter(x['museum'] for x in rows)),
                      'dates':dict(collections.Counter(x['date_decision'] for x in rows))}), flush=True)


if __name__=='__main__':
    first_wave()
