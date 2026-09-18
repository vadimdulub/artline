import importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('x',Path(__file__).resolve().parent/'import-cypriot-expansion.py');x=importlib.util.module_from_spec(s);s.loader.exec_module(x)
from bs4 import BeautifulSoup
people=[];works=[];holds=[]
def receipt(key):return x.read('primary-captures/'+key+'.receipt.json')
def person(key,name,birth,death,r,qid=None,aliases=(),relationship='cultural_affiliation',first=None,last=None):
 e=x.w.entities([qid])[0][qid] if qid else None
 if e:assert (x.w.year(e,'P569'),x.w.year(e,'P570'))==(birth,death),(name,'date disagreement')
 a=dict(key=key,name=name,qid=qid,birth=birth,death=death,first=birth or first,last=death or last,basis='life' if birth else 'activity',aliases=list(set([name,*aliases,*(x.w.labels(e) if e else [])])),country_relationship=relationship,country_note='Cypriot artist identity supported by the cited museum profile; cultural affiliation is not exclusive citizenship.' if relationship=='cultural_affiliation' else 'Painter documented as working in Cyprus. No Cypriot birth or citizenship is inferred.',source_url=r['url'],receipt=r,biography='Painter documented in the cited museum and heritage research. Dates and attribution remain in review.',woman=False)
 people.append(a);return a
qids={'christoforos-savva':'Q20498144','telemachos-kanthos':'Q2401766','michael-chr-kashalos':'Q124812087'}
for key in ['christoforos-savva','telemachos-kanthos','michael-michaeledes','victor-ioannides','michael-chr-kashalos','lefteris-economou','costas-averkiou','takis-fragkoudes']:
 r=receipt('artist-'+key);soup=BeautifulSoup((x.ROOT/r['path']).read_text(),'html.parser');txt=soup.get_text(' ',strip=True)
 birth=int(x.re.search(r'Birth Year: (\d{4})',txt)[1]);death=int(x.re.search(r'Death Year: (\d{4})',txt)[1]);name=soup.find('h1').get_text(' ',strip=True) if soup.find('h1') else {'michael-chr-kashalos':'Michael Chr. Kashalos'}.get(key,key.title().replace('-',' '))
 aliases={'michael-michaeledes':['Michael Michaelides','Μιχάλης Μιχαηλίδης'],'victor-ioannides':['Viktor Ioannidis','Βίκτωρ Ιωαννίδης'],'takis-fragkoudes':['Takis Frangoudes','Takis Frangoudis'],'michael-chr-kashalos':['Michael Kashialos','Michael Kashalos']}.get(key,[])
 person(key,name,birth,death,r,qids.get(key),aliases)
person('stass-paraskos','Stass Paraskos',1933,2014,receipt('paraskos-exhibition'),'Q7602949')
person('ismet-guney','İsmet Güney',1923,2009,receipt('guney-museum'),'Q3555605',['Ismet Guney','İsmet Vehit Güney'])
u=receipt('unesco-painted-churches');v=receipt('venice-routes')
person('minas-marathasa','Minas of Marathasa',None,None,u,aliases=['Minas of Myrianthousa','Minas of Myrianthoussa'],first=1474,last=1474)
person('philippos-goul','Philippos Goul',None,None,u,aliases=['Philip Goul','Philippos Goulas'],relationship='active',first=1494,last=1599)
person('symeon-axentis','Symeon Axentis',None,None,receipt('axentis-authority'),aliases=['Symeon Afxentis','Simeon Auxentis','Symeon Aksentis','Αξέντης Συμεών'],relationship='active',first=1513,last=1514)
people[-2]['biography']='Syrian Orthodox painter documented as working in Cyprus. Sources disagree between 1494 and the early sixteenth century for the Agiasmati decoration; the timeline retains broad source bounds, not a lifespan.'
people[-3]['biography']='Cypriot icon painter from Marathasa, documented by the signed wall paintings at Pedoulas in 1474. Birth and death years are unknown.'
people[-1]['biography']='Painter active in Cyprus, documented at Galata in 1513–1514. Birth and death years are unknown.'
pages={}
for f in (x.RUN/'commons-metadata').glob('*.json'):
 b=json.loads(f.read_text())
 for p in b['data']['query']['pages'].values():pages[p['title']]=(p,b['receipt'])
def work(key,artist,title,d,r,kind='painting',medium=None,accession=None,holding=None,connection=None,commons=None,note=None,url=None,scheme='cypriot-expansion-object',record_id=None):
 item=dict(key=key,artist=artist,title=title,date=d,work_type=kind,medium=medium,accession=accession,source_url=url or r['url'],receipt=r,source_record_id=record_id or key,source_scheme=scheme,museum_connection=connection,holding=holding,collection_label=None,image=None,selection_note=note)
 if commons:
  p,cr=pages[commons];item.update(commons_file=commons,commons_page=p,commons_receipt=cr,image_candidate_url=p['imageinfo'][0]['url'])
 else:item['image_hold']='No verified licence for the underlying modern artwork; metadata and source links retained, no image downloaded.'
 works.append(item);return item
selection={
'minas-marathasa':('File:Église Archelangos Michail de Pedoulas ',[("Annonciation","Annunciation"),("Arrestation du Christ","Arrest of Christ"),("Baptème du Christ","Baptism of Christ"),("Crucifixion","Crucifixion"),("Dormition de la Vierge","Dormition of the Virgin"),("Les Donateurs","Donor family of Vasileios Chamados"),("Nativité","Nativity"),("Saint Michel","Archangel Michael"),("Constantin et sa mère Hélène","Constantine and Helena"),("Présentation de Marie au temple","Presentation of Mary in the Temple")]),
'philippos-goul':("File:Église Sainte-Croix d'Agiasmáti ",[("Baptême du Christ","Baptism of Christ"),("Christ devant Ponce Pilate","Christ before Pontius Pilate"),("Crucifixion","Crucifixion"),("Dormition de la Vierge","Dormition of the Virgin"),("Déposition de la croix","Deposition from the Cross"),("Entrée du Christ à Jérusalem","Entry into Jerusalem"),("La Cène","Last Supper"),("Le Christ devant Caïphe","Christ before Caiaphas")])}
for artist,(prefix,scenes) in selection.items():
 for n,(french,title) in enumerate(scenes):
  file=prefix+french+'.jpg';p,cr=pages[file];site='Archangel Michael, Pedoulas' if artist=='minas-marathasa' else 'Stavros tou Agiasmati'
  d=x.date('1474') if artist=='minas-marathasa' else dict(first=1494,last=1599,precision='range',display='1494 or early 16th century (sources disagree)',eligible=True)
  item=work(artist+'-'+str(n+1),artist,title+' — '+site,d,cr,'fresco',commons=file,url=p['imageinfo'][0]['descriptionurl'],scheme='commons-artwork',record_id=file,note='Editorial highlight selection of a named scene in a documented painted church. This is not a museum masterpiece designation. The photograph preserves the source frame and may show surrounding scenes.')
  item['context_source']=u
  if artist=='philippos-goul':item['date_note']='Older tourism and scholarly sources give 1494; Cyprus UNESCO heritage guide pp.50–51 says early 16th century. 1494–1599 conservatively encloses both supplied dates without inventing an exact year; 1599 is a century boundary, not a claimed creation year. Source conflict remains in review.';item['date_sources']=['https://www.mdpi.com/2076-0752/12/5/186','https://www.visitcyprus.com/wp-content/uploads/files/cultural_routes/Cyprus_island_of_saints_EN.pdf',u['url']]
work('axentis-sozomenos','symeon-axentis','Exterior wall paintings, Agios Sozomenos, Galata',x.date('1513'),v,'fresco',commons='File:Galata Kirche Agios Sozomenos Äußere Fresken 2.jpg',note='Editorial highlight selection of the exterior mural decoration. Cyprus Tourism identifies the councils and Triumph of Orthodoxy on the north wall with Symeon Afxentis; photo is a partial view, not the complete cycle.')
# Modern works with museum catalogue or exhibition evidence. No date inferred from a photograph.
for key,artist,title,year,capture_key,med,accession in [('savva-bathers','christoforos-savva','Bathers in Kyrenia','1957','savva-bathers','Oil on canvas','549'),('michaeledes-left-behind','michael-michaeledes','Those Left Behind','1950','michaeledes-work','Oil on plywood','AGLG 504')]:
 item=work(key,artist,title,x.date(year),receipt(capture_key),medium=med,accession=accession,holding='leventis-gallery',connection=dict(institution='leventis-gallery',basis='Explicit museum collection catalogue'));item['collection_label']='A. G. Leventis Gallery, Cyprus Collection'
 soup=BeautifulSoup((x.ROOT/receipt(capture_key)['path']).read_text(),'html.parser');images=[i.get('src') for i in soup.select('img[src]') if '/uploads/' in i['src']];item['image_candidate_urls']=images
file="File:Leventis Gallery, Nicosia, Cyprus. Telemachos Kanthos - At the Church of St George.jpg";p,r=pages[file]
item=work('kanthos-st-george','telemachos-kanthos','At the Church of St George',x.date(''),r,medium='Oil on canvas',holding='leventis-gallery',url=p['imageinfo'][0]['descriptionurl'],record_id=file,scheme='commons-artwork',connection=dict(institution='leventis-gallery',basis='Commons photograph caption names collection; claim remains in review'));item['collection_label']='A. G. Leventis Gallery';item['image_candidate_url']=p['imageinfo'][0]['url'];item['image_hold']='Creation date unresolved and modern underlying-painting rights not cleared. Photograph licence alone is insufficient.'
item=work('ioannides-leukios','victor-ioannides','Portrait of Leukios Zenon',x.date('1939'),receipt('ioannides-portrait'),'watercolor',medium='Watercolour',accession='CYLHA.10.059.0174',connection=dict(institution_label='Pattichion Municipal Museum, Historical Archive and Research Centre',basis='Explicit contributing museum in university archive object record; source collection is Phedonas Potamitis, not an accepted holding.'));item['image_hold']='Apsida explicitly requires written creator consent to publish or reproduce the image; no image downloaded.'
for key,title,year,collection in [('lovers-ii','Lovers and Romances II','1966','Tate'),('lovers-iii','Lovers and Romances III','1966','Tate'),('clea-justine','Clea and Justine','1965','University of Leeds'),('yellow-still-life','Yellow Still Life','1966','University of Leeds'),('still-life-fish','Still Life with Fish','1966','Artemis ArtForms – Leeds School Board Collection')]:
 item=work('paraskos-'+key,'stass-paraskos',title,x.date(year),receipt('paraskos-paintings'),connection=dict(institution_label=collection,basis='Artist estate catalogue collection caption; review evidence, not an accepted holding.'));item['context_source']=receipt('paraskos-exhibition');item['collection_label']=collection
# Three dated paintings reproduced in a family-assisted interview; titles explicitly unknown.
for key,title,med in [('nude','Nude (descriptive label; title unknown)','Oil on canvas'),('water-jug','Woman with water jug (descriptive label; title unknown)','Oil on canvas'),('still-life','Still life (descriptive label; title unknown)','Oil on canvas')]:
 item=work('guney-'+key,'ismet-guney',title,x.date('1959'),receipt('guney-works'),medium=med,note='Editorial highlight selected from three explicitly 1959-dated works reproduced in the family-assisted artist research. Source states title unknown; descriptive label retained. No museum holding asserted.');item['context_source']=receipt('guney-museum')
holds=[dict(item="Kanthos, Women's Bazaar II",reason='1971 exceeds 1970 artwork cutoff'),dict(item='Agiasmati Ascension and sanctuary images',reason='Recent heritage guide distinguishes sanctuary attribution to Minas. Omitted rather than extrapolating Goul attribution.'),dict(item='Ismet Guney portrait',reason='Commons says own work in 2014, after subject died in 2009; provenance needs reconciliation.'),dict(item='Stass Paraskos portrait',reason='Missing machine-readable creator/description; no verified image authority.'),dict(item='Michael Michaeledes Wikidata Q94295757',reason='Search description says British artist 1927; museum has 1923–2015. Held identity pending reconciliation.'),dict(item='Modern museum reproductions',reason='Photographer CC licence does not clear underlying paintings.'),dict(item='New museum-profiled artists without object records',reason='Kashalos, Economou, Averkiou, Fragkoudes have verified artist profiles; no objects or dates invented when catalogue says no data.')]
x.save(x.RUN/'selected.json',dict(at=x.core.now(),artists=people,institutions=[dict(key='leventis-gallery',id='711003ac-c19b-5029-a909-c252104a7e0b',slug='leventis-gallery',name='A. G. Leventis Gallery',existing=True)],works=works,holds=holds,policy='Selected pre-1971 or unresolved review metadata; only eligible rights-cleared images; no publication.'))
print('SELECTED',len(people),len(works),sum(bool(v.get('commons_file')) for v in works));print([(p['name'],p['birth'],p['death']) for p in people])
