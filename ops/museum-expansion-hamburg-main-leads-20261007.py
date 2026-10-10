#!/usr/bin/env python3
"""Extract research leads from four preserved official pages; no catalogue writes."""
import gzip,hashlib,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('d',Path(__file__).with_name('museum-expansion-hamburg-discovery-20261007.py'));d=importlib.util.module_from_spec(s);s.loader.exec_module(d);m=d.m

def ref(p):return dict(path=str(p.relative_to(m.ROOT)),sha256=hashlib.sha256(p.read_bytes()).hexdigest())

def main():
 source=d.RUN/'main-site-discovery-001.json.gz';pages=m.load(source)['pages'];rows=[];page_counts={}
 assert len(pages)==4
 for page in pages:
  assert 'error' not in page
  cap=page['capture'];raw=gzip.decompress((m.ROOT/cap['body_path']).read_bytes())
  assert hashlib.sha256(raw).hexdigest()==cap['receipt']['sha256'] and cap['receipt']['status']==200
  soup=d.BeautifulSoup(raw,'html.parser');cards=soup.select('div.litebox__caption');page_counts[page['url']]=len(cards)
  assert len(cards)<=25
  for pos,card in enumerate(cards,1):
   outer=card.find('span',recursive=False)
   if outer is None or outer.find('h3',recursive=False) is None:continue
   creator=outer.find('h3',recursive=False).get_text(' ',strip=True)
   p=outer.find('p',recursive=False);assert p
   date=p.select_one('.jahresZahl');date_display=date.get_text(' ',strip=True) if date else None
   title_copy=d.BeautifulSoup(str(p),'html.parser')
   for el in title_copy.select('.jahresZahl'):el.decompose()
   title=title_copy.get_text(' ',strip=True);assert title and creator
   spans=outer.find_all('span',recursive=False);assert len(spans)==3
   lifespan=spans[0].get_text(' ',strip=True)
   info=[x.get_text(' ',strip=True) for x in spans[1].find_all('p',recursive=False)]
   rights=[x.get_text(' ',strip=True) for x in spans[2].find_all('p',recursive=False)]
   rows.append(dict(lead_number=len(rows)+1,page_ordinal=pos,source_url=page['url'],source_reference=ref(source),capture=cap,title=title,creator_label=creator,creator_lifespan_source=lifespan,date_display=date_display,info_paragraphs=info,rights_credit_paragraphs=rights,caption_html=str(card),inventory=None,native_object_id=None,state='research_lead_only',review_flags=['object_identity_and_existing_record_reconciliation_required']+(['explicit_loan_credit'] if 'leihgabe' in ' '.join(rights).casefold() else [])+(['component_identity_required'] if 'retabel' in title.casefold() else [])))
 assert 15<=len(rows)<=60
 m.save(d.RUN/'main-site-leads-001.json.gz',dict(at=m.now(),source_reference=ref(source),rows=rows,page_card_counts=page_counts,policy='Official selected collection captions only. Original literal dates and unknown inventories preserved. No normalized dates, catalogue additions or accepted holdings inferred. Native search access denied; source pages independently accessible.'))
 for r in rows:print(json.dumps({k:r[k] for k in ['lead_number','title','creator_label','date_display','review_flags']},ensure_ascii=False))
 print('TOTAL',len(rows),flush=True)

if __name__=='__main__':main()
