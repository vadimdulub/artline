#!/usr/bin/env python3
"""Freeze selected Polish records after field, date, attribution and unit checks."""
import importlib.util,collections,re
from pathlib import Path
s=importlib.util.spec_from_file_location('m',Path(__file__).with_name('import-poland-collections-20261008.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
s=importlib.util.spec_from_file_location('research',Path(__file__).with_name('research-poland-collections-20261008.py'));research=importlib.util.module_from_spec(s);s.loader.exec_module(research)
rows=[];held=[]
for provider in ['warsaw','krakow','wroclaw','zacheta','lodz','royal','highlights']:
 data=m.load(m.RUN/'poland'/(provider+'.json.gz'))
 for r in data['records']:
  r['year_start'],r['year_end']=research.bounds(r.get('date_display'))
  r['date_decision']='within_cutoff_source_bounds' if isinstance(r['year_start'],int) and r['year_start']<=r['year_end']<=1970 else 'date_review'
  # Later physical casts/reconstructions are not the original 20th-century object.
  years=[int(x) for x in re.findall(r'(?<!\d)([12]\d{3})(?!\d)',r.get('date_display') or '')]
  if years and min(years)>1970:
   held.append(dict(record=r,reason='Explicit source creation after cutoff despite additional date wording'));continue
  if r['provider']=='lodz' and years and max(years)>1970:
   held.append(dict(record=r,reason='Later cast/reconstruction object; original design is not interchangeable with this later physical object'));continue
  assert r['title'] and r['evidence']['status']==200
  assert r['date_decision']!='after_cutoff'
  if r['date_decision'].startswith('within_cutoff'):assert isinstance(r['year_start'],int) and r['year_start']<=r['year_end']<=1970
  label=r.get('creator_label') or ''
  assert 'Powiększ' not in label
  if r['provider']=='royal-warsaw':assert r['raw']['fields']['field-wlasciciel']=='Zamek Królewski w Warszawie – Muzeum'
  if r['provider']=='krakow':assert r['source_url'].startswith('https://zbiory.mnk.pl/pl/katalog/')
  # Exact source qualification and multi-author labels must not become one invented person.
  if 'autor wzoru:' in label or len(re.findall(r'\(\d{4}\s*[-–]',label))>1:
   if not label.startswith('Qualified attribution: '):r['creator_label']='Qualified attribution: '+label
  rows.append(r)
assert len({(r['provider'],r['source_id']) for r in rows})==len(rows)
m.save(m.RUN/'poland/source-records.json.gz',rows);m.save(m.RUN/'poland/editorial-exclusions.json.gz',held)
m.save(m.RUN/'poland/research-summary.json',dict(at=m.now(),selected=len(rows),by_museum=dict(collections.Counter(r['museum'] for r in rows)),by_date=dict(collections.Counter(r['date_decision'] for r in rows)),editorial_exclusions=len(held),bounds='Official Warsaw/Krakow masterpiece selection; 360 Wroclaw painting index records; 40 Zacheta caption pages with detail only for pre-1971 or undated candidates; first 4 Royal Castle painting pages plus Rembrandt highlight; 50 Lodz linked collection objects; selected official highlights. No exhaustive image downloads.'))
print('Source records frozen',len(rows),'excluded',len(held),flush=True)
