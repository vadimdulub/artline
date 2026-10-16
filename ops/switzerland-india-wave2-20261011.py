#!/usr/bin/env python3
"""A second breadth selection: distinct Swiss regional collections and holdings."""
import importlib.util
import re
import json
import collections
from pathlib import Path

s=importlib.util.spec_from_file_location('facts',Path(__file__).with_name('switzerland-india-facts-20261011.py'))
f=importlib.util.module_from_spec(s);s.loader.exec_module(f)
m,RUN=f.m,f.RUN
EXTRA={
 'cedri':('Museo Villa dei Cedri','museo-villa-dei-cedri','https://www.museovilladeicedri.ch','78','Bellinzona'),
 'glarus':('Kunsthaus Glarus','kunsthaus-glarus','https://kunsthausglarus.ch','246','Glarus'),
 'hotel-dieu':("Musée de l’Hôtel-Dieu Porrentruy",'musee-hotel-dieu-porrentruy','https://www.mhdp.ch','474','Porrentruy'),
 'elysee':('Photo Elysée','photo-elysee','https://elysee.ch','330','Lausanne'),
 'artbrut':("Collection de l’Art Brut",'collection-art-brut-lausanne','https://artbrut.ch','326','Lausanne'),
 'tinguely':('Museum Tinguely','museum-tinguely','https://www.tinguely.ch','820','Basel'),
}
f.REGISTRY.update(EXTRA)


def collection(url):
 return m.load(RUN/'CH/collection-discovery'/(m.sha(url.encode())+'.json.gz'))


def named(rows,museum,source,title,creator,date,medium=None,dimensions=None,kind='unknown',accession=None):
 snippet=next(x for x in source['captions'] if f.clean(title) in f.clean(x))
 key=accession or m.sha((creator+'/'+title).encode())[:20]
 f.add(rows,museum,key,title,creator,date,source['evidence'],source['url'],snippet,medium,dimensions,accession,kind)


def run():
 rows=[]
 # Native structured object pages, reached through the museum's own collection portal.
 for provider in ['masi','fribourg']:
  for path in sorted((RUN/'CH/native-discovery').glob(provider+'-index-*.json')):
   source=m.load(path);x=source['data']['data']['item']
   credit=x.get('ObjCreditlineTxt','')
   if re.search('Deposito',credit,re.I):continue # Owner/custodian mapping reserved for a separate reviewed pass.
   date=f.clean(x.get('ObjDateTxt') or 'Date unknown')
   date=re.sub(r'\s*([-–])\s*',r'\1',date)
   if f.bounds(date)[2]=='after_cutoff':continue
   people=x.get('ObjPersonRef',{}).get('Items',[])
   label='; '.join(re.sub(r'\s*\((?:\d{4}[-–]\d{4}|prima metà XVI secolo)\)$','',p.get('LinkLabelTxt','')).strip() for p in people) or None
   typ=x.get('ObjCategoryTxt');typ=typ.get('LabelTxt_en') if isinstance(typ,dict) else typ
   kind={'Painting':'painting','Tableau':'painting','Retable':'painting','Image pieuse':'unknown'}.get(typ,'unknown')
   f.add(rows,provider,x['Id'],x['ObjTitleTxt'],label,date,source['evidence'],source['url'],source['text'],
         x.get('ObjMatTechTxt') or x.get('ObjMaterialTxt'),x.get('ObjDimensionTxt') or x.get('ObjDimensionsTxt'),
         x.get('ObjObjectNumberTxt'),kind,credit=credit,native_fields=x,
         creator_link_hold=bool(label and re.search(r'Atelier inconnu',label,re.I)))

 p,rc,url=f.page('chaux-junod')
 for node in p.select('.caption')[:5]:
  text=f.clean(node.get_text(' ',strip=True))
  match=re.fullmatch(r'(.+?), «(.+)», ([\d–−\-]+) (Huile .+), ([\d., ×x]+ cm)',text)
  assert match,text
  creator,title,date,medium,dimensions=match.groups()
  f.add(rows,'chaux',m.sha((creator+'/'+title).encode())[:20],title,creator,date,rc,url,text,
        medium,dimensions,work_type='painting')

 source=collection('https://www.museovilladeicedri.ch/Collezione-9a3e8a00')
 for title,creator,date,dimensions in [
  ('Inverno a Miazzina','Vittore Grubicy De Dragon','1898','40.5 × 67.5 cm'),
  ('Neve imminente','Vittore Grubicy De Dragon','1897-1915','35.9 × 65.8 cm'),
  ('Ghiacciaio','Emilio Longoni','1910-1912','87 × 156 cm'),
  ('La signora delle ortensie','Adolfo Feragutti Visconti','1920-1921',None),
  ('Giovane donna','Cesare Tallone','1902',None)]:
  named(rows,'cedri',source,title,creator,date,'Olio su tela',dimensions,'painting')

 source=collection('https://kunsthausglarus.ch/de/sammlungen/glarner-kunstverein')
 for title,creator,date in [
  ('Selbstbildnis mit aufgerissenen Augen II','Ferdinand Hodler','1912'),
  ('Klönthalersee (Mittag)','Johann Gottfried Steffan','1873'),
  ('Am Waldrand','Ernst Ludwig Kirchner','um 1935/36'),
  ('Heranziehendes Gewitter','Rudolf Koller','1889'),
  ('Im hinteren Klöntal','Balz Stäger','1902')]:
  named(rows,'glarus',source,title,creator,date)

 source=collection('https://www.mhdp.ch/collections.html')
 for title,creator,date,medium,kind in [
  ("L'été à la campagne",'Albert Schnyder','1957','Dessin au crayon','drawing'),
  ('Jour naissant','Joseph Lachat','1965','Huile sur toile','painting'),
  ('La Tour du Coq','Willi Nicolet','1934','Aquarelle','watercolor'),
  ('Dédié à Caën','Gérard Bregnard','1969','Peinture acrylique sur pavatex','painting')]:
  named(rows,'hotel-dieu',source,title,creator,date,medium,kind=kind)

 source=collection('https://elysee.ch/collections/')
 for title,creator,date in [
  ('Matanzas','Luc Chessex','1962'),
  ('Soleil couchant et glacier','Gabriel Lippmann','vers 1891-1899'),
  ('Nelly van Doesburg','Lucia Moholy','1924'),
  ("Le bateau à vapeur 'Le Rhône' et une barque du Léman, port de Morges",'Adrien Constant-Delessert','1860'),
  ('Nu','Gertrude Fehr','1936')]:
  named(rows,'elysee',source,title,creator,date,kind='photograph')

 source=collection('https://artbrut.ch/fr/evenements/exposition-permanente')
 for title,creator,date,medium,dimensions,kind in [
  ('Napoléon III à Cherbourg','Aloïse Corbaz','1952-1954','Crayon de couleur et suc de géranium sur feuilles de papier cousues ensemble','164 × 117 cm','drawing'),
  ('L’éternelle infidèle','Pascal-Désir Maisonneuve','1927-1928',None,None,'unknown'),
  ('Couronne d’épines de Rosalie en forme de coeur','Adolf Wölfli','1922',None,None,'unknown')]:
  # Source uses a straight apostrophe for Maisonneuve.
  if title.startswith('L’éternelle'):title="L'éternelle infidèle"
  named(rows,'artbrut',source,title,creator,date,medium,dimensions,kind)

 source=collection('https://www.tinguely.ch/de/ausstellungen/ausstellungen/2023/sammlungspraesentation.html')
 for title,date in [('Méta-Matic No. 6','1959'),('Hannibal II','1967')]:
  named(rows,'tinguely',source,title,'Jean Tinguely',date)

 assert len({(r['provider'],r['source_id']) for r in rows})==len(rows)
 m.save(RUN/'CH-wave2/source-records.json.gz',rows)
 m.save(RUN/'institution-registry-wave2.json',{name:dict(slug=slug,website=website,directory_id=did,city=city,country_code='CH') for name,slug,website,did,city in EXTRA.values()})
 print(json.dumps(dict(records=len(rows),museums=dict(collections.Counter(r['museum'] for r in rows)))),flush=True)


if __name__=='__main__':run()
