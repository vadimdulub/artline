"""Bounded next eligible theatre object selection toward200 works."""
import collections,importlib.util,json,re,time
from pathlib import Path
from urllib.parse import urljoin

def module(name,file):
 z=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(z);z.loader.exec_module(v);return v
s=module('s','museum-expansion-kazantzakis-more-common-20261009.py');old=module('old','museum-expansion-kazantzakis-selection-20261009.py');m=s.m;RUN=s.RUN;BASE=old.BASE;old.q.RUN=RUN;old.q.CAP=RUN/'captures';old.q.CAP.mkdir(parents=True,exist_ok=True);capture=old.q.capture;fields=old.fields;clean=old.clean;index=old.index

def main():
 prior=m.load(m.RUN/'native/kazantzakis-20261009/next-source-discovery-001.json.gz');seen={v['source_url']for v in m.load(m.RUN/'native/kazantzakis-20261009/native-selection-001.json.gz')['rows']};leads=[v for v in prior['rows']if v['decision']=='detail_review_next'];assert len(leads)==54;pages=[]
 for page in range(5,11):
  soup,rc=capture('theatre-ascending-page'+str(page)+'-001',BASE+'/aggregator/portal/collections/Kazantzakis/search?page.page='+str(page)+'&resultsMode=GRID&sortResults=YEAR_ASC');rows=index(soup);assert len(rows)==30
  for v in rows:
   date=re.search(r'Χρονολόγηση\s+(\d{4})(?:\s*[-–]\s*(\d{4}))?',v['text']);v.update(first=int(date.group(1))if date else None,last=int(date.group(2)or date.group(1))if date else None);art=any(t in v['text']for t in ['Ζωγραφικό σχέδιο','Σκίτσο','Ζωγραφική']);v['decision']='detail_review_next'if date and v['last']<=1970 and art and v['url']not in seen else'already_reviewed'if v['url']in seen else'other_index_lead'
   if v['decision']=='detail_review_next':assert v['url']not in{w['url']for w in leads};leads.append(v)
  pages.append(dict(page=page,receipt=rc,rows=rows));print(json.dumps(dict(index_page=page,candidate_leads=len(leads),page_states=dict(collections.Counter(v['decision']for v in rows)))),flush=True)
  if len(leads)>=110:break
 selected=leads[:110];assert len(selected)>=88,'Further bounded discovery needed before selection';m.save(RUN/'selected-index-leads-001.json.gz',dict(at=m.now(),prior_discovery_reference=s.ref(m.RUN/'native/kazantzakis-20261009/next-source-discovery-001.json.gz'),new_pages=pages,selected=selected,remaining_candidate_leads=leads[110:],last_new_page=pages[-1]['page'],policy='At most110 individually selected art/date leads,from54 prior leads and at most6 further30-result public index pages. No exhaustive metadata or image download. Index dates/types are leads pending individual review.'))
 output=[]
 for n,v in enumerate(selected):
  suffix=v['url'].split('/aggregator/edm/')[1];soup,rc=capture('selected-'+suffix.replace('/','-')+'-001',v['url']);literal,enrichment=fields(soup);assert literal.get('Τίτλος')and literal.get('Πάροχος');links=[dict(title=clean(a.get_text(' ',strip=True)),url=urljoin(v['url'],a['href']))for a in soup.select('a[href]')if '/records/'in a['href']or '/files/'in a['href']];output.append(dict(number=n+1,source_id=suffix,source_url=v['url'],index=v,fields=literal,enrichment=enrichment,links=links,receipt=rc))
  if (n+1)%10==0:print(json.dumps(dict(individual_records=n+1,last_source=suffix)),flush=True)
  time.sleep(.12)
 m.save(RUN/'native-selection-001.json.gz',dict(at=m.now(),rows=output,selection_reference=s.ref(RUN/'selected-index-leads-001.json.gz'),script_reference=s.ref(Path(__file__).resolve()),policy='Selected public museum-provider metadata with original and enriched fields separate. Physical dates,versions and sheet units still need review. No images or catalogue writes.'))
if __name__=='__main__':main()
