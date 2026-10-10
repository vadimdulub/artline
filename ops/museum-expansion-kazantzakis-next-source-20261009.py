"""Next bounded theatre leads using the public ascending-date sort control."""
import collections,importlib.util,json,re
from pathlib import Path
z=importlib.util.spec_from_file_location('q',Path(__file__).with_name('museum-expansion-kazantzakis-selection-20261009.py'));q=importlib.util.module_from_spec(z);z.loader.exec_module(q);m=q.m;s=q.s;RUN=q.RUN
seen={v['source_url']for v in m.load(RUN/'native-selection-001.json.gz')['rows']};pages=[];leads=[]
for page in range(1,5):
 u=q.BASE+'/aggregator/portal/collections/Kazantzakis/search?page.page='+str(page)+'&resultsMode=GRID&sortResults=YEAR_ASC';soup,rc=q.q.capture('next-theatre-ascending-page'+str(page)+'-001',u);rows=q.index(soup);assert len(rows)==30
 for v in rows:
  found=re.search(r'Χρονολόγηση\s+(\d{4})(?:\s*[-–]\s*(\d{4}))?',v['text']);v['index_date']=found.group(0)if found else None;v['first']=int(found.group(1))if found else None;v['last']=int(found.group(2)or found.group(1))if found else None;v['already_reviewed']=v['url']in seen;v['art_type_lead']='Ζωγραφικό σχέδιο'in v['text']or'Σκίτσο'in v['text']or'Ζωγραφική'in v['text'];v['date_eligible_lead']=bool(found and v['last']<=1970);v['decision']='detail_review_next'if v['date_eligible_lead']and v['art_type_lead']and not v['already_reviewed']else'already_reviewed'if v['already_reviewed']else'other_index_lead';leads.append(v)
 pages.append(dict(page=page,receipt=rc,rows=rows));print(json.dumps(dict(page=page,counts=dict(collections.Counter(v['decision']for v in rows)),dates=sorted({v['index_date']or'unknown'for v in rows}))),flush=True)
assert len({v['url']for v in leads})==len(leads)
m.save(RUN/'next-source-discovery-001.json.gz',dict(at=m.now(),pages=pages,rows=leads,counts=dict(collections.Counter(v['decision']for v in leads)),control_evidence=s.ref(RUN/'captures/theatre-index-page4-001.json'),script_reference=s.ref(Path(__file__).resolve()),policy='Four index pages120leads only,using public sortResults YEAR_ASC option observed in the collection form. No individual detail fetches or images. Index dates/types are discovery leads,not final eligibility or artwork approval. Continue new physical-object review toward200 while preserving existing source decisions.'))
