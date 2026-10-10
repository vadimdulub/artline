"""Explicit decisions for individually evidenced City Art Centre artworks."""
import collections,gzip,hashlib,importlib.util,json
from pathlib import Path
def module(name,file):
 z=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(z);z.loader.exec_module(v);return v
f=module('f','museum-expansion-city-art-additions-facts-20261009.py');i=module('i','museum-expansion-city-art-additions-identity-20261009.py');s=f.s;m=s.m;RUN=s.RUN;ref=s.ref;checked=s.checked
HELD={1:'Ramsay KatherineHall c1736 needs version comparison with privatelyowned NGSloanNGL001.08 and threequarterCityportrait, plus TateN06066LadyHall1752. CurrentNGS403accesshold;do notmerge different sitters/versions orborrowownership.',15:'Cameron GarmentWar creation unresolved;discovery sources disagreec1926/c1936. Keep conflict,notWWIvisit1917ascreation.',18:'Paolozzi exactCitybronzeedition/castdateunresolved;1946concretemodeldoesnotdatebronze. Needindividualcastsource.',19:'PowFallenAngels collectionidentified,but1945–2000exhibitionrange crosses1970. Seekobjectcreationdate.',20:'RobbCoolHouse collectionidentified butcreationunresolved;exhibition/acquisitionnotcreation. Seekobjectdate.',21:'BlackadderIrises collectionwatercolouridentified butexternal1982lead suggestsoutsidecutoff. Seeknativeobjectdate;otherIrisesversionsnotinterchangeable.'}
LINKS={12:'ad501e87-0f8e-5dc0-a5bf-5c2977390991'}
NOTES={
2:'Specific1886Cadenhead motherportrait withJapanese screen andgoldfish. Sourcecaptionandimage differentiateotherartists’ motherportraits,MacNicolGreenHat andCadenheadMaryLivesey. Fullcreatorpoolreviewed.',
3:'Cadell1914standingwoman bymantel withtallfeatheredblackhat. Tenexistinglocalimagecomparison includesfourCadellworks withdistinctseatedposes andsettings. AgnesCadellOrangeHat isdifferentmaker.',
4:'Kingc1907ArtNouveaudrawing namedFraunchyse inrecentCitygift. ExistingKingFrogPrince1913differenttitleandobject; otherKing/CharlesKing/ElisabethKing surnamehitsnotidentity.',
5:'BoughWindsorwatercolour24x34cm,oneRobinsonbequest1989object. Boughtonworks aredifferentmaker;noSamBoughsameobjectcandidate. Dateunknown.',
6:'McTaggart1887children crouchingonrockyshore depictedandcredited incuratorcaption. ExistingTateSummerSundownN06044,HarvestMoonN04701 andEmigrantsN04610 retainseparateobjecttitles/dates/inventories/sourcehistories;noexactobjectsourcecollision.',
7:'MacGregorMelrosec1919villagewithhillbehind identifiedinCitycuratorcaption. ExistingCarseLecropt,Fuenterrabia,Lochscene andotherMacGregor makersnotthisnamedtownscene.',
8:'JosephineHaswellMillerc1935canalhousewithbaretrees. OtherHaswellMillerartistArchibald andhisnamedToledo/Italianworks notthisartist/object;HawkinsLochshore differentmaker.',
9:'Cityc1905–1906horizontalPeploe darkstilllife withfruitplateleft,whitebluevaseandpink/whiteflowersright. Existing1919Tulips,1933BrownJar andGreyJar images differinorientation,objects,andcomposition. Tate1923TulipsN04224 isvertical61x50.8cm;WilliamWatsonPeploeKIRMG328differentmaker. Retaincuratorrange.',
10:'JohnDuncanAoife Highlandwarriorprincess,oilcanvas,explicitCitylenderitem1. FullDuncancreatorpoolincludingQueenSheba,AngusOg,Jephtha,MasqueLove,Phlegethon hasnoAoifesource/title. OthergallerylendersnotassignedCity. Unknowncreation.',
11:'JohnDuncanKingArthur receivingExcalibur,oilcanvas,explicitCitylenderitem3;notAoife,Tristan,Sheba,AngusOg orotherDuncanworks. Unknowncreation.',
12:'ExistingWikiArt1912TristanandIsolde,creatorJohnDuncan,restoredexactrawbody,andlocalimagewithlovers/potiononboat agreewithUniversityguideitem4TristanandIseult1912tempera. Unique matchingexistingobject currentlyunlinked andinreview. Addholdingonly;preservetitle,date,type,image,creatorlinksandstatus.',
13:'Robertson1917namedfellowambulancevolunteerGeorgeRomneyFoxdrawing,notWalter/Archibald/Andrew/SuzeRobertsonportraits. FullEricRobertsonpoolincludesDespair,Cartwheels,Cecile andFleetBay,noneidentity.',
14:'RobertsonShellburstc1919angularwartimepainting visuallycaptionedwithCitycredit. NotEricRobertsonDespair/Cartwheels/Cecile/FleetBay;allheldcurrentrecords preserved.',
16:'LewisNaomiMitchison1930–1932pencilwash46x36cm,seatedsitterbroochandcoiledhair,aliasTragicMuse. NotothernamedLewisportraitsMrsStix,EdithSitwell,Froanna,GladysHoskyns orSeatedNude.2000fundingnotcreation.',
17:'Fergusson1909BlueHat nativeholding andPallantdatedcredit;selected300pxreference shows sideprofilewoman,two glasses,cafétable. Distinctfromexisting1907AnneEstelleRice streetportrait and1950numberedhat closeup. Preservecopyrightlabel;noimageattachment.'}
def build():
 rs,errors=f.rows();assert rs==m.load(RUN/'candidate-facts-001.json.gz')['rows'];identity=m.load(RUN/'identity-002.json.gz');assert rs==identity['rows'];cs=i.comparisons(rs,identity['state']);assert cs==identity['comparisons']
 for fn in ['comparison-source-context-002.json.gz','physical-object-review-001.json.gz']:
  for dep in m.load(RUN/fn)['body_references']:checked(dep)
 out=[]
 for row,c in zip(rs,cs):
  n=row['number'];cap=row['source_capture'];raw=gzip.decompress((m.ROOT/cap['body_path']).read_bytes());assert cap['receipt']['status']==200 and hashlib.sha256(raw).hexdigest()==cap['receipt']['sha256'];assert not c['source_hits'];state='editorial_hold' if n in HELD else 'approved_existing_holding' if n in LINKS else 'approved_review_only_addition';note=NOTES.get(n,row['version_note'])
  out.append(dict(number=n,source_id=row['source_id'],institution_id=s.IID,state=state,facts=row['facts'],comparison=c,comparison_basis=HELD.get(n,note+' Full institution scope and bounded maker/title/source candidates reviewed. Similarity is discovery,not identity.'),version_note=row['version_note'],hold_reason=HELD.get(n),existing_artwork_id=LINKS.get(n),confidence=.94 if state!='editorial_hold' else None,confidence_kind='editorial assessment,not calibrated probability',basis='Exact collection narrative,curatorcaption,lenderlist orprimaryacquisitionfunder identifiesindividualphysicalwork. '+note,limitation='Collection association only;no currentdisplay,custodyorlegalownership claim. Existingmetadata/images/statuses unchanged. Unknowncreation andunlinkedmakerlabels explicit. Newsletterwinter2014bylineunspecified.',retrieved_at=row['retrieved_at'],source_capture=cap,source_record_reference=row['source_record_reference'],supplementary_source=row.get('supplementary_source'),physical_object_count=0 if state=='editorial_hold' else 1))
 assert collections.Counter(v['state'] for v in out)=={'approved_review_only_addition':14,'approved_existing_holding':1,'editorial_hold':6};assert sum(v['facts']['first'] is not None for v in out if v['state']=='approved_review_only_addition')==11
 return out
def main():
 out=build();paths={Path(__file__).resolve(),Path(f.__file__),Path(i.__file__),Path(s.__file__)}|{p for p in RUN.rglob('*') if p.is_file()}
 for fn in ['comparison-source-context-002.json.gz','physical-object-review-001.json.gz']:paths|={checked(v) for v in m.load(RUN/fn)['body_references']}
 m.save(RUN/'editorial-reviewed-001.json.gz',dict(at=m.now(),decisions=out,dependencies=[ref(p) for p in sorted(paths)],reviewer_reference=ref(Path(__file__).resolve()),policy='14newreviewworks,11dated/3unknown;1existing1912Duncanlinkedwithoutmetadataoverwrite;6holds. Priorqueues preserved.'))
 print(json.dumps(dict(new=14,dated=11,unknown_dates=3,existing_links=1,holds=6)))
if __name__=='__main__':main()
