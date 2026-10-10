"""Explicit physical-object decisions for Box continuation; uncertain versions held."""
import collections,gzip,hashlib,importlib.util,json
from pathlib import Path
def module(name,file):
 z=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(z);z.loader.exec_module(v);return v
f=module('f','museum-expansion-box-continuation-facts-20261009.py');i=module('i','museum-expansion-box-continuation-identity-20261009.py');s=f.s;m=s.m;RUN=s.RUN;ref=s.ref;checked=s.checked
HELD={1903:'Spencer Hoe Nursery Garden needs physical comparison with MoMA Nursery78487/c764e50c-a2dd-40f3-b572-47494d7debad. Commission1955 differs from1936source date,but differences alone do not resolve version. No duplicate or date overwrite.',1912:'Olsson moonlight/searchlight pier scene needs physical comparison with legacy Moonlit Shore,Moonrise on the Bar and Moonlight St Ives Bay. Unknown creation is not proof of separate version.',1918:'Williams Royal William Yard circa1836 needs physical comparison with existing551f6e25-d986-5e7e-84df-98a2642c3aa7,inventory118/1933,sourceRAMM1844–1845. Existing source mismatch hold retained;no duplicate or reassignment.',200005:'Drake Cup funder gives c1571,with conflicting traditional gift stories. Seek native creation/attribution and decorative-object documentation before addition;do not promote traditions into facts.'}
ALREADY={1921:'00d1ced5-419e-5d21-9705-3b3465724548',1966:'7d27e197-0bee-5b94-928c-d89d1340c256'}
NOTES={
1810:'Specific1907portrait with flowered-hat woman and bowler-hatted Walter Sickert. Other Gore portraits Artist Wife1913 and North London Girl1911–1912 are distinct named contexts;no matching catalogue/source record.',
1863:'Ben Hartley rural lane1968,explicitly from Box collection. Same-surname Marsden Hartley candidates do not identify this work. Turner partner painting is not selected.',
1881:'Finished approximately150x120cm beach-auction painting,not abandoned nine-foot canvas or sketches. Native1962acquisition and Newlyn subject distinguish it from other Forbes bride,children andAmericanwar pictures.',
1888:'Douglas Walter Lang1965Tamar road and rail bridges viewed fromCornwall;gift1969. Broad surname/alias hits do not establish creator or object identity.',
1891:'Source attributed Danckerts1675harbour landscape with recentlybuiltCitadel is not DorothyWard1933gouache or ReynellDock painting. Native explicitly distinguishes Yale version. Attribution remains qualified.',
1894:'Reginald Brill1950sWestHoe street scene with two women headed seafront,not PaulBril landscapes or ReginaldSwanage/quarry works. Decade remains qualified.',
1897:'WilliamGibbons scene with picnickers andCremyllferry,not GrinlingGibbons stilllife or later similarlynamedartists. Building/ferryhistory not used ascreation.',
1900:'NicholasPocock specific Duttonshipwreck painting with Citadel,MountBatten andrescue lines. Available creator pool consists different named ships/Bristol andMillHillscenes. Depicted1796notcreation;notLunyversion.',
1909:'Ginner1923Plymouthpier oil identifies venue,subject andsupport. Separate from GinnerPorthleven,Clayhidon,London andLeedspictures.1987acquisition/1988fundingsupport difference retained.',
1915:'Attributed van deVelde Younger oil ofPlymouthCitadel/flagship,circa1670;other sea/battle scenes have distinct Dutch/Swedishsubjects.1666title is not creationdate.',
1947:'KateNicholson specific fern/ivy/glassbottle/jug stilllife bought1958;not Ben,WilliamorFrancisNicholson works. Unknown creationretained.',
2030:'Reynolds LadyAnnBonfoy female sitter in green/pink dress,handonhip,landscape background. Different from CaptainJohnFoote male portrait andother named sitters. Boxexplicitlyowns collection association acquired2007,but painting remains atPortEliot;noonsiteclaim.',
2038:'Barns-Graham1967–1969CardTable geometric abstraction;not otherGrahamartists or her genericlandscapes. Gift1976notcreation.',
2085:'Hart1839original giant JaneGreyexecution canvas,gift1879,museum1911,rolledin storage. Namedmaker/historydistinguishesDelarocheversion;conditionassessmentnotnewobject.',
2105:'ElizabethForbes1898ShakespeareImogenpainting,not EileenWatson1922Imogen. Source names romanticplayandacquisition1904.',
2142:'WinifreddeVanyportrait ofJacquelineGlanvillebequeathed2022,not CatherineSaverychildportrait. Unknown creationretained.',
92142:'Second portrait explicitlyheld bysameartistdepicts curatorA.A.Cumming,notGlanville. Do notderive datefrom employment1937–1978.',
200001:'Rowlandsonwatercolourboats andforegroundpeople/horses gifted2006,not Met1822handcolouredetching. Literal1756–1827artistlifespan rejectedascreationrange.',
200002:'Turner1814smallwatercolour15.6x24.1cmforSouthernCoastseries,notAmbroseBowdenJohnsoilviewcirca1821. Originalwatercolournotpublicationengraving.',
200003:'TurnerKilchurnCastle/LochAwewatercolour51x78cm,one1955Cookbequestitem.1775–1851lifespan isnotcreation;fullbequestnotmultiplied.',
200004:'One1880human-facedMartinwarecrabsculpture,21x48.5cm,acquired2020. Uniquephysicalobject,not106otherMartinwarepieces;noexistingcrabcandidate.'}
def build():
 facts=m.load(RUN/'candidate-facts-001.json.gz');rs,errors=f.rows();assert rs==facts['rows'];identity=m.load(RUN/'identity-002.json.gz');assert rs==identity['rows'];cs=i.comparisons(rs,identity['state']);assert cs==identity['comparisons'];ctx=m.load(RUN/'comparison-source-context-002.json.gz')
 for dep in ctx['body_references']:checked(dep)
 out=[]
 for row,c in zip(rs,cs):
  n=row['number'];v=row['facts'];cap=row['source_capture'];raw=gzip.decompress((m.ROOT/cap['body_path']).read_bytes());assert cap['receipt']['status']==200 and hashlib.sha256(raw).hexdigest()==cap['receipt']['sha256'];assert not c['source_hits'];state='editorial_hold' if n in HELD else 'already_catalogued' if n in ALREADY else 'approved_review_only_addition';note=NOTES.get(n,row['version_note'])
  out.append(dict(number=n,source_id=row['source_id'],institution_id=s.IID,state=state,facts=v,comparison=c,comparison_basis=HELD.get(n,note+' Bounded source/title/inventory and creator candidates plus full institution scope reviewed. Similarity is discovery,not proof.'),version_note=row['version_note'],hold_reason=HELD.get(n),existing_artwork_id=ALREADY.get(n),confidence=.94 if state=='approved_review_only_addition' else None,confidence_kind='editorial assessment,not calibrated probability',basis='Museum collection narrative or primary acquisition-funder record identifies selected physical work. '+note,limitation='Collection association only,not current display,custody or legal ownership. Port Eliot physical location retained in source facts. Unknown dates,qualified creators and unlinked maker labels remain explicit. No image or publication update.',retrieved_at=row['retrieved_at'],source_capture=cap,source_record_reference=row['source_record_reference'],supplementary_source=row.get('supplementary_source'),physical_object_count=1 if state=='approved_review_only_addition' else 0))
 assert collections.Counter(v['state'] for v in out)=={'approved_review_only_addition':21,'editorial_hold':4,'already_catalogued':2};assert sum(v['facts']['first'] is not None for v in out if v['state']=='approved_review_only_addition')==13
 return out
def main():
 out=build();paths={Path(__file__).resolve(),Path(f.__file__),Path(i.__file__),Path(s.__file__)}|{p for p in RUN.rglob('*') if p.is_file()};ctx=m.load(RUN/'comparison-source-context-002.json.gz');paths|={checked(v) for v in ctx['body_references']};m.save(RUN/'editorial-reviewed-001.json.gz',dict(at=m.now(),decisions=out,dependencies=[ref(p) for p in sorted(paths)],reviewer_reference=ref(Path(__file__).resolve()),policy='21selected additions,13dated/8unknown;4editorialholds and2alreadycatalogued. Allpriorqueues/holdsremain. Noexistingmetadataorholdingchanges.'))
 print(json.dumps(dict(new=21,dated=13,unknown_dates=8,already=2,holds=4)),flush=True)
if __name__=='__main__':main()
