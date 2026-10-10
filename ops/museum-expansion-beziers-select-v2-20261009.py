"""Refine discovery to200 Fine Arts metadata candidates, avoiding postcard harvesting."""
import importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('s',Path(__file__).with_name('museum-expansion-beziers-source-20261009.py'));s=importlib.util.module_from_spec(z);z.loader.exec_module(s);m=s.m;RUN=s.RUN
def main():
 url='https://tabular-api.data.gouv.fr/api/resources/7e3307c2-f2ff-455c-bbca-bb6f11aec7bb/data/?Code_Museofile__exact=M0467&Domaine__contains=beaux-arts&page_size=200'
 raw,rc=s.capture('joconde-finearts-002',url);data=json.loads(raw);assert all(v['Code_Museofile']=='M0467' and 'beaux-arts' in v['Domaine'] for v in data['data'])
 previous=m.load(RUN/'joconde-current-001.json.gz');by={v['Reference']:v for v in previous['rows']}
 for v in data['data']:
  if v['Reference'] in by:assert by[v['Reference']]==v
  by[v['Reference']]=v
 m.save(RUN/'joconde-selected-001.json.gz',dict(at=m.now(),receipts=previous['receipts']+[rc],rows=sorted(by.values(),key=lambda v:v['Reference']),finearts_total=data['meta']['total'],finearts_next=data['links']['next'],overall_total=previous['total'],overall_next=previous['next_page'],policy='400 initial metadata plus200 Fine Arts refined ceiling; no exhaustive collection retrieval, no image downloads. Public contains filter documented by data.gouv.fr.'))
 print(json.dumps(dict(finearts_total=data['meta']['total'],finearts_selected=len(data['data']),distinct_captured=len(by),next=data['links']['next'])),flush=True)
if __name__=='__main__':main()
