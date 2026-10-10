"""Explicit dispositions of40 source-selected Guildhall artwork leads."""
import collections,csv,gzip,hashlib,importlib.util,io,json
from pathlib import Path
z=importlib.util.spec_from_file_location('f',Path(__file__).with_name('museum-expansion-guildhall-facts-v3-20261009.py'));f=importlib.util.module_from_spec(z);z.loader.exec_module(f);m=f.m;RUN=f.RUN;ref=f.ref;checked=f.checked
NOTES={
1:'Anonymous bridge-demolition painting; intertwined signature is only read as J.W.S., not a resolved named creator. Different-museum-scope bridge leads have different named makers and subjects. Retain circa1833, without substituting construction dates.',
2:'Rossetti1873 La Ghirlandata is also called The Lady of the Wreath. Existing The Lady of Pity1881 is a different named subject; Flora Lion1907 portrait is a different maker. No exact object/source or museum match.',
4:'Marlow view of Blackfriars Bridge and St Pauls differs from Burn Waterloo Bridge, Schlee Red Pillars, Scott Pool of London and Lloyds Queenhithe. Preserve museum circa1762 as supplied, including its tension with later bridge completion; no invented correction. The other oval version mentioned in narrative is not separately imported.',
5:'Guildhall577 is the1882 Clytemnestra,239x174cm. Archival study distinguishes it from WorcesterFAO3,c1914,238x147.8cm, with different dress,weapon and architecture. Existing FAO3 remains unchanged. Another museum uses577 for John Lessore Woman Writing at a Desk; accession numbers are museum-scoped.',
7:'Dated1739 GAC object and official permanent-gallery entry1739–40 support the named Griffier the Younger work. Preserve range and literal source discrepancy. The narrative contains biographical confusion; no biography is imported. Undated presentation8 is not another work.',
11:'1848 Hunt finished painting, full title Flight of Madeline and Porphyro during the Drunkenness Attending the Revelry. The source explicitly credits Millais with the Baron head; preserve that contribution in evidence without inventing a primary artist link. Distinct from preparatory oil study12.',
12:'1848 oil study for The Eve of Saint Agnes is a separate physical preparatory painting: four arches versus three in the finished painting, and different porter/bloodhound arrangement. Not a detail photograph or second presentation of11.',
14:'Dated1860 museum and City of London asset pages give identical title,maker,narrative and Guildhall location; the latter explicitly supplies oil on canvas. Count one physical work. Earlier undated generic presentation remains a research lead, not a second object.',
15:'Grimshaw1884 Thames and Southwark Bridge painting; source records acquisition1967 and acknowledges at least five versions. No same-maker London version match found in comparison; existing Liverpool Quay by Moonlight is a different city. Undated Thames by Moonlight lead13 remains held.',
16:'John Rogers Herbert1847 Youth of Our Lord, explicit Guildhall object page. Herbert Moxon Cook Sound of Jura is a false surname match. Two other versions mentioned by source are not imported; preserve that version caveat.',
19:'Leighton1877 Music Lesson, with Connie Gilchrist model context. Existing Eeckhout Music Lesson1655 and other named-maker versions are different works. Undated source24 not counted separately.',
20:'Exact Dordrecht exhibition story asset explicitly credits London Guildhall and calls this the full-size oil sketch. Official Guildhall acquisition history identifies the full-size1829–31 oil sketch. Retained TateN01814 metadata identifies a small365x511mm study; Bishops Grounds,Lower Marsh,Avon and Harnham Ridge are different compositions. Generic earlier Salisbury asset is an unverified lead only. Historical loan does not make this a Dordrecht holding or prove current display.',
21:'Lecomte du Nouy1882 Reading of the Bible by the Rabbis,also Souvenir of Morocco. Exact museum-published collection context and dated asset; no matching object found in bounded creator/title/museum/source scope.',
22:'Stanfield painting explicitly created and exhibited1832. The1831 bridge-opening event is not substituted as creation. Burn Waterloo Bridge and Graham London Bridge to Arizona are different makers and scenes.',
25:'Niels Moeller Lund1904 Heart of the Empire, exact dated Guildhall object page. No corresponding physical object or source identifier found.',
26:'Millais1863 My First Sermon, corroborated by official Gassiot bequest history. Companion My Second Sermon1864 is a different unselected work, not inferred from this asset.',
29:'Jacqueline Stanley1969 Smithfield Market painting meets artwork-creation cutoff. Do not exclude by artist lifetime or modern style. Exact explicit Guildhall location, no duplicate found.',
34:'Ken Howard1962 Billingsgate Market painting meets artwork-creation cutoff. Exact dated Guildhall asset, no object identity match found.',
37:'Goodall1860 Early Morning in Wilderness of Shur,formerly An Arabian Encampment at Wells of Moses,oil on canvas. Existing Riviere Temptation1898 is different maker and subject;1858 travel date is not substituted for creation.',
38:'John Phillip1864 Faith,oil on canvas,personification as Spanish Catholic woman. Watts1890s painting and Aldegrever/van Leyden sixteenth-century prints are different makers and physical works.',
39:'Edward Armitage1868 Herods Birthday Feast,oil on canvas. Guildhall Peggy Angus Birthday Feast1941 differs in maker,subject and date. Source narrative discusses underpainting; no separate hidden-image artwork added.',
40:'Luke Fildes1914 Naomi,explicit museum location and dated asset in the collection story. No exact source/title/maker object match found.'}
HOLDS={
6:'Unknown creation date.1666 is depicted Great Fire event, not supported creation; preserve after-Waggoner qualification.',
8:'Undated presentation of Griffier Great Frost subject; no independent physical version established. Candidate7 represents the dated work; do not double count.',
9:'Undated Delaroche asset lacks Guildhall holding evidence. Existing National Gallery execution painting entries need their own reconciliation; publisher branding is not ownership.',
10:'Undated copy after Canaletto; original artwork or building dates cannot date this copy.',
13:'Undated Thames by Moonlight may repeat dated Grimshaw candidate15; no independent physical version established.',
17:'Undated Copley finished battle-painting lead lacks required creation fields. Existing two National Gallery of Art studies are separate physical studies. Resolve exact finished object/date before addition.',
18:'Millais Woodmans Daughter generic asset has no supported creation date or explicit holding fields. Retain for selected native research.',
23:'Official history documents Millais1849 watercolour Lorenzo and Isabella, but undated generic asset/version mapping remains unresolved. Do not attach its source identifier to the watercolour by assumption.',
24:'Undated Leighton Music Lesson presentation not a second physical work; dated candidate19 selected.',
27:'John Virtue Landscape715 explicitly2003–2004 is outside pre1971 creation scope.',
28:'Unknown-date copy after Samuel Scott. Prototype and Tate-version dates cannot date this copy.',
30:'Ben Johnson Market Arcade1986 is outside pre1971 creation scope.',
31:'Frank Brangwyn Tower Bridge undated asset lacks explicit holdings metadata; Kokoschka1925 is different maker. Further exact date/source research needed.',
32:'Harold Workman Chaos on London Bridge has unknown creation date; do not date by bridge event.',
33:'Geoffrey Fletcher Exmouth Market1997 is outside pre1971 creation scope.',
35:'Anonymous Foundation Stone of Royal Exchange undated work;1842 ceremony is not evidence of creation year.',
36:'Nebot painted multiple Covent Garden versions. Existing TateN01453 is1737,648x1228mm. Guildhall asset lacks inventory/dimensions to resolve this near-identical composition; retain without new record.'}
EXISTING={3:'Existing Guildhall artwork3fdb99d2-8f50-5d01-ac0b-706a771c63e6,Lavery1922,inventory1027,already linked in wave85. No duplicate or second holding.'}
def comparison_sources():
 for v in m.load(RUN/'comparison-source-context-001.json.gz')['rows']:
  raw=checked(v['body_reference']).read_bytes()
  if v['format']!='wikidata':raw=gzip.decompress(raw)
  assert hashlib.sha256(raw).hexdigest()==v['raw_sha256']
  if v['format']=='wikidata':assert json.loads(raw)['entities'][v['data']['id']]==v['data']
  elif v['format']=='csv':assert [x for x in csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))) if x['accession_number']==v['selected_accession']]==v['data']
  else:assert json.loads(raw)==v['data']
def build():
 rs=m.load(RUN/'native-candidates-003.json.gz')['rows'];assert rs==f.rows();comparison_sources();identity=m.load(RUN/'native-identity-003.json.gz');assert identity['rows']==rs and identity['candidate_reference']==ref(RUN/'native-candidates-003.json.gz');comps={v['number']:v for v in identity['comparisons']};assert set(NOTES)|set(HOLDS)|set(EXISTING)==set(range(1,41)) and not(set(NOTES)&set(HOLDS));out=[]
 for row in rs:
  num=row['number'];v=row['facts'];c=comps[num];approve=num in NOTES;state='approved_review_only_addition' if approve else ('already_catalogued' if num in EXISTING else 'editorial_hold');basis=(NOTES if approve else EXISTING if num in EXISTING else HOLDS)[num]
  if approve:assert row['state']=='candidate' and not c['source_hits'] and not c['presentation_alias_hits'] and 100<=v['first']<=v['last']<=1970 and not v['date_issue'] and not v['native_issues']
  out.append(dict(number=num,source_id=row['source_id'],institution_id=f.IID,facts=v,source_reference=row['source_reference'],comparison=c,state=state,confidence=.95 if approve else None,basis=basis,limitation='Editorial confidence is not a calibrated probability. Source collection evidence is not a current-display,custody or legal-ownership determination. Missing fields remain unknown; original labels,rights and date discrepancies retained in evidence. No images or artist-authority changes.',retrieved_at=row['retrieved_at']))
 assert len(NOTES)==22 and len(HOLDS)==17 and len(EXISTING)==1;return out
def main():
 dest=RUN/'editorial-reviewed-001.json.gz';assert not dest.exists();rs=build();deps=[RUN/p for p in ['native-candidates-003.json.gz','native-identity-003.json.gz','identity-citations-003.json.gz','comparison-source-context-001.json.gz','scholarly-version-source-001.json']];m.save(dest,dict(at=m.now(),decisions=rs,dependencies=[ref(p) for p in deps],reviewer_reference=ref(Path(__file__).resolve()),policy='Explicit per-object decisions; duplicate presentations and prior object remain excluded. New records only in review. Exact source/creator/title/inventory scopes and physical-version evidence; no automatic acceptance from similarity scores.'));print(json.dumps(dict(states=dict(collections.Counter(v['state'] for v in rs)))),flush=True)
if __name__=='__main__':main()
