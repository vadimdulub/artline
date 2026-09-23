#!/usr/bin/env python3
"""Pinned editorial decisions for the owner-requested local Cyprus expansion."""
import importlib.util
import json
import re
import unicodedata
import uuid
from pathlib import Path

from bs4 import BeautifulSoup
import psycopg
from psycopg.rows import dict_row

spec = importlib.util.spec_from_file_location('cyprus_capture', Path(__file__).with_name('cyprus-collections-20260921.py'))
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)


def norm(value):
    return ' '.join(re.sub(r'[^\w\s]', ' ', ''.join(c for c in unicodedata.normalize('NFKD', value).lower() if not unicodedata.combining(c))).split())


def uid(value):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'artline:cyprus-review-20260921:' + value))


def evidence(url):
    return core.capture(url)[1]


def dated(display):
    """Preserve qualifiers; broad century bounds never imply a precise year."""
    if not display:
        return dict(display='Date unknown', first=None, last=None, precision='unknown')
    numbers = [int(n) for n in re.findall(r'(?<!\d)\d{3,4}(?!\d)', display)]
    centuries = [int(n) for n in re.findall(r'(?<!\d)(\d{1,2})(?:th|st|nd|rd|ος|ου|ο)?(?:\s*[-–]\s*\d{1,2}(?:ος|ου)?)?\s*(?:century|αι)', display, re.I)]
    if '17-18' in display: centuries = [17, 18]
    if '18th-19th' in display: centuries = [18, 19]
    if numbers and not centuries and len(set(numbers)) == 1:
        n = numbers[0]
        return dict(display=display, first=n, last=n, precision='circa' if re.search('circa|Γύρω', display, re.I) else 'exact')
    if centuries and not numbers:
        return dict(display=display, first=(min(centuries)-1)*100+1, last=max(centuries)*100,
                    precision='century' if len(set(centuries)) == 1 else 'range')
    return dict(display=display + ' — dating unresolved', first=None, last=None, precision='unknown')


# These are reviewed object-specific dates, not saint lifespans or comparison works.
ASINOU_DATES = {
    45222: (1105,1105,'1105','exact'), 45226: (1105,1105,'1105','exact'),
    45229: (1631,1631,'1631','exact'), 45234:(1201,1300,'Late 13th century','century'),
    45236:(1201,1300,'Late 13th century','century'),
    45242:(1101,1400,'12th-century layer; 14th-century repainting','range'),
    45243:(1101,1400,'12th-century layer; 14th-century repainting','range'),
    45244:(1301,1400,'14th century','century'), 45246:(1301,1400,'14th century; earlier layer reported','century'),
    45250:(1301,1400,'14th century','century'), 45251:(1301,1400,'14th century','century'),
    45252:(1301,1400,'14th century','century'), 45255:(1301,1400,'14th century','century'),
    45256:(1501,1600,'16th century','century'), 45257:(1201,1400,'13th- and 14th-century layers','range'),
    45258:(1301,1400,'14th century','century'), 45262:(1101,1200,'12th century','century'),
    45266:(1105,1105,'1105','exact'), 45268:(1201,1400,'13th- and 14th-century layers','range'),
    45269:(1301,1400,'14th century','century'), 45270:(1101,1400,'12th- and 14th-century layers','range'),
    45271:(1101,1400,'12th- and 14th-century layers','range'),
    45273:(1301,1400,'Probably 14th century','century'),
    45274:(1101,1400,'12th-century composition; 14th-century layer','range'),
    45275:(1301,1400,'14th century','century'), 45276:(1301,1400,'14th century','century'),
    45284:(1105,1105,'1105','exact'), 45288:(1201,1400,'Late 13th / early 14th century','range'),
    45302:(1332,1332,'1332','exact'), 45303:(1201,1300,'Early 13th century','century'),
    45333:(1332,1332,'1332','exact'), 45334:(1501,1600,'16th century','century'),
    45336:(1501,1600,'16th century','century'), 45337:(1201,1400,'Late 13th / early 14th century','range'),
    # 45338 contradicts itself (late 13th / 1332), retained with unknown date.
}
EXCLUDED = {
    13503:'Founding inscription; contextual evidence, not a separately selected painting',
    13507:'Furniture and architecture view', 13508:'General view overlaps individually catalogued murals',
    13563:'Detail of Christ Pantocrator composition 13562', 13568:'Partial view of Ascension composition 13570',
    13609:'Detail of ascetic saints 13608', 13610:'Fragment requiring scene-level identity reconciliation',
    13611:'Fragment requiring scene-level identity reconciliation', 13613:'Fragment requiring scene-level identity reconciliation',
    13620:'Crucifixion detail already represented in 13617', 13623:'Altar furniture and inscription',
    13624:'Architectural view',13625:'Architectural view',14618:'Architectural view',
    14528:'General view overlapping individual Akathist scenes',14529:'General view overlapping individual Akathist scenes',
    14530:'General view overlapping individual Akathist scenes',14531:'General view overlapping individual Akathist scenes',
    15221:'1987 creation is outside the confirmed 1970 cutoff',15222:'Iconostasis overview and woodcarving, overlaps individual icons',
    15647:'Mixed icon/relic photograph without sufficiently distinct object identity',16530:'General monastery view',
    18559:'Generic illustration of icon painting, not a uniquely identified artwork',18725:'Church photograph, not a uniquely identified painting',
    45339:'Building material specimens, not paintings',
    13509:'Possible overlap with existing Jesus Pantocrator photograph; identity reconciliation needed',
    13554:'Possible overlap with existing unidentified saint photograph; identity reconciliation needed',
}
ALIASES = {17883:15164,17888:15173,17893:21943,17899:21942,20085:21942,20089:21943,20117:15188}


def archive_works():
    inventory = json.loads((core.RUN/'archive-inventory.json').read_text())
    assert not inventory['errors']
    records = {r['id']:r for r in inventory['records']}
    works, decisions = [], []
    for ident,r in records.items():
        if ident in EXCLUDED or ident in ALIASES:
            decisions.append({'id':ident,'decision':'alias' if ident in ALIASES else 'held',
                              'canonical_id':ALIASES.get(ident),'reason':EXCLUDED.get(ident,'Same object; alternate archive photograph')})
            continue
        f=r['fields']; title=' '.join(f['Title'][0].split()); desc=' '.join(f.get('Description',[]))
        rawdate=' '.join(f.get('Date',[])); notes=[]
        if ident>=45216:
            d=dated('')
            if ident in ASINOU_DATES:
                first,last,display,precision=ASINOU_DATES[ident];d=dict(first=first,last=last,display=display,precision=precision)
            notes.append('Dublin Core Date 2006 and Creator Marinos Ioannides describe the digital documentation, not the medieval painter or creation year.')
            if ident==45338:notes.append('Source dating conflicts: late 13th century versus the 1332 programme. No precise year selected.')
        else:
            d=dated(rawdate)
        if ident in (12196,12197,13555,13562):
            d=dated('');notes.append('Source dates renovation to 1503. Original creation date is unresolved; renovation is not treated as creation.')
        if ident==15180:
            d=dated('');notes.append('Source mixes 1806 offering and 1856 creation statements. Date conflict retained for editorial review.')
        if ident in (15181,15182,15185,15186):notes.append('1951 repainting and subsequent conservation are preserved in source evidence; they are not a new object.')
        if d['first'] and d['first']>1970:
            decisions.append({'id':ident,'decision':'held','reason':'Creation after 1970'});continue
        fresco = ident<15100 or ident in (15548,18538) or ident>=45216
        creator=None;label='Unidentified painter'
        if 'painted by joseph chourri' in desc.lower():creator='Joseph Chourri'
        if 'painted by theodoros apseudis' in desc.lower():creator='Theodore Apsevdis'
        if ident==21942:creator='Theodore Apsevdis'
        if ident==21943:label='Painter from the imperial palace in Constantinople, commissioned by Saint Neophytos'
        if ident==15188:label='Theophylaktos (Theophylactos)'
        if ident==15180:label='Ioannis Cornaros (Cretan painter)'
        if ident==20096:label='In the style of Panaretos'
        if ident in (45226,45285):creator='Asinou Master'
        dimensions=re.search(r'Dimensions\s*:?\s*([\d.,]+\s*[xX×]\s*[\d.,]+(?:\s*cm)?)',desc,re.I)
        medium='Egg tempera on wood' if 'egg tempera on wood' in desc.lower() else None
        context='Cyprus — '+('wall painting' if fresco else 'icon; production place unverified')
        url=f'https://apsida.cut.ac.cy/items/show/{ident}'
        extras=[records[k] for k,v in ALIASES.items() if v==ident]
        works.append(dict(key='apsida-'+str(ident),title=title,alternate_title='; '.join(f.get('Alternative Title',[])) or None,
            url=url,receipt=r['capture'],source_fields=f,additional_sources=extras,source_id=str(ident),scheme='apsida-item',
            date=d,work_type='fresco' if fresco else 'painting',object_form=None if fresco else 'icon',creator=creator,
            creator_label=label,medium=medium,dimensions=dimensions.group(1) if dimensions else None,cultural_context=context,
            creation_country='CY' if fresco else None,notes=notes,
            institution='saint-neophytos-monastery' if ident<45216 and any('Holy Monastery of Saint Neophytos' in c for c in f.get('Creator',[])) else
                        'kykkos-monastery-museum' if any('Museum of Kykkos' in c for c in f.get('Creator',[])) else None,
            connection='Archival documentation; holding and current display not asserted'))
    return works,decisions


def artist(name,url,birth=None,death=None,activity=None,relationship='cultural_affiliation',aliases=(),note='',entity_type='person'):
    if death is not None:
        assert birth is not None
        first,last=birth,death;basis='life';display=f'{first}–{last}'
    elif activity:
        first,last=activity;basis='activity';display=f'Documented activity: {first}–{last}'
    else:
        assert birth is not None
        first=last=birth;basis='life';display=f'Born {birth}; activity dates unrecorded'
        note+=' Only the sourced birth is plotted as a point; no death or full lifespan is inferred.'
    return dict(name=name,url=url,receipt=evidence(url),birth=birth,death=death,first=first,last=last,basis=basis,display=display,
                relationship=relationship,aliases=list(aliases),note=note,entity_type=entity_type)


def artists():
    # Exact dates and explicit Cyprus identity on gallery-authored catalogue pages.
    choices = [
      ('andreas-asproftas','Andreas Asproftas',1919,2004,None),
      ('andreas-charalambides','Andreas Charalambides',None,None,(1975,1975)),
      ('andreas-chrysochos','Andreas Chrysochos',1929,None,(1952,1993)),
      ('aristotelis-demetriou','Aristotelis Demetriou',1962,None,None),
      ('bambos-michlis','Bambos Michlis',1947,None,(1969,1985)),
      ('charilaos-dikaios','Charilaos Dikaios',1912,2000,None),
      ('christos-foukaras','Christos Foukaras',1944,None,(1970,1996)),
      ('costas-economou','Costas Economou',1925,2016,None),
      ('costas-joachim','Costas Joachim',1936,None,(1966,1981)),
      ('george-kotsonis','George Kotsonis',None,None,(1960,1994)),
      ('george-kyriacou','George Kyriacou',1940,None,(1961,1996)),
      ('giorgos-skotinos','Giorgos Skotinos',1937,None,(1961,1982)),
      ('glyn-hughes','Glyn Hughes',1931,2014,None),
      ('john-kiki','John Kiki',1943,None,(1972,1995)),
      ('konstantinos-giannikouris','Konstantinos Giannikouris',1939,None,(1961,1996)),
      ('lanitis-kikos','Kikos Lanitis',1948,None,None),
      ('lefteris-olympios','Lefteris Olympios',1953,None,(1978,2012)),
      ('maria-papacharalambous','Maria Papacharalambous',1964,None,(1984,1990)),
      ('mattheos-christou','Mattheos Christou',1956,None,(1986,2017)),
      ('michalis-charalambides','Michalis Charalambides',1968,None,None),
      ('nicos-nicolaides','Nicos Nicolaides',1884,1956,None),
      ('nikos-kouroussis','Nikos Kouroussis',1937,None,(1960,2001)),
      ('panayiotis-kalorkoti','Panayiotis Kalorkoti',1957,None,(1994,1994)),
      ('renos-loizou','Renos Loizou',1948,2013,None),
      ('stelios-votsis','Stelios Votsis',1929,2012,None),
      ('susan-kerr','Susan Kerr',1943,None,(1966,2014)),
      ('thraki-rossidou-jones','Thraki Rossidou Jones',1920,2007,None),
      ('vasilis-vrionides','Vasilis Vrionides',1883,1958,None),
      ('xanthos-hadjisoteriou','Xanthos Hadjisoteriou',1920,2003,None),
    ]
    out=[]
    for key,name,birth,death,activity in choices:
        note='Catalogue-authored artist identity and source dates retained in review. Artist-level collection references do not establish any particular artwork holding.'
        if key in ('andreas-charalambides','george-kotsonis'):note+=' Birth year conflicts within source: '+('1938/1939' if key=='andreas-charalambides' else '1939/1940')+'. Birth remains unknown.'
        aliases={'giorgos-skotinos':['George Skotinos','Yiorkos Skotinos'],'andreas-chrysochos':['Andreas Chrysohos','Andreas Chryssochos'],
          'konstantinos-giannikouris':['Constantinos Yiannikouris'],'nicos-nicolaides':['Nikos Nikolaides','Nikos Nicolaides'],
          'vasilis-vrionides':['Vasilis Vryonides','Vassilis Vryonides'],'xanthos-hadjisoteriou':['Xanthos Hadjisotiriou']}.get(key,[])
        out.append(artist(name,'https://cypriaauctions.com/artist/'+key,birth,death,activity,
                          relationship='active' if key in ('glyn-hughes','susan-kerr') else 'cultural_affiliation',aliases=aliases,note=note))
    for key,name,birth,death,activity,relation in [
        ('marios_loizides','Marios Loizides',1928,1988,None,'cultural_affiliation'),
        ('andreas_ladommatos','Andreas Ladommatos',1940,None,(1960,1964),'birth'),
        ('fotos_hadjisoteriou','Fotos Hadjisoteriou',1919,2004,None,'birth'),
        ('john_corbidge','John Corbidge',1935,2003,None,'active'),
        ('mikis_nicodemou','Mikis Nicodemou',1941,None,(1959,1963),'birth')]:
        out.append(artist(name,'https://www.psatharis-auctions.com.cy/bio_'+key+'.htm',birth,death,activity,relation,
                          aliases=['John Corbridge'] if key=='john_corbidge' else []))
    out += [artist('Rüzen Atakan','https://www.ruzenatakan.com/',1966,activity=(1988,1988),relationship='birth',aliases=['Ruzen Atakan']),
            artist('Ümit İnatçı','https://umitinatciartcenter.com/about',1960,activity=(1984,1984),relationship='birth',aliases=['Umit Inatci']),
            artist('Niki Marangou','https://www.marangou.com/',1948,relationship='birth'),
            artist('Kallinikos Stavrovouniotis','https://www.appios.org/work/kallinikeio-museum',1920,relationship='birth',
                   note='Museum designer documents the iconographer and museum collection. No individual undated icon is invented.'),
            artist('Theophylaktos','https://apsida.cut.ac.cy/api/items/15188',activity=(1501,1600),relationship='active',
                   aliases=['Theophylactos'],note='Source dates the Enkleistriani icon to the beginning of the 16th century. Broad century plotting bounds; lifespan unknown.'),
            artist('Asinou Master','https://apsida.cut.ac.cy/api/items/45226',activity=(1105,1105),relationship='active',
                   entity_type='anonymous_master',note='Source uses this conventional attribution for the 1105 Asinou frescoes; personal identity unknown.'),
            artist('Lydia Masterkova','https://xeniartspace.com/guidechanneled',1927,activity=(1969,1969),relationship=None,
                   note='International painter represented in XeniArtSpace exhibition. No Cypriot origin inferred.')]
    for name,birth,relation in [
        ('Alexandros Yiorkadjis',1981,'birth'),('Andrea Evangelou',1991,'birth'),
        ('Elena Anastasiou Neocleous',None,'cultural_affiliation'),('Anastasia Krivenko',None,'active'),
        ('Thekla Papadopoulou',None,'active'),('Daphne Christoforou',None,'cultural_affiliation'),
        ('Achilleas Michaelides',1982,'active'),('Pascalis Anastasi',1965,'cultural_affiliation'),
        ('Nicolas Polychronis',1982,'birth'),('Nikolas Antoniou',1988,'birth'),
        ('Christiana Vouzouni',1999,'birth'),('Themis Themistokleous',1951,'birth'),
        ('Michalis Theodosiou',None,'active'),('Nata Chebarkova',1991,'active')]:
        out.append(artist(name,'https://xeniartspace.com/cyprusorbits',birth,activity=(2025,2025),relationship=relation,
              aliases=['Paparazzi'] if name=='Achilleas Michaelides' else [],
              note='Painter or artist with a documented painting practice in the Cyprus Orbits exhibition. 2025 is an exhibition activity anchor, not a lifespan. Later artworks remain outside the 1970 selection cutoff.'))
    return out


def additional_works():
    guide='https://xeniartspace.com/guidechanneled';orbits='https://xeniartspace.com/cyprusorbits'
    rows=[]
    for title,creator,year,medium,url,dimensions in [
        ('Sphinge','Leonor Fini',1969,'Oil on paper',guide,None),
        ('Metaphysical Abstraction','Lydia Masterkova',1969,'Mixed media on canvas',guide,None),
        ('Celestial Division','Lynne Drexler',1966,'Oil on canvas',guide,None),
        ('Blue landscape','Renos Loizou',1966,'Oil on handmade paper laid on board',orbits,'63 × 56 cm'),
        ('Blue Nude','Christoforos Savva',None,'Pencil, pen and gouache on paper',orbits,'68 × 58 cm (framed)'),
        ('Cypriot Woman from the Countryside','Loukia Nicolaides-Vassiliou',1935,'Watercolour on paper',
         'https://www.boccf.org/en-gb/homepage/museums-collections2/sulloge-sugkhrones-kupriakes-tekhnes/sulloge/','29 × 21 cm')]:
        key=('boccf-' if 'boccf' in url else 'xeniartspace-')+norm(creator+' '+title).replace(' ','-')
        rows.append(dict(key=key,title=title,url=url,receipt=evidence(url),scheme='cyprus-reviewed-object',source_id=key,
              date=dated(str(year) if year else ''),work_type='watercolor' if 'boccf' in url else 'drawing' if title=='Blue Nude' else 'painting',
              object_form=None,creator=creator,creator_label=None,medium=medium,dimensions=dimensions,
              cultural_context=None,creation_country=None,institution='boccf' if 'boccf' in url else 'xeniartspace',
              connection='Collection catalogue' if 'boccf' in url else 'CHANNELLED exhibition (22 September 2026–5 March 2027)' if url==guide else 'Cyprus Orbits exhibition (17 May–26 July 2025)',
              notes=['Institutional connection is sourced; permanent membership and current display are not inferred from an exhibition.'] if 'xeniartspace' in url else [],
              source_fields={'title':title,'creator':creator,'year':year,'medium':medium,'dimensions':dimensions},additional_sources=[]))
    return rows


def plan():
    assert not (core.RUN/'applied.json').exists(), 'Applied selection is immutable; use a new campaign for additions'
    aa=artists();ww,decisions=archive_works();ww+=additional_works()
    for w in ww:
        if w['key']=='apsida-15188':w['creator']='Theophylaktos'
    with psycopg.connect(core.DSN,options='-c default_transaction_read_only=on -c statement_timeout=15000',row_factory=dict_row) as db:
        identities=db.execute("SELECT id::text,display_name,normalized_name,slug,status,(SELECT jsonb_agg(alias) FROM artist_aliases x WHERE x.artist_id=a.id) aliases FROM artists a").fetchall()
        lookup={}
        for a in identities:
            for n in [a['display_name'],*(a['aliases'] or [])]:lookup.setdefault(norm(n),set()).add(a['id'])
        for a in aa:
            hits=set().union(*(lookup.get(norm(n),set()) for n in [a['name'],*a['aliases']]))
            assert len(hits)<=1,('Ambiguous painter identity',a['name'],hits)
            a['existing']=bool(hits);a['id']=next(iter(hits)) if hits else uid('artist:'+a['name'])
            a['slug']=norm(a['name']).replace(' ','-')
            lookup.setdefault(norm(a['name']),set()).add(a['id'])
        for w in ww:
            if w['creator']:
                hits=lookup.get(norm(w['creator']),set());assert len(hits)==1,(w['creator'],hits)
                w['artist_id']=next(iter(hits))
            else:w['artist_id']=None
            urls=[w['url']]+[f"https://apsida.cut.ac.cy/items/show/{r['id']}" for r in w['additional_sources']]
            hits=db.execute("""SELECT DISTINCT a.id::text,a.title,a.status FROM artworks a WHERE
              EXISTS(SELECT 1 FROM citations c WHERE c.entity_type='artwork' AND c.entity_id=a.id AND c.source_url=ANY(%s))
              OR EXISTS(SELECT 1 FROM external_identifiers e WHERE e.entity_type='artwork' AND e.entity_id=a.id AND e.canonical_url=ANY(%s))""",(urls,urls)).fetchall() if w['scheme']=='apsida-item' else []
            titlehits=db.execute("""SELECT a.id::text,a.title,a.date_display FROM artworks a WHERE a.normalized_title=%s
               AND EXISTS(SELECT 1 FROM artwork_artists x WHERE x.artwork_id=a.id AND x.artist_id=%s::uuid)""",(norm(w['title']),w['artist_id'])).fetchall() if w['artist_id'] else []
            if not hits and titlehits:
                # Same title/creator alone cannot resolve separate saint panels/variants.
                distinct = w['key'] in ('apsida-15166','apsida-15176')
                decisions.append({'id':w['key'],'decision':'distinct_panels' if distinct else 'identity_check','matches':titlehits,
                  'reason':'Deesis/apostle-row panel has different dimensions and iconostasis position from the existing mourning panel beside the Crucifixion.' if distinct else 'Requires review'})
            assert len(hits)<=1,('Conflicting object authority',w['key'],hits)
            w['existing']=bool(hits);w['id']=hits[0]['id'] if hits else uid('artwork:'+w['key'])
            w['slug']='cyprus-'+norm(w['title']).replace(' ','-')[:110]+'-'+w['id'][:8]
        baseline=json.loads((core.RUN/'baseline.json').read_text())
        existing_selection=[dict(id=w['id'],title=w['title'],url=next((c['source_url'] for c in w['citations'] or [] if c.get('source_url','').startswith('https://')),None))
             for w in baseline['works'] if not (w['creation_year_start'] and w['creation_year_start']>1970)]
        assert all(w['url'] for w in existing_selection)
        owner=db.execute("SELECT * FROM curated_collections WHERE institution_id IS NULL AND curator_kind='owner'").fetchone()
    result=dict(version=1,created_at=core.now(),cutoff=1970,local_only=True,status='review',artists=aa,works=ww,
        existing_selection=existing_selection,decisions=decisions,owner_collection_id=str(owner['id']))
    # Each plan revision is retained; applying always requires the exact SHA-256.
    planpath=core.RUN/'application-plan.json'
    if planpath.exists():
        old=planpath.read_bytes();core.save(core.RUN/'plan-history'/(core.hashlib.sha256(old).hexdigest()+'.json'),old)
        planpath.unlink()
    core.save(planpath,result)
    print(json.dumps({'artist_candidates':len(aa),'new_artists':sum(not a['existing'] for a in aa),
          'work_candidates':len(ww),'new_works':sum(not w['existing'] for w in ww),'existing_selections_reviewed':len(existing_selection),
          'identity_checks':[d for d in decisions if d['decision']=='identity_check']},ensure_ascii=False))


if __name__=='__main__':
    plan()
