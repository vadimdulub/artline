"""Review existing holdings with explicit physical-version and native-source checks."""
import collections,gzip,hashlib,importlib.util,json
from pathlib import Path
def module(name,file):
 z=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(z);z.loader.exec_module(v);return v
i=module('i','museum-expansion-britain-eight-identity-20261009.py');f=i.f;s=f.s;m=f.m;RUN=f.RUN;ref=f.ref;checked=f.checked
n=module('n','museum-expansion-britain-eight-native-20261009.py');editor=module('ed','museum-expansion-britain-eight-decisions-20261009.py');HOLDS=editor.HOLDS;NOTES=editor.NOTES
LIMIT='Confidence is an editorial assessment,not a calibrated probability. Saved Wikidata collection/location statements and their ArtUK references are correlated secondary evidence,not independently fetched ArtUK confirmation. Exact Southampton native corroboration is separately identified. Holdings do not establish ownership,current custody or current display. Preserve metadata,dates,qualified/unlinked creator labels,images and review status. Unknown dates do not establish pre1971 eligibility.'
RESOLVED={99:['filename_or_title_qualification'],137:['filename_or_title_qualification']}
EXPECTED={
13:('Air, Water, Stone','John Wells (1907-2000)','1955','SOTAG : 2006/57'),
43:('Composition','John Selby-Bigge (1892-1973)','1930','SOTAG : 2005/28'),
45:('Good Shooting','Roland Penrose (1900-1984)','1939','SOTAG : 1977/48'),
97:('Untitled','Humphrey Jennings (1907-1950)','1941','SOTAG : 1982/16'),
135:('Time for Tea (Foliage Fantasy)','John Banting (1902-1972)','1934','SOTAG : 2002/3'),
173:('The Hermit Discovered','Desmond Morris (b.1928)','1948','SOTAG : 2002/4')}
def raw_capture(row):
 cap=row['capture'];raw=gzip.decompress((m.ROOT/cap['body_path']).read_bytes());assert hashlib.sha256(raw).hexdigest()==cap['receipt']['sha256'];return raw
def native_rows():
 x=m.load(RUN/'native-objects-001.json');assert not x['requests_stopped'];out={}
 for row in x['rows']:
  assert row['state']=='captured_metadata';raw=raw_capture(row);p=n.parsed(raw);soup=n.n.BeautifulSoup(raw,'html.parser');p['headings']=[h.get_text(' ',strip=True) for h in soup.select('h1,h2,h3')];p['tables']=[t.get_text(' ',strip=True) for t in soup.select('table')];assert p==row['parsed']
  title=soup.select_one('h1');fields={}
  for tr in soup.select('table tr'):
   cells=tr.select('td,th');assert len(cells)==2;fields[cells[0].get_text(' ',strip=True)]=cells[1].get_text(' ',strip=True)
  out[row['number']]=dict(row,native_title=title.get_text(' ',strip=True),native_creator=title.parent.select_one('p.uppercase').get_text(' ',strip=True),fields=fields)
 assert set(out)==set(EXPECTED);return out
def native_guard(number,row,facts):
 title,maker,date,inventory=EXPECTED[number]
 assert row['url'].startswith('https://southamptoncityartgallery.com/object/') and row['native_title']==title and row['native_creator']==maker
 fields=row['fields'];assert fields['Date']==date and fields['Acquisition Number']==inventory and fields['Credit Line']
 assert facts['title']==title and str(facts['first'])==date and str(facts['last'])==date
 normalized='/'.join(reversed(inventory.split(' : ')[1].split('/')))
 if number==13:assert normalized=='57/2006' and facts['inventory']=='56/2006' and number in HOLDS
 else:assert normalized==facts['inventory']
 return row
def physical_guard(src):
 expected={20:(89,67.2),29:(91,201.5),35:(126.4,101),56:(61.2,91.3),87:(230,200.7),110:(122.4,92),115:(37.5,55.2),136:(79.2,117.8),174:(59.3,41.9)}
 for number,dims in expected.items():
  e=src[number]['entity'];actual=[]
  for prop in ['P2048','P2049']:
   v=f.val(e,prop);assert v['unit']=='http://www.wikidata.org/entity/Q174728';actual.append(float(v['amount']))
  assert tuple(actual)==dims,(number,actual)
 for number,support in [(35,'Q12321255'),87 and (87,'Q12321255'),(174,'Q11472')]:
  es=f.statements(src[number]['entity'],'P186');values={v['mainsnak']['datavalue']['value']['id'] for v in es};assert values=={'Q296955',support}
def kidner_guard():
 x=m.load(RUN/'kidner-selected-native-001.json');rows={v['provider']:v for v in x['rows']};assert set(rows)=={'gulbenkian','flowers'}
 for row in rows.values():assert n.parsed(raw_capture(row))==row['parsed']
 t=rows['gulbenkian']['parsed']['text']
 for v in ['Brown, Blue and Violet No.2','Date 1964','Acrylic paint on canvas','Height 124,50 cm; Width 152,50 cm','Inventory no. PE191']:assert v in t
 assert "Michael Kidner's Brown, Blue and Violet No. 2 from the Southampton City Art Gallery collection" in rows['flowers']['parsed']['text']
 web=m.load(RUN/'kidner-web-research-001.json');text=json.dumps(web,ensure_ascii=False)
 for v in ['Michael Kidner (1917–2009)','Brown, Blue and Violet No. 2','Southampton City Art Gallery © The Estate']:assert v in text
 return 'https://www.southamptoncityartgallery.com/wp-content/uploads/2020/10/Shadows-and-Light-leaflet-pages.pdf'
def verified_creators():
 x=m.load(RUN/'unlinked-creator-authorities-001.json.gz');receipt=m.load(checked(x['capture_reference']));raw=gzip.decompress(checked(x['body_reference']).read_bytes());assert hashlib.sha256(raw).hexdigest()==receipt['raw_sha256'];entities=json.loads(raw)['entities']
 for row in x['rows']:
  e=entities[row['qid']];assert e==row['entity'];labels={v['value'] for v in e.get('labels',{}).values()}|{v['value'] for vs in e.get('aliases',{}).values() for v in vs};assert row['label_match'] and m.norm(row['existing_label']) in {m.norm(v) for v in labels}
 return {v['number']:v for v in x['rows']}
def build():
 src={v['number']:v for v in m.load(RUN/'source-context-001.json.gz')['rows']};rs=f.rows();cs={v['number']:v for v in m.load(RUN/'identity-001.json.gz')['comparisons']};own={v['existing_artwork_id'] for v in rs};verified=verified_creators();native=native_rows();kidner=kidner_guard();physical_guard(src);out=[];invs=collections.defaultdict(list)
 for row in rs:invs[(row['institution_id'],i.i.q.compact(row['facts']['inventory']))].append(row['number'])
 for numbers in invs.values():
  if len(numbers)>1:assert all(n in HOLDS for n in numbers)
 for row in rs:
  number=row['number'];v=row['facts'];source=src[number];art=source['artwork'];aid=art['id'];c=cs[number];assert c['source_hits'] and {h['entity_id'] for h in c['source_hits']}=={aid};hold=HOLDS.get(number)
  external=[h for h in c['hits'] if h['id'] not in own and h['same_creator']];assert not external or number in NOTES or hold,('Unreviewed comparison',number)
  issues=list(v['issues']);note=NOTES.get(number,'Exact source object,creator and museum-scoped inventory reviewed. Generic title matches do not identify different creator identities.');confidence=.8;native_url=None;native_ref=None
  if 'creator_authority_requires_reconciliation' in issues:
   author=verified[number];assert author['qid']==v['creator_qid'] and author['existing_label']==v['creator_label'];issues.remove('creator_authority_requires_reconciliation');note+=' Exact source authority verifies existing unlinked creator text only; no artist record or painter link is added.'
  for issue in RESOLVED.get(number,[]):assert issue in issues;issues.remove(issue)
  if number in native:
   nr=native_guard(number,native[number],v);native_url=nr['url'];native_ref=ref(RUN/'native-objects-001.json');confidence=.9
  elif number==35:
   native_url=kidner;native_ref=ref(RUN/'kidner-web-research-001.json');confidence=.85
  else:note+=' No exact native object corroboration is claimed. Official general collection pages are context only; the holding basis remains the referenced museum-scoped secondary object.'
  if any(h['id'] not in own and not h['same_creator'] and 'inventory' in h['hit_types'] for h in c['hits']):note+=' Bare accession collisions in other creator/collection scopes are not object identity.'
  if v['date_precision']=='unknown':note+=' Creation remains unknown and excluded from eligible-date totals. Acquisition,subject,career and artist life dates are not substituted.'
  if v['inventory'].startswith('HH'):note+=' HH is a retained historical registration prefix. Object-level City Art Centre collection evidence supports this holding; shared city venues do not establish present building or display.'
  if source.get('additional_pending_assertions'):assert hold,'Unreviewed multiple pending claims'
  if not hold:assert not issues and art['current_institution_id'] is None and art['status']=='review',('Unresolved issue',number,issues)
  out.append(dict(number=number,institution_id=row['institution_id'],existing_artwork_id=aid,facts=v,state='editorial_hold' if hold else 'approved_existing_holding',confidence=None if hold else confidence,basis=hold or 'Exact existing object ID,title/alias,creator,referenced museum-scoped inventory and chronology checked. '+note,limitation=LIMIT,derived_fields=[],retrieved_at=source['pending_assertion']['checked_at'],source_reference=source['body_reference'],source_raw_sha256=source['raw_sha256'],native_evidence_reference=native_ref,selected_native_object_url=native_url,pending_assertion_id=source['pending_assertion']['id'],additional_pending_assertion_ids=[h['id'] for h in source.get('additional_pending_assertions',[])],previous_network_assertion_id=None,previous_institution_id=art['current_institution_id'],comparison=c,source_issues=v['issues'],resolved_issues=[j for j in v['issues'] if j not in issues],existing_status=art['status']))
 assert len(out)==191;return out
def main():
 dest=RUN/'editorial-reviewed-001.json.gz';assert not dest.exists();ds=build();names=['source-context-001.json.gz','candidate-facts-001.json.gz','identity-001.json.gz','identity-citations-001.json.gz','comparison-source-context-001.json.gz','retained-primary-comparisons-001.json.gz','unlinked-creator-authorities-001.json.gz','native-probes-001.json','native-selected-001.json','native-objects-001.json','kidner-web-research-001.json','kidner-selected-native-001.json'];m.save(dest,dict(at=m.now(),decisions=ds,reviewer_reference=ref(Path(__file__).resolve()),editorial_notes_reference=ref(Path(editor.__file__).resolve()),dependencies=[ref(RUN/n) for n in names],policy='Selected existing holdings only. No new artworks,metadata,images,painter links,publication or display changes. Triptych components,attribution/accession conflicts and unresolved physical versions held.'))
 print(json.dumps(dict(approved=sum(v['state']=='approved_existing_holding' for v in ds),held=[v['number'] for v in ds if v['state']=='editorial_hold'],by_museum=dict(collections.Counter(v['institution_id'] for v in ds if v['state']=='approved_existing_holding')),unknown_dates_preserved=sum(v['state']=='approved_existing_holding' and v['facts']['date_precision']=='unknown' for v in ds))),flush=True)
if __name__=='__main__':main()
