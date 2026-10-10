"""Editorial review of91 Royal Collection objects, including creator and version conflicts."""
import collections,gzip,hashlib,importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('f',Path(__file__).with_name('museum-expansion-royal-facts-20261009.py'));f=importlib.util.module_from_spec(z);z.loader.exec_module(f);s=f.s;m=f.m;RUN=f.RUN;ref=f.ref;checked=f.checked
HOLDS={
 1:'Holding references only a Commons file; exact RCIN exists but independently supported object-level collection evidence remains missing. Preserve candidate without accepting this pass.',
 5:'Riding School is a literal subject,not qualified authorship. Separate creator chronology conflict: database Thomas Spencer1740–1756; fresh source identifies circa1700 and several conflicting death claims1753,1763,1767. Resolve artist chronology before relying on the1758 work.',
 10:'1762 work points to source and existing artistQ950751 Richard Wright,born1960. Same-name creator conflict; do not silently relink or rewrite.',
 25:'Four-panel aggregate and source creatorQ21453429 Robert Jones,born1943 conflict with circa1810. Resolve whole/component identity and historical decorator before selection.',
 32:'No accession or active RCIN identifier and only Commons-based holding reference. Exact physical-object identity remains unresolved.',
 52:'1868 work uses creatorQ21463827 Peter Graham,whose fresh source birth is1959. Preserve object-level label and resolve historical painter identity.',
 56:'RCIN402308 identifier is deprecated for link rot; this alone is not proof of wrong identity. Source also cites NPGmw00086 and a related derivative. Resolve original,replica and collection identity before accepting Royal holding.',
 57:'Boy404492 versus existing Boz400978: nearly identical33.3x38.5cm and33.2x38.2cm formats with one-letter title difference. Distinct recorded inventories are insufficient to settle potential alternate title/version without composition evidence.',
 59:'Source filename names John Cleveley,died1777,while sourceQ6226371 and current artist link name the Younger1747–1786. Resolve father/son attribution and1761 work; preserve both evidence labels.',
 66:'1868 work uses creatorQ21463827 Peter Graham,born1959 in current authority. Historical same-name painter remains unresolved; preserve object-level label.',
 76:'Sliema/Marsamxett harbour titles can refer to overlapping locations. Royal18.6x47.4cm and StJohnLDOSJ1701 22x54cm require composition/provenance checking; do not treat a place-name difference as proof of different artwork.',
 89:'1867 work points to source and current George SmithQ21463764,born1870. Same-name creator conflict requires reconciliation.'
}
NOTES={
 2:'Different named sitter from Princess Royal’s Prince Henry400772; Charlotte406630 and Henry400772 remain separate portraits.',
 4:'Taylor403900 is a small portrait-format38.1x27.5cm ruin landscape,distinct from large horizontal101cm landscapes404591,405054 and404590.',
 6:'The1886 group of Victoria,Helena and Beatrice is143.5x183cm; Melville’s1845 single Queen portraitSG794 is127.5x104.2cm. Different composition,format and source inventory.',
 9:'Retained Walters37.217 primary text explicitly distinguishes its head-and-torso replica from Sanders’s Royal Collection Byron-and-companion original: altered arm,telescope,background and waistcoat. Walters91.6x71.4cm versus Royal112.5x89.4cm. Existing Walters holding unchanged.',
 14:'Müller’s Victoria Melita400744,Marie400742 and Alfred400746 identify different named siblings. Their shared1880 date does not merge the portraits.',
 16:'Exact source creatorQ155566 and fresh English authority label match existing unlinked Princess Alice label. Keep object-level label; no new painter link.',
 22:'Exact source creatorQ59386946 is Kate Thompson,active1874–1888. Keep existing object-level label; do not substitute another Thompson.',
 24:'Exact source creatorQ152245 and fresh label identify Prince Albert as maker,not merely royal subject. Keep object-level creator label.',
 26:'Taylor’s three large landscapes have separately referenced concurrent Royal inventories:404591 figures1793,405054 fishermen1770,404590 large tree1780. Similar standard formats are recorded,not used alone as identity. Distinct canonical subjects,dates and object IDs support separate works; Donald Taylor hit is another creator.',
 27:'P195 referencesQ113961045,verified as the Royal Collection website. Exact RCIN421666 agrees across inventory,native identifier and source filename. P1639 explicitly relates a separate pendant421665; this does not make one aggregate. No newly fetched native object page.',
 31:'Exact source creatorQ3132711 and fresh label identify Henry Daniel Thielcke. Existing unlinked label retained.',
 35:'Dee and Rhône are separately named landscapes with distinct inventory/date evidence; William Barnes Wollen hit is a different maker.',
 37:'Victoria,Princess Royal is the recorded maker. Victoria Hutson Huntley and Fantin-Latour Victoria hits are different identities,not duplicate still lifes.',
 39:'P195 references the verified Royal Collection website entityQ113961045. RCIN421665 is the Albert pendant to421666,not the1851 two-person portrait406916. Source specifies6–23May1844; existing exact1844 remains unchanged. Parser range/exact difference is precision only,not a contradictory year.',
 41:'Taylor405054 fishermen1770 is separately catalogued alongside404591 figures1793 and404590 tree1780. Preserve distinct source identities and similar dimensions; no invented title merge.',
 43:'Foster’s Saint Mark403899 and Saint Luke403898 are distinct named subjects and inventories,both1876.',
 44:'Melville400873 is18.2x13.1cm,1845. Explicit P144 relates it to Winterhalter401411,128.3x102.8cm,1843. Different creator,physical scale,date and inventory support a distinct derivative object; retain relation as evidence,not a maker reassignment.',
 45:'Royal1921 Nowell405251 and Burycirca1935FA000312 have similar76x63cm formats. Reciprocal source P4969/P144 explicitly distinguishes the later derivative from the Royal original; BuryP144 cites the exact Royal405251 page. No independent visual comparison claimed and Bury record unchanged.',
 46:'Herbert Smith’s Ferdinand407131,Ernest407125 and young Albert403730 are different named sitters. Full source filename identifies Herbert Luther Smith.',
 50:'Thorburn406916 depicts Albert with Ernest in1851;421665 depicts Albert alone in1844. Named composition and separate accession identify different works.',
 54:'Müller’s Alfred400746 differs from sibling portraits Marie400742 and Victoria Melita400744. Cranach Albrecht hit is a different artist and century.',
 55:'Saint Luke403898 is distinct from Foster’s Saint Mark403899; preserve each physical object.',
 62:'Taylor404590 large-tree landscape1780 is a separately referenced Royal object;403900 ruin landscape1776 is38.1x27.5cm versus101.6x127.2cm. Keep separate from other Taylor landscape subjects.',
 68:'Herbert Luther Smith’s Ernest407125 and Ferdinand407131 identify different sitters;403730 is young Albert.',
 70:'Prince Henry400772 and Princess Charlotte406630 are different named sitters,despite same royal maker.',
 79:'Young Albert403730 differs from Herbert Smith’s adult Ferdinand407131 and Ernest407125 portraits.',
 80:'Persimmon406503 is Adrian Jones1896;406475 is Edwin Douglas1897. Separate source creators,RCINs and dates support distinct portraits of the same horse; similar format alone is not identity. John Paul Jones hit is another maker.',
 88:'Persimmon406475 is Edwin Douglas1897,distinct source creator and inventory from Adrian Jones406503 of1896. Both source records retained without merging by horse name.',
 90:'Fresh sourceQ155566 confirms Princess Alice’s existing object-level creator label. No painter link or biography added.'
}
def raw_checked():
 cache={}
 for name in ['source-context-001.json.gz','comparison-source-context-001.json.gz']:
  for row in m.load(RUN/name)['rows']:
   if not row.get('body_reference'):continue
   path=checked(row['body_reference']);key=str(path)
   if key not in cache:
    raw=gzip.decompress(path.read_bytes()) if path.suffix=='.gz' else path.read_bytes();cache[key]=(hashlib.sha256(raw).hexdigest(),raw)
   sha,raw=cache[key];assert sha==row['raw_sha256']
   if name.startswith('source-'):assert json.loads(raw)['entities'][row['source_id']]==row['entity']
 return len(cache)
def authorities():
 out={}
 for name in ['unlinked-creator-authorities-001.json.gz','authority-conflicts-001.json.gz']:
  x=m.load(RUN/name);c=x['capture'];raw=gzip.decompress((m.ROOT/c['body_path']).read_bytes());assert hashlib.sha256(raw).hexdigest()==c['receipt']['sha256'];assert json.loads(raw)['entities']==x['entities'];out.update(x['entities'])
 return out
def build():
 initial=m.load(RUN/'initial-scope-001.json.gz');facts,errors=f.rows();assert not errors;identity=m.load(RUN/'identity-001.json.gz');assert identity['rows']==facts;comps={v['number']:v for v in identity['comparisons']};src={v['number']:v for v in m.load(RUN/'source-context-001.json.gz')['rows']};auth=authorities();artists={v['id']:v for v in initial['painters']};out=[]
 for row in facts:
  n=row['number'];r=src[n];a=r['artwork'];fact=row['facts'];comp=comps[n];assert {v['entity_id'] for v in comp['source_hits']}=={a['id']};state='editorial_hold' if n in HOLDS else 'approved_existing_holding';chron=[]
  for link in fact['artist_links']:
   ar=artists[link['artist_id']]
   if fact['first'] and ((ar['birth_year'] and fact['last']<ar['birth_year']) or(ar['death_year'] and fact['first']>ar['death_year'])):chron.append(dict(artist_id=ar['id'],birth=ar['birth_year'],death=ar['death_year']))
  if chron:assert state=='editorial_hold'
  if state=='approved_existing_holding':
   allowed=[]
   if n in [16,22,24,31,90]:
    e=auth[fact['creator_qid']];assert e['labels']['en']['value']==fact['creator_label'];allowed=['creator_authority_requires_reconciliation'];assert not fact['artist_links']
   elif n in [27,39]:
    assert auth['Q113961045']['descriptions']['en']['value']=='website of The Royal Collection art collection';allowed=['related_version_component_or_pendant_requires_review','missing_exact_native_object_collection_reference','source_catalogue_date_mismatch']
   elif n in [44,45]:allowed=['related_version_component_or_pendant_requires_review']
   assert not set(row['issues'])-set(allowed),(n,row['issues']);assert fact['rcin']==fact['native_object_id'];assert fact['last'] is None or fact['last']<=1970
  basis='Exact saved artwork QID,creator label and Royal Collection-qualified RCIN identify this object. Referenced secondary collection statement and separate RCIN identifier agree. '
  basis+=NOTES.get(n,'No same-creator physical-version conflict survives the bounded source,title,inventory and collection comparison.')
  limitation='Saved Wikidata statements with Royal Collection references; no freshly fetched Royal Collection object confirmation because RCT returned403. References are correlated secondary evidence,not multiple independent confirmations. Royal Household overview is institution context only. Holding does not establish legal ownership,current custody,palace location or current display. Existing dates,attributions,creator links,images,status and all descriptive metadata remain unchanged. Confidence is editorial,not a calibrated probability.'
  if fact['date_precision']=='unknown':limitation+=' Unknown creation remains excluded from eligible pre1971 totals; no event or accession date substituted.'
  out.append(dict(number=n,state=state,institution_id=s.IID,existing_artwork_id=a['id'],previous_institution_id=None,pending_assertion_id=r['pending_assertion']['id'],supersede_assertion_ids=[r['pending_assertion']['id']] if state=='approved_existing_holding' else [],facts=fact,comparison=comp,source_reference=r['body_reference'],source_raw_sha256=r['raw_sha256'],retrieved_at=r['pending_assertion']['checked_at'],confidence=.9 if n==9 else .85,basis=basis,limitation=limitation,hold_reason=HOLDS.get(n),creator_chronology_conflicts=chron,metadata_review_note=NOTES.get(n)))
 assert collections.Counter(v['state'] for v in out)=={'approved_existing_holding':79,'editorial_hold':12};return out
def main():
 dest=RUN/'editorial-reviewed-001.json.gz';assert not dest.exists();bodies=raw_checked();decisions=build();paths=[RUN/n for n in ['initial-scope-001.json.gz','source-context-001.json.gz','candidate-facts-001.json.gz','identity-001.json.gz','identity-citations-001.json.gz','comparison-source-context-001.json.gz','native-probes-001.json','royal-household-context-001.json','unlinked-creator-authorities-001.json.gz','authority-conflicts-001.json.gz','boz-comparison-001.json.gz','melville-related-original-001.json.gz','snapshot-helper-equivalence-001.json']];m.save(dest,dict(at=m.now(),decisions=decisions,reviewer_reference=ref(Path(__file__).resolve()),dependencies=[ref(p) for p in paths],verified_raw_bodies=bodies,policy='79 selected existing-object holdings;12 exact creator,version or source holds. Three dates remain unknown. Keep all original fields and review status; source site access refusal respected.'))
 print(json.dumps(dict(approved=79,held=12,unknown=sum(v['state']=='approved_existing_holding' and v['facts']['date_precision']=='unknown' for v in decisions),verified_raw_bodies=bodies)),flush=True)
if __name__=='__main__':main()
