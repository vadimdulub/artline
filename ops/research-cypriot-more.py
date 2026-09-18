"""Selected additions, backed by retained primary records. No exhaustive downloads."""
import importlib.util,json,re
from pathlib import Path
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('x',Path(__file__).with_name('import-cypriot-more.py'));x=importlib.util.module_from_spec(s);s.loader.exec_module(x)
prior=json.loads((x.ROOT/'docs/research/cypriot-expansion-20260914/application-plan.json').read_text())
people=[];works=[]
def receipt(key):return x.read('primary-captures/'+key+'.receipt.json')
def person(key,name,birth,death,r,aliases=(),first=None,last=None,active=False,woman=False,bio=None):
 a=dict(key=key,name=name,qid=None,birth=birth,death=death,first=birth or first,last=death or last,basis='life' if birth else 'activity',aliases=list(aliases),country_relationship='active' if active else 'cultural_affiliation',country_note='Documented work in Cyprus; no birth or citizenship inferred.' if active else 'Cypriot painter identity documented by the cited foundation, museum or cultural research; not exclusive citizenship.',source_url=r['url'],receipt=r,biography=bio or 'Painter documented in the cited Cypriot cultural research. Source dates retained for review.',woman=woman)
 if woman:a['gender_evidence']=dict(explicit_women_statement=True,source_url=r['url'],context='Foundation exhibition identifies the named participants as women artists and supplies individual painter biographies.',source_checksum=r['sha256'])
 people.append(a);return a
for key in ['minas-marathasa','philippos-goul']:
 a=next(a.copy() for a in prior['artists'] if a['key']==key);a['existing']=True;people.append(a)
f=receipt('women-foundation');m=receipt('cyprus-modernism');v=json.loads((x.ROOT/'docs/research/cypriot-expansion-20260914/primary-captures/venice-routes.receipt.json').read_text())
person('eleni-charikleidou','Eleni Charikleidou',1926,1978,f,['Eleni Charikleides','Ελένη Χαρικλείδου'],woman=True)
person('vera-gavrielides-hadjida','Vera Gavrielides-Hadjida',1936,2012,f,['Vera Gavrielidou Hadjida','Βέρα Γαβριηλίδου Χατζηδά'],woman=True)
person('katy-stephanides','Katy Stephanides',1925,2012,f,['Katy Phasouliotou-Stephanidou','Katy Fasouliotou-Stephanidou','Kaiti Stephanidou'],woman=True)
person('tassos-stephanides','Tassos Stephanides',1917,1996,m,['Tasos Stephanides'],bio='Cypriot painter discussed in Klitsa Antoniou’s doctoral research at Cyprus University of Technology; the study supplies the lifespan 1917–1996.')
person('joseph-chourri','Joseph Chourri',None,None,receipt('apsida-joseph'),['Iosif Hourris','Ιωσήφ Χούρρη'],first=1544,last=1544,active=True,bio='Icon painter documented in 1544 at the Monastery of Saint Neophytos in Cyprus. Birth and death years are unknown.')
person('giovanni-kyprios','Giovanni Kyprios',None,None,v,['Ioannis o Kyprios','Giovanni Ciprioto','Ioannis Kyprios','Zuane Ciprioto'],first=1589,last=1593,bio='Cypriot painter documented by Cyprus Tourism as the creator of the dome frescoes (1589–1590) and the bema Ascension (1593) at San Giorgio dei Greci in Venice. Birth and death years are unknown.')
# Factual transcription of the primary museum record retrieved through web.open.
cv=dict(url='https://cvar.severis.org/en/collections/item/dervis-mansion/5237/',retrieved_at=x.core.now(),capture_method='web.open primary catalogue; direct HTTP client returned 403',facts=dict(creator='Çağdaş, Cevdet Hüseyin (1926-2019)',identity='Turkish Cypriot painter',title='Derviş Mansion',date='ca. 1960',medium='Pastel',classification='Drawing',identifier='PNT-00092',dimensions='30 x 40 cm',rights='Foundation holds or manages copyright in object and digital reproduction; reuse requires permission.'))
cvpath=x.RUN/'primary-captures/cagdas-museum.facts.json'
if cvpath.exists():cv=json.loads(cvpath.read_text())
else:x.save(cvpath,cv)
cvr=dict(url=cv['url'],retrieved_at=cv['retrieved_at'],sha256=x.core.sha(cvpath.read_bytes()),path=str(cvpath.relative_to(x.ROOT)),capture_method=cv['capture_method'])
person('cevdet-cagdas','Cevdet Hüseyin Çağdaş',1926,2019,cvr,['Cevdet Cagdas','Cevdet Hüseyin Çagdas'],bio='Turkish Cypriot painter, educationalist and museologist documented by the Centre of Visual Arts and Research collection catalogue.')
pages={}
for file in (x.RUN/'commons-metadata').glob('scenes-*.json'):
 b=json.loads(file.read_text())
 for page in b['data']['query']['pages'].values():pages[page['title']]=(page,b['receipt'])
def work(key,artist,title,d,r,kind='painting',medium=None,accession=None,commons=None,connection=None):
 item=dict(key=key,artist=artist,title=title,date=d,work_type=kind,medium=medium,accession=accession,source_url=r['url'],receipt=r,source_record_id=key,source_scheme='cypriot-more-object',museum_connection=connection,holding=None,collection_label=None,image=None,selection_note='Editorial highlight selected from documented cultural or scholarly research; not an institutional masterpiece designation.')
 if commons:
  p,cr=pages[commons];item.update(commons_file=commons,commons_page=p,commons_receipt=cr,source_url=p['imageinfo'][0]['descriptionurl'],source_scheme='commons-artwork',source_record_id=commons)
 else:item['image_hold']='No verified reusable image licence; preserve metadata and provenance without downloading reproduction.'
 works.append(item);return item
scenes={'minas-marathasa':('File:Église Archelangos Michail de Pedoulas ',[('Entrée du Christ à Jérusalem','Entry into Jerusalem'),('Mise au tombeau','Entombment'),('Résurrection et descente aux enfers','Resurrection and Descent into Hell'),('St Kyriaki','Saint Kyriaki'),('Vierge Marie','Virgin Mary')]),'philippos-goul':("File:Église Sainte-Croix d'Agiasmáti ",[('Naissance de Marie','Birth of Mary'),('Nativité','Nativity'),('Reniement de Pierre','Denial of Peter'),('Résurrection de Lazare','Raising of Lazarus'),('Résurrection','Resurrection'),('Présentation au temple','Presentation in the Temple')])}
for artist,(prefix,entries) in scenes.items():
 template=next(t for t in prior['works'] if t['artist']==artist)
 for n,(french,title) in enumerate(entries):
  filename=prefix+french+'.jpg';p,cr=pages[filename];site='Archangel Michael, Pedoulas' if artist=='minas-marathasa' else 'Stavros tou Agiasmati'
  item=work(artist+'-more-'+str(n+1),artist,title+' — '+site,template['date'],cr,'fresco',commons=filename)
  for k in ['context_source','date_note','date_sources']:
   if k in template:item[k]=template[k]
  item['selection_note']+=' Distinct scene; source frame may show adjacent decoration. French source label: '+french+'.'
for key,artist,title,year,medium,figure in [('katy-cubist','katy-stephanides','Cubist Landscape',1963,'Oil on canvas',27),('katy-cypriot-motif','katy-stephanides','Cypriot Motif (Op Art)',1968,'Acrylic on canvas',28),('katy-untitled-op','katy-stephanides','Untitled (Op Art)',1969,'Acrylic on canvas',29),('tassos-echoes','tassos-stephanides','Echoes',1967,'Oil on canvas',25),('tassos-memories','tassos-stephanides','Memories',1968,'Oil on canvas',26)]:
 item=work(key,artist,title,x.date(str(year)),m,medium=medium);item['source_locator']='Klitsa Antoniou doctoral dissertation, figure '+str(figure);item['selection_note']='Editorial highlight: named work analysed and illustrated in university doctoral research on Cypriot modernism. No collection holding is inferred.'
for key in ['apsida-joseph',*['joseph-'+str(n) for n in [15219,15218,15214,15213,15212,15211]]]:
 r=receipt(key);soup=BeautifulSoup((x.ROOT/r['path']).read_text(),'html.parser');values={}
 for el in soup.select('.element'):
  h=el.find(['h2','h3']);contents=el.select('.element-text')
  if h and contents:values[h.get_text(' ',strip=True)]=[c.get_text(' ',strip=True) for c in contents]
 assert 'Joseph Chourri' in ' '.join(values['Description']) and '1544' in ' '.join(values['Date']),values
 item=work('chourri-'+r['url'].rsplit('/',1)[-1],'joseph-chourri',values['Title'][0],x.date('1544'),r,accession=values['Identifier'][0],connection=dict(institution_label='Holy Monastery of Saint Neophytos',basis='Monastery-contributed object record in Cyprus University of Technology Apsida archive.'))
 item.update(source_scheme='apsida-object',source_record_id=r['url'].rsplit('/',1)[-1],raw_metadata=values,image_hold='Apsida object rights explicitly require written permission to publish or reproduce; image not downloaded.')
for key,title,year in [('dome','Dome frescoes, San Giorgio dei Greci','1589–1590'),('ascension','Ascension in the bema, San Giorgio dei Greci','1593')]:
 work('kyprios-'+key,'giovanni-kyprios',title,x.date(year),v,'fresco')['image_hold']='Two licensed photographs inspected but rejected as unrelated views; no verified image matched to this work.'
work('cagdas-dervis','cevdet-cagdas','Derviş Mansion',x.date('c. 1960'),cvr,'drawing','Pastel','PNT-00092',connection=dict(institution_label='Centre of Visual Arts and Research / Costas and Rita Severis Foundation',basis='Explicit museum collection record; holding not accepted automatically.'))
holds=[dict(item='Paul Hierographos / Walters iconostasis panels',reason='Museum offers tentative stylistic attribution. Held for attribution reconciliation and accessible verified image asset.'),dict(item='Venice photographs 30468440444 and 30482552213',reason='Visual QA shows Annunciation wall and church interior, not the documented dome. Rejected and originals preserved in backup.'),dict(item='Pavlina Pavlides',reason='Foundation documents sculpture; current painter-focused selection does not assume painter identity.'),dict(item='Eleni and Vera artwork dates',reason='Exhibition date range 1960–1980 crosses cutoff; no individual object dates or titles invented. Artist profiles retained.'),dict(item='Onufri Qiprioti',reason='Additional named-object and authority reconciliation needed; do not conflate with Onufri Argitis.')]
x.save(x.RUN/'selected.json',dict(at=x.core.now(),artists=people,works=works,institutions=[],holds=holds,policy='Selected research records, all review. Only verified pre-1971 licensed reproductions.'))
print('Selected',sum(not a.get('existing') for a in people),'new artists,',len(works),'works,',len(pages),'images')
