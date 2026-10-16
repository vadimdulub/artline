#!/usr/bin/env python3
"""Editorially reviewed country breadth, institution identity, and delivery planning."""
import argparse,collections,gzip,importlib.util,json,re
from pathlib import Path
s=importlib.util.spec_from_file_location('facts',Path(__file__).with_name('south-america-facts-20261011.py'));f=importlib.util.module_from_spec(s);s.loader.exec_module(f);c=f.c;d=c.d

def manual():
    rows=[]
    def add(co,provider,museum,ident,url,title,creator,date,medium,dimensions,inv=None,kind='painting',**extra):
        raw,rc=c.capture(url)
        row=f.f.fact(provider,museum,ident,url,title,creator,date,medium,dimensions,inv,kind,rc,dict(editorial=extra.pop('editorial','Exact source caption and explicit museum collection; no current-display claim.')),country_code=co,creator_link_hold=True,**extra)
        b=f.date_bounds(date);assert b,(title,date)
        row.update(year_start=b[0],year_end=b[1],date_decision='eligible');rows.append(row);return row
    bo='https://www.lexivox.org/norms/BO-DS-25549.xhtml'
    for key,title,creator,date,dim,inv in [
      ('1-025','Descanso en la Huida a Egipto','Melchor Pérez Holguín','1720/25','151 x 104 cm','1-025'),
      ('virgen-toledo','Virgen de Toledo con Carlos II','Anónimo','1670','166 x 99,5 cm',None),
      ('asiel','Asiel Timor Dei. Arcángel Arcabucero','Anónimo','1680','214 x 144 cm',None)]:
        add('BO','bolivia-decree','Museo Nacional de Arte (La Paz)','DS25549-'+key,bo,title,creator,date,'Óleo sobre lienzo',dim,inv,source_provider_name='Bolivia, Decreto Supremo 25549 (1999), museum loan annex — LexiVox transcription',holding_confidence=.90,holding_basis='Decree explicitly identifies all listed paintings as property of the Museo Nacional de Arte, La Paz, with a temporary loan and required return. Archival holding evidence; no assertion of current display.',editorial='Original decree annex; museum identity cross-checked against its current official website. The San Pedro painting is held separately because two catalogues give conflicting dimensions and titles.')
    add('GY','guyana-national','National Gallery of Art, Castellani House','burrowes-dolorous-garde-1951','https://www.stabroeknews.com/2015/05/03/features/guiana-land-of-the-dolorous-garde/','Guiana, Land of the Dolorous Garde','Edward Rupert Burrowes','1951','Oil on canvas',None,source_provider_name='Stanley Greaves and Akima McPherson — Conversation on Art, Stabroek News (2015)',holding_confidence=.94,holding_basis='Artist conversation explicitly identifies the Guyana National Collection at Castellani House; caption supplies artist, creation year and medium with photograph credited to the National Gallery. Its May 2015 exhibition dates are not a current-display assertion.')
    add('SR','suriname-stedelijk','Stichting Surinaams Museum','surinamese-school-reader-2021-p58-maxie','https://stedelijkstudies.com/wp-content/uploads/2021/07/Surinamese-School-Reader-2021.pdf','MAXIE Queen of Paramaribo','Nic Loning','1967','Oil on linen',None,source_provider_name='Stedelijk Museum Amsterdam — Surinamese School reader (2021), page 58',holding_confidence=.97,holding_basis='Visually verified printed page 58 names Stichting Surinaams Museum, Paramaribo as the collection. Amsterdam is the exhibition venue, not the holding museum.',editorial='Caption visually checked against rendered PDF page 58. No inventory or dimensions supplied in the caption; left unknown. Reproduction is outside the existing image cutoff.')
    ve='https://www.wikiart.org/en/arturo-michelena/miranda-en-la-carraca-1896'
    v=next(d.load(p) for p in (c.RUN/'VE/wikiart-objects').glob('*') if d.load(p)['index']['url']==ve)
    row=add('VE','venezuela-wikiart','Galería de Arte Nacional (Caracas)',v['metadata']['_id'],ve,v['metadata']['title'],v['metadata']['artistName'],'1896','Oil on canvas','197 x 245.2 cm',source_provider_name='WikiArt — approved artwork source',holding_confidence=.94,holding_basis='WikiArt explicitly names National Art Gallery (GAN), Caracas, Venezuela. Full-size 197 x 245.2 cm version, not the smaller artist replicas.',image_url=v['metadata']['image'],image_rights_label='Public domain',image_license_url=ve,image_credit='Arturo Michelena; reproduction via WikiArt',image_evidence=v['evidence'],image_match_confidence=.99)
    py='https://www.portalguarani.com/detalles_museos_otras_obras.php?PqwoiflUYTeslk=MTYzOA=='
    add('PY','paraguay-mnba-portal','Museo Nacional de Bellas Artes de Asunción','1638',py,'PESCADO Y MESA','VICENTE FORTE','1962','Óleo sobre tela','100 x 72 cms.',source_provider_name='Portal Guaraní — Museo Nacional de Bellas Artes catalogue (2003)',holding_confidence=.91,holding_basis='Exact catalogue caption reproduced with museum director Lotte Schulz and Instituto Cultural Paraguayo Alemán–Goethe Zentrum credits. Creator is Vicente Forte, as printed; not Juan Carlos Forte.')
    gf=add('FR','french-guiana-pop','Musée Alexandre-Franconie (Cayenne)','M1063000042','https://pop.culture.gouv.fr/notice/joconde/M1063000042','Le fameux satyre de Solesme au Bagne','LK','1901–1950','Papier; crayon','H. 28,5 cm, l. 21,5 cm','MDA 92.1.6','drawing',source_provider_name='Ministère de la Culture — POP / Joconde',territory_code='GF',editorial='Source creation field is 1ère moitié 20e siècle; explicit range 1901–1950 is its conventional interpretation, not an exact year. Monogram LK retained without invented identity. French Guiana is a South American French territory, not a thirteenth independent country.')
    gf['date_display']='1ère moitié 20e siècle'
    names=collections.defaultdict(set)
    with d.connect() as db:
        for a in db.execute("SELECT id::text,display_name name FROM artists WHERE status<>'archived' UNION SELECT a.id::text,al.alias FROM artists a JOIN artist_aliases al ON al.artist_id=a.id WHERE a.status<>'archived'"):names[d.norm(a['name'])].add(a['id'])
    for row in rows:
        if row['creator_label']!='Anónimo' and len(names[d.norm(row['creator_label'])])==1:row['verified_artist_id']=next(iter(names[d.norm(row['creator_label'])]))
    d.save(c.RUN/'BREADTH/manual-facts.json.gz',dict(records=rows,held=[dict(country='BO',title='San Pedro de Alcántara asistido por Cristo / Éxtasis de San Pedro de Alcántara',reason='1701 agrees, but 82 x 55 cm in the decree versus 72.5 x 55 cm in José de Mesa exhibition catalogue. Physical version/dimension reconciliation held; not counted as new.',sources=[bo,'https://www.bolivian.com/angeles/salcantara.html'])]));print('Manual country breadth',len(rows),flush=True)

def registry():
    reg={};geo={}
    def add(name,slug,website,co,city,url=None,basis=None,receipt=None):
        reg[name]=dict(slug=slug,website=website,country_code=co,city=city)
        if receipt is None:
            x=c.probe(url);assert not x.get('error') and x['evidence']['status']==200;receipt=x['evidence']
        geo[slug]=dict(city=city,country_code=co,evidence=receipt,basis=basis or 'Explicit city and country on the source institution page.')
    add('Museu de Arte de São Paulo Assis Chateaubriand (MASP)','museum-source-17422a1d729e01c241e8','https://masp.org.br','BR','São Paulo','https://masp.org.br')
    add('Museo Nacional de Bellas Artes (Santiago)','museo-nacional-bellas-artes-santiago','https://www.mnba.gob.cl','CL','Santiago','https://www.mnba.gob.cl')
    directories={co:d.load(c.RUN/co/'directory.json.gz')['records'] for co in ['CL','CO']}
    for name,slug,website,co,city,ident in [
       ('Museo Regional de Rancagua','museo-regional-rancagua','https://www.museorancagua.gob.cl','CL','Rancagua','6426'),
       ('Pinacoteca Universidad de Concepción','pinacoteca-universidad-concepcion','https://extension.udec.cl','CL','Concepción','10508'),
       ('Banco de la República — Colección de Arte','banco-republica-coleccion-arte','https://colecciones.banrepcultural.org','CO','Bogotá','6143')]:
        entry=next(x for x in directories[co] if x['directory_id']==ident)
        add(name,slug,website,co,city,receipt=entry['evidence'],basis=dict(directory=entry,identity='Collection authority and its Bogotá museum complex, distinct from the Museo Botero venue.' if co=='CO' else 'Exact museum/university collection and directory locality.'))
    add('Museo de Arte de Lima','museo-arte-lima','https://www.mali.pe','PE','Lima','https://www.mali.pe')
    add('Museo Nahím Isaías','museo-nahim-isaias-guayaquil','https://colecciones-ecuador.skin-web.org/es/pagina/museo-nahim-isaias/6a79ee87382a0e1107b1227e?v=mosaic','EC','Guayaquil','https://turismo.guayaquil.gob.ec/es/experiencias/cultura')
    add('Museo Nacional de Arte (La Paz)','museo-nacional-arte-la-paz','https://museonacionaldearte.gob.bo','BO','La Paz','https://museonacionaldearte.gob.bo/')
    add('National Gallery of Art, Castellani House','national-gallery-castellani-house','https://portal.gov.gy/agencies/castellani-house','GY','Georgetown','https://portal.gov.gy/agencies/castellani-house')
    sr=d.load(c.RUN/'pdfs/SR-stedelijk.json')
    add('Stichting Surinaams Museum','stichting-surinaams-museum',None,'SR','Paramaribo',receipt=sr,basis='Page 58, institutional lender caption explicitly names Paramaribo. Museum website omitted pending site-integrity review; .net currently contains unrelated betting material and .org has conflicting location metadata.')
    ve='https://www.wikiart.org/en/arturo-michelena/miranda-en-la-carraca-1896'
    add('Galería de Arte Nacional (Caracas)','galeria-arte-nacional-caracas',None,'VE','Caracas',ve,basis='Approved WikiArt object Location field explicitly states National Art Gallery (GAN), Caracas, Venezuela. FMN website DNS failed; no invented replacement website.')
    gf='https://pop.culture.gouv.fr/notice/joconde/M1063000042'
    add('Musée Alexandre-Franconie (Cayenne)','musee-alexandre-franconie-cayenne',None,'FR','Cayenne',gf,basis='French Ministry of Culture object record explicitly identifies Cayenne museum and Collectivité territoriale de Guyane. France country retained; territory GF reported separately.')
    old={}
    for p in [c.PREVIOUS/'institution-registry.json',*c.PREVIOUS.glob('institution-registry-wave*.json')]:old.update(d.load(p))
    for name in ['Museo Nacional de Bellas Artes Neuquén','Museo Nacional de Artes Visuales','Museo Nacional de Bellas Artes de Asunción']:
        reg[name]=old[name];reg[name].pop('directory_id',None)
        slug=reg[name]['slug'];found=[]
        for base in [c.PREVIOUS,c.OLD]:
            for p in base.glob('*/geography-reviewed.json'):
                found.extend(x for x in d.load(p) if x['name']==name)
        if not found:
            for base in [c.PREVIOUS,c.OLD]:
                path=base/'geography-evidence'/(slug+'.json.gz')
                if path.exists():
                    x=d.load(path);found.append(dict(name=name,evidence=x['evidence'],basis=x));break
        assert found,name
        x=found[-1];c.capture(x['evidence']['url']);geo[slug]=dict(city=reg[name]['city'],country_code=reg[name]['country_code'],evidence=x['evidence'],basis=x['basis'])
    d.save(c.RUN/'institution-registry.json',reg)
    for slug,x in geo.items():d.save(c.RUN/'geography-evidence'/(slug+'.json.gz'),x)
    d.save(c.RUN/'country-registry.json',{co:dict(record=dict(code=co,name=label,region_code='south-america'),evidence=next(v['evidence'] for v in geo.values() if v['country_code']==co),basis='Source explicitly identifies country; ISO 3166 alpha-2 code and South America geography.') for co,label in [('BO','Bolivia'),('EC','Ecuador'),('GY','Guyana'),('SR','Suriname')]})
    print('Institution registry',len(reg),flush=True)

def reuse():
    for co,tag in [('AR','complete'),('UY','final')]:
        x=d.load(c.PREVIOUS/co/(tag+'-facts.json.gz'))
        for row in x['records']:c.capture(row['evidence']['url']);row['country_code']=co
        d.save(c.RUN/co/'reuse-facts.json.gz',x);print('Reused exact native evidence',co,len(x['records']),flush=True)

def plan(country,tag,phase,limit):
    records=d.load(c.RUN/country/(tag+'-facts.json.gz'))['records']
    for row in records:
        if row['museum']=='Museo Nacional de Bellas Artes':row['museum']='Museo Nacional de Bellas Artes (Santiago)'
        if re.search(r'\b(comodato|préstamo|prestamo|empréstimo|emprestimo|loan|depósito|deposito)\b',row.get('credit') or '',re.I):
            row['editorial_hold']='Source credit identifies a loan/deposit; owner-versus-custodian holding semantics need separate review'
        if row['provider']=='brazil-masp' and 'fundicao' in d.norm(row.get('creator_label')):
            row['editorial_hold']='Source names a separate foundry; model date versus physical bronze cast date requires version-specific review'
        if row['provider']=='brazil-masp':
            bio=row['raw']['source_fields'].get('Dados biográficos','')
            years=[int(v) for v in re.findall(r'(?<!\d)(1[0-9]{3}|20[0-9]{2})(?!\d)',bio)]
            if len(years)==2 and years[0]<years[1] and (row['year_start']>years[1] or row['year_end']<years[0]):
                row['editorial_hold']='Native creation field conflicts with native creator lifespan; do not silently correct the date or infer an eligible year'
    # Balance Chile's final selection across researched institutions first.
    if country=='CL':
        grouped=collections.defaultdict(list)
        for row in records:grouped[row['museum']].append(row)
        records=[]
        while any(grouped.values()):
            for name in sorted(grouped):
                if grouped[name]:records.append(grouped[name].pop(0))
    d.save(c.RUN/country/(phase+'-facts.json.gz'),dict(records=records))
    c.c.RUN=c.RUN;c.c.source_plan(country,phase,phase,limit)

def geography(phase):
    g=c.module('south_geography','switzerland-southern-cone-geography-20261011.py');g.d=d;g.run(phase)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['manual','registry','reuse','plan','apply','geography']);p.add_argument('--country');p.add_argument('--tag');p.add_argument('--phase');p.add_argument('--limit',type=int);a=p.parse_args()
    if a.action=='plan':plan(a.country,a.tag,a.phase,a.limit)
    elif a.action=='apply':d.apply(a.phase)
    elif a.action=='geography':geography(a.phase)
    else:globals()[a.action]()
