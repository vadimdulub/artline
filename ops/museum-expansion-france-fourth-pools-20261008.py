#!/usr/bin/env python3
import gzip,json,re,sys
from pathlib import Path
RUN=Path('docs/research/museum-expansion-20261006/native/france-fourth-minimum-20261008')
x=json.loads(gzip.decompress((RUN/'native-identity-002.json.gz').read_bytes()));by={a['id']:a for a in x['state']['artworks']};links={}
for v in x['state']['links']:links.setdefault(v['artwork_id'],[]).append(v['display_name'])
for spec in sys.argv[1:]:
 parts=spec.split(':',1);n=int(parts[0]);cmp=x['comparisons'][n-1];print('CANDIDATE',n,cmp['creator_terms'])
 for aid in cmp['creator_pool_ids']:
  a=by[aid];cre=';'.join(links.get(aid,[]))+ ';'+(a['unlinked_creator_label'] or '')
  if len(parts)>1 and not re.search(parts[1],cre,re.I):continue
  print(aid,a['title'],'|',cre,'|',a['date_display'],'|',a['medium_text'],'|',a['dimensions_text'],'|',a['accession_number'])
