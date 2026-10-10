#!/usr/bin/env python3
"""Build an immutable, individually reviewable museum and artwork selection."""
import importlib.util, re, json, gzip, collections, hashlib
from pathlib import Path
spec=importlib.util.spec_from_file_location('m',Path(__file__).with_name('morocco-africa-20261008.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def page(key):return m.load(m.RUN/'pages'/(key+'.json'))
def ref(path):return dict(path=str(path.relative_to(m.ROOT)),sha256=hashlib.sha256(path.read_bytes()).hexdigest())
def institution(key,name,city,country,source,anchor,kind='museum',note=''):
    assert anchor in source['text'],(key,anchor)
    return dict(key=key,id=m.uid('institution/'+key),slug='africa-'+key,name=name,city=city,country=country,kind=kind,
        source_url=source['receipt']['url'],receipt=source['receipt'],anchor=anchor,note=note,
        confidence=.98,confidence_basis='Exact institution identified by its operator or national heritage authority; source name and city retained. Editorial assessment, not a calibrated probability.')

def directory():
    out=[]
    cities={26:'Marrakech',27:'Rabat',28:'Tanger',29:'Safi',30:'Marrakech',31:'Rabat',32:'Tanger',33:'Tanger',34:'Tétouan',35:'Tétouan',36:'Rabat',37:'Meknès',38:'Tanger',39:'Rabat',40:'Marrakech',41:'Agadir',42:'Azilal',43:'Salé',44:'Fès',45:'Agadir',46:'Casablanca',54:'Casablanca'}
    for n,city in cities.items():
        d=m.load(m.RUN/'fnm-museums'/(str(n)+'.json'));name=d['headings'][0]
        out.append(institution('fnm-'+str(n),name,city,'MA',d,name,note='Official FNM directory entry. Object-level research separate; no assertion that every museum holds eligible visual art.'))
    manual=[
      ('almada','Fondation Al Mada — Collection des Villas des Arts','Casablanca','MA','almada',"Al Mada Foundation's masterpieces",'foundation','Collection belongs to the foundation. Works are not assigned to either Casablanca or Rabat venue without object-level evidence.'),
      ('macaal','Musée d’Art Contemporain Africain Al Maaden (MACAAL)','Marrakech','MA',None,'MACAAL','museum',''),
      ('legation','Tangier American Legation Museum','Tanger','MA','legation','Tangier American Legation','museum',''),
      ('belkahia','Musée Farid Belkahia','Marrakech','MA','belkahia','Visite du musée','museum',''),
      ('ysl','Musée Yves Saint Laurent Marrakech','Marrakech','MA','ysl','MUSÉE YVES SAINT LAURENT MARRAKECH','museum',''),
      ('berber','Musée Pierre Bergé des Arts Berbères','Marrakech','MA','ysl','Pierre Bergé Museum of Berber Arts','museum','Separate museum at Jardin Majorelle, not the Yves Saint Laurent museum.'),
      ('photo','Maison de la Photographie de Marrakech','Marrakech','MA','photo','Maison de la Photographie de Marrakech','museum',''),
      ('mouassine','Musée de la Musique — Musée Mouassine','Marrakech','MA','mouassine','Musée de la Musique','museum','Mouassine and the music museum are one institution; not duplicated.'),
      ('tiskiwin','Musée Dar Tiskiwin','Marrakech','MA','tiskiwin','Dar Tiskiwin Museum','museum','Bert Flint collection; not a second institution under the founder’s name.'),
      ('bank-rabat','Musée de Bank Al-Maghrib','Rabat','MA','bank','MUSEE DE BANK AL-MAGHRIB','museum','Operator currently announces temporary closure for works; no opening/on-view claim.'),
      ('bank-fes','Musée de la Monnaie de Fès-Médina','Fès','MA','bank-fes','Musée de la Monnaie de Fès-Médina','museum','Distinct Fès museum operated by Bank Al-Maghrib.'),
      ('jewish','Musée du Judaïsme Marocain','Casablanca','MA','jewish-valid','Musée du Judaïsme','museum',''),
      ('nejjarine','Musée Nejjarine des Arts et Métiers du Bois','Fès','MA','morocco-tourism','Nejjarine Museum','museum',''),
      ('borj-belkari','Musée Borj Bel Kari','Meknès','MA','morocco-tourism','Borj Bel Kari Museum','museum','Source identity only; visitor status is not asserted.'),
      ('essaouira','Musée Sidi Mohammed Ben Abdellah','Essaouira','MA','essaouira','Sidi Mohammed Ben Abdellah','museum','FNM redevelopment partnership confirms identity; not current-opening evidence.'),
      ('jag','Johannesburg Art Gallery','Johannesburg','ZA','jag','Johannesburg Art Gallery','museum',''),
      ('iziko','South African National Gallery','Cape Town','ZA','iziko-valid','South African National Gallery','museum','Reuse existing Q1419469 institution; do not merge with the wider Iziko operator or Social History Centre.'),
      ('yemisi','Yemisi Shyllon Museum of Art, Pan-Atlantic University','Lagos','NG','yemisi-valid','Yemisi Shyllon Museum of Art','museum',''),
      ('kenya','National Museums of Kenya — National Collection','Nairobi','KE','kenya','National Museums of Kenya','museum','National collection and archives. No individual object assigned to Nairobi Gallery or another branch without evidence.'),
      ('rwanda-art','Rwanda Art Museum','Kigali','RW','rwanda-art','Rwanda Art Museum','museum',''),
      ('namibia','National Art Gallery of Namibia','Windhoek','NA','namibia','National Art Gallery of Namibia','museum',''),
      ('zimbabwe','National Gallery of Zimbabwe','Harare','ZW','zimbabwe','NATIONAL GALLERY OF','museum','National collection; no automatic assignment to Bulawayo, Mutare or Tengenenge.'),
      ('zinsou','Musée de la Fondation Zinsou','Ouidah','BJ','benin','Musée de Ouidah','museum','Distinct from the LAB exhibition venue in Cotonou.'),
      ('bardo','Musée National du Bardo','Tunis','TN','tunisia-museum','Bardo Museum','museum','Tunisian museum, not the same-named museum in Algiers.'),
      ('nmec','National Museum of Egyptian Civilization','Cairo','EG','egypt-nmec','National Museum of Egyptian Civilization','museum',''),
    ]
    for key,name,city,country,src,anchor,kind,note in manual:
        d=page(src) if src else m.load(m.RUN/'macaal-page.json')
        out.append(institution(key,name,city,country,d,anchor,kind,note))
    # The national Nigerian directory contains outlets as well as museums. Select
    # museum headings only, consolidate repeated headings, and hold the Yola alias.
    d=page('nigeria-museums');raw=gzip.decompress((m.ROOT/d['receipt']['body_path']).read_bytes());s=m.BeautifulSoup(raw,'html.parser')
    names=list(dict.fromkeys(x.get_text(' ',strip=True) for x in s.select('h2')))
    for name in names:
        if not name.startswith(('National Museum','National War Museum')):continue
        if 'Fombina' in name:continue
        city=re.sub(r'^National (?:War )?Museum(?: of Colonial History)?[, ]*','',name)
        if city=='Yola':note='Fombina/Yola alternate headings held for identity reconciliation; one Yola museum row only.'
        else:note='Museum individually listed in Nigeria’s National Commission for Museums and Monuments directory. Object catalogue pending.'
        out.append(institution('ng-'+m.norm(city).replace(' ','-'),name,city,'NG',d,name,note=note))
    d=page('tanzania-museum')
    for name,city in [('Museum and House of Culture','Dar es Salaam'),('Village Museum','Dar es Salaam'),('National Natural History Museum','Arusha'),('Arusha Declaration Museum','Arusha'),('Mwl. J. K Nyerere Museum','Butiama'),('Majimaji Memorial Museum','Songea'),('Dr. Rashid M. Kawawa Memorial Museum','Songea')]:
        out.append(institution('tz-'+m.norm(name).replace(' ','-'),name,city,'TZ',d,name))
    d=page('algeria-museums')
    for key,name,anchor in [('algiers-fine-arts','Musée National des Beaux-Arts d’Alger','المتحف الوطني للفنون الجميلة'),('algiers-antiquities','Musée National des Antiquités et des Arts Islamiques','المتحف الوطني للآثار القديمة و الفنون الاسلامية'),('algiers-bardo','Musée National du Bardo — Alger','المتحف الوطني باردو'),('algiers-modern','Musée Public National d’Art Moderne et Contemporain d’Alger','المتحف الوطني للفن الحديث و المعاصر')]:
        out.append(institution(key,name,'Algiers','DZ',d,anchor,note='Official ministry museum register; French name is an editorial translation of the preserved Arabic source label.'))
    # The Egyptian Ministry of Culture identifies these lending collections in its
    # 2024 exhibition catalogue. This does not assign them to the exhibition venue.
    url='https://www.fineart.gov.eg/AllPics/Catalogs/PDF/376/Mahmoud-Said.pdf';receipt,_=m.capture(url)
    text=Path('/tmp/artline-egypt-said.txt').read_text();d=dict(receipt=receipt,text=text)
    out.append(institution('mahmoud-said','Mahmoud Said Museum','Alexandria','EG',d,'Mahmoud Said Museum in Alexandria',note='Museum holding credits from Ministry of Culture catalogue; exhibition venue is not the collection owner.'))
    before=m.load(m.RUN/'initial-directory.json.gz')['institutions']
    for row in out:
        matches=[i for i in before if i['normalized_name']==m.norm(row['name']) or i['slug']==row['slug']]
        if row['key']=='iziko':matches=[i for i in before if i['id']=='f899b96c-0005-584f-ab1a-85af573d1441']
        assert len(matches)<=1,(row['key'],matches)
        row['existing']=matches[0] if matches else None
        if matches:row['id']=matches[0]['id'];row['slug']=matches[0]['slug']
    assert len({r['key'] for r in out})==len(out)
    return out

def work(key,institution,title,creator,date,first,last,precision,kind,medium,dimensions,url,receipt,note,accession=None,raw=None):
    return dict(key=key,id=m.uid('artwork/'+key),slug='africa-work-'+hashlib.sha256(key.encode()).hexdigest()[:20],institution_key=institution,title=title,creator=creator,date_display=date,first=first,last=last,date_precision=precision,work_type=kind,medium=medium,dimensions=dimensions,source_url=url,receipt=receipt,review_note=note,accession=accession,raw=raw,confidence=.97,confidence_basis='Individual institution catalogue/caption identifies title, creator and held object; versions distinguished by inventory or measurements. Editorial assessment, not calibrated probability.')

def works():
    out=[];holds=[]
    labels=['Artiste','Technique','Dimensions',"Année d'exécution",'Type','Support','Référence']
    for row in m.load(m.RUN/'villa-object-queue-expanded.json'):
        p=m.RUN/'villa-objects'/(row['reference']+'.json');d=m.load(p)
        if 'text' not in d:holds.append(dict(key=row['reference'],reason='source_unavailable',source=d));continue
        fields={}
        for label in labels:
            match=re.search(re.escape(label)+r'\s*:\s*\n([^\n]+)',d['text']);assert match,(label,row)
            fields[label]=match[1].strip()
        assert fields['Référence']==row['reference']
        dates=fields["Année d'exécution"];year=int(dates) if dates.isdigit() and int(dates)<=1970 else None
        if year is None:holds.append(dict(key=row['reference'],reason='date_requires_review',source=d));continue
        kind={'Peinture':'painting','Dessin':'drawing','estampe':'print'}.get(fields['Type'])
        if not kind:holds.append(dict(key=row['reference'],reason='type_requires_review',source=d));continue
        # Printed multiples require physical edition/impression evidence.
        if kind=='print':holds.append(dict(key=row['reference'],reason='impression_date_or_edition_unresolved',source=d));continue
        out.append(work('villa/'+row['reference'],'almada',d['headings'][0],fields['Artiste'],dates,year,year,'exact',kind,
            fields['Technique']+'; '+fields['Support'],fields['Dimensions'],row['url'].split('?')[0],d['receipt'],
            'Exact foundation inventory, execution-year field, support and dimensions. No year inferred from inventory. Foundation collection; no current branch/display claim.',row['reference'],d))
    # Collection captions individually read against rendered PDF pages 13–15.
    url='https://www.fnm.ma/uploads/press-archives/2025-Dossier%20de%20presse%20-%20Exposition%20Permanente%20Horizon%28s%29%20en%20mouvement%20%282%29.pdf';rc,_=m.capture(url)
    for n,title,creator,date,f,l,precision,kind,medium,dims in [
       (13,'Sans titre',"Mohammed BEN ALI 'RBATI",'Circa 1920–30',1920,1930,'circa_range','watercolor','Aquarelle et pastel sur papier','71.5 x 58 cm'),
       (14,'Fqih apprenant aux élèves à lire et à écrire','Haj Abdelkrim OUAZZANI','1946',1946,1946,'exact','drawing','Encre sur papier','30 x 21 cm'),
       (15,'Homme assis','Mohamed SARGHINI','1957',1957,1957,'exact','painting','Huile sur carton marouflé sur bois','79,5 x 58 cm')]:
        out.append(work('mmvi/horizons-2025/'+str(n),'fnm-31',title,creator,date,f,l,precision,kind,medium,dims,url+'#page='+str(n),rc,'Rendered bilingual caption explicitly credits Collection MMVI-FNM. Page 13 additionally credits donation El Khalil Belguench. Artwork caption only; adjacent 1981 painting excluded.',raw=dict(pdf_page=n,visual_review='13–15 rendered and individually inspected',credit='Collection MMVI-FNM')))
    d=page('legation-collection')
    for key,title,creator,year,precision,kind,medium,dims,anchor in [
        ('zohra','Zohra','James McBey',1952,'exact','painting','Oil on canvas','21 ½ × 24 inches','JAMES MCBEY, ZOHRA, MAY 1952'),
        ('magistrat','Magistrat au prétoire',"Mohammed Ben Ali R’bati",1935,'circa','watercolor','Watercolor','13 × 8 ½ inches','MAGISTRAT AU PRÉTOIRE, C. 1935'),
        ('storyteller','The Storyteller','James McBey',1912,'exact','print','Drypoint etching','11 ¼ × 6 ¾ inches','THE STORYTELLER, 1912')]:
        assert anchor in d['text']
        out.append(work('legation/'+key,'legation',title,creator,('c. ' if precision=='circa' else '')+str(year),year,year,precision,kind,medium,dims,d['receipt']['url']+'#'+key,d['receipt'],'Museum explicitly identifies its own collection highlight with creator, date, medium and dimensions. Print retained as the museum’s catalogued object, without inferred edition or inventory.',raw=dict(caption_anchor=anchor)))
    d=page('belkahia')
    for year,medium,dims,anchor in [(1952,'Peinture sur papier','81 x 45 cm','Couple peinture sur papier, 81 x 45 cm, 1952'),(1962,'Peinture sur bois','128 x 76 cm','Couple peinture sur bois, 128 x 76 cm, 1962')]:
        assert anchor in d['text'];out.append(work('belkahia/couple-'+str(year),'belkahia','Couple','Farid Belkahia',str(year),year,year,'exact','painting',medium,dims,d['receipt']['url']+'#couple-'+str(year),d['receipt'],'Permanent collection identifies two separate works by date, support and size; do not conflate their common title.',raw=dict(caption_anchor=anchor)))
    # GAC provider records: no generic partner attribution or chronology repair.
    approved_iziko={'eQH3nWGIVRdJzw','dgFzQFpfp8VpYg','8gGb-Z6i8n9yPw','YQGIbbMPt_C3uw','GAG65LWApnAz8w','JAGkTbL5pw_hwg','OgF7oKC_KaR5Lg','pgFfqO5QIEwPqQ'}
    for p in sorted((m.RUN/'gac-objects').glob('*.json')):
        d=m.load(p);f=d.get('fields',{});inst=d['institution'];date=f.get('Date Created');reason=None
        if inst=='jag':reason='Museum supplied dates include demonstrable errors; print impressions and photographic-print dates need separate evidence.'
        elif inst=='iziko-valid' and p.stem not in approved_iziko:reason='Outside selected dated painting scope; includes chronology conflicts, post-1970 works and separate social-history holdings.'
        elif inst=='yemisi-valid' and (not date or not re.fullmatch(r'\d{4}',date) or int(date)>1970):reason='Post-1970 or unreviewed date.'
        elif inst=='yemisi-valid' and f.get('Type')=='Print':reason='Physical impression chronology unresolved.'
        if reason:holds.append(dict(key='gac/'+p.stem,reason=reason,source=d));continue
        if inst=='kenya':first=last=None;precision='unknown';date='Creation date not supplied by source'
        else:
            match=re.fullmatch(r'(c\.)?(\d{4})',date);assert match
            first=last=int(match[2]);precision='circa' if match[1] else 'exact';assert last<=1970
        typ=f['Type'];kind='watercolor' if inst=='kenya' else 'drawing' if typ in ['Drawing','Works on paper'] else 'painting'
        if inst=='iziko-valid':assert 'south-african-national-gallery' in f.get('External Link','')
        assert f.get('Creator') and f.get('Medium')
        out.append(work('gac/'+p.stem,{'iziko-valid':'iziko','yemisi-valid':'yemisi','kenya':'kenya'}[inst],f['Title'],f['Creator'],date,first,last,precision,kind,f['Medium'],f.get('Physical Dimensions'),d['url'],d['receipt'],
          'Museum-authored object record. Preserve full provider fields and rights. Creator biography dates/nationality are not imported. '+('Source gives no creation date; retain a real review record with unknown chronology and no automatic eligibility.' if inst=='kenya' else 'Creation field is explicit and reviewed; collection association is not a current display statement.'),raw=d))
    # Egypt: no dates are supplied in these captions. Do not use artist life dates.
    url='https://www.fineart.gov.eg/AllPics/Catalogs/PDF/376/Mahmoud-Said.pdf';rc,_=m.capture(url)
    egypt=[(14,'The artist’s mother','Oil on canvas','88 x 70 cm'),(14,"The artist’s father",'Oil on canvas','160 x 100 cm'),(14,"The artist’s wife in a hat",'Oil on canvas','45 x 38 cm'),(14,"The artist’s wife",'Oil on canvas','80.8 x 64.8 cm'),(14,'Nadia in the white dress','Oil on canvas','162 x 130 cm'),(15,'Ahmed Rasem','Oil on cardboard','35.8 x 25 cm'),(15,'Madam Youssef Zulfiqar','Oil on wood','103 x 71 cm'),(15,'My sister’s daughter','Oil on canvas','99.7 x 74 cm'),(16,'Ahmed Mazloum','Oil on canvas','75.5 x 53.5 cm'),(16,'My uncle Muharram','Oil on solitex','44.6 x 33.5 cm'),(17,'Portrait of Listas','Oil on wood','79 x 62.9 cm'),(17,'My friend in the mixed courts','Oil on canvas','81 x 65 cm')]
    for n,title,medium,dims in egypt:
        out.append(work('said-2024/'+m.norm(title).replace(' ','-'),'mahmoud-said',title,'Mahmoud Said','Creation date not supplied by source',None,None,'unknown','painting',medium,dims,url+'#page='+str(n),rc,'Rendered Ministry of Culture catalogue caption explicitly credits Mahmoud Said Museum in Alexandria. Title, support and size distinguish portraits. Undated review record; no date inferred from artist biography or the 2024 exhibition.',raw=dict(pdf_page=n,credit='Mahmoud Said Museum in Alexandria',visual_review='Pages 14–17')))
    return out,holds

def main():
    inst=directory();records,held=works()
    m.save(m.RUN/'proposed-directory.json',inst);m.save(m.RUN/'proposed-artworks.json',records);m.save(m.RUN/'source-holds.json.gz',held)
    print('Institutions',len(inst),dict(collections.Counter(x['country'] for x in inst)))
    print('Artwork candidates',len(records),dict(collections.Counter(x['institution_key'] for x in records)),'unknown dates',sum(x['first'] is None for x in records),'held',len(held))
if __name__=='__main__':main()
