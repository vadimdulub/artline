"""Selected Southampton highlight object pages, retaining exact native fields."""
import gzip,hashlib,importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('n',Path(__file__).with_name('museum-expansion-southampton-native-20261009.py'));n=importlib.util.module_from_spec(z);z.loader.exec_module(n);m=n.m;RUN=n.RUN;ref=n.ref
def parsed(raw):
 p=n.parsed(raw);s=n.n.n.BeautifulSoup(raw,'html.parser');h=s.select_one('h1');p['object_title']=h.get_text(' ',strip=True) if h else None;maker=h.parent.select_one('p.uppercase') if h else None;p['object_creator']=maker.get_text(' ',strip=True) if maker else None;p['fields']=[]
 for tr in s.select('table tr'):
  cells=tr.select('th,td')
  if len(cells)==2:p['fields'].append(dict(label=cells[0].get_text(' ',strip=True),value=cells[1].get_text(' ',strip=True)))
 p['narrative']=h.parent.get_text(' ',strip=True) if h else None
 return p
def main():
 dest=RUN/'native-captured-001.json.gz';assert not dest.exists();old=n.PRIOR/'native-selected-001.json';new=RUN/'additional-indexes-001.json';cards={}
 for path in [old,new]:
  x=m.load(path)
  for row in x['rows']:
   if '/collection/' not in row['url']:continue
   for a in row.get('parsed',{}).get('links',[]):
    if '/object/' in a['href'] and a['text']:
     c=dict(title=a['text'],url=a['href'],source_id=a['href'].rstrip('/').split('/')[-1],index_url=row['url'],index_reference=ref(path));assert c['url'].startswith(n.BASE+'/object/');assert c['url'] not in cards or cards[c['url']]['title']==c['title'];cards[c['url']]=c
 existing={r['url']:r for r in m.load(n.PRIOR/'native-objects-001.json')['rows']};selected=list(cards.values());assert len(selected)==80 and set(existing)<=set(cards)
 m.save(RUN/'native-selection-001.json',dict(at=m.now(),rows=selected,reused_object_urls=sorted(existing),index_references=[ref(old),ref(new)],policy='80 curated highlight cards in eight selected historical collection sections;74 new metadata requests and6 retained exact-page captures. No exhaustive4,000-object or image download. Category/artist dates are not creation evidence. Existing records,versions,attributions,loans and print editions need review.'))
 out=[];failed=0;stopped=False
 for number,card in enumerate(selected,1):
  path=RUN/'native-selected-001'/('%03d.json'%number);assert not path.exists();row=dict(number=number,card=card)
  if stopped:break
  try:
   if card['url'] in existing:
    cap=existing[card['url']]['capture'];raw=gzip.decompress((m.ROOT/cap['body_path']).read_bytes());assert hashlib.sha256(raw).hexdigest()==cap['receipt']['sha256'];row['reused_reference']=ref(n.PRIOR/'native-objects-001.json')
   else:raw,cap=n.n.n.capture('southampton',card['url'])
   row.update(state='captured_metadata',capture=cap,parsed=parsed(raw));failed=0
  except Exception as e:failed+=1;row.update(state='source_error',error=type(e).__name__+': '+str(e));stopped=failed>=3 or any(t in str(e) for t in ['403','429'])
  m.save(path,row);out.append(dict(number=number,state=row['state'],reference=ref(path)));print(json.dumps(dict(number=number,title=card['title'],state=row['state'],fields=row.get('parsed',{}).get('fields'),error=row.get('error'))),flush=True)
 m.save(dest,dict(at=m.now(),rows=out,selection_reference=ref(RUN/'native-selection-001.json'),script_reference=ref(Path(__file__).resolve()),requests_stopped=stopped,unprocessed_numbers=list(range(len(out)+1,len(selected)+1)),policy='Exact museum object metadata only. No images or database mutations. Explicit creation and collection evidence required before new review records.'))
if __name__=='__main__':main()
