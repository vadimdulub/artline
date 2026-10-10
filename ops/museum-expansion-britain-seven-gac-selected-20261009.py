"""Select candidate-matching Guildhall publisher metadata before bounded detail requests."""
import difflib,importlib.util,json,re
from pathlib import Path
from urllib.parse import urljoin
z=importlib.util.spec_from_file_location('g',Path(__file__).with_name('museum-expansion-britain-seven-gac-20261009.py'));g=importlib.util.module_from_spec(z);z.loader.exec_module(g);p=g.p;m=g.m;RUN=g.RUN
def key(v):return re.sub(r'^the ','',m.norm(v))
def tokens(v):return set(m.norm(v).split())-{'sir','lord','the','after','by','or','john','william','frederick','frederic','ii','younger'}
def parsed(raw):
 soup=p.n.BeautifulSoup(raw,'html.parser');fields=[]
 for li in soup.select('li.XD0Pkb'):
  label=li.select_one('.PUhAff')
  if label:fields.append(dict(label=label.get_text(' ',strip=True).rstrip(':'),value=li.get_text(' ',strip=True)[len(label.get_text(' ',strip=True)):].strip(),links=[dict(text=a.get_text(' ',strip=True),url=urljoin(g.BASE,a['href'])) for a in li.select('a[href]')]))
 h2=soup.select_one('h2.SThaNc');h3=soup.select_one('h3.To7WBf');return dict(headings=[h.get_text(' ',strip=True) for h in soup.select('h1')],subtitle=h2.get_text(' ',strip=True) if h2 else None,publisher_heading=h3.get_text(' ',strip=True) if h3 else None,fields=fields,canonical=[x.get('href') for x in soup.select('link[rel=canonical]')],partner_links=sorted({a['href'] for a in soup.select('a[href]') if a['href'].startswith('/partner/')}),text=soup.get_text(' ',strip=True))
def main():
 dest=RUN/'guildhall-gac-selected-001.json.gz';assert not dest.exists();source=RUN/'guildhall-gac-indexes-001.json.gz';candidates=RUN/'candidate-facts-001.json.gz';cs=[v for v in m.load(candidates)['rows'] if v['facts']['museum_qid']=='Q4968030'];selection=[]
 for card in m.load(source)['rows']:
  if re.match(r'^Detail\b',card['title'],re.I):continue
  hits=[]
  for r in cs:
   f=r['facts'];score=max(difflib.SequenceMatcher(None,key(card['title']),key(t)).ratio() for t in f['titles']);samecreator=bool(tokens(card['creator'])&tokens(f['creator_label']))
   if score==1 or samecreator and score>=.67:hits.append(dict(number=r['number'],title=f['title'],creator=f['creator_label'],title_similarity=round(score,4),creator_token_overlap=samecreator))
  if hits:selection.append(dict(card=card,candidate_leads=hits))
 select=RUN/'guildhall-gac-selection-001.json';assert not select.exists();m.save(select,dict(at=m.now(),rows=selection,index_reference=p.ref(source),candidate_reference=p.ref(candidates),policy='Title/maker similarity selects metadata for research only. No approval from score. Exclude image-detail cards; studies and duplicate publisher assets remain explicit version questions.'))
 out=[];failures=0;stopped=False
 for number,v in enumerate(selection,1):
  row=dict(number=number,**v);path=RUN/'guildhall-gac-selected-001'/('%03d.json'%number);assert not path.exists()
  try:
   raw,cap=p.n.capture('guildhall_gac',v['card']['url']);row.update(state='captured_metadata',capture=cap,parsed=parsed(raw));failures=0
  except Exception as e:failures+=1;row.update(state='source_error',error=type(e).__name__+': '+str(e));stopped=failures>=3 or any(t in str(e) for t in ['403','429'])
  m.save(path,row);out.append(dict(number=number,state=row['state'],reference=p.ref(path)));print(json.dumps(dict(number=number,selected=len(selection),state=row['state'])),flush=True)
  if stopped:break
 m.save(dest,dict(at=m.now(),rows=out,selection_reference=p.ref(select),script_reference=p.ref(Path(__file__).resolve()),requests_stopped=stopped,unprocessed=len(selection)-len(out),policy='Selected publisher metadata only. No image download or access to denied ArtUK,LondonPictureArchive or Smartify. Exact object identity,dates,qualifications and holdings still require review.'))
if __name__=='__main__':main()
