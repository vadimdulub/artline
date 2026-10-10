"""Record remaining source-note and Vicenza physical-sheet review observations."""
import copy,importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('f',Path(__file__).with_name('museum-expansion-italy-fourth-facts-v2-20261008.py'));f=importlib.util.module_from_spec(z);z.loader.exec_module(f)
TEXT='''450|CampiGaleazzoVirginChildJohnRosaChristopher1500–49; tentative1503inscriptionversushistorylate1510swithinrange. Alenirejected.|aleni,campi
451|MeloneCalvary1500–10survivingfragmentof131x150paintingpartlydestroyedinwar; donotaddoriginalwholeasanotherwork.|melone,meloni
453|SecchiJerome1535copyCesareSestoBrerawithaddedlion/landscapeandflyonskull.|sesto,bernazzano
454|GattiVirginSebastianRoch1525formerGiulioCampi.|campi
455|OrsiMargaret16cformerlyParmigianino.|parmigianino,mazzola
456|Parmigianinoschoolwomanputtofresco16cprofileagainstfoliage; schoolqualifierpreserved.
457|ParmigianinoschoolCupid16c,separatefrom456womanputtocomposition.
458|GambaraCupidbutterflies1550–99decorativefragment; countphysicalsupportnotfigures.
459|Romaninosainthead1500–49,white/redrobe,blondpartedhair; different460profileand461curls/greygarment.|romanino,romani
460|RomaninoAddolorataprofile1500–49warmbrownredagainstlight, sourceafter1517fitsrange.|romanino,romani
461|RomaninoSaintheadheader1500–10versushistoryafter1517; holdchronology.|romanino,romani
462|RomaninoApostlehead1500–49obliquefigure/yellowredground,sourceafter1517.|romanino,romani
463|Magi16cformerlyyoungElGreco,nownamedVenetianMadonnaro/unnamedschool.|greco,theotokopoulos,theotokopulos
464|BoccaccinoGodBlessing16cpossiblysurvivingcimasa; formerBonifacioVeronese/FrancescoVecellio.|pitati,bonifacio,vecellio
465|BonifacioPitatischoolLevisupperca1550, preserveformerlyfirmcurrent-schooldistinction.
466|CarpioniBacchanal17c,possibleCarlointerventionnotfirmjointattribution.
467|VirginChildsaints1690s,VirginreadswhileChildsleeps,silencegestures; Cantarini/Creti comparisons.|cantarini,creti
468|ProcacciniJosephChild1590s, differentScarpaGallerysame-subjectversion.
469|ProcacciniDormition1600–49sourcehistorylate1610s,1973exhibitionnotcreationdate.
470|StephenBorromeo1650–74inv84; formerGimignani/Trevisaniunresolved, currentRomanSchoolkept.|gimignani,trevisani,romanelli,brandi
471|MachiavelliattributedVirginBartholomewMagdaleneMartinAnthony1450–74; comparisonPisaandDijonnotthiscomposition.|machiavelli,macchiavelli
472|BaldassarreBiagiocircleVirgin1460–70inv277, AmicodiBaldassarre, afterLippiMunichprototype.|lippi,baldassarre,biagio,boccati
473|ParenzanoattributedRoch1480–89inv228, separatependantSebastian229; possibletriptych/organwings.|parenzano,parentino,mantegna
474|ParenzanoattributedSebastian1480–89inv229, eightarrows/tree, separateRoch228.|parenzano,parentino,mantegna
475|LuccheseVisitation1484–90inv156/20/1IV; formerFrancescoGiorgio,Pacchiarotto,Neroccio,museuminventory20collisionawaitsreconciliation.|giorgio,pacchiarotto,neroccio,botticini,botticelli,filipepi,martini,ciampanti,montalcino
476|CiampantiattributedBarbara1490s,inventory9also496; manyformerattributions,holdinventoryreconciliation.|botticelli,filipepi,lippi,botticini,parenzano,parentino,bartolomeo,giovanni,garbo,raffaellino
477|MembriniVirginAugustineMonicaNicholasJeromeinv34; header1500–10versusdocumentaryhistoryca1492,hold.|lippi,rosselli,cosimo,membrini,lathrop
478|MembriniVirginStephenJerome1500–10inv42, formerPerugino/Francia/Brea; distinguishedfrom477different accompanying saints.|perugino,francia,brea,membrini,lathrop
479|Fredianicircle1487fauxtriptychJohnsRochinv167/37/7IV; inventory37shared497,hold.|frediani,buonvisi,lippi,garbo
480|CiampantimannerFrancisorphans1490sroundel325; onepanelwithpaintedfruitborder.|ciampanti,stratonice
481|ZacchiaAssumption1527inv43,S.Agostinoorigin; S.PierSomaldiAssumptionandS.SalvatoreResurrectiondifferentworks.|zacchia,ezechia
482|ZuccariKeysPeter1593inv440,StPierMaggioreBuonvisialtar, transferredseveraltimes; distinctPastorsMagicommissions.
483|PassignanoattributedPeterhealsca1593inv455/29; sourceexplicitPushkin72x56.7modelseparatephysicalwork.|passignano,cresti
484|GuidottiLibertyLucca1611inv361,largecanvaspairedSorriCallingPeterbutdifferentwork.
485|LuccheseVirginBishopMartyr1500–24inv365, fromPitti1925; Zacchia/Marti/Malatestadebate, retainunnamedschoolandquestionmarksaints.|zacchia,ezechia,marti,malatesta
486|LuccheseVirginAugustineJeromeMonica1559inv369dated; rejectedBrandimarte, copiesSartoPortaPintigroup.|brandimarte,sarto
487|FraPaolinoVirginCatherineDominicMagdalene1534inv448, distinct1538innerconventpalanowBibbiena; formerFraBartolomeo/SuorAurelia.|paolino,bartolomeo,fiorentini
488|BulgariniJohnpolyptychcomponent, sourcecategoryhold; no extra wholeensemblecreated.
489|UnnamedPopefresco1340–60inv564, formerAugustinetitle questionedbytiara; sourceprovenancePietrasantauncertainpreserved.|agostino
490|TrainiattributedMichael1340–60inv657, formerlytemporarilySanMatteoPisa, eventuallyGuinigi; comparePisasourceidentity.|traini
491|Fivesaintsoneextendedfresco1340–60inv464/1, notfiveartworks; formerSpinello influence rejected.|spinello
492|Starninapolyptychwinginv287,category/componenthold.
493|Starninaotherwinginv287/288shared287,category/componenthold.
494|NeriFrancescomannerVirgin1350–74diptichcompartment;categoryhold, formerPuccinelli.|puccinelli
495|AnguillacircleVirginSaints1400–24inv310oneassembleddossale; formerRosselloFranchi.|franchi
496|PriamoQuerciaMichaelstories1425–49inv147/9complexaltarwithmultiplepanels; shared9with476, holdphysicalunit/inventory.
497|AspertiniVirginGeorgeJosephJohnSebastianca1515–20inv37/II1; centralpanelwithlostBlaiseandSpadaChristopherwings, shared37with479,hold.
498|NeroniVirginBirthca1560–70inv346,CappellaAnzianicanvas; Beccafumi/Bigio/Francomodelsnotfirmmakers.|riccio,neroni,beccafumi,bigio,franco
499|BattistaFrancoVisitation1550–60inv347/III3, formerGirolamoMassei; checkexistingVisitationrecord.|semolei,massei,franco
500|MannuccibottegaMagdalene1600–49inv455/39,existingexacttitlecandidate; needsphysicalcomparison.
501|MannuccibottegaJerome1600–49inv455/20, pendantbishop455/24separatecanvas.
502|MannuccibottegaunnamedBishop1600–49inv455/24,pendantJerome501; donotnameasMartininference.
503|NicholasTolentinofire1709inv455/71, Venice1479depictednotcreation; FGNGanonymousinitials.
504|NicholasPurgatory1703inv455/70, otherPurgatory455/22sameyear508needsphysicalversioncheck.
505|Nicholasecstasy1707inv455/25,FGNGunknown, Scorsinistylesuggestionnotfirm.|scorsini
506|Nicholashealed1704inv455/21, MadonnaandAugustine/Monicaqualified; onecanvas.
507|Nicholasvision1703inv455/10,distinctfromecstasyandhealingcompanions.
508|NicholasPurgatory1703inv455/22,monksarchesversus504angelraisingonesoul,comparephysicalsizes.
509|Nicholastramplesdemonca1700–10inv359,narrowarchedcanvas,separatefiveFGNGstories.
510|FGNGHolyFamilyca1700–24inv455/46copiesTrevisaniMunich6123; pendantAnthony511anothercanvas.|trevisani
511|FGNGAnthonyChildca1700–24inv455/5,pendantHolyFamily510,differentsubject.
512|Jeromevision17cinv455/4 is a copy of Parmigianino1526–27Londonoriginal.|parmigianino,mazzola
513|IsabellaFiorentiniattributedVirginBarbaraDominictwoCatherines1632inv455/64; nunnameAurelia, preservesattribution.|fiorentini,bartolomeo
514|GherardiattributedLuccaRepublicca1675–99inv494,Serchioallegory,differentGuidotti1611largecanvas.|gherardi,coli
515|FarnetaCharterhouse18cviewinv380; dates1340–58 referbuildingsnotpainting.
516|MannuccibottegaChristSamaritan1600–49inv455/19,distinctMadonna/saintcanvases.
517|Flagellation1700–49inv455/3compositequotationRosselli/Sarto, onecanvas.|rosselli,sarto
518|SaniattributedGuinigiOrsetticoatarmsca1600–24inv656,donationGuinigifamily,marrriageoccasionuncertain.
519|HolyFamilywalkingwithyoungJesusca1675–79inv479,Cortonescoschool,historylate17cwith18c-lookingface,retainrangeandschool.|cortona,berrettini
520|CecchiattributedMassaciuccoliscavi1756inv418,paintingdocumentingfindsnotarchaeologicalobjects.
521|Lamentation1525–49inv239MissWrightgift,relatedPerinHermitagepaintingandMunich2555drawing; existingtitlecompare.|perin,perino,vaga
522|SorrowingVirgin1625–49inv455/51,initialsSMFunresolved.
523|Approvalreligiousrule1700–49inv455/68,probablefemaleAugustinianorder remainsqualified.
524|BishopAugustine(?)1500–49inv230formerlyIgnatiusandMartiattribution; frescoappliedwood1855, sourcequestionretained.|marti,ignazio
525|ZacchiaVirginRochSebastian1525–49inv275,Sardini1911,Brugierireplacementcopyinchurchandpreparatorystudyseparate.|zacchia,ezechia,brugieri
526|ZacchiaNativity1500–24inv32formerlyLorenzoZacchia1576confusion/Rossellischool, followsSpagnaVaticanwithlandscapechanges.|zacchia,ezechia,rosselli,spagna,perugino
529|CigolimannerFrancisc1590/1610inv237,armscrossed,tablewithcandle/skull/booksandhoodup,MissWrightgift.|cigoli,cardi
531|ReturnEgypt17cinv423,VirginChildJoseph; unknownmakerretained.
532|HolyFamilyJohn1512inv424, sourceexactyearretained; distinct18cFGNGfamily.
535|VirginMercy1600–1799inv455/17expresscopyFraBartolomeo; compareexistingoriginal/copy.|bartolomeo,porta
536|Deposition17cinv455/23,relinedonecanvasMaryJohnChrist.
538|Francisecstasy17cinv455/33with2men,relinedonecanvas.
540|Magdalene17cinv455/38holdscross, distinctpenitent455/39requiresphysicaldescription.
545|AbbotCapparoni17cinv455/47,relinedportrait; namedsubjectsourceonly.
546|AbbotDMinutoli17cinv455/48,relinedportrait.
547|AbbotBuzzaccarini17cinv455/49,relinedportrait.
548|BishopManfredonia17cinv455/50, enlargedandrelined; unknownpersonalname.
551|AbbotBuzzini17cinv455/54,enlargedandrelinedportrait.
552|AbbotBoccella17cinv455/55,relinedportrait.
557|BlessedArcangeloBologna17cinv455/61,relinedportrait.
559|Portraits559–564shareoldinscribed66, current455/66A–F; distinctsupportsneedconfirmation,donotcount6fromsuffixalone.
565|Assumption17cinv455/75,relinedonecanvas.
566|VirginChild16cinv477,old12clabelrejectedbyMonaco1966proposing15–16c; retaincurrent16cheaderandhistory.
579|ByzantineLamentation16cinv707priority,emptytitleheld; recoverliteraldescriptivetitlethroughseparatereviewwithoutinventing.
581|PietroTestaportrait17cprint,GiovanniCesareengraver,Pietrodraughtsman,Pasquinelligift; preservesroles.
582|Proserpinarapeprint121.1/2hasalternative121III1/3shared583; holdinventory.
583|Artsallegoryprint121.1/3sharedhistorical121III1/3with582; erroneoushistoryportraitwording,hold.
584|InnocentXallegoricaltriumphprint121.1/4,notportrait; Pasquinelligift.
585|Peterfreedangelprint121.1/5afterTesta,notoriginalpainting.
586|Sebastianmartyrdomprint121.1/6dedicationAbbotGhislieri.
587|Jeromeprint121.1/7Testa,inscriptionGiovanniGiacomoRossipublisher.|rossi
588|AchillesdragsHectorprint121.1/8Testa,Rossipublisher.|rossi
589|Peaceallegoryprint121.1/9Testa,MinervaVenus.
590|Iphigeniasacrificeprint121.1/10Testa,inventor/engraverrolespreserved.
591|VenusrestrainsAdonisprint121.1/11Testaattributed,qualificationpreserved.
592|Virtueallegoryprint121.1/12Testa,dedicationRondenino,Rossipublisher.|rossi
593|LastCommunionJerome17cprint121.1/13,CesareTestaengravesDomenichinoinvention,notVaticanpainting.|domenichino,zampieri
594|CharlesBourbonDukeLuccaprint19cinv121.1/14,inscriptionBerlin1828,makerrolesretained.
595|ChildportraitsourceCarloLudovicoversusinscriptionFerdinandoCarloheir; holdsubjectidentity.
596|CarloLudovicoentryLucca1833print121.1/17,Buonori,PortaSanDonatonuova.
597|MarsiliLorenzoNottoliniportraitprint19c121.1/18,Bertinilithographerinscription.|bertini
598|SanFrancescotemporaryfacade19cprint121.1/22,Marsiliinventor/DeSantiengraver.
599|Papi1835funerarymonumentprint121.1/19,Citti; notphysicalmonument.
600|NericiSanMartinosquare19cprint121.1/24,cathedralMichelettipalace,distinctothersquares.
601|SanMichelesquare19cprint121.1/25,possiblyMatraja/Nerici,keepanonymouslabel.|matraja,nerici
602|Forisportamsquare19cprint121.1/26,Verico/Matraja.
603|PietroSomaldisquare19cprint121.1/27,Verico/Matraja.
604|SanFrancescosquare19cprint121.1/28,Verico/Matraja.
605|Luccaplan1820Nericiprint121.1/31, distinct1843versions606/617.
606|Luccaplan1843print121.1/32cutandappliedvellum, compare617physicaledition/supportbeforecountingboth.|sinibaldi,bertini
607|1785Luccaracingamphitheatreprint121.1/36,Nericiengraver/DeSantiinventor.
608|LasinioCarloLudovicochild1803print121.2/1,lion/kingfiguresdistinct595.
609|Mansigardenoverallview18cprint121.2/11,GiustidrawingAngeli engraving.
610|Mansilargefishpondandwoodavenue18cprint121.2/12,separateview609/611.
611|Mansifishpondinsidewood18cprint121.2/13, distinctoverallpond610.
612|Mansicountryhousefront18cprint121.2/14,notpainting/physicalhouse.
613|Mansicountryhouserear18cprint121.2/15, differentfront612.
614|Mansivilla18cprint121.2/16 lacksview-specificinscription; compare612/613physicalcomposition.
615|Marsili19clithographangelwithlute121.2/23afterFraBartolomeo,notoriginalpainting.
616|Nocchi19cprintMagdalene121.2/24afterMurillo,Morghendirector; differentMannucciworkshoppainting500.
617|Bertini/SinibaldiLuccaplan1843print121.2/29,comparecroppedvellum-mounted606.
618|VogelVogelstein/ZoellnerLouiseBourbon1835print121.2/30,Dresdenpublisher, literalcreatorlabelspellingretained.|vogel,vogelstein'''

def main():
 prior=f.RUN/'source-editorial-working-001.json';x=copy.deepcopy(f.m.load(prior));rs={r['number']:r for r in f.m.load(f.RUN/'native-candidates-002.json.gz')['rows']}
 for line in TEXT.splitlines():
  p=line.split('|');n=int(p[0]);assert str(n) not in x['observations'];x['observations'][str(n)]=dict(source_id=rs[n]['source_id'],title=rs[n]['facts']['title'],note=p[1])
  if len(p)>2:x['extra_creator_terms'][str(n)]=p[2].split(',')
 for n,why in {461:'Header1500–10 versus historyafter1517.',477:'Header1500–10 versus documentaryhistoryca1492.',476:'Sharedinventory9with496.',496:'Sharedinventory9with476andcomplexmultipartaltar.',479:'Sharedinventory37with497.',497:'Sharedinventory37with479.',582:'Sharedhistoricalinventory121III1/3with583.',583:'Sharedhistoricalinventory121III1/3with582.',595:'SitterCarloLudovicoversusFerdinandoCarloconflict.'}.items():x['holds'][str(n)]=why
 x.update(at=f.m.now(),prior_reference=f.ref(prior),script_reference=f.ref(Path(__file__).resolve()));x['read_history_numbers']=sorted(set(x['read_history_numbers'])|set(range(450,619)))
 f.m.save(f.RUN/'source-editorial-working-002.json',x)
 # These63 drawings have now had source unit descriptions and relevant existing
 # object comparisons read; later final selection still checks all pinned evidence.
 identity=f.m.load(f.RUN/'selected-identity-003.json.gz');comps={v['number']:v for v in identity['comparisons']};notes={}
 chosen=[n for n,r in rs.items() if r['institution_id']=='51697e0d-bfe1-5fe0-adc8-287e1f65d079' and r['state']=='candidate' and n!=121]
 for n in chosen:
  v=rs[n]['facts'];description=' '.join(v['root_fields'].get(f.a.DC+'description',[]));notes[n]=v['creator_label']+'; '+v['date_display']+'; inventory '+v['inventory']+'. '+description+' One individually catalogued paper support; multiple studies, elevations, floorplans, pasted flaps or accompanying descriptive letters do not increase the artwork count.'
  if v['title']=='interno':notes[n]+=' Existing local Perrissinotti praying spouses and Gasparello studio are different figurative scenes and makers.'
  elif n in [140,141,142]:notes[n]+=' Existing Castegnaro1835 neoclassical rotunda is a different architectural subject/maker.'
  elif n in [139,695]:notes[n]+=' Existing Magagnato1938 Jewish cemetery is a different maker and period.'
  elif n==143:notes[n]+=' Existing Montefusco children name a different maker; this source explicitly identifies Perlotto daughters.'
  elif n==648:notes[n]+=' Existing DePisis1930 stilllife with a painted nude has a different composition/date; this is the1941 seated male figure on paper.'
  elif n==649:notes[n]+=' Source signed4.9.47 head watercolor; existing DePisis1942 seated young man is a different dated/composed work.'
  elif n==657:notes[n]+='1814PiusVII memorial design differs from LelioRossi1898ManfredoFanti project.'
  elif n in [661,662]:notes[n]+=' Ground-floor1076 andupper-floor1077 plans are separate sheets;140 is the exterior-elevation sheet79.'
  elif n in [663,664]:notes[n]+='1087(A) facade with pasted alternative and1088side elevation are distinct sheets; pasted flap is part of1087(A).'
  elif n in [673,674,675]:notes[n]+=' Three separately inventoried velarium project sheets have distinct recorded sizes; no extra count for the attached letter or flap.'
  elif n in [135,137,636,637,698]:notes[n]+=' Returned local views name other makers and different places or dates; no competing Picutti physical identity returned.'
  if n==137:notes[n]+=' Preserve literal source title Oviedo and inscription Ovieto as evidence; no city correction invented.'
  assert not comps[n]['source_hits']
 assert len(notes)==63
 f.m.save(f.RUN/'vicenza-editorial-working-001.json',dict(at=f.m.now(),notes=notes,deferred={121:'Bassano-mannerMagi needs physical-version comparison with sparse GerolamoBassano and otherMagi records.'},identity_reference=f.ref(f.RUN/'selected-identity-003.json.gz'),context_reference=f.ref(f.RUN/'comparison-source-context-001.json.gz'),source_reference=f.ref(f.RUN/'native-candidates-002.json.gz'),script_reference=f.ref(Path(__file__).resolve()),policy='Source/physical-unit review ready for final release review; no database additions yet. All review/publication/date/source safeguards remain.'))
 print(json.dumps(dict(observations=len(x['observations']),holds=len(x['holds']),vicenza_ready=len(notes))))
if __name__=='__main__':main()
