"""Extract bounded, date-selected artwork metadata leads from two public museum stories."""
import gzip,importlib.util,json,re
from pathlib import Path
z=importlib.util.spec_from_file_location('n',Path(__file__).with_name('museum-expansion-leeds-native-20261009.py'));n=importlib.util.module_from_spec(z);z.loader.exec_module(n);m=n.m;RUN=n.RUN;ref=n.ref

def walk(value):
 if isinstance(value,list):
  if len(value)>4 and isinstance(value[0],str) and isinstance(value[4],str) and value[4].startswith('/asset/'):
   yield dict(title=value[0],date_display=value[1],creator=value[2],provider=value[3],url='https://artsandculture.google.com'+value[4])
  else:
   for v in value:yield from walk(v)

def main():
 stories=m.load(RUN/'selected-discovery-stories-001.json.gz');found={}
 for story in stories['rows']:
  raw=gzip.decompress((m.ROOT/story['capture']['body_path']).read_bytes()).decode();decoder=json.JSONDecoder()
  for match in re.finditer(r"window\.INIT_data\['[^']+'\]\s*=\s*",raw):
   value,_=decoder.raw_decode(raw[match.end():])
   for r in walk(value):found.setdefault(r['url'],dict(r,story_url=story['url']))
 rows=[]
 for r in found.values():
  years=[int(v) for v in re.findall(r'\d{4}',r['date_display'] or '')];r['state']='selected_metadata_lead' if years and max(years)<=1970 else 'date_not_eligible_or_unknown';rows.append(r)
 rows.sort(key=lambda r:r['title']);m.save(RUN/'additional-object-leads-001.json.gz',dict(at=m.now(),rows=rows,story_reference=ref(RUN/'selected-discovery-stories-001.json.gz'),script_reference=ref(Path(__file__).resolve()),policy='Only creation-date-selected metadata leads. Not approved holdings or new artworks; museum ownership,correct venue and duplicate/version review required. No images.'))
 for r in rows:print(json.dumps(r,ensure_ascii=False),flush=True)
 selected=[r for r in rows if r['state']=='selected_metadata_lead'];sample=selected[0];raw,c=n.n.capture('gac',sample['url']);p=n.parsed(raw);m.save(RUN/'additional-object-sample-001.json.gz',dict(at=m.now(),lead=sample,capture=c,parsed=p));print('SAMPLE',p['text'],flush=True)
if __name__=='__main__':main()
