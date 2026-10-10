"""Review of selected museum acquisitions; impression identity and source boundaries explicit."""
import collections,copy,gzip,hashlib,importlib.util,json
from pathlib import Path
def module(name,file):
 z=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(z);z.loader.exec_module(v);return v
f=module('f','museum-expansion-augustiner-facts-20261009.py');i=module('i','museum-expansion-augustiner-identity-v3-20261009.py');s=f.s;m=s.m;RUN=s.RUN;ref=s.ref;checked=s.checked
HELD={103:'Museum report2023 narrative PDF4 gives1852/53, acquisition appendixPDF20 givesum1855; press discovery givesc1853/54. Native object portal denies access. Hold exact dating/version reconciliation; no catalogue date selected by convenience.'}
NOTES={
6:'A specific oil sketch of a weeping Italian woman held by her arm, not the complete1836bandit scene Røvere overfalder rejsende atSMK KMS1111 or the lovers landscape KMS1112. Preserve unknown creation and study identity.',
8:'Augustiner gift fromUlrikeErber-Bader26Jan2021, one1632etching. Cleveland1946.310 andMiaP.1,280 are separately catalogued impressions. No unlinked same-physical-object source found; no state or lifetime impression asserted.',
9:'Augustiner gift26Jan2021 specifies Caprichos titleleaf1799. ArtInstitute1948.110.1 and1927.3191, Cleveland1922.363 are distinct institutional impressions. Met35.103.1 and1975.1.976 are drawings, not this titleleaf. OtherGoyapaintedselfportraits are different objects.',
10:'Augustiner2021gift identifies1913standing,drawing selfportrait drypoint. Met26.61.21 is another institutional impression; Met26.61.17 is1912DrawingPad. Do not merge impressions or substitute existingMet holding.',
43:'Abbey view individually listed separately from the valley view, Scharfenstein view and rock site view in the same acquisition list.',
44:'Münsterthal valley andSanktTrudpert individually listed; not the separateabbey view.',
45:'Scharfenstein(Münstertal) individually listed; not the separately named rock bearing formerHabsburgcastle.',
46:'Specific rock of formerHabsburgScharfensteincastle, a separately listed sheet fromScharfenstein(Münstertal).',
69:'Augustiner2022gift29March, museum datesc1650. NGA1943.3.7225,Cleveland1941.658,AIC1938.1768 are separately inventoried impressions. Retain museum circa date; do not silently harmonize edition dates or relocate other impressions.',
72:'HermannReich head portrait, separately listed from shoulder-length portrait in same2022gift; two actual paintings, not two descriptions of one item.',
73:'HermannReich shoulder-length portrait separately listed from headportrait; retain specific version.',
77:'Opfingen rear of farmstead, first of three individually titled1924Schusterwatercolours.',
78:'Opfingen half-timbered houses bystream, second individually listedSchusterwatercolour.',
79:'Opfingen farmhouse,courtyard and adjoininghouses, third individually listedSchusterwatercolour.',
86:'Handcoloured RobertMacaireJournaliste fromLesRobertMacaires, reported1836–1838. ExistingMacairebanker,bookseller,lawyer,dentist,travellingsalesman,director andotherleaves have different subjects or separately inventoried institutionalimpressions; no substitution between leaves.',
87:'1849youngman leftprofile acquired2023, notPushkin1851male/selfportraitЖ-3527(42.5x35cm), Metmale nude drawings orotherFeuerbachnamedpaintings. Museum acquisitiondate not creation.',
88:'One1892Mühlenbacherin;2023and2024reports repeat this samework. ExistingGräßelGutachWomanMeadow1900M89/006,MeadowFlowers1904M86/015,Home188512479,MeadowSlope1888M88/001 andChildrenGeese188712398 differ.',
94:'EmmaHimmelsbach portrait in2022-Decembergift reported2023, notHermannHimmelsbach orGeorgHimmelsbach1923; each has own listed sitter.',
95:'HermannHimmelsbach portrait, notEmma orGeorg. OtherVogelmakers andDionysGanterJohannRombach1840 differentcreator/sitter.',
99:'Exact1781Choffard engraved vignette afterPâris onpage146of1782publication. Preserve engraving creation1781 andpublication1782as evidence; roles not collapsed.',
100:'ThomasCook1807reproductiveprint afterHogarth, titlementions1761originalcatalogue. Creation is1807, not1761.',
101:'ThomasCook1809reproductiveprint afterHogarth; existingNGA1944.5.121isHogarth1761original. HowardCookselfportraits andHogarth1757selfportrait are differentworks.',
102:'Augustiner2023Petermanngift one1586RomanHeroesplate4. SMKKKSgb8155 andMet49.97.691 are otherinventoriedimpressions; FrenchCurtiusE.Cl.1533e isanonymousafterGoltzius painting. Noedition/state inferred.',
104:'WilhelmHanemann1905selfportrait, notHansThoma1871,Corinth1923/24,Gerhardi1907 orotherartists’ genericselfportraits. Samegift separatelylistsLotteFrank1920 andpossibleMarieHanemann1919.',
106:'Possible sitterMarieHanemann remains question-marked; no definitive sitter identity asserted.',
117:'HansThomac1880redchalkNeptuneprocession withNereid/Tritons; notThoma1880VillaBorgheseputtifountain drawingCleveland2010.541.',
118:'Original1880penExlibrisAliceKoch drawing only. The separatelymentioned1916reproduction is excluded, not asecondcount.',
119:'MarieDürr-Grossmann1884LeoBlustportrait; notBerthaBlustcompanion orworksbyWilhelmDürrtheElder.',
120:'MarieDürr-Grossmann1884BerthaBlustportrait separatelylisted withLeoBlust, notduplicate.',
121:'UndatedLudwigZornBurkheimpaintingin2024gift, notAndersZornworks orLudwigZorn1904CloudyWeather and1906ZastlerHut.',
123:'1903Feldbergwinter byLudwigZorn; existingKarlHauptmannWinter1916M84/009 andHermannDischlerTodtnauerHut1905M30/015 aredifferentmakers. ZornCloudyWeather1904 andZastlerHut1906 aredistinctnamedviews.',
126:'FranzXaverHochc1895Italianlandscape2024gift; notMaxWilhelmRomanItalianlandscapeKarlsruhe1145, HochClaus19082021/211 orEifeldorf1903printCleveland1933.83.',
127:'Augustiner1897etchingSchwarzwaldpartieStBlasien; Met2010.42 is1900drawing ViewintheBlackForest. Distinctmedium/date; noholdingtransfer.',
129:'Source attributes small landscape toEvaEisenlohr but explicitly unsigned andundated. Retain unknowncreation; noautodate orartistauthoritylink.'}
def build():
 rs,_=f.rows();identity=m.load(RUN/'identity-003.json.gz');assert rs==m.load(RUN/'candidate-facts-001.json.gz')['rows']==identity['rows'];assert len(rs)==130;out=[]
 for row,c in zip(rs,identity['comparisons']):
  assert row['source_id']==c['source_id'] and not c['source_hits'];n=row['number'];facts=copy.deepcopy(row['facts']);corrections=[]
  if n==3:
   facts['work_type']='unknown';corrections.append('Mischtechnik identifies technique only; source does not classify this individual work as drawing. Final work_type unknown rather than inferred drawing.')
  state='editorial_hold' if n in HELD else 'approved_review_only_addition';note=NOTES.get(n,'Individually titled acquisition in the Augustiner section. Full museum scope and maker/title candidates checked; other makers,subjects and institutional print impressions are not the same physical acquisition.')
  out.append(dict(number=n,source_id=row['source_id'],institution_id=s.IID,state=state,facts=facts,comparison=c,comparison_basis=HELD.get(n,note),version_note=row['version_note'],hold_reason=HELD.get(n),existing_artwork_id=None,confidence=.94 if n not in HELD else None,confidence_kind='editorial assessment,not calibrated probability',basis=f"Museum-published {facts['source_fields']['report']} individual acquisition/gift list, PDF page {facts['source_fields']['pdf_page']}. "+note,limitation='Documented collection association only. No current display,custody,legal ownership,print state or lifetime impression claim. Missing inventory,dimensions andcreation retained; creatorlabels not automatically resolved toauthorities.',retrieved_at=row['retrieved_at'],source_capture=row['source_capture'],source_record_reference=row['source_record_reference'],supplementary_source=[],physical_object_count=0 if n in HELD else 1,source_fidelity_corrections=corrections))
 assert collections.Counter(v['state'] for v in out)=={'approved_review_only_addition':129,'editorial_hold':1};return out
def main():
 out=build();paths={Path(__file__).resolve(),Path(f.__file__),Path(i.__file__),Path(s.__file__)}|{p for p in RUN.rglob('*') if p.is_file()}
 for dep in m.load(RUN/'comparison-source-context-003.json.gz')['body_references']:paths.add(checked(dep))
 m.save(RUN/'editorial-reviewed-001.json.gz',dict(at=m.now(),decisions=out,dependencies=[ref(p) for p in sorted(paths)],reviewer_reference=ref(Path(__file__).resolve()),policy='129distinct review additions,126dated/3unknown;oneFeuerbachdatehold. Reportrepeatdeduplicated; printimpressions andoriginalvsreproductiveversions distinct. Mischtechniktype corrected tounknown. Noexistingmetadata/holding/image changes.'))
 print(json.dumps(dict(new=129,dated=126,unknown=3,holds=1)))
if __name__=='__main__':main()
