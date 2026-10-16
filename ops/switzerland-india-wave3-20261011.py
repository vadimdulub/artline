#!/usr/bin/env python3
"""Additional Swiss collections: selected physical objects, never venue placeholders."""
import collections
import importlib.util
import json
from pathlib import Path

s=importlib.util.spec_from_file_location('f',Path(__file__).with_name('switzerland-india-facts-20261011.py'))
f=importlib.util.module_from_spec(s);s.loader.exec_module(f)
m,RUN=f.m,f.RUN
EXTRA={
 'thun':('Kunstmuseum Thun','kunstmuseum-thun','https://kunstmuseumthun.ch','640','Thun'),
 'pauli':('Fondation Toms Pauli','fondation-toms-pauli','https://www.toms-pauli.ch','1021','Lausanne'),
 'interlaken':('Kunsthaus Interlaken','kunsthaus-interlaken','https://kunsthausinterlaken.ch','1264','Interlaken'),
 'deusser':('August Deusser Museum','august-deusser-museum','https://www.deusser.ch','789','Bad Zurzach'),
 'abegg':('Abegg-Stiftung','abegg-stiftung','https://www.abegg-stiftung.ch','499','Riggisberg'),
 'sanmaterno':('Museo Castello San Materno','museo-castello-san-materno','https://www.museoascona.ch/it/museo-castello-san-materno','1334','Ascona'),
 'rehmann':('Rehmann-Museum','rehmann-museum','https://www.rehmann-museum.ch','902','Laufenburg'),
}
f.REGISTRY.update(EXTRA)

def discovery(key):return m.load(RUN/'CH/native-discovery'/(key+'.json'))
def collection(url):return m.load(RUN/'CH/collection-discovery'/(m.sha(url.encode())+'.json.gz'))
def add(rows,museum,source,title,creator,date,medium=None,dimensions=None,accession=None,kind='unknown',**extra):
 text=source.get('text') or source['source_text']
 key=accession or m.sha((str(creator)+'/'+title).encode())[:20]
 f.add(rows,museum,key,title,creator,date,source['evidence'],source['url'],text,medium,dimensions,accession,kind,**extra)

def run():
 rows=[]
 add(rows,'jenisch',discovery('jenisch'),'Les Nuées (Vallée de Lauterbrunnen)','Charles Giron','1901','huile sur toile',kind='painting',credit='Musée Jenisch Vevey, don de la Société des Beaux-Arts de Vevey')
 add(rows,'thun',discovery('thun-insekten'),'Insekten','Paul Klee','1919','Lithografie','Blattmass: 31 × 24.8 cm','1584','print',version_note='Physical lithographic impression, inventory 1584; not the 1917 drawing or impressions held elsewhere.')
 add(rows,'pauli',discovery('pauli-andromeda'),'Andromeda II (Andromède II)','Magdalena Abakanowicz','1964','haute lisse, technique personnelle; laine, coton, crin','195 × 285 cm','CAP166','textile')
 add(rows,'pauli',discovery('pauli-ombres'),'Ombres','Jean Lurçat (modèle); atelier Raymond Picaud (exécution)','1965','basse lisse; laine','152 × 227 cm','APP060','textile',creator_link_hold=True)
 add(rows,'pauli',discovery('pauli-scipion'),'La Continence de Scipion','Gianfrancesco Penni, Giulio Romano (modèle); atelier de Gerard van der Strecken (exécution)','1660',"tapisserie de lisse; laine, soie, filé d’or, filé d'argent",'471 × 557 cm','TOMS025','textile',creator_link_hold=True)
 add(rows,'interlaken',collection('https://kunsthausinterlaken.ch/sammlung/'),'Eigerwand et glacier de l‘Eiger','Francois Diday','um 1850','Öl auf Papier / Leinwand','36 × 53 cm',kind='painting')
 add(rows,'deusser',discovery('deusser-327'),'Kanoniere in Stellung','August Deusser','1893','Öl auf Papier auf Hartfaser','47.0 × 35.5 cm','461','painting',catalogue_raisonne='WVD-Nr. 1')
 src=collection('https://www.abegg-stiftung.ch/ausstellung/sammlung')
 for title,creator,date,medium,dims,acc,kind in [
  ('Zwei Marien einer Kreuzigungsgruppe',None,'1240–1250','Kupfer, getrieben, vergoldet','H. 24.1 cm','8.59.63','metalwork'),
  ('Thronende Madonna mit Kind','auch Hans Multscher zugeschrieben','um 1425/30','Nussbaum- und Nadelholz, gefasst','H. 67 cm','11.44.75','sculpture'),
  ('Triptychon mit der Kreuzigung Christi','Rogier van der Weyden, Werkstatt','1440–1445','Öl auf Holz','H. 103.5 cm','14.2.63','painting')]:
  add(rows,'abegg',src,title,creator,date,medium,dims,acc,kind,creator_link_hold=True)
 src=collection('https://www.museoascona.ch/it/museo-castello-san-materno/collezione')
 for title,creator,date,medium,dims,acc in [
  ('Fiori in due vasi','Lovis Corinth','1919','olio su legno','72 × 58 cm','FKBA 12'),
  ('Autunno a Worpswede','Hans am Ende','circa 1895','olio su tela, su faesite','35.5 × 47.8 cm','FKBA 01'),
  ('Natura morta','Erich Heckel','1913','olio su tela','65 × 45 cm','FKBA 26')]:
  add(rows,'sanmaterno',src,title,creator,date,medium,dims,acc,'painting',credit='Collezione della Fondazione per la cultura Kurt e Barbara Alten; housed at Museo Castello San Materno. Collection custody, not a transfer of ownership.')
 src=collection('https://www.rehmann-museum.ch/museum/sammlung')
 for title,date,medium,dims in [
  ('Raumereignis VI','1959','Eisen, Pièce Unique','60 × 65 × 56 cm'),
  ('Strahlenbündel I','1960','Eisen, Pièce Unique','60 × 85 × 370 cm'),
  ('Eisenplastik II','1963','Eisen, Pièce Unique','70 × 100 × 143 cm'),
  ('Aluminiumplastik I','1964','Aluminium, Pièce Unique','105 × 43 × 228 cm'),
  ('Kleine Tropfenschnittplastik IV','1969','Aluminiumbronze, Pièce Unique','28 × 6 × 13 cm')]:
  add(rows,'rehmann',src,title,'Erwin Rehmann',date,medium,dims,kind='sculpture')
 # Three single, dated paintings; the open data's later inscription makers
 # are retained as evidence, never promoted to primary artwork creators.
 source=m.load(RUN/'CH/rietberg-open-objects.json.gz')
 for obj in source['data']:
  acc=obj['Inventarnummer'].rsplit('.',1)[-1].replace('_',' ')
  if acc not in ['RCH 1020','RCH 1021','RCH 1023']:continue
  date={'RCH 1020':'1556','RCH 1021':'1574','RCH 1023':'1649'}[acc]
  title=next(t['Titel'].strip() for t in obj['Titel_Bezeichnungen'] if t['Titel_Typ']=='Titel/Untertitel EN')
  makers=[v for v in obj['Urheber*innen'] if v['UrheberIn_von'] in ['', 'Malerei']]
  assert len(makers)==1 and makers[0]['Zuschreibung'] in ['', 'eindeutig']
  f.add(rows,'rietberg',obj['ID'],title,makers[0]['UrheberIn_Label'].strip(),date,source['evidence'],source['evidence']['url'],json.dumps(obj,ensure_ascii=False),json.dumps(obj['Material_Technik'],ensure_ascii=False),json.dumps(obj['Masse'],ensure_ascii=False),acc,'painting',native_fields=obj,date_basis='Explicit dated year in Date_Label, preserved alongside broader catalogue search bounds.',image_candidate=acc)
 assert len({(r['provider'],r['source_id']) for r in rows})==len(rows)
 m.save(RUN/'CH-wave3/source-records.json.gz',rows)
 m.save(RUN/'institution-registry-wave3.json',{name:dict(slug=slug,website=website,directory_id=did,city=city,country_code='CH') for name,slug,website,did,city in EXTRA.values()})
 print(json.dumps(dict(records=len(rows),museums=dict(collections.Counter(r['museum'] for r in rows)))),flush=True)

if __name__=='__main__':run()
