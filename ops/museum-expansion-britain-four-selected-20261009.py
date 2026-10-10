"""Bounded native metadata capture for 239 previously selected existing objects."""
import argparse,importlib.util,json
from pathlib import Path
from urllib.parse import urljoin
def module(name,file):
 z=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(z);z.loader.exec_module(v);return v
b=module('b','museum-expansion-britain-four-brighton-20261009.py');u=module('u','museum-expansion-britain-four-ulster-20261009.py');m=b.m;n=b.n;RUN=b.RUN;ref=b.ref
def ulster_parsed(raw):
 soup=n.BeautifulSoup(raw,'html.parser');dl=soup.select_one('dl.full_record_data');assert dl;fields={}
 for dt in dl.select('dt'):
  dd=dt.find_next_sibling('dd');assert dd;key=dt.get_text(' ',strip=True);assert key not in fields;fields[key]=dd.get_text('\n',strip=True).split('\n')
 return dict(fields=fields,headings=[v.get_text(' ',strip=True) for v in soup.select('h1,h2,h3')],text=soup.get_text(' ',strip=True))
def main(provider):
 dest=RUN/(provider+'-native-001.json.gz');assert not dest.exists();qid={'brighton':'Q2790574','ulster':'Q3547979'}[provider]
 rs=[v for v in m.load(RUN/'source-context-001.json.gz')['rows'] if v['museum_qid']==qid];assert len(rs)=={'brighton':120,'ulster':119}[provider]
 selection=RUN/(provider+'-native-selection-001.json');assert not selection.exists();m.save(selection,dict(at=m.now(),rows=[dict(number=v['number'],artwork_id=v['artwork']['id'],inventory=v['artwork']['accession_number']) for v in rs],source_reference=ref(RUN/'source-context-001.json.gz'),policy='Selected existing inventory metadata only; no images or catalogue-wide search.'))
 out=[];failures=0;stopped=False
 for r in rs:
  row=dict(number=r['number'],artwork_id=r['artwork']['id'],inventory=r['artwork']['accession_number']);item=RUN/(provider+'-selected')/('%03d.json'%r['number']);assert not item.exists()
  try:
   if provider=='brighton':
    data,cap=b.search(row['inventory']);matches=[v for v in data if v.get('accessionId')==row['inventory']];row.update(search_capture=cap,search_results=data)
    if len(matches)==1:
     v=matches[0];assert v['_id']==v['id'];row.update(state='captured_exact_inventory',parsed=v,object_url=n.SITES[provider]+'/records/'+v['_id'])
    else:row['state']='no_unique_exact_inventory_result'
   else:
    raw,cap=u.search(row['inventory']);soup=n.BeautifulSoup(raw,'html.parser');matches=[]
    for box in soup.select('section.summary-box'):
     inv=box.select_one('.card-title');link=box.select_one('a[href]')
     if inv and link and inv.get_text(' ',strip=True)==row['inventory']:matches.append(dict(inventory=inv.get_text(' ',strip=True),url=urljoin(n.SITES[provider]+'/',link['href']),text=box.get_text(' ',strip=True)))
    row.update(search_capture=cap,search_matches=matches)
    if len(matches)==1:
     raw,cap=n.capture(provider,matches[0]['url']);data=ulster_parsed(raw);assert data['fields']['Catalogue Number']==[row['inventory']];row.update(state='captured_exact_inventory',object_capture=cap,parsed=data,object_url=matches[0]['url'])
    else:row['state']='no_unique_exact_inventory_result'
   failures=0
  except Exception as error:
   failures+=1;row.update(state='capture_error',error=type(error).__name__+': '+str(error));stopped=failures>=3 or any(t in str(error) for t in ['403','429','Forbidden'])
  m.save(item,row);out.append(dict(number=row['number'],state=row['state'],reference=ref(item)));print(json.dumps(dict(provider=provider,number=row['number'],state=row['state'],complete=len(out),selected=len(rs))),flush=True)
  if stopped:break
 m.save(dest,dict(at=m.now(),rows=out,selection_reference=ref(selection),script_reference=ref(Path(__file__).resolve()),search_script_reference=ref(Path(b.__file__ if provider=='brighton' else u.__file__).resolve()),requests_stopped=stopped,consecutive_failures=failures,unprocessed_numbers=[v['number'] for v in rs if v['number'] not in {r['number'] for r in out}],policy='Exact native inventory is source evidence, not automatic editorial approval. Preserve source dates and maker qualifications separately. Holdings do not imply ownership, custody or current display.'))
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('provider',choices=['brighton','ulster']);main(parser.parse_args().provider)
