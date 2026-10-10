#!/usr/bin/env python3
"""Separate native creator names/qualifiers from biography, without catalogue writes."""
import argparse,copy,importlib.util,json,re
from pathlib import Path
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('i',Path(__file__).with_name('museum-expansion-wallace-identity-20261007.py'));i=importlib.util.module_from_spec(s);s.loader.exec_module(i);f=i.w;m=i.m;RUN=i.RUN
original_search_terms=i.search_terms

def creator_parts(el):
 assert el is not None;node=BeautifulSoup(str(el),'html.parser').find();original=node.get_text(' ',strip=True);parts=[]
 for span in node.select('.tspReferenceLinkList'):
  names=[a.get_text(' ',strip=True) for a in span.select('a .tspReferenceLink')];assert names
  biographies=[a.get_text(' ',strip=True) for a in span.select(':scope > .tspValue')]
  parts.append(dict(names=names,biographical_labels=biographies))
  anchors=list(span.find_all('a',recursive=False));assert len(anchors)==len(names)
  for child in list(span.contents):
   if child not in anchors:child.extract()
 assert parts
 label=node.get_text(' ',strip=True)
 return dict(original_statement=original,creator_label=label,parts=parts,policy='Native artist-link text and attribution prefix retained; only sibling biographical spans within the artist reference wrapper removed. No lifespan used as creation.')

def search_terms(facts):
 value=copy.deepcopy(facts)
 # Generational/name suffixes remain in the catalogue label but should not
 # replace the surname in the discovery query.
 for key in ['creator_label','detail_creator_label']:
  if value.get(key):value[key]=re.sub(r'\s+(?:senior|junior|fils|père)$','',value[key],flags=re.I)
 return original_search_terms(value)
i.search_terms=search_terms

def refine():
 source=RUN/'native-candidates-002.json.gz';dest=RUN/'native-candidates-003.json.gz';assert not dest.exists();rows=copy.deepcopy(m.load(source)['rows']);changes=[]
 for r in rows:
  if 'facts' not in r:continue
  record,p,t=f.checked_record(m.ROOT/r['source_reference']['path']);assert f.facts(record,p,t)==r['facts']
  detail=BeautifulSoup(f.c.saved_body(record['capture']),'html.parser').select_one('#collectionDetail .ListArtist');index=BeautifulSoup(record['index_row']['source_html'],'html.parser').select_one('.LbArtist')
  a,b=creator_parts(detail),creator_parts(index);assert a['creator_label']==b['creator_label'] and a['parts']==b['parts']
  before=r['facts']['creator_label'];r['facts'].update(creator_label=a['creator_label'],detail_creator_label=a['creator_label'],creator_extraction=dict(detail=a,index=b,previous_parser_label=before))
  if before!=a['creator_label']:changes.append(dict(source_id=r['source_id'],inventory=r['facts']['inventory'],previous=before,selected=a['creator_label']))
 out=dict(at=m.now(),rows=rows,counts=m.load(source)['counts'],source_reference=f.ref(source),changes=changes,policy='Explicit structural creator extraction from retained native HTML. Original statements, biographical labels, attribution qualifiers, index and object captures preserved. Date/source holds remain unchanged. No database writes.')
 m.save(dest,out);print(json.dumps(dict(rows=len(rows),creator_labels_refined=len(changes),changes=changes),ensure_ascii=False),flush=True)

def identity():
 i.main('003')

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['refine','identity']);a=p.parse_args();refine() if a.command=='refine' else identity()
