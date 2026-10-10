#!/usr/bin/env python3
"""Correct bounded catalogue fields from immutable captured HTML; retain originals."""
import importlib.util,gzip
from pathlib import Path
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('m',Path(__file__).with_name('import-poland-collections-20261008.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
folder=m.RUN/'poland';rows=m.load(folder/'source-records.json.gz');captures={m.load(p)['sha256']:p.with_suffix('.body.gz') for p in (folder/'captures').glob('*.json')};out={};audit=[]
fields={'accession_number':'numer inw.:','date_display':'rok powstania:','medium':'materiał/technika:','dimensions':'wymiary:'}
for r in rows:
 if r['provider']!='zacheta':continue
 sp=BeautifulSoup(gzip.decompress(captures[r['evidence']['sha256']].read_bytes()),'html.parser');values={}
 for b in sp.select('li > b'):
  label=b.get_text(' ',strip=True);values[label]=b.parent.get_text(' ',strip=True)[len(label):].strip() or None
 corrections={k:values[label] for k,label in fields.items() if label in values and values[label]!=r.get(k)}
 assert 'date_display' not in corrections,('Date bounds need explicit reclassification',r['source_id'])
 if corrections:
  key=r['provider']+'/'+r['source_id'];out[key]=corrections;audit.append(dict(key=key,before={k:r.get(k) for k in corrections},after=corrections,source_sha256=r['evidence']['sha256'],basis='Exact labelled list item in captured official object HTML, excluding adjacent description paragraphs.'))
m.save(folder/'source-field-corrections.json.gz',out);m.save(folder/'source-field-correction-audit.json.gz',audit)
for p in [folder/'plan.json.gz',folder/'plan-pin.json',folder/'input-records.json.gz',m.BACKUP/'poland/plan-preimages.json.gz',m.BACKUP/'poland/locked-before.json.gz']:
 if p.exists():
  archive=p.parent/'rolled-back-unbounded-inventory';archive.mkdir(exist_ok=True);assert not(archive/p.name).exists();p.rename(archive/p.name)
print('Corrected exact source fields',len(out),flush=True)
