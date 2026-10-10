#!/usr/bin/env python3
"""Retain selected official masterpiece cards without inferring import approval."""
import gzip,hashlib,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('d',Path(__file__).with_name('museum-expansion-thyssen-discovery-20261007.py'));d=importlib.util.module_from_spec(s);s.loader.exec_module(d);m=d.m;RUN=d.RUN
def main():
 source=RUN/'masterpiece-page-001.json.gz';page=m.load(source);cap=page['capture'];raw=gzip.decompress((m.ROOT/cap['body_path']).read_bytes());assert hashlib.sha256(raw).hexdigest()==cap['receipt']['sha256']
 soup=d.d.BeautifulSoup(raw,'html.parser');rows=[]
 for card in soup.select('a.snippet__caption[href]'):
  url=d.urljoin(page['url'],card['href'])
  if '/en/collection/artists/' not in url:continue
  creator=card.select_one('.snippet__title');title=card.select_one('.snippet__subtitle');date=card.select_one('.snippet__text');assert creator and title and date
  date=date.get_text(' ',strip=True)
  rows.append(dict(source_url=url,title=title.get_text(' ',strip=True),creator_label=creator.get_text(' ',strip=True),date_display=date,caption_html=str(card),state='outside_1970_scope' if date=='1971' else 'unapproved_research_lead',source_reference=dict(path=str(source.relative_to(m.ROOT)),sha256=hashlib.sha256(source.read_bytes()).hexdigest()),inventory=None))
 assert len(rows)==len({r['source_url'] for r in rows})==32
 assert sum(r['state']=='outside_1970_scope' for r in rows)==1
 m.save(RUN/'masterpiece-leads-001.json.gz',dict(at=m.now(),rows=rows,policy='32distinct museum-selected masterpiece cards,not64duplicated image/caption anchors.31date-screened research leads and one1971scope exclusion. Exact physical object,detail-page dates,ownership/loan labels and existing catalogue reconciliation remain pending. No images or DB additions.'))
 print(json.dumps(dict(distinct_cards=len(rows),pre1971_research_leads=31,excluded_1971=1)),flush=True)
if __name__=='__main__':main()
