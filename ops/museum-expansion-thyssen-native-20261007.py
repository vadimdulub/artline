#!/usr/bin/env python3
"""Capture bounded, explicitly selected public artwork pages; never query denied search."""
import argparse,collections,gzip,hashlib,importlib.util,json,re
from pathlib import Path
from urllib.parse import urlsplit
s=importlib.util.spec_from_file_location('d',Path(__file__).with_name('museum-expansion-thyssen-discovery-20261007.py'));d=importlib.util.module_from_spec(s);s.loader.exec_module(d);m=d.m;RUN=d.RUN
s=importlib.util.spec_from_file_location('dates',Path(__file__).with_name('museum-expansion-birmingham-facts-20261007.py'));dates=importlib.util.module_from_spec(s);s.loader.exec_module(dates)
def ref(p):return dict(path=str(p.relative_to(m.ROOT)),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def text(el):return re.sub(r'\s+',' ',el.get_text(' ',strip=True)).strip() if el else None
def creation(raw):return dates.creation(re.sub(r'\s+',' ',raw or '').strip())
def body(cap):
 raw=gzip.decompress((m.ROOT/cap['body_path']).read_bytes());assert hashlib.sha256(raw).hexdigest()==cap['receipt']['sha256'] and cap['receipt']['status']==200;return raw
def parsed(raw):
 soup=d.d.BeautifulSoup(raw,'html.parser');art=[json.loads(s.get_text()) for s in soup.select('script[type="application/ld+json"]')];art=[x for x in art if x.get('@type')=='VisualArtwork'];assert len(art)==1,'No unique public VisualArtwork'
 art=art[0];info=soup.select_one('.js-zoom-map-info');assert info and len(info.select('h1'))==1
 group=info.select_one('div.u-font-size-sm');assert group;rows=group.find_all('div',recursive=False);assert len(rows)>=3
 dimensions=rows[0].select('.field--string');assert len(dimensions)<=1
 physical=d.d.BeautifulSoup(str(rows[0]),'html.parser')
 for x in physical.select('.field--string'):x.decompose()
 inventory=text(rows[2]);assert inventory.startswith('Inv. no.'),inventory
 iv=[text(x) for x in rows[2].select('.field--string')]
 canonical=soup.select_one('link[rel="canonical"]');assert canonical
 related=[]
 for card in soup.select('a.snippet__caption[href]'):
  url=d.urljoin(art['url'],card['href'])
  if '/en/collection/artists/' not in url:continue
  creator=card.select_one('.snippet__title');title=card.select_one('.snippet__subtitle');date=card.select_one('.snippet__text')
  if not (creator and title and date):continue
  related.append(dict(source_url=url,creator_label=text(creator),title=text(title),date_display=text(date),caption_html=str(card)))
 return dict(canonical=canonical['href'],jsonld=art,title=text(info.select_one('h1')),creator_label=text(info.select_one('#rs_artwork_artist')),creator_url=info.select_one('#rs_artwork_artist')['href'],date_display=text(info.select_one('.field--FechasThyssen')),medium=text(physical) or None,dimensions_text=text(dimensions[0]) if dimensions else None,credit_line=text(rows[1]),inventory_display=inventory[len('Inv. no.'):].strip(),inventory_fields=iv,source_location_text=text(rows[3]) if len(rows)>3 else None,description_html=str(soup.select_one('#rs_artwork_description')),description_text=text(soup.select_one('#rs_artwork_description')),tags=[text(a) for a in soup.select('a.tag')],related=related,rights_text=' '.join(text(x) for x in soup.select('.splash') if 'Terms of Use' in (text(x) or '')) or None)
def checked_record(p):
 x=m.load(p);parsed_again=parsed(body(x['capture']));assert parsed_again==x['parsed'];return x,parsed_again
def capture_rows(rows,suffix,selection_reference):
 assert 1<=len(rows)<=150 and len({r['source_url'] for r in rows})==len(rows)
 out=[];stop=False
 for number,row in enumerate(rows,1):
  url=row['source_url'];assert url.startswith(d.BASE+'/en/collection/artists/') and len(urlsplit(url).path.split('/'))==6 and not urlsplit(url).query,url
  key=hashlib.sha256(url.encode()).hexdigest()[:20];dest=RUN/('objects-'+suffix)/(key+'.json.gz')
  if dest.exists():record=m.load(dest);assert record['index']==row and record['selection_reference']==selection_reference
  else:
   try:
    raw,cap=d.n.capture('thyssen',url);p=parsed(raw);record=dict(index=row,selection_reference=selection_reference,capture=cap,parsed=p)
   except Exception as ex:
    record=dict(index=row,selection_reference=selection_reference,error=type(ex).__name__+': '+str(ex));stop=True
   m.save(dest,record)
  if 'error' in record:stop=True
  out.append(ref(dest));print(suffix,number,'of',len(rows),record.get('error') or record['parsed']['title'],flush=True)
  if stop:break
 m.save(RUN/('selected-capture-'+suffix+'.json.gz'),dict(at=m.now(),requested=len(rows),records=out,stopped_on_error=stop,policy='Only selected public artwork pages linked from accessible museum pages. No denied search endpoints, alternate access routes, images or DB writes. Original HTTP and HTML retained.'))
def masterpieces():
 p=RUN/'masterpiece-leads-001.json.gz';rows=[r for r in m.load(p)['rows'] if r['state']=='unapproved_research_lead'];assert len(rows)==31
 capture_rows(rows,'001',ref(p))
def related(source_suffix,dest_suffix,limit):
 assert 1<=limit<=150;source=RUN/('selected-capture-'+source_suffix+'.json.gz');selection=[];all_leads=[];seen={r['source_url'] for r in m.load(RUN/'masterpiece-leads-001.json.gz')['rows']}
 for p in sorted(RUN.glob('selected-capture-*.json.gz')):
  for ref0 in m.load(p)['records']:seen.add(m.load(m.ROOT/ref0['path'])['index']['source_url'])
 by_url={}
 for ref0 in m.load(source)['records']:
  x,p=checked_record(m.ROOT/ref0['path'])
  for row in p['related']:
   url=row['source_url'];dt=creation(row['date_display']);entry=dict(row,creation_screen=dt,parent_references=[ref0],already_captured_or_masterpiece=url in seen)
   if url in by_url:
    old=by_url[url];assert all(old[k]==entry[k] for k in ['creator_label','title','date_display']),url;old['parent_references'].append(ref0)
   else:by_url[url]=entry
 for row in by_url.values():
  if row['already_captured_or_masterpiece']:row['selection_state']='already_seen'
  elif row['creation_screen']['date_issue']:row['selection_state']='date_review'
  elif len(selection)>=limit:row['selection_state']='bounded_followup'
  else:row['selection_state']='selected_research_only';selection.append(row)
  all_leads.append(row)
 out=RUN/('related-leads-'+dest_suffix+'.json.gz');m.save(out,dict(at=m.now(),source_reference=ref(source),rows=all_leads,selected=selection,counts=dict(collections.Counter(r['selection_state'] for r in all_leads)),policy='Bounded metadata selection from publicly linked related-work cards; complete source dates screened before detail capture. No selection implies identity/holding approval.'))
 print(json.dumps(dict(leads=len(all_leads),selected=len(selection),counts=dict(collections.Counter(r['selection_state'] for r in all_leads)))),flush=True)
def capture_related(suffix):
 p=RUN/('related-leads-'+suffix+'.json.gz');capture_rows(m.load(p)['selected'],suffix,ref(p))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['masterpieces','related','capture_related']);p.add_argument('--source');p.add_argument('--suffix');p.add_argument('--limit',type=int,default=140);a=p.parse_args()
 if a.command=='masterpieces':masterpieces()
 elif a.command=='related':related(a.source,a.suffix,a.limit)
 else:capture_related(a.suffix)
