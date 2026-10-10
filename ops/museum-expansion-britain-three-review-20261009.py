"""Individual Cardiff/Bristol decisions, preserving network, version and date uncertainty."""
import collections,gzip,hashlib,importlib.util,json,re
from pathlib import Path
z=importlib.util.spec_from_file_location('i',Path(__file__).with_name('museum-expansion-britain-three-identity-20261009.py'));i=importlib.util.module_from_spec(z);z.loader.exec_module(i);f=i.f;s=f.s;m=f.m;RUN=f.RUN;ref=f.ref;checked=f.checked
NETWORK='d55f4987-94f6-5e4c-8d9b-c2c1b1fa2daf'
HOLDS={31:'Le Bas Head of a Boy has a same-maker/same-title Tullie comparison,1930-1940,34.4x24.5cm versus Cardiff1929,31x23.7cm. These modest size/date differences do not by themselves resolve a potential physical-version identity.',33:'Landscape verso NMW A19885R and recto NMW A19885 share a base inventory and physical support. The native search has no separate exact verso inventory. Keep verso pending to avoid counting the reverse as another resolved physical object.',139:'Trevelyan Durham Wharf1935 has another same-maker/same-title record dated1946 at Pallant, with no comparison dimensions. The native Cardiff record confirms its own inventory, but a date difference alone does not resolve the versions.',233:'The source image filename qualifies the Berchet attribution. The existing unlinked creator label is unqualified, while the title only records former attribution to Verrio. Keep pending for separate attribution reconciliation.'}
NOTES={
12:'After the Blast describes the subject, not an after-artist attribution. The native record identifies Vincent Evans without a maker qualification.',
23:'Cedric Morris is distinct from Morris Kantor and Philip Richard Morris; the generic self-portrait comparisons name different makers.',
37:'Arthur Ralph Middleton Todd is distinct from Daphne Todd. The portrait sitter and dates also differ.',
44:'David Jones differs from Samuel Maurice Jones and Ernest Yarrow Jones; overlapping landscape titles do not identify the same maker.',
60:'Existing title explicitly preserves the after-Nicolas-Poussin relationship. The native object identifies John Dyer1730,NMW A(L)1512. This is the Dyer copy, not a Poussin original; the loan inventory prefix is retained without an ownership assertion.',
66:'Mornewick/Mornewicke spelling variants retain the exact inventory and John Orlando Parry sitter. The existing unlinked label matches the verified creator authority; no painter link is made.',
77:'Native NMW A440 identifies the complete1854 coastal landscape by Dessoulavy. The existing title includes detail, but only this one source/inventory object is linked; no separate crop or additional artwork is created.',
80:'Arthur George Walker is distinct from Henry O. Walker; the Goscombe John sitter differs from the Evans family portrait.',
91:'Ceri Richards is distinct from Richard Peter Richards; the pipe and donkey subjects differ.',
106:'Native creator WILLIAMS, William Oliver corresponds to existing William Oliver on this exact inventory and sitter; the native label is retained separately without altering the painter link.',
115:'T.H. Thomas is Thomas Henry Thomas, not Thomas Rowlandson. The latter unnamed drawing is not this Grassholm bird scene.',
117:'Percy Elizabeth Flora Thomas differs from Thomas Sully and Thomas Rowlandson; the Vulliamy sitter and1902 portrait are distinct.',
125:'The existing title explicitly identifies an Edmund Gustavus Müller copy after William James Müller. Preserve the copy relationship, maker, circa1845 date and K4490 inventory; do not substitute the prototype.',
131:'Native NMW A19885 is the physical Landscape support. Link this existing recto record only; leave the separately catalogued verso19885R pending. The Harvey-named comparison makers are Alfred Harvey Moore, George Harvey and John Rabone Harvey, not Gertrude Harvey.',
133:'Llewellyn Petley-Jones differs from Jack Jones, Calvert Jones and Edward Burne-Jones; their sitters and dates differ.',
140:'Isaac John Williams is distinct from J.E.Hughes Williams, William Williams, Benjamin Williams Leader, Fred Williams, Edward Williams and George Augustus Williams. The exact native1893 inventory identifies this landscape.',
142:'Chamberlain Cardiff1949 canvas102.3x76.8cm differs from The Fishing Net34.7x29.5cm,with distinct title,inventory and physical format.',
185:'The Cardiff Burton portrait95.5x87cm differs substantially from the Parliamentary127x76.2cm canvas. Same sitter does not merge these distinct physical formats.',
193:'Arthur Wilde Parsons is distinct from Alfred Parsons. His own1899 Seascape59x90cm differs in subject,date and format from the1915 Bristol landscape72.6x122.5cm.',
229:'Board School Children describes children at a school, not a school-of-artist attribution. Native Barnett Samuel Marks1874 is unqualified.',
237:'Native full painting NMW A5089 measures79x104.2cm,created1911. Its separate sketch NMW A5090 measures25x34cm; source titles, formats and inventories distinguish the two.',
254:'Cardiff Maitland Thames painting22.9x32.7cm differs from York Boats Moored on the Thames17.1x30.5cm. The selected fresh comparison entity confirms a different support aspect and inventory; no date is inferred for York.',
257:'T.H.Thomas is Thomas Henry Thomas,not Thomas Rowlandson; the biblical subject is not the unnamed Rowlandson object.',
266:'Mornewick/Mornewicke spelling variants retain the exact inventory and Reverend John Evans sitter. Existing unlinked creator text remains unchanged.',
270:'Thomas Henry Thomas differs from Thomas Rowlandson. The Elijah subject is distinct from the Rowlandson fable/miser subjects and unnamed drawing.',
275:'Cardiff Fedden1946 Fruit and Flowers61x50.8cm differs from the1948 Flowers1,54.6x44.5cm,and Flowers2,75x49.5cm. Different dates,inventories and formats support separate works.',
278:'The existing record is already published. This pass adds only the supported holding and preserves that historical publication status; it does not publish or unpublish any work.',
283:'Native sketch NMW A5090 measures25x34cm and explicitly names the separate full painting. NMW A5089 measures79x104.2cm. Preserve the sketch title and circa1911 catalogue date.'}
HOLDS.update({85:'Exact native K1388 names both Charles Branwhite and J.Hardy as artists. The current record has only Branwhite; retain both source labels and defer the holding until creator roles are reconciled.',157:'Exact native K503 explicitly describes a painting by two artists:William H.Hopkins and Edmund Havell II. The current record names Hopkins only. Defer until this shared authorship is reconciled.'})
COMMON='Exact existing Wikidata object ID, literal title/alias, creator identity, creation evidence and museum-scoped inventory agree. Referenced current collection and location statements name the same specific museum. No competing source-ID or inventory collision. '
LIMIT='Editorial confidence is not a calibrated probability. Wikidata collection/location claims are correlated secondary evidence, not independent confirmation. Art UK references were not newly fetched; its access hold remains. Native Museum Wales object evidence corroborates only its own stated facts; the source museum mapping remains separately identified. Holdings do not assert legal ownership, physical custody or current display. Preserve all metadata, dates, creator links, images and historical statuses.'

def native_rows():
 capture=m.load(RUN/'cardiff-native-001.json.gz');assert not capture['requests_stopped'] and not capture['unprocessed_numbers'];assert len(capture['rows'])==134
 out={}
 for v in capture['rows']:
  p=checked(v['reference']);r=m.load(p);assert r['number']==v['number'];out[r['number']]=r
 return out

def build():
 src=m.load(RUN/'source-context-001.json.gz');srcby={v['number']:v for v in src['rows']};rs=f.rows();identity=m.load(RUN/'identity-001.json.gz');comps={v['number']:v for v in identity['comparisons']};own={v['existing_artwork_id'] for v in rs};verified={v['number']:v for v in m.load(RUN/'unlinked-creator-authorities-001.json.gz')['rows']};native=native_rows();network=m.load(RUN/'bristol-network-context-001.json.gz');assert len(network['rows'])==123
 cap=RUN/'comparison-authority-capture-001';raw=gzip.decompress((cap/'body.json.gz').read_bytes());assert hashlib.sha256(raw).hexdigest()==m.load(cap/'receipt.json')['raw_sha256'];comparison_entities=json.loads(raw)['entities'];assert comparison_entities['Q119781257']['claims']['P2048'][0]['mainsnak']['datavalue']['value']['amount']=='+17.1'
 coartists=m.load(RUN/'bristol-multiple-creators-context-001.json.gz')['rows'];assert {v['number'] for v in coartists}=={85,157}
 for v in coartists:checked(v['body_reference'])
 assert 'Artist : HARDY, J' in coartists[0]['text'] and 'Artist : HAVELL, Edmund II' in coartists[1]['text'] and 'painted by two artists' in coartists[1]['text']
 out=[];invs=set()
 for row in rs:
  number=row['number'];v=row['facts'];source=srcby[number];art=source['artwork'];c=comps[number];aid=art['id'];key=(row['institution_id'],i.i.q.compact(v['inventory']));assert key not in invs;invs.add(key);assert c['source_hits'] and {h['entity_id'] for h in c['source_hits']}=={aid}
  in_network=art['current_institution_id']==NETWORK;hold=HOLDS.get(number)
  if in_network:
   hold='Already accepted in the wider Bristol Museums network under exact native catalogue evidence. Network and specific branch are different authorities. Preserve the123 accepted network holdings and defer branch reassignment until object-level branch evidence resolves it. No double count or institution merge.'
  external=[h for h in c['hits'] if h['id'] not in own and (h['same_creator'] or 'inventory' in h['hit_types'])];assert not external or number in NOTES or hold
  unresolved=list(v['issues']);note=NOTES.get(number,'No unresolved outside-target same-maker/version comparison. Specific source identity,inventory and title retained; generic within-batch titles do not merge different creators.')
  if 'creator_authority_requires_reconciliation' in unresolved:
   author=verified[number];assert author['label_match'] and author['qid']==v['creator_qid'] and author['existing_label']==v['creator_label'];unresolved.remove('creator_authority_requires_reconciliation');note+=' Existing unlinked creator text is verified against its exact authority; no painter link is added.'
  if number in [12,60,125,229]:unresolved.remove('filename_or_title_qualification')
  if number==278:assert art['status']=='published';unresolved.remove('existing_nonreview_status_requires_review')
  native_ref=None;confidence=.8;basis=COMMON+note
  if number in native:
   nr=native[number]
   if nr['state']=='captured_exact_inventory':
    p=nr['parsed'];assert p['fields']['Item Number']==v['inventory'] and p['fields']['Collection Area']=='Art';assert len(p['creators'])==1 and p['creators'][0]['role']=='Role: Artist';assert not re.search(r'\b(?:attributed|circle|workshop|school|manner|follower)\b',p['creators'][0]['name'],re.I)
    native_ref=ref(RUN/'cardiff-selected'/('%03d.json'%number));confidence=.9;basis+=' Exact native Museum Wales inventory,title and creator were reviewed,including abbreviated and spelling variants. Native dates,biography,acquisition and location fields are preserved separately; none replaces catalogue metadata.'
    if p['fields'].get('Location','').startswith('Currently on loan'):basis+=' Native loan status is preserved as evidence; this remains a collection association without a present-custody or display claim.'
    periods=[cc['period'] for cc in p['creators'] if cc['period']];assert not any(re.fullmatch(r'Period: (?:19[7-9]\d|20\d\d)(?: ca)?',p) and not p.startswith('Period: 1970') for p in periods),'Explicit post1970 native creation needs review'
   else:assert number==33 and hold
  if v['date_precision']=='unknown':basis+=' Unknown or broad creation dates remain unknown in the catalogue and are excluded from eligible-date counts; no lifespan or acquisition year is used as a creation date.'
  if v['inventory'].startswith('NMW A(L)'):basis+=' Preserve the literal loan-series inventory prefix; no ownership is inferred.'
  if not hold:assert not unresolved and art['current_institution_id'] is None and art['status'] in ['review','published']
  out.append(dict(number=number,institution_id=row['institution_id'],existing_artwork_id=aid,facts=v,state='editorial_hold' if hold else 'approved_existing_holding',confidence=None if hold else confidence,basis=hold or basis,limitation=LIMIT,derived_fields=[],retrieved_at=source['pending_assertion']['checked_at'],source_reference=source['body_reference'],source_raw_sha256=source['raw_sha256'],native_evidence_reference=native_ref,pending_assertion_id=source['pending_assertion']['id'],comparison=c,source_issues=v['issues'],resolved_issues=[j for j in v['issues'] if j not in unresolved],existing_status=art['status']))
 assert len(out)==284 and sum(v['state']=='approved_existing_holding' for v in out)==155
 assert collections.Counter(v['institution_id'] for v in out if v['state']=='approved_existing_holding')==dict(zip(s.IIDS,[131,24]))
 return out

def main():
 dest=RUN/'editorial-reviewed-002.json.gz';assert not dest.exists();ds=build();names=['source-context-001.json.gz','candidate-facts-001.json.gz','identity-001.json.gz','identity-citations-001.json.gz','comparison-source-context-001.json.gz','unlinked-creator-authorities-001.json.gz','native-probes-001.json','cardiff-native-001.json.gz','bristol-network-context-001.json.gz','bristol-multiple-creators-context-001.json.gz','comparison-authority-capture-001/receipt.json','comparison-authority-capture-001/body.json.gz','source-access-holds-001.json','review-revision-001.json'];m.save(dest,dict(at=m.now(),decisions=ds,reviewer_reference=ref(Path(__file__).resolve()),dependencies=[ref(RUN/n) for n in names],policy='155 existing holding links:131 Cardiff,24 Bristol. Preserve123 accepted Bristol network holdings;six other version/attribution cases held. Earlier157-link draft was revised before any database write after native co-artist evidence was found. No new artworks,metadata,dates,images,painter or publication changes.'))
 print(json.dumps(dict(approved=155,held=129,network_holds=123,other_holds=sorted(HOLDS),unknown_dates=sum(v['facts']['date_precision']=='unknown' for v in ds if v['state']=='approved_existing_holding'),published_preserved=sum(v['existing_status']=='published' for v in ds if v['state']=='approved_existing_holding'))),flush=True)
if __name__=='__main__':main()
