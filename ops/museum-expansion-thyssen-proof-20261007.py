#!/usr/bin/env python3
"""Validate the captured public-card to detail-page source chain offline."""
import hashlib,importlib.util
from functools import lru_cache
from pathlib import Path
s=importlib.util.spec_from_file_location('f',Path(__file__).with_name('museum-expansion-thyssen-facts-20261007.py'));f=importlib.util.module_from_spec(s);s.loader.exec_module(f);m=f.m;n=f.n;RUN=f.RUN
def checked_reference(reference):
 p=m.ROOT/reference['path'];assert hashlib.sha256(p.read_bytes()).hexdigest()==reference['sha256'];return p
@lru_cache(maxsize=400)
def checked_record(path,digest):
 p=m.ROOT/path;assert hashlib.sha256(p.read_bytes()).hexdigest()==digest;x,parsed=n.checked_record(p);selection=m.load(checked_reference(x['selection_reference']));row=x['index']
 if 'selected' in selection:
  assert row in selection['selected'] and row['selection_state']=='selected_research_only' and row['creation_screen']['date_issue'] is None
  assert row['parent_references']
  for parent in row['parent_references']:
   parent_x,parent_parsed=checked_record(parent['path'],parent['sha256'])
   assert {k:row[k] for k in ['source_url','creator_label','title','date_display','caption_html']} in parent_parsed['related']
 else:
  assert row in selection['rows'] and row['state']=='unapproved_research_lead'
  original=m.load(checked_reference(row['source_reference']));soup=n.d.d.BeautifulSoup(n.body(original['capture']),'html.parser')
  assert any(str(card)==row['caption_html'] for card in soup.select('a.snippet__caption[href]'))
 assert n.creation(row['date_display'])['date_issue'] is None
 return x,parsed
def facts(reference):
 x,p=checked_record(reference['path'],reference['sha256']);return f.facts(x,p)
