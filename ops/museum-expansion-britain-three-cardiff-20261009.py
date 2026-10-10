"""Capture only the134 already selected Cardiff object inventories and exact matches."""
import importlib.util,json
from pathlib import Path
from urllib.parse import urlencode,urljoin
z=importlib.util.spec_from_file_location('x',Path(__file__).with_name('museum-expansion-britain-three-native-20261009.py'));x=importlib.util.module_from_spec(z);z.loader.exec_module(x);m=x.m;RUN=x.RUN;ref=x.ref;n=x.n

def parsed(raw):
 soup=n.BeautifulSoup(raw,'html.parser');fields={}
 for node in soup.select('.object_detail_fields > .object_field'):
  head=node.find('h4');assert head
  key=head.get_text(' ',strip=True);assert key not in fields
  fields[key]=node.get_text(' ',strip=True).removeprefix(key).strip()
 creators=[dict(name=v.select_one('.creation_name').get_text(' ',strip=True),role=v.select_one('.creation_role').get_text(' ',strip=True) if v.select_one('.creation_role') else None,period=v.select_one('.creation_period').get_text(' ',strip=True) if v.select_one('.creation_period') else None,bibliography=v.select_one('.bibliography').get_text(' ',strip=True) if v.select_one('.bibliography') else None) for v in soup.select('.object_creation')]
 return dict(fields=fields,creators=creators,headings=[v.get_text(' ',strip=True) for v in soup.select('h1,h2')],text=soup.get_text(' ',strip=True))

def main():
 dest=RUN/'cardiff-native-001.json.gz';assert not dest.exists()
 rs=[v for v in m.load(RUN/'source-context-001.json.gz')['rows'] if v['museum_qid']=='Q1321874'];assert len(rs)==134
 selection=RUN/'cardiff-native-selection-001.json';assert not selection.exists();m.save(selection,dict(at=m.now(),rows=[dict(number=v['number'],artwork_id=v['artwork']['id'],inventory=v['artwork']['accession_number']) for v in rs],source_reference=ref(RUN/'source-context-001.json.gz'),policy='Selected existing artworks only, metadata pages only. No exhaustive collection crawl, images or catalogue writes.'))
 out=[];failures=0;stopped=False
 for r in rs:
  row=dict(number=r['number'],artwork_id=r['artwork']['id'],inventory=r['artwork']['accession_number']);item=RUN/'cardiff-selected'/('%03d.json'%r['number']);assert not item.exists()
  url='https://museum.wales/collections/online/?'+urlencode(dict(field0='string',value0=row['inventory']))
  try:
   raw,cap=n.capture('cardiff',url);soup=n.BeautifulSoup(raw,'html.parser');matches=[]
   for box in soup.select('.result_box_text'):
    inv=box.select_one('.result_identifier');link=box.select_one('h3 a[href]')
    if inv and link and inv.get_text(' ',strip=True)==row['inventory']:matches.append(dict(inventory=inv.get_text(' ',strip=True),title=link.get_text(' ',strip=True),url=urljoin(url,link['href']).split('?',1)[0],text=box.get_text(' ',strip=True)))
   row.update(search_capture=cap,search_matches=matches)
   if len(matches)==1:
    raw,cap=n.capture('cardiff',matches[0]['url']);data=parsed(raw);assert data['fields']['Item Number']==row['inventory'];row.update(object_capture=cap,parsed=data,state='captured_exact_inventory')
   else:row['state']='no_unique_exact_inventory_result'
   failures=0
  except Exception as error:
   failures+=1;row.update(state='capture_error',error=type(error).__name__+': '+str(error));stopped=failures>=3 or any(t in str(error) for t in ['403','429','Forbidden'])
  m.save(item,row);out.append(dict(number=row['number'],state=row['state'],reference=ref(item)));print(json.dumps(dict(number=row['number'],state=row['state'],complete=len(out),selected=len(rs))),flush=True)
  if stopped:break
 m.save(dest,dict(at=m.now(),rows=out,selection_reference=ref(selection),script_reference=ref(Path(__file__).resolve()),requests_stopped=stopped,consecutive_failures=failures,unprocessed_numbers=[v['number'] for v in rs if v['number'] not in {r['number'] for r in out}],policy='Native exact inventory matches are evidence, not automatic editorial approval. Preserve original metadata and existing status. Museum-wide ownership and location text does not establish a specific current display.'))

if __name__=='__main__':main()
