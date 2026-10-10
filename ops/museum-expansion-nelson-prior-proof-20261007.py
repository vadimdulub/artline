#!/usr/bin/env python3
"""Verify retained primary comparison bodies without new network requests."""
import hashlib,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('f',Path(__file__).with_name('museum-expansion-nelson-facts-20261007.py'));f=importlib.util.module_from_spec(s);s.loader.exec_module(f);m=f.m;RUN=f.RUN
def build():
 rows=[]
 for name in ['supplemental-identity-001.json.gz','version-citations-002.json.gz']:
  for c in m.load(RUN/name)['citations']:
   if c['entity_id'] not in ['f6340634-d0cd-5599-a8d3-21b3ffc47f04','8e9aee2d-a928-5186-92d2-5dfd8a0ad634','b15fd395-8592-5eaa-9888-660473036e05']:continue
   j=json.loads(c['evidence_note']);receipt=j.get('source_receipt',j.get('receipt'));p=m.ROOT/receipt['path'];raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()==receipt['sha256'];assert len(raw)==receipt['bytes']
   if c['entity_id'].startswith('f634'):
    soup=f.w.d.d.BeautifulSoup(raw,'html.parser');text=soup.get_text(' ',strip=True);assert '157 x 121' in text;basis='Existing WikiArt object explicitly measures 157 x 121 cm, versus native Nelson panel-size canvas 101.6 x 81.92 cm; source date discrepancy alone is not used to distinguish the versions.'
   else:
    source=json.loads(raw);text=json.dumps(source,ensure_ascii=False);assert 'wall' in text.lower();basis='Retained original Cyprus record describes a wall painting in the Monastery of Saint Neophytos, not either portable Russian wooden panel gifted by Fred Irwig.'
   rows.append(dict(artwork_id=c['entity_id'],source_url=c['source_url'],body_reference=f.ref(p),raw_sha256=receipt['sha256'],citation_reference=f.ref(RUN/name),basis=basis))
 assert len(rows)==3;return rows
if __name__=='__main__':
 rows=build();m.save(RUN/'prior-body-verification-001.json.gz',dict(at=m.now(),rows=rows,script_reference=f.ref(Path(__file__).resolve()),policy='Original retained source bytes rehashed; no images downloaded or new source access. Comparison facts do not rewrite existing catalogue values.'));print('Verified primary comparison bodies',len(rows))
