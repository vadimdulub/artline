"""Review exact existing RWA and Ferens holdings without changing artwork metadata."""
import collections,importlib.util,json,re
from pathlib import Path
def module(name,file):
 z=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(z);z.loader.exec_module(v);return v
i=module('i','museum-expansion-britain-six-identity-20261009.py');f=i.f;s=f.s;m=f.m;RUN=f.RUN;ref=f.ref;checked=f.checked
w=module('wn','museum-expansion-britain-six-ferens-v2-20261009.py');p=module('pn','museum-expansion-britain-six-rwa-20261009.py');editor=module('ed','museum-expansion-britain-six-decisions-20261009.py');HOLDS=editor.HOLDS;NOTES=editor.NOTES
LIMIT='Confidence is an editorial assessment,not a calibrated probability. Saved Wikidata collection/location statements and their Art UK references are correlated secondary evidence,not independently fetched primary confirmation. Ferens exact native metadata is separately identified; RWA artist biographies are context only. Holdings do not establish legal ownership,current custody or current display. Preserve metadata,dates,qualified or unlinked creator labels,images and review status. Unknown dates do not establish pre1971 eligibility.'
def native_rows():
 x=m.load(RUN/'ferens-native-002.json.gz');assert not x['requests_stopped'] and not x['unprocessed_numbers'] and len(x['rows'])==101;out={}
 for v in x['rows']:
  row=m.load(checked(v['reference']));assert row['number']==v['number'];row['evidence_reference']=v['reference'];out[row['number']]=row
 return out
def rwa_rows():
 x=m.load(RUN/'rwa-native-001.json.gz');assert not x['requests_stopped'] and not x['unprocessed_creators'] and len(x['rows'])==79;out={}
 for v in x['rows']:
  row=m.load(checked(v['reference']));assert row['creator']==v['creator'];row['evidence_reference']=v['reference']
  for number in row['numbers']:assert number not in out;out[number]=row
 assert len(out)==147;return out
def native_guard(number,fields,hold):
 maker='; '.join(fields.get('Artist / Maker:',[]));description='; '.join(fields.get('Brief Description:',[]));date='; '.join(fields.get('Date/Period:',[]))
 if re.search(r'\b(?:attrib(?:uted)?|circle|workshop|school|manner|follower|unknown)\b',maker,re.I) or re.search(r'\b(?:attributed to|school of|copy after|follower of)\b',description,re.I):assert hold,'Unreviewed native maker qualification '+str(number)
 if any(int(y)>1970 for y in re.findall(r'\b(?:19|20)\d{2}\b',date)):assert hold,'Native creation later than1970 '+str(number)
 return maker,date
def build():
 src={v['number']:v for v in m.load(RUN/'source-context-001.json.gz')['rows']};rs=f.rows();cs={v['number']:v for v in m.load(RUN/'identity-001.json.gz')['comparisons']};own={v['existing_artwork_id'] for v in rs};verified={v['number']:v for v in m.load(RUN/'unlinked-creator-authorities-001.json.gz')['rows']};native=native_rows();rwas=rwa_rows();out=[];invs=collections.defaultdict(list)
 for row in rs:invs[(row['institution_id'],i.i.q.compact(row['facts']['inventory']))].append(row['number'])
 for numbers in invs.values():
  if len(numbers)>1:assert all(n in HOLDS for n in numbers),'Unreviewed repeated inventory'
 for row in rs:
  number=row['number'];v=row['facts'];source=src[number];art=source['artwork'];aid=art['id'];c=cs[number];assert c['source_hits'] and {h['entity_id'] for h in c['source_hits']}=={aid};hold=HOLDS.get(number);external=[h for h in c['hits'] if h['id'] not in own and h['same_creator']];assert not external or number in NOTES or hold,('Unreviewed same-maker comparison',number)
  issues=list(v['issues']);note=NOTES.get(number,'Exact source object,creator and museum-scoped inventory reviewed. Generic title similarities do not merge different creator identities.');confidence=.8;selected_native=None
  unrelated=[h for h in c['hits'] if h['id'] not in own and not h['same_creator'] and 'inventory' in h['hit_types']]
  if unrelated:note+=' Same accession tokens also occur in other creator/collection scopes; those returned records are not identified with this museum-qualified object.'
  if 'creator_authority_requires_reconciliation' in issues:
   author=verified[number];assert author['label_match'] and author['qid']==v['creator_qid'] and author['existing_label']==v['creator_label'];issues.remove('creator_authority_requires_reconciliation');note+=' The exact source authority verifies the existing unlinked creator text; no artist record or painter link is added.'
  if number in [126,235]:issues.remove('filename_or_title_qualification')
  if number==126:note+=' After belongs to the storm subject in After the Gale,not a copy attribution.'
  if row['institution_id']==s.IIDS[1]:
   nr=native[number]
   if nr['state']=='captured_exact_inventory':
    fields=nr['parsed']['fields'];assert len(fields['Accession No:'])==1 and w.invkey(fields['Accession No:'][0])==w.invkey(v['inventory']);native_guard(number,fields,hold);selected_native=nr['object_url'];confidence=.9
    if not hold:assert fields.get('Object Name:')==['painting'],('Unreviewed object type',number)
    note+=' Exact native accession,title,maker,creation text,description and dimensions reviewed. Native date/support/spelling variations remain evidence; no catalogue value is silently replaced. The undated display label does not establish current display.'
   else:
    assert nr['state']=='no_unique_exact_inventory_result',('Unresolved capture',number,nr['state']);note+=' The selected native inventory search returned no unique exact object; no primary object corroboration is claimed.'
  else:
   nr=rwas[number];assert nr['creator']==v['creator_label'];note+=' The official site was searched for this selected creator. Biography and general collection context do not independently confirm this exact work; the holding basis remains the exact referenced museum-scoped secondary record.'
  if v['date_precision']=='unknown':note+=' Creation remains unknown and excluded from eligible-date totals; acquisition,election,subject and artist life dates are not substituted.'
  if not hold:assert not issues and art['current_institution_id'] is None and art['status']=='review',('Unresolved issue',number,issues)
  out.append(dict(number=number,institution_id=row['institution_id'],existing_artwork_id=aid,facts=v,state='editorial_hold' if hold else 'approved_existing_holding',confidence=None if hold else confidence,basis=hold or 'Exact existing object ID,title/alias,creator,referenced museum-scoped inventory and chronology checked. '+note,limitation=LIMIT,derived_fields=[],retrieved_at=source['pending_assertion']['checked_at'],source_reference=source['body_reference'],source_raw_sha256=source['raw_sha256'],native_evidence_reference=nr['evidence_reference'],selected_native_object_url=selected_native,pending_assertion_id=source['pending_assertion']['id'],previous_network_assertion_id=None,previous_institution_id=art['current_institution_id'],comparison=c,source_issues=v['issues'],resolved_issues=[j for j in v['issues'] if j not in issues],existing_status=art['status']))
 assert len(out)==248;return out
def main():
 dest=RUN/'editorial-reviewed-001.json.gz';assert not dest.exists();ds=build();names=['source-context-001.json.gz','candidate-facts-001.json.gz','identity-001.json.gz','identity-citations-001.json.gz','comparison-source-context-001.json.gz','retained-primary-comparisons-001.json.gz','unlinked-creator-authorities-001.json.gz','ferens-native-002.json.gz','rwa-native-001.json.gz','native-probes-001.json','source-discovery-002.json','ferens-collection-probe-001.json'];m.save(dest,dict(at=m.now(),decisions=ds,reviewer_reference=ref(Path(__file__).resolve()),editorial_notes_reference=ref(Path(editor.__file__).resolve()),dependencies=[ref(RUN/n) for n in names],policy='Selected existing holdings only. No new artworks,metadata,images,painter links,publication or display changes. Unknown dates and qualified makers remain explicit. Series of separate panels are distinguished from paired sides and aggregate components.'))
 print(json.dumps(dict(approved=sum(v['state']=='approved_existing_holding' for v in ds),held=[v['number'] for v in ds if v['state']=='editorial_hold'],by_museum=dict(collections.Counter(v['institution_id'] for v in ds if v['state']=='approved_existing_holding')),unknown_dates_preserved=sum(v['state']=='approved_existing_holding' and v['facts']['date_precision']=='unknown' for v in ds))),flush=True)
if __name__=='__main__':main()
