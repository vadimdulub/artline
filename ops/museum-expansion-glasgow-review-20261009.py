"""Review exact Glasgow objects without converting storage labels into branch holdings."""
import collections,gzip,hashlib,importlib.util,json
from pathlib import Path
def module(name,file):
 z=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(z);z.loader.exec_module(v);return v
f=module('f','museum-expansion-glasgow-facts-v2-20261009.py');s=f.s;m=f.m;RUN=f.RUN;ref=f.ref;checked=f.checked
HOLDS={
 6:'Creation remains unknown. The native description identifies Scargill as NUM president and records purchase in1985; do not treat this as pre1971 eligibility. Resolve creation scope before selecting this modern portrait.',
 11:'Saved image filename qualifies Richard Phelps as attributed to; current primary artist link is unqualified. Retain attribution discrepancy for a separate explicit metadata review.',
 38:'Denune lady portraits have different institution inventories but close physical dimensions76.2x63.5cm versus73.6x60.8cm. Sitter and canvas identity need stronger comparison; titles and different catalogues alone do not settle this.',
 57:'Native description says attributed to Juan de las Roelas although current primary artist link is unqualified. Preserve qualified source wording and defer metadata reconciliation.',
 71:'Lavery Pavlova versions include Tate Le Mort du Cygne and an unverified Anna Pavlova as The Swan record. Glasgow1581 is198.1x144.8cm versus Tate198.1x146.7cm; close dimensions do not resolve physical version or duplicate record.',
 117:'Likely duplicate of existing WikiArt1903 Willowood record a7e84ad0-4640-5352-bb17-f2692b5a0700. Original gesso panel, possible details and modern replica require physical-object reconciliation. Do not count both.',
 208:'Knox Nelson Monument versions have Kelvingrove3338 and HunterianGLAHA:43921 inventories, but near-identical67.6x90.5cm and67.3x90.2cm dimensions. Possible versions or historical transfer require stronger composition/provenance evidence.',
 227:'Native maker label A Reddoch attributed to and saved filename attributed to disagree with unqualified existing A.Reddock artist link. Preserve the qualified evidence; no automatic attribution rewrite.',
 248:'Native record878 lists Joseph Adam and Robert Henry Roe as makers. Current source-derived record only links Roe. Preserve co-creator conflict and defer full object/attribution review.'
}
NOTES={
 9:'Cadell Reflections2194 is116.8x101.6cm,c1915; Girl in Blue–Reflections2793 is61x50.8cm,c1912. Distinct source objects and substantially different physical canvas dimensions resolve the near-title match.',
 14:'Brothers1934 comparison is by Malvin Gray Johnson; this Little Brother is by Norah Neilson Gray. Different creator identities, not a shared surname match.',
 34:'Native portrait title Charles Cameron Baillie and self-portrait description identify the same PP.1981.39. Native circa1921–1960 retained as evidence; existing unknown creation unchanged.',
 39:'Native Mrs J M Robertson is explicitly mother of John M Robertson. Inventory1430 and John Moir support the same object; retain existing Mrs Elizabeth Murdoch Robertson title.',
 52:'Native twentieth-century wording and1965 gift are evidence, not a creation year. Preserve unknown date.',
 59:'Native full maker Francis Harrison Howard matches source Francis Howard. Mrs Harry Payne Whitney and Mrs Williams-Hope hits have different makers Howard Gardiner Cushing and Charles Howard Hodges.',
 62:'Native circa1925–1926 and imported1926 differ in precision. Same inventory1679 and maker; preserve both as evidence without changing catalogue date.',
 72:'Native circa1886–1939 remains evidence; existing unknown creation unchanged.',
 80:'Native object title Caronia and inventoryT.1973.10.ac match; native omits creation date. Source circa1948 remains unchanged; acquisition-like inventory digits are not creation.',
 83:'Native full maker Andrew Gibbon Williams differs from Kyffin Williams,Margaret Lindsay Williams and Benjamin Williams Leader hits. Native twentieth-century date does not establish cutoff; existing date stays unknown.',
 96:'Native maker field lists Upper Clyde Shipbuilders, but description explicitly credits Charles Keith Miller1873. Retain both source fields. Alfred Jacob Miller hits are different creators.',
 112:'Native catalogueT.2008.8 confirms Tom Purvis work. Out on Loan is custody wording, not loss of collection holding. Accept network collection only, no loan destination, custody or display claim; preserve unknown creation.',
 124:'Exact native inventoryPP.1978.121.5 and description by John Gibson match saved object creator and existing unlinked label. Keep that object-level label; no artist identity/link inference. Native1768–1852 coincides with creator lifespan in saved filename and is not accepted as creation.',
 125:'After Rehearsal is the literal subject/title, not an after attribution; already accepted network holding is preserved.',
 136:'Native Location says Kelvingrove Picture Promenade while secondary source says Resource Centre. Accept only broader Glasgow Museums collection; no fresh display or branch assignment.',
 173:'Native1886 is retained evidence for TEMP.5903; existing unknown creation remains unchanged.',
 188:'Native3139 explicitly offers John Dalrymple,2nd Earl of Stair OR John Campbell,Duke of Argyll. Exact inventory supports object identity, not a resolved sitter. Retain both labels in citation; do not rewrite title. John McGill comparison is a different named portrait.',
 204:'Native2593 says My Garden Under Snow,1940; catalogue says Urban Garden under Snow,c1946. Exact inventory,maker and garden subject support object identity. Retain native narrative/date and legacy values; no silent metadata rewrite.',
 205:'Native NR.161 says1880 or1889 while existing date is1880–1889. Preserve disjunctive source wording in evidence, not as a silent date correction.',
 213:'Children Coming from School is the subject/title, not a school attribution. Existing network holding preserved.',
 217:'P1679 retrieval-date and English-language qualifiers describe the reference, not creation. No new ArtUK fetch.',
 229:'Native circa1940s is retained evidence; existing unknown creation remains unchanged.',
 230:'Native late1890s is retained evidence; existing unknown creation remains unchanged.',
 234:'Fresh official Glasgow Life Dalí page identifies the1951 Christ of St John of the Cross,city acquisition1952 and Kelvingrove association. This independently supports the otherwise Wikipedia-referenced P195 claim. Observed Navigator object1 link was not fetched after access hold.',
 238:'Exact sourceQ119138185,inventory1790 and creatorQ21457017/image filename James Hamilton1853–1894 match existing unlinked creator label. Preserve label; do not link a different same-name painter.'
}
def primary_rows():
 return [v for v in m.load(RUN/'comparison-source-context-001.json.gz')['rows'] if v.get('format')=='glasgow_html']
def validate_raw():
 cache={}
 for name in ['source-context-001.json.gz','comparison-source-context-001.json.gz']:
  for row in m.load(RUN/name)['rows']:
   if not row.get('body_reference'):continue
   path=checked(row['body_reference']);key=str(path)
   if key not in cache:
    raw=gzip.decompress(path.read_bytes()) if path.suffix=='.gz' else path.read_bytes();cache[key]=(hashlib.sha256(raw).hexdigest(),raw)
   digest,raw=cache[key];assert digest==row['raw_sha256']
   if name.startswith('source-'):assert json.loads(raw)['entities'][row['source_id']]==row['entity']
 return len(cache)
def build():
 initial=m.load(RUN/'initial-scope-001.json.gz');sources={v['number']:v for v in m.load(RUN/'source-context-001.json.gz')['rows']};facts,errors=f.rows();assert not errors;identity=m.load(RUN/'identity-002.json.gz');assert identity['rows']==facts;comps={v['number']:v for v in identity['comparisons']};primary=primary_rows();out=[]
 for row in facts:
  num=row['number'];src=sources[num];a=src['artwork'];fact=row['facts'];c=comps[num];own=a['id'];assert {v['entity_id'] for v in c['source_hits']}=={own};natives=[v for v in primary if v['artwork_id']==own];assert len({(v['source_url'],v['raw_sha256']) for v in natives})<=1
  if natives:assert natives[0]['parsed']['fields']['ID Number']==fact['inventory']
  preserved=a['current_institution_id']==s.NETWORK;state='preserved_existing_network_holding' if preserved else 'editorial_hold' if num in HOLDS else 'approved_existing_holding';target=s.NETWORK if src['institution_id']==s.IIDS[0] else src['institution_id'];assert a['current_institution_id'] in [None,s.NETWORK]
  if preserved:assert natives and any(h['artwork_id']==own and h['institution_id']==s.NETWORK and h['review_state']=='accepted' and h['superseded_by'] is None for h in initial['snapshot']['assertions'])
  unresolved=[v for v in row['issues'] if v not in ['existing_network_holding_requires_review']]
  if state=='approved_existing_holding':assert not unresolved or num in [124,234,238]
  basis=('Preserve existing exact-object accepted network holding. ' if preserved else 'Exact saved object QID,title,creator and collection-qualified inventory support the holding. ')
  if natives:basis+='Checksum-verified retained official Navigator object record corroborates collection membership; source location wording is preserved separately. '
  else:basis+='Referenced Wikidata/ArtUK statements are correlated secondary evidence, not independently fetched ArtUK confirmation. '
  if target==s.NETWORK:basis+='Official Glasgow Life collection/Resource Centre pages establish the institutional relationship. Only network membership is accepted; Resource Centre storage is unresolved. '
  basis+=NOTES.get(num,'')
  limitation='Museum collection holding only; no legal ownership,current custody,current display,room,or venue claim. Source dates and maker/title conflicts are evidence only; existing metadata,images,artist links and review status remain unchanged. Confidence is editorial,not a calibrated probability.'
  if fact['date_precision']=='unknown':limitation+=' Unknown creation is retained and excluded from pre1971-eligible totals.'
  supersede=[h['id'] for h in initial['snapshot']['assertions'] if h['artwork_id']==own and h['institution_id']==target and h['review_state']=='review' and h['superseded_by'] is None and h['claim_type']=='holding'] if state=='approved_existing_holding' else []
  if src['institution_id']==s.IIDS[0]:assert src['pending_assertion']['id'] not in supersede
  retrieved=src['pending_assertion']['checked_at'];nativeproof=[{k:v[k] for k in ['citation_id','source_url','source_id','body_reference','raw_sha256','parsed']} for v in natives]
  out.append(dict(number=num,state=state,institution_id=target,source_institution_id=src['institution_id'],source_museum_qid=src['museum_qid'],existing_artwork_id=own,previous_institution_id=a['current_institution_id'],pending_assertion_id=src['pending_assertion']['id'],supersede_assertion_ids=supersede,facts=fact,comparison=c,source_reference=src['body_reference'],source_raw_sha256=src['raw_sha256'],native_evidence=nativeproof,dali_evidence_reference=ref(RUN/'dali-native-001.json') if num==234 else None,retrieved_at=retrieved,confidence=.95 if natives or num==234 else .85,basis=basis,limitation=limitation,hold_reason=HOLDS.get(num),unresolved_parser_issues=unresolved,metadata_review_note=NOTES.get(num)))
 assert collections.Counter(v['state'] for v in out)=={'preserved_existing_network_holding':183,'approved_existing_holding':61,'editorial_hold':9};return out
def main():
 dest=RUN/'editorial-reviewed-001.json.gz';assert not dest.exists();bodies=validate_raw();decisions=build();deps=[RUN/v for v in ['initial-scope-001.json.gz','source-context-001.json.gz','candidate-facts-002.json.gz','identity-002.json.gz','identity-citations-002.json.gz','comparison-source-context-001.json.gz','native-probes-001.json','native-selected-searches-001.json','dali-native-001.json']];m.save(dest,dict(at=m.now(),decisions=decisions,reviewer_reference=ref(Path(__file__).resolve()),dependencies=[ref(v) for v in deps],verified_raw_bodies=bodies,policy='Selected holding review.183 network records preserved;61 previously unlinked objects accepted;9 held. No branch relocation. Retain every unresolved Resource Centre assertion. No duplicate artwork creation or metadata change.'))
 approved=[v for v in decisions if v['state']=='approved_existing_holding'];print(json.dumps(dict(states=dict(collections.Counter(v['state'] for v in decisions)),targets=dict(collections.Counter(v['institution_id'] for v in approved)),unknown=sum(v['facts']['date_precision']=='unknown' for v in approved),superseded=sum(len(v['supersede_assertion_ids']) for v in approved),raw_bodies=bodies)),flush=True)
if __name__=='__main__':main()
