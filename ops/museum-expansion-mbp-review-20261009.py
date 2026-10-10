"""Individual MBP identity/edition decisions, with distinct physical supports retained."""
import collections,copy,importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('i',Path(__file__).with_name('museum-expansion-mbp-identity-20261009.py'));i=importlib.util.module_from_spec(z);z.loader.exec_module(i);s=i.s;m=i.m;RUN=i.RUN;ref=s.ref;checked=s.checked
NOTES={
 2:'Twentieth-century impression of an older Ioannikios plate;1900–1999 retained, date eligibility requires review. Inventory188 differs from198 and sheet lengths34.3/38.5cm differ.',
 3:'Separate impression198, not188; physical print date1900–1999 retained instead of the seventeenth-century plate date.',
 6:'1816 Polykarpos certificate75 differs from already catalogued1811 certificate74; engraved date,inventory and source object differ.',
 8:'One partial-plate impression6,26x37cm,distinct from larger AllSaints impression201 and wooden icon238.',
 9:'AllSaints201,53.8x75.3cm,1840–1860; distinct from26x37cm partial-plate print6 and wooden icon238.',
 10:'Wooden AllSaints icon238,28x37.7cm; not either paper impression6 or201. Museum attributes it to a Macedonian workshop.',
 13:'Source materials explicitly say paper although description explains cloth antimensia generally. Preserve paper for this impression236; do not turn it into a textile.',
 16:'1846 inscription is uncertain in description; retain1846(?) as circa.',
 17:'Cloth impression135,64x48.7cm,1805. Separate from63,50.5x76cm,whose inscription adds1806consecration. Consecration is not replacement creation year.',
 18:'Actual inventoried paper impression71,40.3x52.5cm,creation unknown. Review record, not automatically eligible.',
 19:'Independent cloth impression63,50.5x76cm,not135. Preserve1805print date and1806consecration only as source evidence.',
 22:'1918copper-engraved cloth70,57x67.5cm,distinct from1930paper lithograph69 by same named engraver.',
 23:'1930paper lithograph69,67.6x54cm; not1918cloth impression70.',
 24:'Painted antimension95,1727,black ink on lined textile; painting category from source, not a copperplate print.',
 26:'Small Russian-style panel165,21.7x26cm,distinct from larger named/anonymous Archangel panels. Undated Cyprus comparator78be24b0 is a mural atAsinou;826518d4 is Cyclades object300358,notMBP165.',
 28:'Paper impression187,1900–1999;1699inscription concerns an older border design. Source names Hadjikyriakis who is described as patron/workshop funder, so no artist authority assigned.',
 31:'Surviving central triptych panel107 only,20.5x27.2cm. No complete triptych parent added. Distinct from83,85,95 and existing large503. Cyprus comparator724f577e is ceiling mural;98fb4c12 isHagiaSophia mosaic.',
 32:'Pantocrator85,42x60.2cm,dedicatory inscription1640 with structured1640–1641 retained. Distinct from83,95,107 and503.',
 33:'Pantocrator83,17.8x25.5cm,head to shoulders with Russian iconographic traits; distinct from85,95,107 and503.',
 34:'Enthroned Pantocrator95,50x60cm,1775–1799; other similarly titled panels have different sizes/inventories/compositions.',
 35:'Small egg-tempera panel84,24.5x42cm,1600–1624; exact-title comparators are other creators,media,dimensions or earlier Duccio panel43.5x46cm.',
 36:'Surviving central panel56 of a triptych,12.5x18cm; side leaves missing. One physical panel, no invented whole triptych.',
 37:'HighPriest60,15.5x21cm; differs from Damaskenos BXM13169,110x69.5cm and LambardosGE2990,113x77.7cm.',
 39:'Colonette with attached capital3231/31 is one carved object,13.5cmhigh. Distinct from detached capital3231/9,10.5cmhigh.',
 40:'Detached capital3231/9,10.5cmhigh,distinct from colonette3231/31 andAG1,50cmhigh. Existing2021.4capital measures26x37x28.5cm.',
 41:'Large Corinthian lyre capitalAG1,50cmhigh,475–549; independent of medieval small3231/9 and3231/31.',
 52:'One catalogued tomb-wall painting assemblage65/A–D with sea/rowing scene. Count once and preserve combinedinventory; not the family-worship178orAdam/Eve156A tomb.',
 57:'Double-sided marble relief520 is one slab,88x105cm; count once despite two faces and later circular hollow.',
 58:'Papadopoulos coloured print80,19.3x28.7cm,not Kyrillos-derived1950lithograph3,33.5x47.7cm.',
 59:'1950physical lithographic reproduction explicitly dated20March1950;1847is the earlier Kyrillos engraving date. Publisher/issuer distinguished from unidentified lithographer.',
 60:'One paper sheet186 with eight scenes; count once.1900–1999creation range remains under review.',
 61:'National object715484 explicitly says1833engraved/printed and inventory127,34.5x48.5cm. This resolves the native page1798narrative versus1833field conflict. NativeEnglish230page duplicates that narrative incorrectly;Greek230is a different1871lithograph51.3x63.6cm. No230addition in this selected national batch.',
 62:'1936physical lithographic copy onpaper/plywood37; source describes earlier Tziolakoglou copper engraving, so do not assign the earlier engraving date or authorship to this impression.',
 65:'One inventoried floor-mosaic fragment12 fromIoulianou18/Athinas residence; multiple geometric panels remain one record. Schema has no mosaic work_type; retainunknown category with explicit floor-mosaic description.',
 66:'One preserved floor-mosaic section23 fromMoreas43 basilica; do not add the other excavation sections or lostpanel described in context.',
 67:'One inventoried Galerian floor-mosaic group3A–Γ; count once and leave unreconstructed wholefloor absent.',
 68:'Single detached wall fragment92,95x65cm,from a larger multi-figure scene; possibleDormition identification retained only as evidence.',
 71:'One catalogued tomb-painted assemblage165/A–Z; combinedinventory and whole-tomb dimensions preserved; no separate records for each depictedbird/tree.',
 72:'One catalogued painted tomb assembly95/A,B withmarbleimitation andChristogram,141x139cm; count once.',
 74:'One combinedwall-painting inventory68/A,B,Γ,E; gourd stilllife/paradisebirds distinguished fromother tombs. Count once.',
 75:'One detached southern tombwall painting91/A,B withgarlands; count once under combinedinventory.',
 77:'Single detached long-side wall painting128/Δ,crossandbirds,220x140cm; distinguish from99A,102/E–Z andexistingother tombs.',
 78:'One catalogued assembly102/E–Z ofthree detachedwall sections; one record preserves combinedidentity. Distinct fromsmall99Asinglewall.',
 79:'Single narrow-wall fragment99A,86x82cm,crossandleaves; not102/E–Zassembly102x115cm.',
 80:'Single western tombwall Danielwithlions119,95x98cm,250–274; differentinventory andsubject fromexistingtombworks.',
 81:'One combinedpainted tombwall assembly158/A–D,geometric/marblepanels; distinct fromexistingAdam/Eve156A. Countonce.',
 82:'Sinai print167,36x30.5cm,1688,Rokou; distinct from166,68.5x58.6cm,1693–1694 andotherprintmakers165/168.',
 83:'Twentieth-century Sinai lithograph46; earlier1778prototype is not this physicalimpression date. Differentfromexisting1804print233.',
 84:'Sinai print166,68.5x58.6cm,1693–1694; different fromsmaller1688Rokouprint167 andexisting1804print233.',
 86:'Averkios1866Athosprint148,68.3x58cm; notexisting1767anonymousprint248,81x57cm.',
 87:'Matthaios1706Sinaiwoodcut168,68.5x45.6cm; independentfromAkakios1665print165andRokou166/167.',
 88:'Akakios1665Sinaiprint165,68.5x45.8cm; distinctcreator,date,inventory fromMatthaios1706print168despitesimilardimensions.',
 89:'Papadopoulos1856colouredprint10,24.4x31.4cm; genericHolyTrinitycomparatorshaveothercreators/periods,notthisimpression.',
 90:'1824lithographicimpression7,27.2x39.7cm; distinctinventoriedsheetfrom9,26x37.6cm and8,31.7x46.8cm. Alloneimagecompositiondoesnotmakephysicalsheetssameobject.',
 91:'1824lithographicimpression9,26x37.6cm; independentphysicalsheetfrom7and8,withdistinctinventoryanddimensions.',
 92:'1824print8,31.7x46.8cm; distinctphysicalsheetfrom7and9,and1787print225.',
 93:'1787print225,33.4x44.2cm,distinctdateandcompositionfrom1824impressions7/8/9.',
 95:'Cut panel958 ofPoulakisJosephcycle,45.8x53cm,Potipharsale scene; separatefromcataloguedwellscene959andJacob956. Existinga5d1275c imagevisuallymatchesthewellscene959,not958; duplicate959recordrequireslaterreconciliation,notanotheraddition.',
 108:'Iconostasisdoor467α–β withtwoleavesandhierarchs countsasoneobject; differentfromexisting15thcenturydoor97withPeter/Paul.',
 111:'Cut panel956,JacobwithJosephshirt,45.5x53.2cm; separatephysicalfragmentfrom958Potipharsale and959wellscene. Historiccutparentnotadded.',
 114:'Nineteenth-centurylithograph4,33x49cm,VirginholdingdeadChrist; otherLamentationexacttitlesaredifferentnamedRenaissancepaintersor1517woodcut28x18cm.',
 115:'One1742Constantinoplemap256 includescityview andHagiaSophia insetplan/views; countonesheet,notseparateartworksforeachinset.',
 116:'Meteora chromolithograph159,86x59cm,1875–1899; distinctfrom1882lithograph158,73.7x53.6cm.',
 117:'Meteora1882lithograph158,73.7x53.6cm; notchromolithograph159withdifferentdimensionsandmaker.',
}
def build():
 x=m.load(RUN/'production-identity-001.json.gz');assert x['rows']==i.f.rows()[0];by={v['id']:v for v in x['state']['artworks']};out=[]
 for row,c in zip(x['rows'],x['comparisons']):
  d=copy.deepcopy(row);d['comparison']=copy.deepcopy(c);f=d['facts'];n=row['number'];assert not c['source_hits']
  if n in [73,76]:
   d.update(state='held_editorial_review',basis='BT170andBT139 have differentinventories/dates but matchingtombdimensions,closelyoverlappingdescriptions andsamefindspot. Holdbothuntiloriginaltomb/catalogueidentityresolved.');out.append(d);continue
  if n in [95,111]:d['comparison']['hits'].append(dict(copy.deepcopy(by['a5d1275c-f630-5bd9-a16e-aee4ab6cf54d']),hit_types=['creator_subject_comparator'],same_museum=False))
  if n==59:f['creator_label']='Unidentified lithographer; issued by M. M. Iordanitis; after Kyrillos (monk, original engraving)'
  if n==28:f['creator_label']='Unidentified woodcutter; Hadjikyriakis Vourliotis of Sinai (patron/workshop funder named by source)'
  if n==10:f['creator_label']='Anonymous; Macedonian workshop (museum attribution)'
  if n==32:f['creator_label']='Anonymous; Macedonian workshop, possibly connected with Mount Athos (museum attribution)'
  if n==36:f['creator_label']='Unidentified painter, probably northern Greece, possibly Mount Athos (museum attribution)'
  if n in [31,36]:f['description_md']='Surviving central panel of a triptych. The complete triptych and missing side panels are not represented by additional records.'
  if n in [95,111]:f['description_md']='A surviving cut panel from Theodoros Poulakis’s Joseph cycle. The museum describes the cycle as fragments of an earlier single painting.'
  if n in [65,66,67]:f['description_md']='Floor mosaic: one museum-catalogued fragment or assembly under inventory '+f['inventory']+'. The source classification is retained; the current catalogue has no dedicated mosaic category.'
  if n in [52,71,72,74,75,78,81]:f['description_md']='One catalogued wall-painting assembly, inventory '+f['inventory']+'. Its component sections are counted together; the source dimensions may describe the tomb or assembly.'
  if n==108:f['description_md']='One iconostasis door comprising two painted leaves, inventoried together as ΒΕΙ 467 α–β.'
  detail=NOTES.get(n,'Independent museum-inventoried object; title,material,dimensions,date andsourceidentifier distinguish it from the existing31museumrecords and boundedtitle/creatorcomparators.')
  basis='Museum provider274 andstoreLocation6051 explicitlyidentifyMBP; object '+f['source_id']+', inventory '+f['inventory']+'. '+detail
  d.update(state='approved_review_only_addition',basis=basis,confidence=.95,limitation='Editorialconfidence,notcalibratedprobability. Holdingonly; nofreshdisplay,custodyorownershipclaim. Reviewstatus,unknownsandqualifiedcreatorlabelsretained. Noartistauthorityorimageattachment.');out.append(d)
 assert len(out)==91 and sum(v['state']=='approved_review_only_addition'for v in out)==89;return out
if __name__=='__main__':
 ds=build();deps=[RUN/v for v in ['candidate-facts-001.json.gz','production-identity-001.json.gz','production-identity-citations-001.json.gz','production-initial-scope-001.json.gz','national-details-001.json.gz','poulakis-comparator-snapshot-001.json.gz','poulakis-visual-inputs-001.json','greek-print-resolution-001.json.gz','native-icons-001.json.gz']];m.save(RUN/'editorial-reviewed-001.json.gz',dict(at=m.now(),decisions=ds,dependencies=[ref(v)for v in deps],reviewer_reference=ref(Path(__file__).resolve()),policy='89selectedreviewadditions;2tombidentityholds,9factholds,17alreadyknown.3explicit1977impressionsnotadded. ExistingPoulakiswellscene959duplicateevidencepreserved,nomergeinthispass.'))
 print(json.dumps(dict(states=dict(collections.Counter(v['state']for v in ds)),eligible=sum(v['state']=='approved_review_only_addition'and v['facts']['first']is not None and v['facts']['last']<=1970 for v in ds))),flush=True)
