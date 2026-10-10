"""Individual Williamson and Perth holdings with qualified source and branch evidence."""
import collections,gzip,hashlib,importlib.util,json,re
from pathlib import Path
def module(name,file):
 z=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(z);z.loader.exec_module(v);return v
i=module('i','museum-expansion-britain-five-identity-20261009.py');f=i.f;s=f.s;m=f.m;RUN=f.RUN;ref=f.ref;checked=f.checked
w=module('wn','museum-expansion-britain-five-williamson-v2-20261009.py');p=module('pn','museum-expansion-britain-five-perth-retained-20261009.py');editor=module('ed','museum-expansion-britain-five-decisions-20261009.py');HOLDS=editor.HOLDS;NOTES=editor.NOTES;NETWORK=s.NETWORK
LIMIT='Confidence is an editorial assessment,not a calibrated probability. Saved Wikidata collection/location claims are correlated secondary evidence,not independent primary confirmation. MDS is museum-supplied network evidence. Native facts and uncertainty remain explicit. Art UK and Perth catalogue access holds remain. Holdings do not assert ownership,current custody or current display. Preserve artwork metadata,dates,creator links,images and review status.'
def native_rows():
 x=m.load(RUN/'williamson-native-002.json.gz');assert not x['requests_stopped'] and not x['unprocessed_numbers'] and len(x['rows'])==126;out={}
 for v in x['rows']:
  row=m.load(checked(v['reference']));assert row['number']==v['number'];row['evidence_reference']=v['reference'];out[row['number']]=row
 for row in m.load(RUN/'williamson-recovery-001.json')['rows']:
  assert out[row['number']]['state']=='capture_error';row['evidence_reference']=ref(RUN/'williamson-recovery-001.json');out[row['number']]=row
 for row in m.load(RUN/'perth-retained-native-001.json.gz')['rows']:
  row['evidence_reference']=ref(RUN/'perth-retained-native-001.json.gz');out[row['number']]=row
 assert len(out)==244;return out
def perth_object(row):
 objects=row['objects']
 if row['number']==63:
  selected=[v for v in objects if v['url']=='https://museumdata.uk/objects/e87d3967-3b84-3451-97a4-5ade3331525c'];assert len(objects)==2 and len(selected)==1;return selected[0]
 return objects[0] if len(objects)==1 else None
def native_guard(number,fields,hold,perth=False):
 maker='; '.join(fields.get('Object production person' if perth else 'Maker',[]))
 if re.search(r'\b(?:attrib(?:uted)?|circle|workshop|school|manner|follower|unknown)\b',maker,re.I):assert hold,'Unreviewed maker qualification '+str(number)
 date='; '.join(fields.get('Object production note' if perth else 'Date Made',[]))
 # MDS production notes can include later catalogue cross references. Inspect the
 # leading creation expression only; acquisition and artist life dates are separate.
 years=re.findall(r'\b(?:19|20)\d{2}\b',date) if not perth else re.findall(r'\b(?:19|20)\d{2}\b',date.split(';')[0])
 if any(int(y)>1970 for y in years):assert hold,'Native creation later than1970 '+str(number)
 return maker,date
def build():
 src={v['number']:v for v in m.load(RUN/'source-context-001.json.gz')['rows']};rs=f.rows();cs={v['number']:v for v in m.load(RUN/'identity-001.json.gz')['comparisons']};own={v['existing_artwork_id'] for v in rs};verified={v['number']:v for v in m.load(RUN/'unlinked-creator-authorities-001.json.gz')['rows']};native=native_rows();network=m.load(RUN/'perth-network-context-001.json.gz');neth={v['assertion']['artwork_id']:v for v in network['rows'] if v['assertion']['review_state']=='accepted'};assert len(neth)==34;out=[];invs=set()
 for row in rs:
  number=row['number'];v=row['facts'];source=src[number];art=source['artwork'];aid=art['id'];c=cs[number];key=(row['institution_id'],i.i.q.compact(v['inventory']));assert key not in invs;invs.add(key);assert c['source_hits'] and {h['entity_id'] for h in c['source_hits']}=={aid};hold=HOLDS.get(number);external=[h for h in c['hits'] if h['id'] not in own and(h['same_creator'] or 'inventory' in h['hit_types'])];assert not external or number in NOTES or hold,('Unreviewed comparison',number)
  issues=list(v['issues']);note=NOTES.get(number,'Exact creator and museum-scoped identity reviewed. Generic title similarities do not merge distinct maker identities.');confidence=.8;nr=native[number];in_network=art['current_institution_id']==NETWORK;selected_native=None
  if 'creator_authority_requires_reconciliation' in issues:
   author=verified[number];assert author['label_match'] and author['qid']==v['creator_qid'] and author['existing_label']==v['creator_label'];issues.remove('creator_authority_requires_reconciliation');note+=' Existing unlinked creator label matches the verified exact authority; no painter link is added.'
  if number in [21,99,116]:issues.remove('filename_or_title_qualification')
  if number==55:
   assert art['accession_number'] is None;issues.remove('missing_catalogue_inventory');issues.remove('source_catalogue_date_mismatch')
  if row['institution_id']==s.IIDS[0]:
   if nr['state']=='captured_exact_inventory':
    fields=nr['parsed']['fields'];assert fields['From:']==['Williamson Art Gallery and Museum'];assert len(fields['Object number'])==1 and w.invkey(fields['Object number'][0])==w.invkey(v['inventory']);native_guard(number,fields,hold);confidence=.9;selected_native=nr['object_url'];note+=' Official exact object metadata reviewed; inventory colon/period and letter case are normalized for comparison only. Raw titles,maker labels,dates,materials,dimensions and rights labels remain separate evidence.'
   else:
    assert nr['state']=='no_unique_exact_inventory_result';note+=' The public native inventory search did not return one exact object; approval uses referenced saved object evidence without claiming native corroboration.'
  else:
   obj=perth_object(nr)
   if obj is not None:
    fields=obj['fields'];assert fields['Collection']==['Culture Perth & Kinross'] and fields['Object number']==[v['inventory']];native_guard(number,fields,hold,True);selected_native=obj['url'];confidence=.85
    if not hold:
     assert any('painting' in t for t in fields.get('Object name',[])),('Not painting',number)
     assert any('fine art' in t.lower() for t in fields.get('Associated concept',[])),('No fine-art context',number)
    note+=' Exact museum-supplied MDS inventory,maker,title,production and Fine Art fields reviewed. Gallery assignment is an editorial inference combining that object evidence,the official2023 transition to Perth Art Gallery including the Fergusson Collection,and exact referenced Wikidata claims naming the gallery. Network and branch remain separate authorities. Frame dimensions are not treated as support dimensions.'
   elif nr['objects']:assert hold
   else:note+=' The saved museum-supplied inventory search has no exact object. The referenced secondary record names this specific gallery and its scoped accession; no primary object confirmation is claimed. The official gallery transition is context only.'
  net_assertion=None
  if in_network:
   assert aid in neth;net_assertion=neth[aid]['assertion']['id']
   if not hold:
    assert selected_native and row['institution_id']==s.IIDS[1];issues.remove('existing_institution_requires_review');confidence=.85;note+=' Supersede only the accepted broader network assertion and selected pending branch assertion. Preserve their evidence and all other unaccepted historical assertions.'
  if v['date_precision']=='unknown':note+=' The creation date remains unknown,does not enter eligible-date counts,and is not inferred from acquisition or artist life dates.'
  if not hold:assert not issues and art['current_institution_id'] in [None,NETWORK] and art['status']=='review',('Unresolved issue',number,issues)
  out.append(dict(number=number,institution_id=row['institution_id'],existing_artwork_id=aid,facts=v,state='editorial_hold' if hold else 'approved_existing_holding',confidence=None if hold else confidence,basis=hold or 'Exact existing object ID,title/alias,creator identity,referenced museum-scoped inventory and chronology checked. '+note,limitation=LIMIT,derived_fields=[],retrieved_at=source['pending_assertion']['checked_at'],source_reference=source['body_reference'],source_raw_sha256=source['raw_sha256'],native_evidence_reference=nr['evidence_reference'],selected_native_object_url=selected_native,pending_assertion_id=source['pending_assertion']['id'],previous_network_assertion_id=net_assertion,previous_institution_id=art['current_institution_id'],comparison=c,source_issues=v['issues'],resolved_issues=[j for j in v['issues'] if j not in issues],existing_status=art['status']))
 assert len(out)==244;return out
def main():
 dest=RUN/'editorial-reviewed-001.json.gz';assert not dest.exists();ds=build();names=['source-context-001.json.gz','candidate-facts-001.json.gz','identity-001.json.gz','identity-citations-001.json.gz','comparison-source-context-001.json.gz','unlinked-creator-authorities-001.json.gz','williamson-native-002.json.gz','williamson-recovery-001.json','perth-network-context-001.json.gz','perth-retained-native-001.json.gz','perth-catalogue-availability-001.json'];m.save(dest,dict(at=m.now(),decisions=ds,reviewer_reference=ref(Path(__file__).resolve()),editorial_notes_reference=ref(Path(editor.__file__).resolve()),dependencies=[ref(RUN/n) for n in names],policy='Selected existing holding links and explicit network-to-branch refinements only. No new artworks,metadata,images,painter links,publication or display changes. Preserve components,qualified makers,source conflicts and unknown dates.'))
 print(json.dumps(dict(approved=sum(v['state']=='approved_existing_holding' for v in ds),held=[v['number'] for v in ds if v['state']=='editorial_hold'],by_museum=dict(collections.Counter(v['institution_id'] for v in ds if v['state']=='approved_existing_holding')),branch_refinements=sum(v['state']=='approved_existing_holding' and bool(v['previous_network_assertion_id']) for v in ds))),flush=True)
if __name__=='__main__':main()
