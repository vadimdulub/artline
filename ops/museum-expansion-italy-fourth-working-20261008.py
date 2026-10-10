"""Persist editorial observations from individual source-note reading; not approvals."""
import importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('f',Path(__file__).with_name('museum-expansion-italy-fourth-facts-v2-20261008.py'));f=importlib.util.module_from_spec(z);z.loader.exec_module(f)
TEXT='''1|Copy of Crespi flea scene; Barber Birmingham prototype and Chicago copy explicitly separate. Header1708–1799 conflicts with closing seventeenth-century history.|crespi
3|Later copy of Correggio Il Giorno, not the Parma original.|correggio,allegri
4|Magdalene identified against former generic allegory; inventories7588/1881IV350/Poggio1124.
5|Ferrer flame identifies subject formerly called Dominic; Correggio copied-label attribution expressly a transcription error.|correggio,allegri
6|Generic Virgin; Dolci Annunciata and Furini comparisons are stylistic, not firm makers.|dolci,furini
7|Wheatear and Florence view possibly Crusca emblem; former VanderWerff manner.|werff
9|Partial panel copy after Titian mirror Venus, unlike NGA1552–55 canvas and Nemes/Stockholm variants.|titian,tiziano,vecellio,bronzino,dyck
12|Augustine identified by flaming heart and pen; former unnamed bishop.|giordano
13|Source says6553 belongs to another object; inventory/physical identity unresolved.|caravaggio,merisi,manfredi
14|Virgin Child John; Albertinelli/FraBartolomeo comparisons.|albertinelli,bartolomeo
16|Copy of SSAnnunziata fresco showing Virgin alone; pendantAngel7264 is another canvas.
17|Male head formerly Furini; MasterSolomon,Tournier,Vouet comparisons; badly damaged.|furini,tournier,vouet
18|Andrew after Cortona; previous Bolognese school.|cortona,berrettini
19|Holy Family4980 fromUffizi1881; Albertinelli,Sogliani,FraBartolomeo context.|albertinelli,sogliani,bartolomeo
20|Landscape source header17c versus history18c; nearly illegible and old inventory numbers uncertain.
21|Bartholomew source revised17c to16c; AndreaSarto context.|sarto
23|Eustace vision1590s, Muziano influence.|muziano
25|Baptist? Literal subject JohnEvangelist; Sagrestani tradition only, preserve original title.|sagrestani
26|Holy Family saints1690s; Mehus/Dandini context.|mehus,dandini
27|Vision of Lucrezia, subject qualifier preserved.
28|Nun praying perhaps Catherine, unspecified sixteenth-century prototype; no named saint invented.
29|Annunciation3541 transferred fromPoggioCaiano1910, historical5140/9689.
30|CainAbel reverse inventory inscriptions expressly not pertinent; hold.
31|Anthony Child18c versus earlier20c inventory; source chronology needs explicit reconciliation.
32|Naples landscape7397; FilippoNapoletano comparison.|angeli,napoletano
33|Flemish genre6866; formerTeniers, nowSteen/Ostade analogies.|teniers,steen,ostade
34|Marriage Virgin7598,Monteoliveto; Rosselli suggestion.|rosselli
35|Cassana attributed female head6577; UffiziCook1707 comparison not identical subject.|cassana
36|Roman tavern7303;17c header versus18c old inventory needs dating review.
37|Malehead7356 formerOttavioSemino, poor legibility.|semino
38|Two female hands6514: independently painted study copying detail of Titian Palatina Magdalene.|titian,tiziano,vecellio
39|HerculesOmphale7703 is one wooden tablet;7700/7701/7702 are different subjects.|giordano,ciocchi,dandini
40|Landscape7463 formerlyJohn+ChildJesus unreadable; defer subject identity.
41|Immaculate7357 broad ca1650–1850 source range retained.
42|JohnBoy7714 revised from17cFlemish; Correggio/Parmigianino/NiccoloAbate analogies.|correggio,allegri,parmigianino,mazzola,abate
43|Female martyr7350; companion6515 is another painting, Lippi circle suggestion.|lippi
45|Family scene4936 subject illegible; defer physical identity.
46|Luti attributed Virgin7129,exStApollonia1865; possible copy, preserve qualification.|luti
48|Malehead7681 copies Correggio ParmaDome Baptist detail; not originalfresco.|correggio,allegri,furini,bravo,ficherelli,pignoni
49|SeaStorm6538 Tempesta/Bril/Tassi/Filippo/Montagna analogies; generic version check.|mulier,tempesta,bril,tassi,angeli,napoletano,montagna
50|Landscape7065 Bril/Filippo/Tassi comparisons.|bril,tassi,angeli,napoletano
51|Bridgefigures6592 fromMonticelli; Domenichino/Dughet/MarcoRicci.|domenichino,zampieri,dughet,ricci
53|Landscape7654 erroneous Caravaggio transcription; comparisonRosa GrottaPalatina.|caravaggio,merisi,rosa
54|Annunciation6418 partial SSAnnunziata copy showing MaryANDangel, unlike Virgin-only7265.
55|FrancescaRomana guardianangel7548; RomanCortona context.|cortona,berrettini
56|Seascape monster7184 possiblyPerseusAndromeda; historicalTribunalePenale1913deposit requires custody reconciliation.
58|VenetoVirginChild6975,1450–1499 canvas,explicitByzantine influence; priority.
59|Magi7517 is a copy of Giordano Lappeggi work.|giordano
60|Fame7475; CesareDandini/Curradi context.|dandini,curradi
61|Landscape7481 current18c versus formerRoman17c; Borgognoneinfluence.|borgognone
62|Romanlandscape7074,Carracci tradition.|carracci
63|Allegoryvisualarts7509 pendant6743; Roxin/Benefial comparisons.|roxin,benefial
64|Empoli circle VirginChild7353, attached paper bib is part of onepainting.|empoli,chimenti
65|Magdalene6971withcross/skull; Allori/Cigoli analogies.|allori,cigoli,cardi
66|EcceHomo7381,Christopensside; Volterrano/Dolci prototype context, distinct111crossedhands.|volterrano,franceschini,dolci
67|Jerome3539 fromPoggioCaiano1910,old5141/9690; private devotion is function, not current ownership.
68|Dominic6979 star/lily/book; Reni/Dolci iconotypes.|reni,dolci
69|Teresa7149 formerlyDorinoLippi probablyDinozzo;7036/6412 different comparators.|lippi
70|BottiFrancesco attributed MaryJohncross7051, traces of attached cross do not create another work.|botti,curradi,pignoni,mehus,bravo
71|MagdalenaPazzi7489 identified against unnamednun and erroneous13c copy; Curradiproto.|curradi
72|Countryfair7707 maypole andgrandducalGG; onecanvas.
73|Venetocountryfigures6590 possiblyBassano seasons/months, exactmonth unknown.|bassano,ponte
74|CatherineSiena7386 erroneousSarto copy label,archaizing devotional.|sarto
75|Francis7203 generic prayer, compare77/90inventories.
77|Francis7370 beforecross; compare75/90, distinct inventories not sufficient alone.
78|Magdalene6527 formerCortona,Mehusstyle; DetroitJerome analogouscompositiondifferent subject.|cortona,berrettini,mehus
79|LuigiGonzaga6470 header17c, history18c; chronology conflict.
80|Flemishlandscape4982,18c almostillegible; physical version review.
81|ReturnEgypt7260 formerlyFlight/HolyFamily; literal corrected return title.|curradi,vignali,cortona,berrettini,ulivelli
82|Music7567 prior18c inventory,current17c,PietroRicchistyle; oldCoccapani/Rosi rejected.|ricchi,coccapani,rosi
84|MysticCatherine7730 twochildrenwithjug; Parmigianino/Bedoli/Calvaert variants.|parmigianino,mazzola,bedoli,calvaert
85|Battle7361 Borgognone manner; canvas pinned toboard, not separate panel.|borgognone,bavarese
86|Borromeo7251 woodpanel; compare118inventory6652.
87|HagarAngel7258 pendantRestEgypt7584/OA0900034903, anotherwork.|cortona,berrettini
88|Riverlandscape6595 Bril influence.|bril
89|Romanlandscape6492 formerlyVeronese; Bril/Elsheimer/Pynas/Carracci.|bril,elsheimer,pynas,carracci
90|Francis7531 current17c versus old18c, Caravaggesque; compare75/77.
92|ThomasAquinas7081 SantiDiTito/AlessandroAllori style.|tito,allori
93|Crucifixion6715 SantiDiTito school history; onecanvaswithmultiplefigures.|tito
94|SleepingChild6965 header17c,history18c, inscription attributionuncertain.
96|Dominic7483 header1600–1661,history18c only; hold.
97|JosephChild7257 Dandini tradition secondhalf18c.|dandini
99|Breastfeedingwoman7166 reverse1881number expresslynotpertinent; holdinventory.
100|RoseLimaChild7069 identificationcorrectsolder18c label; preservehistory.
102|EmilianMagdalene7292,DalSole style,cliff/tree setting.|sole
103|Francisstigmata7194 canvas copy of Cigoli1596signedwoodoriginalFuligno.|cigoli,cardi
104|Bishop7541 ovalimagewithinrectangularcanvas, onecopyexercise.
105|Nunfallingpriest5633 relinedcanvasappliedboard, Sagrestani/Crespi/Magnasco style.|sagrestani,crespi,magnasco
106|Kitchenwoman6950 sourcecorrectsold18c tolate17cFlemish.
107|AnneMary7329 Gherardini environment.|gherardini
108|GrecoAdriaticAnnunciation7243,slash1590/1610 agreesgraph; woodgoldarchaizing,VeroneseNGAprototype.|veronese,caliari
109|VenetianAnnunciation6536 sourceexplicitVenetoCretan,Accademiawaxmarks.
110|Beardedhead7040 formerNeapolitan,currentTuscanPillori style.|pillori
111|EcceHomo7144wood,handscrossedandfingersjoined,distinct66Christopensside.
112|Flemishlandscape7054 totallyillegible; generic version unresolved.
114|Romanlandscape7628 header17c versus historyold18c; pendant7627.
115|Redeemer6473 copySartoSSAnnunziata model.|sarto
116|RisenChristMagdalene6734,VenetoCretan,gold,exSanGirolamo; priority.
117|Vanitas7363 is astilllife, distinct2sleepingchildVanitas.
118|Borromeo6652 exAccademia1853,1825inv2666; compare86panel7251.
236|Finoglio attributedMaryQueenAngels1610–20, preserve young-work attribution.
237|Batoni attributedDianaEndymionca1730; Eton/Windsor drawing is a separate paper study.|batoni
239|Criscuolo attributedDormitionAssumptionMichael copiesGaetaAnnunziataDormitio.|criscuolo
240|Romanwomanbasketeggs1630–50inv30, replicaSpadarino; tentativepainterdaughterquestion retained.|spadarino,galli
242|Neri circleartichokeslettuceasparagusinv57, preservecircle qualification.
243|DucksSnakeinv58 oldBelvedere rejected forDeCaroinfluence.|belvedere,caro
244|Rivalta attributedkitchenstilllifeinv204,Magini/Levoli/Resani/Lodicomparisons.|magini,levoli,resani,lodi
245|HeaderLevoli1700–24 versus historyArcangeloResani: hold attribution/date conflict.
246|Travi circlelandscapeinv132; historyfirmer attribution doesnoterasecircle.
247|CatherineAlexandriatitle versus Siena description; hold subject identity.
249|Artemisia attributedMagdalene1640–45 smallpanel, comparisonsCavallinoCecilia/Stanzione not samework.|cavallino,stanzione
250|Habert circlefishcauliflower;1649Parisprototype comparison separate.|boucle,stoskopff,fyt,heem
251|FelixCantalicetitle versus AnthonyPadua description; hold subjectidentity.
252|Melendez attributedboybasketinv103 formerlyjointLorenzoTiepolo; preservecurrentqualification.|tiepolo,melendez
253|Germanheader versusEnglishhistory; nationalIDhyphenconflict, hold.
255|MasterBarletta attributedVirginChild; Sabatini/Raphael/Machuca comparisons.|sabatini,raphael,raffaello,machuca
256|Soens attributedBaptist smallcopperinv218, Carracci1585Baptism comparator not this work.|carracci,soens
258|Verdier temptation1690s explicitlyanotherLouvreversion; history saysattributed, appendqualification before release.|verdier
260|Champaigne workshopChristfallsinv182; formerLeBrun/Bourdon suggestions.|brun,bourdon,champaigne
261|LeSueurLaurencemartyrdom is preparatorybozzetto, notBoughtonHousealtarpiece.|sueur
262|ArtemisiaProcnePhilomela1630–40 historysaysattributed, retainqualification; possibleCodazzicollaborationnotfirm.|gentileschi,codazzi
264|HeaderMeica1650–60 versus historyBorzoneearly1620s; hold.
265|Bourdon attributedbaccanale1634–37 showsMediciVase, not the vase object.|bourdon
266|HeaderBaglioneselfportrait versus historyLionelloSpada; hold.
267|Readerinv70 largerreplicaofLecceCastromediano, currentMasterAnnunciationcircle preserved.|fracanzano
268|Nome attributedSebastian1620–30 smallcopper, imaginedclassicalarchitecture; not NomescapodimonteTitus.|nome,desiderio,barra
269|Dughet attributedlandscapeboZZetto1640–45, distinctWalpolefinishedpainting/CorsiniRinaldo/Arezzo comparisons.|dughet,poussin
270|Swanevelt1648signeddatedmountainsruinspastors, comparePoussinRouenTempestmodel.|swanevelt,poussin
271|Francisinv185,Naplesschool1651–75replicawithvariantsofReniGerolamini.|reni
272|OttinocircleBorromeoVirginplagueinv216, bozzettoforVeronachurchwork.|ottino
274|SpinelliattributedMercuryArgus,1630s–60s documentedcontextnotassertedfirm.
276|SpinelliattributedPanSyrinx(?) subjectquestion retained.
277|CastelloattributedBenedettoGiustinianiportrait published1997privateRome, historicprovenancenotcurrentprivateholding.|castello
278|DeLioneattributedunidentifiedmyth/biblicalscene; preserveunknownsubject.|lione,castiglione,grechetto
279|DeBellisattributedIsaacsacrifice1640–50; BudapestMoses/MilanNoahcomparatorsdifferentevents.|bellis
280|BonziCallingPeter1620–30 historysaysattributed, appendqualification.|bonzi
282|Rosa circleMercuryArgus1640–60, Sydneyversionseparate.|rosa
283|FracanzanoattributedAnthonyPaulraven1640–50bozzetto, distinctLecceReader.|fracanzano
285|FilippoNapoletanoMarine1610–20 historysaysattributed, appendqualification.|angeli,napoletano
286|Stomerattributedprophet/evangelist1630–40; formerCaraccioloFinogliaVitale.|stom,stomer,caracciolo,finoglia,vitale
287|CeranoVirginhead1600–24 historysaysattributed, appendqualification.|crespi,cerano
288|BizamanoworkshopRedeemerFrancisBernardino1540s,Cretanpriority; BariVirginCatherine isanothercomposition.|bizamano
289|ScupulatitleemptyandoriginallyjoinedFrancisstigmata companion; holdphysicalunit/title.
290|BathasattributedVirginChild lacksarchangels ofBarlettaversion; DamaskinosHellenicVeniceprototype, possibleRitzos.|bathas,damaskinos,ritzos
293|VouetschoolMargaretinv197 expresslyancientcopy ofHartfordoriginal, notbozzetto.|vouet
294|DeFerrarischoolXavierdeathheader1700–24 versus historylast17cdecade; holdchronology.
296|PinoschoolShepherdsca1568–77cropcompositionfromLouvredrawing22474/Cortprint; differentRuvo/MarenaMagicanvases.|pino,cort
297|Farinelliportrait1740–60inv87,Falciatore/Fabris context.|falciatore,fabris
298|Spanishmalebust1824–28inv161formerlyGoya.|goya
299|Domenicanfriar1567–77smallpanel attributedElGreco inhistory; Longhicopperisdistinct, appendqualification.|greco,theotokopoulos,theotokopulos
300|Thornscrowning1626–50paintedonbackofetchedcopperplate; countonephysicalplate.
302|HeaderJanMielselfportrait versus historyPieterVanLaer; hold.
303|SweertsWomanToilet1646–54 another version ofSanLucaBellaToeletta.|sweerts
306|AdriaticSainthead1300–49survivingfragment,backGiovanniRiminiZeriattribution.|rimini
307|MarchesschoolFlagellation1590scopyFedericoZuccari.|zuccari,zuccaro
309|FiginoattributedBorromeo1590swalnutpanel, compareCenacolocopiesonlyphysicalevidence.
310|HerculesNessusDeianira1700–49smallmonochromepanelinv217.
316|HeaderDeVitoeruption1790–1810 versus historyFabris; holdmaker/date.
317|HeaderWilliamHamilton versus historyGavinHamilton; holdidentity.
318|GericaultattributedRedSeaboZZetto1815–24; historydeath1924typonotcreationdate.|gericault
319|Jerome1776–1800inv222,pendantMagdalene signedTischbein; distinctpainting.|tischbein
320|DellaGattawomanCapuchin1800–24inv180,gouache.
323|EnglishAssumption1790spossibleBenjaminWest/Americanschool; preservequalifiedschool.|west
325|TomaattributedOphelia(?)1870–80,oralDevannaproposal notfirm.|toma
326|SouthItalyputti1741–60inv172oldGimignani rejected.|gimignani
328|PortaNicolaMadonna1730–40afterGiaquintoMolfetta1726–27variants.|giaquinto,porta
330|RomanChristthorns1700–24inv98copyReni.|reni
332|NaplesPieta1740–60inv227Solimena/DeCaro circle.|solimena,caro
343|Frescobishopheadhandpastoral,formerlyBembo.|bembo
347|FrescoVirginChildmartyr ca1415, differentdated1410source353; possibleGiovanniBembo.|bembo,moretti
351|BemboattributedCosmasDamian1448,formerBenedetto/Zavattari.|bembo,zavattari
352|Virginrosegarden1450–99fresco nearBenedetto/BonifacioBembo, Gardnerfragmentscomparative.|bembo,besozzo
353|VirginChildmartyr1410datedinscription, distinctfragment347ca1415; comparephysicaldimensions.
355|VirginChild15cpanel sourceVenetoCretanartisan/byzantinerepertoire; priority.
356|VirginChild15c embossedcopperauras,goldground; distinctwood/frescoversions.
357|ChristfromtombPassionca1430–40GregoryMassiconography, LorenzoMonacocontext.|monaco
358|BemboVirginMercy1450–60,formerBenedetto, distinctcentralcoronation359.|bembo
359|Centralpanelofreconstructedtriptych; twoDenverwingsexplicitlyotherphysicalpanels, notwholetriptych.|bembo,zavattari
390|Bembocirclemonkand2devoteesca1460smallfragmentpanel,oneexistingphysicalunit.
394|GerolamoBemboVirginangels1468–69,previously1478Romano/Gerolamo; preservecurrentdate.|bembo
395|Oldheadwithwidegreenhatandred/yellowgarment, explicitlycompareanotheroldhead397; inspectdimensions.
396|VirginChildsaintfresco15c relatedtoCemmo; compareRochSebastian398differentfigures.|cemmo
397|OldheadgreenhatANDgreengarment, sameoriginas395differentfragment; inspectdimensions.
402|ErriVirginChildca1460half-lengthinbiforastonewindow.|erri
403|WinkingEyesMasterVirgin15c hasFerrara/Blumenthal/Lucernereplicas; distinguishversions.
404|WinkingEyesMasterBernardino15csamedimensionsas403butdifferentsaint/panel.
405|ThronedVirginca1480Ferrara/Bembo/PieroFrancescacomparisons.|bembo,francesca
406|CornaNativityJohn1490–1510formerParenzano; BagattiValsecchiprototypecomparison.|parenzano,parentino,corna
407|CornaRaphaelTobias1490–1510formerlyAltobelloMelone, currentfresco.|melone,meloni,corna
408|CornaVirginadoringChild1490–1510fresco,treestwoshields, distinct407angelTobias.
409|VirginChild15cgothicthronegoldgarden,Vivarini context.|vivarini
410|Nativityca1520anonymousBoccaccinocontext, distinct1490–1510Corna.|boccaccino
412|BeciVirginChild1500–49formerlyTacconioldinventoryA126.|tacconi,beci
415|VirginChildJohn16ctondoinsquareframe, weakimitationLorenzoCrediBorghese.|credi
416|BissoloJerome1490–1510formerlyPalmaVecchio, littlecrucifixupperright.|palma,bissolo
417|GiovanniAgostinoLodiJerome16cformerlySolario; darkrobeandlargeheldcross.|solario,lodi,boccaccino
418|Bishopca1450fullfiguregoldground, distinct343frescoheadfragment.|moretti,badile,vivarini
419|Bernardino15c Foppa/Bergognonecontext, distinct404namedMasterpanel.|foppa,bergognone
420|Martyr15c saltirecrossperhapsAndrew, preserveunnamedtitle.
425|MansuetiTrinityFrancisBernardinoca1495formerCiverchio; NGA? LondonNG/SanSimonecomparisonsdifferentworks.|civerchio,mansueti
427|Fivefresconotices427–431sameanonymousauthor, distinctsubjectsbutphysical-supportverificationrequired.
432|Triumphalprocessions432–434couldfragments/samefrieze; do not countwithoutdistinctsupportcheck.
435|BembinoVirginChildJohnNicholas16c, damagedbyFochetzer18crepair, not18ccreation.|bembo
436|Header15c versus SabatinifollowerRaphaelesquemanner: dating/author context requiresreview.|sabatini,sesto
437|CamilloBoccaccino1544VirginMichaelAmbrogio, Brera1532 isotheraltarpiece.|boccaccino
438|BagnacavalloVirginFrancisZachariasJohn16c formerEmilianschool.|ramenghi,bagnacavallo
439|Charitablesaint15c headerBembino,historyBagnacavallo/Carpinoni/Vetraroreassignments; reconcile.|ramenghi,bagnacavallo,carpinoni,vetraro,bembo
440|Michael15c fragment companion439, historyendsBemboreassignment; version/datechecks.|ramenghi,bagnacavallo,carpinoni,bembo
441|MazzolinoVirginPeterAnneca1522–24formerDosso; BerlinDisputationdifferentcomposition.|dossi,dosso,mazzolino
442|AntoninoDeFerrariSaintlife2scenes1400–45onefrescowithinternalpaintedframes,not2works.|ferrari
443|Header1530–35 conflictswithhistoryca1490andsourceartistdeath1510; hold.
444|Lazarusca1530–35onepanel, companion445Supper; Parmigianinoetchingprototype.|boccaccino,parmigianino,mazzola
445|LastSupperca1530–35anotherpanelpairedLazarus444; preserveindividualphysicalunit.
446|SofonisbagentlemanformerlyVincenzoCampi, compareversions.|campi,anguissola
447|VincenzoCampimannercalvary1550–99formerlyBernardinoCampi; ChristnailedonGround,twohorses.|campi
448|AleniChristblessing1500–49formerlyGaleazzoCampi; sourceearly16c.|campi,aleni
449|Aleni1515VirginadoringChildJohnAnthonyangel, Breradepotprecedingversiondistinct.|aleni'''
HOLDS={1:'Creation chronology conflict in historical note.',13:'Explicitly wrong inventory number.',20:'Source date and old inventory uncertain.',30:'Inventory inscriptions expressly not pertinent.',31:'Conflicting historical dating requires review.',36:'Historical dating discrepancy.',40:'Illegible subject with former identification.',45:'Illegible family subject.',56:'Historical court deposit needs custody reconciliation.',79:'17c header and18c history conflict.',94:'17c header and18c history conflict.',96:'1600–1661 header versus18c history.',99:'Reverse inventory numbers expressly not pertinent.',114:'17c header versus18c history; companion needs review.',245:'Levoli/Resani maker-date conflict.',247:'CatherineAlexandria/Siena subject conflict.',251:'FelixCantalice/AnthonyPadua subject conflict.',253:'SourceID andschool conflicts.',264:'Mei/Borzone maker/date conflict.',266:'Baglione/Spada selfportrait identity conflict.',289:'Empty title and joined-compartment identity.',294:'Header18c versus historylate17c.',302:'JanMiel/PieterVanLaer selfportrait conflict.',316:'DeVito/Fabris identity conflict.',317:'William/GavinHamilton identity conflict.',436:'15c range andlatermannerism attribution require reconciliation.',439:'Conflicting attribution history.',443:'1530–35 header versus1490 history and1510 artistdeath.'}
def main():
 source=f.RUN/'native-candidates-002.json.gz';rs={r['number']:r for r in f.m.load(source)['rows']};obs={};extra={}
 for line in TEXT.splitlines():
  parts=line.split('|');n=int(parts[0]);assert n in rs and n not in obs;obs[n]=dict(source_id=rs[n]['source_id'],title=rs[n]['facts']['title'],note=parts[1]);
  if len(parts)>2:extra[n]=parts[2].split(',')
 f.m.save(f.RUN/'source-editorial-working-001.json',dict(at=f.m.now(),observations=obs,holds=HOLDS,extra_creator_terms=extra,history_attribution_qualifiers=[258,262,280,285,287,299],read_history_numbers=list(range(1,119))+list(range(236,336))+list(range(336,360))+[r['number'] for r in rs.values() if 390<=r['number']<=449 and r['state']=='candidate'],source_reference=f.ref(source),script_reference=f.ref(Path(__file__).resolve()),policy='Manual source-note observations and comparison-only former/prototype maker terms. No artwork approval. Remaining physical identities, historical inventories, supports and dates require review; title strings and comparison terms do not rewrite catalogue metadata.'))
 print(json.dumps(dict(observations=len(obs),holds=len(HOLDS),extra_terms=len(extra))))
if __name__=='__main__':main()
