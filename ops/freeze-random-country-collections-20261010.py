#!/usr/bin/env python3
"""Editorial exclusions and source-backed field corrections before immutable planning."""
import runpy,collections,re,json,gzip
from pathlib import Path
r=runpy.run_path(str(Path(__file__).with_name('research-random-country-collections-20261010.py')))
ROOT=r['RUN'];load=r['b'].load;save=r['b'].save
registry={
'Royal Museum of Fine Arts Antwerp':('wikimedia-museum-q1471477','https://www.kmska.be'),
'Museum of Fine Arts Ghent (MSK)':('museum-of-fine-arts-ghent','https://www.mskgent.be'),
'Groeningemuseum — Musea Brugge':('groeningemuseum','https://www.museabrugge.be/'),
'Mu.ZEE, Art Museum by the Sea':('muzee-ostend','https://www.muzee.be/'),
'Royal Museums of Fine Arts of Belgium, Brussels, Belgium':('museum-source-1a4e0b935a6155cf33c1','https://fine-arts-museum.be/'),
'Latvian National Museum of Art, Riga, Latvia':('museum-source-1123be9a71901dcc03cd','https://lnmm.gov.lv/en/latvian-national-museum-of-art'),
'Art Museum Riga Bourse':('wikimedia-museum-q1954623','https://lnmm.gov.lv/en/art-museum-riga-bourse'),
'Romans Suta and Aleksandra Beļcova Museum':('romans-suta-aleksandra-belcova-museum','https://lnmm.gov.lv/en/romans-suta-and-aleksandra-belcova-museum'),
'National Museum of Modern Art, Zagreb':('national-museum-modern-art-zagreb','https://nmmu.hr/'),
'Museum of Modern Art Dubrovnik':('museum-modern-art-dubrovnik','https://ugdubrovnik.hr/'),
'Museum of Fine Arts, Split':('museum-fine-arts-split','https://galum.hr/')}
(ROOT/'institution-registry.json').write_text(json.dumps({name:dict(slug=slug,website=web,shared_domain_branch=name=='Romans Suta and Aleksandra Beļcova Museum') for name,(slug,web) in registry.items()},ensure_ascii=False,indent=2))
for code,files in [('BE',['vkc','rmfab']),('LV',['lnmm']),('HR',['nmmu','croatia-highlights'])]:
 r['phase'](code);rows=[];holds=[];changes=[]
 for name in files:
  d=load(name+'-records.json.gz');rows+=d['records'];holds+=d['held']
 final=[];seen={}
 for w in rows:
  old=dict(w);reason=None
  if code=='LV':
   if not w.get('creator_label') or re.search('photograph|member card',w.get('medium') or '',re.I):reason='Memorial photograph/document outside selected painting/drawing/sculpture scope'
   if w.get('creator_label') and '.' in w['creator_label']:
    creator,prefix=w['creator_label'].split('.',1);w['creator_label']=creator.strip();prefix=prefix.strip()
    if prefix.startswith(('Decorative plate','Vase')):reason='Decorative object held outside this selected pictorial batch'
    else:w['title']=prefix+' — '+w['title']
   if w['title'].startswith('Brooch'):reason='Decorative object outside selected pictorial batch'
   if re.search(r'darbnīca|school|workshop|after|from .*original',w['creator_label']+' '+(w.get('medium') or ''),re.I):w['creator_link_hold']='Explicit workshop/copy qualification preserved'
   if 'eļļa' in (w.get('medium') or ''):w['source_type']='painting'
   if re.search('oforts|mecotinta',w.get('medium') or ''):w['source_type']='print'
   if '/sculpture-collection/' in w['source_url'] and w['source_type']=='unknown':w['source_type']='sculpture'
  if code=='HR':
   if re.search('photograph',w.get('medium') or '',re.I):reason='Photograph outside selected pictorial/sculptural categories'
   if w['provider']=='croatia-highlight' and w['date_display'] is None:
    mt=re.match(r'^(.+),\s*((?:sredina|kraj|početak|druga polovica)\s+\d+\.\s*st\.?)$',w['title'])
    if mt:w['title'],w['date_display']=mt.groups()
   if w.get('date_display'):
    lo,hi=r['bounds'](w['date_display']);w.update(year_start=lo,year_end=hi)
    w['date_decision']='within_cutoff_source_bounds' if lo is not None and hi<=1970 else 'after_cutoff' if lo and lo>1970 else 'date_review'
  if reason:holds.append(dict(key=w['provider']+'/'+w['source_id'],reason=reason,source_record=w));continue
  assert w['title'] and len(w.get('creator_label') or '')<150
  key=(w['museum'],re.sub(r'\W+','',(w.get('creator_label') or '').casefold()),re.sub(r'\W+','',w['title'].casefold()),w.get('year_start'),w.get('year_end'))
  if key in seen and w.get('accession_number')==seen[key].get('accession_number'):
   holds.append(dict(key=w['provider']+'/'+w['source_id'],reason='Duplicate same collection/title/creator/date/inventory',duplicate_of=seen[key]['source_id']));continue
  seen[key]=w;final.append(w)
  if old!=w:changes.append(dict(key=w['provider']+'/'+w['source_id'],before=old,after=w))
 save('editorial-changes.json.gz',changes);save('research-held.json.gz',holds);save('source-records.json.gz',final)
 print(code,'selected',len(final),'held',len(holds),'museums',dict(collections.Counter(w['museum'] for w in final)),flush=True)
