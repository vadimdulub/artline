"""Individual editorial decisions; source facts and physical units stay explicit."""
import collections,copy,importlib.util,json,re
from pathlib import Path
z=importlib.util.spec_from_file_location('s',Path(__file__).with_name('museum-expansion-italy-third-supplement-v2-20261008.py'));s=importlib.util.module_from_spec(z);z.loader.exec_module(s)
i=s.i;f=i.f;m=i.m;RUN=i.RUN;ref=i.ref;checked=i.checked
working=m.load(RUN/'oderzo-editorial-working-001.json');NOTES={int(k):v for k,v in working['notes'].items()}
for n in [69,71]:NOTES[n]+=' The returned Martini Nel sonno is a separately sourced1906–1907 oil canvas,65×80cm; this is an ink illustration sheet with a dwarf, not that painting.'
NOTES.update({
126:'Manfredini Francesino,1912 pastel on paper, catalogued as a gift from the artist to Trucco. Different author/subject from the Trucco portraits; no same-maker identity returned.',
127:'Giglioli, called Cirillo: caricature of Signora Macchi with doves,1900–1924. Existing Trucco India, Rosetta and other portraits have different authors and subjects. Preserve the Cirillo attribution and range.',
128:'Trucco Idillio messicano,1950–1960 watercolor on card. One individually catalogued composition; returned global Figure records name other artists and media. No matching Trucco identity returned.',
158:'Trucco ballerine,1928–1960 charcoal/watercolor drawing on paper. Preserve the broad creation range. Other Dancers hits are works by Degas, Picasso, Dehn and other named artists; no competing Trucco drawing returned.',
166:'Spagnolo fisherman in sunlight, individually inventoried painting. The maker/subject search returned no physical identity conflict; date and source inventory retained.',
167:'Micali portrait of Damaso Bianchi. Named sitter and maker distinguish it from the existing Bari portraits; no competing identity returned.',
168:'Fourteenth-century fresco of George and the dragon. One catalogued painted object, not the entire church decoration; no duplicate source or existing identity returned.',
169:'Saint Stephen,1290–1299 fresco. The source records territorial public-body custody; preserve detenzione as custody evidence, not an ownership assertion.',
170:'Saint Vincent and Saint Theodore,1290–1299 fresco on canvas. Both saints belong to one catalogued physical work; do not create two artworks from its figures.',
198:'Twelfth-century fresco of Andrew the Apostle. Preserve the unnamed school label, explicit range and physical medium; no conflicting identity returned.',
201:'Burgundian-school Saint Michael with saints,1490–1510 panel. One individually inventoried panel; no whole-cycle or figure count inferred.',
202:'Cretan-school Christ carrying the cross,1550–1599 panel. Preserve school attribution and unknown named maker. Recorded Bari custody supports inclusion; no current display inferred.',
203:'Marco Pino Trinity, sixteenth-century panel. Different period/support and subject from the selected eighteenth-century Trinity appearing to Casimir; no competing identity returned.',
204:'Byzantine-school Holy Family with Catherine of Alexandria, sixteenth-century panel. Existing Giaquinto and Manfredi Holy Families name different accompanying saints, periods and makers; Vaccaro Catherine is an individual saint.',
206:'Venetian-school Magdalene,1600–1610. Individually inventoried painting with no identity conflict returned; retain school label rather than invent a named author.',
208:'Seventeenth-century Announcement to the Shepherds, attributed in the catalogue to the named anonymous master. Earlier Mantegna/Perugino and Carracci Adorations are different compositions. Search translations are not replacement titles.',
209:'Master of Cain and Abel: Sebastian tended by the pious women, seventeenth century. Returned Mantegna and Perugino tied/standing Sebastian compositions are earlier works by different masters; preserve the named-master label.',
211:'Ippolito Borghese Pieta,1600–1610. The similarly named Borghese di Piero fourteenth-century multi-scene object is a different maker and physical work. Territorial custody retained literally.',
212:'Neapolitan-school Mystic Marriage of Catherine, seventeenth century. The Bari Malinconico Agatha martyrdom comparison depicts a different saint and event.',
213:'Fracanzano philosopher,1625–1649. Preserve the question mark in the subject label. No conflicting same-maker physical identity returned.',
214:'Gargiulo Sebastian martyrdom, inventories1557/95D/975. De Caro Addolorata candidate222 shares1557 and stays outside this release pending inventory reconciliation; Malinconico Agatha is a different subject.',
215:'Stomer Peter released from prison by an angel, seventeenth century. Individually inventoried canvas; no competing physical identity returned.',
216:'Neapolitan-school Christ mocked,1600–1649. Preserve the unnamed creator and catalogue date range; no conflicting identity returned.',
223:'Attributed De Matteis Baptism,1690s. The Scupula Resurrection, Ascension and Flagellation comparisons depict other events and belong to an earlier maker. Attribution qualifier preserved.',
224:'Celesti Adoration of the Shepherds,1690s. Scupula Passion scenes and Ciennatiemo Matthew calling are different events and makers.',
225:'Eighteenth-century Flight into Egypt. Literal deposito occurs inside the verified current museum location and means storage here; no external-deposit destination or current public-display claim inferred.',
226:'Saint Januarius,1700–1749. Current museum record includes the storage label deposito; retain that evidence and do not present it as fresh on-view status.',
228:'Tiso workshop Dream of Joseph. Existing Tiso Dream of Jacob depicts a different biblical person/event. Workshop qualification and independently inventoried canvas retained.',
231:'Two smiling male figures,1790–1810. One painting containing two figures, not two artwork records. No identity conflict returned.',
233:'Eighteenth-century Carmelite saint, with the source question mark preserved. Unknown individual identity and school remain qualified; no conflicting physical work returned.',
235:'View of Santa Maria della Salute in Venice,1760–1799. Named architectural view and inventory retained; no matching physical identity returned.',
237:'Harbour view,1750–1774. Existing Pastina Rome profile is a1922 view of a different city; preserve the original source attribution and range.',
238:'Seventeenth-century child portrait. Existing Volpe girl is a late-nineteenth/early-twentieth-century work; the Madonna and Postiglione mother-and-child scenes depict other subjects.',
239:'Eighteenth-century Roch with angel. One individually inventoried painting, no duplicate identity returned.',
240:'Carella Healing of a Cripple,1766,inventory1622/526. Candidate241 Isaac blessing Jacob shares526 and is deferred for reconciliation; no competing existing work returned for this healing scene.',
245:'Stanzione Apollonia,1625–1649. Existing Bardellino Anthony Abbot represents a different saint and period.',
246:'Eighteenth-century Trinity appearing to Casimir. Distinct accompanying saint and period from the Marco Pino Trinity panel; count one canvas.',
247:'Nineteenth-century Salento-school praying Virgin. Earlier Giaquinto Immaculate Conception is a different composition and maker; preserve school label.',
250:'Spagnolo violinist, circa1890–1936. Different subject from his selected fisherman and Perotti portrait; no matching identity returned.',
251:'Spagnolo Armando Perotti portrait. Existing Passaro Riccardo Ferrara and Volpe young girl depict other named sitters/makers.',
252:'Piccinni smiling girl in profile, lithograph, circa1860–1920. Source describes hair covering the left eye and hatching. Netti interior study is a different maker, medium and scene.',
253:'Laudati Richiamo,1931 seated female figure. Individually inventoried painting; no conflicting physical identity returned.',
286:'Landucci manner, circa1830 young male half-length,inventory745. Separate from existing Landucci black-bearded man and the female pendant746; preserve maniera rather than firm authorship.',
287:'Landucci manner woman with cuffs and shawl,inventory746. Female pendant to745, not the male painting. Earlier Suttermans/Luchi and later named widow portraits have distinct source identities.',
289:'Cecchi Elijah before Ahab and priests,inventory455/36,circa1823–1825. The1822 commission is history, not an invented exact creation year; no competing identity returned.',
290:'Paolini-school silk merchant,inventory13(5018),1675–1699,tying a torsello bale. Subject and dated school distinguish named Van Diemen and Santini portraits.',
291:'Austrian officer,inventory22(5027),1800–1810,pale-blue uniform,plumed hat and sword belt. Retain unknown maker; the Austria-related Medici woman is a different sitter.',
292:'Ecclesiastic in purple vestments against dark background,inventory21(5026),seventeenth century. Separate from cardinal24(5029), whose hands/book and liturgical objects define another canvas.',
293:'Paolo Antonio Parensi,inventory11(5016),1725–1749,aged man with pronounced jaw. Source expressly identifies another replica at Palazzo Orsetti2494/OA0900522864. Existing Girolamo Parensi is a different sitter.',
298:'Maria Gualanducci,inventory8(5013),1650–1674,hand touching hair. Preserve anonymous attribution; the Anna Maria Van Diemen and named Santini portraits are different sitters.',
300:'Cenami Luisa Borromei,1909,inventory6930,pastel on canvas,standing at table in striped clothing and green hat. Other returned portraits depict different named sitters and periods.',
306:'Inventory127,1600–1649 central-Italian copy of Tintoretto Saint Mark freeing the slave. Source explicitly calls this a later copy, not the Accademia1547–1548 original or the related sea-rescue/recovery scenes.',
307:'Attributed Scaglia Antonio Santini,inventory35/I87,circa1640–1660. The source inscription identifies the seven-year-old boy with the estate and Mercury statue. Helst male adult portraits and girl are different subjects; retain qualified attribution.',
309:'Reschi assault on a fortress,inventory161,1650–1699,bridge and fortified gate with artillery and dead/wounded foreground figures. No physical identity conflict returned.',
313:'Battista Franco Deposition,inventoryCom128,1538–1540,formerly attributed to Daniele da Volterra. Its national object, source description and chronology distinguish Volterra1545 fresco; preserve former attribution in history.',
316:'Federico Zuccari selfportrait,inventory126,circa1585,scroll and PhilipII medal. Source expressly distinguishes the earlier San Luca and later Pitti versions and documents transfer from Uffizi to Lucca1847.',
321:'Barocci and Vitali Federico Ubaldo,inventoryCom100,1607,two-year-old in red with racket and ball. Existing Vitali infant in cradle1605–1606 has a different age/composition. Preserve joint attribution.',
322:'Zacchia Ezechia selfportrait(?),inventory171,1519,man pointing to a cartello. Preserve question mark and historical Bacchiacca/Flemish suggestions; named Medici/Bronzino subjects and later Lucca selfportraits are different works.',
323:'Tuscan old man with cap,inventory157,1550–1599,fur-trimmed black clothing on yellow-brown ground. Earlier doge/jurist suggestions remain qualified; returned Bronzino women,children and named Medici portraits are different subjects.',
327:'Bonifacio de Pitati manner Holy Family with Catherine,inventory169,sixteenth-century panel: Child leans toward Joseph at left,Catherine at right. Other returned paintings have Barbara,Tobias/Raphael or Dorothy and different compositions.',
329:'Catena circle Holy Family with John,inventoryCom136,circa1500–1531,Child gives apple to Joseph,John at left. Historical Licinio and Vincenzo delle Destre comparisons do not create authority links; individual Baptist paintings differ.',
330:'Beccafumi Continence of Scipio,inventory162,1525–1530,cassone front. The source distinguishes the Siena Bindi Sergardi fresco. Restituita describes the legendary captive bride, not return of the physical painting.',
339:'Peeters circle Brabant port,inventory186,1700–1710,moored ships and a city with two towers. Preserve qualified maker and uncertainty over a proposed historical collection inventory; no competing physical identity returned.',
349:'Manfredi circle caricature,inventory153,seventeenth century,weeping man holding hand to eyes under brown hat. Historical Caravaggio label remains source history; no matching physical identity returned.',
355:'Ecclesiastic,inventory24(5029),1600–1610,white garment/purple cape,book and liturgical objects. Distinct from21(5026)purple-vested man; both are independent canvases, not title variants of one record.',
356:'Saint Pietro Parenzo,inventory15(5020),1690–1710,axe and sword. Preserve the saint label and unnamed maker; no matching physical identity returned.',
357:'Gasparo Mansi,inventory17(5022),1650–1699,elderly man holding letter. The pre-lining inscription identifies Mansi; existing Gaspare Van Diemen depicts another sitter.',
358:'Ottavio Mansi,inventory18(5023),1690–1699,posthumous portrait with letter dated3December1691. Preserve the range, not an inferred manufacture date from the letter.',
359:'Emilian widow,inventory16(5021 as literally recorded,circa1590–1610,book and armchair. Unknown maker and malformed inventory punctuation retained; returned CosimoI is a different sitter.',
361:'Early-eighteenth-century Alexander scene: one canvas with seated king,kneeling elder,dignitaries and soldiers. Plural Stories in the title does not create multiple artwork records; inventory remains unknown.',
362:'Dal Sole workshop Minerva generating the olive,1700–1710,one central ceiling painting. The broader multi-wall mythological suite363 remains excluded, preventing ensemble/component double counting.',
365:'One Massoni-gift still-life canvas,inventory747,blackbird/other birds with peaches and cherries. Separate physical pendant from748–750; no additional four-picture ensemble counted.',
366:'One Massoni-gift still-life canvas,inventory748,duck with peaches and pomegranate. Different birds/fruit composition from747,749,750.',
367:'One Massoni-gift still-life canvas,inventory749,snipe and mushrooms. Separate canvas in the explicitly documented four-picture group.',
368:'One Massoni-gift still-life canvas,inventory750,thrush,nuts,chestnuts and mushrooms. Distinct from the three other individually inventoried pendants.',
372:'Brandimarte Magdalene,inventory455/37,circa1590–1599,cross,ointment and book. Existing Schiavone and Scaglia Magdalene records have different makers/periods and independently catalogued identities.',
373:'Lucchese-school Virgin with sleeping Child,inventory320,circa1640–1660. Explicit later copy after Reni Doria Pamphilj1627; source rejects identification with the1819 Grotta-house copy. Other Reni prints and multi-saint compositions remain separate.',
374:'Anonymous Lucchese portrait labelled Selfportrait of Pietro Testa,inventory260,circa1650–1699. Source questions physiognomic identity against UffiziA931. Retain literal title and school, without assigning Testa as creator.',
375:'Attributed Luchi Holy Family,inventoryOSL243,circa1740–1760,Child reaching to Anne. Former Tuscan seventeenth-century opinion remains history; not the1759 Guamo prototype.',
376:'Cortonesque Guardian Angel,inventory713,circa1675–1699. Retain the school/follower label; comparison search for Cortona/Berrettini produced no competing identity.',
382:'Bruno Cordati selfportrait,1925,inventory396. Source medium says Tela only; do not invent oil technique. Returned Campriani,De Servi and Ridolfi selfportraits depict different makers.',
403:'Ridolfi1817 tempera cartoon on card,inventory206/92I,Christ with five saints. Preparatory object is distinct from the finished Macerata painting. The1875 municipal-Pinacoteca deposit is historical; current object and museum URI locate it at Mansi.',
404:'Checchi Mansi estate at Moriano,inventory25(5030),eighteenth-century drawing on paper,bird-eye view. Utens comparison is stylistic; maker lifespan is not substituted for creation range.',
405:'Parensi family tree,1695,drawing on paper with founder and Lucca walls. Count one physical drawing, not the people in its genealogy; separate subject/support from both deferred Mansi family trees.'})
PISA_NOTES={
410:'Mariano da Scorno,inventory4553,seventeenth century. Named male sitter; related Ceci Ferrari gentleman1791 has a separate national identity and inventory.',
411:'Girl in red dress,inventory4557,eighteenth century. Distinguish from adult female/male portraits and twentieth-century Griselli/Rosi works.',
412:'Benevieni da Scorno,inventory4559,eighteenth century,unframed canvas. Separate named sitter and inventory from Mariano4553 and Ceci gentleman1791.',
413:'Francesco Maria del Testa,inventory4548,circa1765,Austrian-school single-sitter canvas. Different physical composition from Sicilian-school arched double portrait4501.',
414:'Court lady with red cloak,inventory4980,sixteenth-century oval. Separate from blue-cloak oval4981; preserve colour-specific title and distinct inventory.',
415:'Court lady with blue cloak,inventory4981,sixteenth-century oval. Distinct colour/composition label from red-cloak4980; no figure/ensemble count inferred.',
416:'Large Claudia de Medici portrait,inventory1494,seventeenth century. Separate named sitter from Margherita1492 and other court portraits.',
417:'Large CosimoII portrait,inventory4506,seventeenth century. Distinct ruler and inventory from CosimoIII5000 and CosimoI variants outside this release.',
418:'Large Margherita de Medici portrait,inventory1492,seventeenth century. Different named sitter from Claudia1494 and modern Griselli women.',
419:'Violante of Bavaria,inventory4999,1709. Preserve explicit year; not the male Bourbon/Lorraine rulers or Ceci anonymous woman1803.',
421:'Lady with fruit,inventory4972,seventeenth century. Source distinguishes later Lady with fruit and flowers2190 by inventory/period/title; anonymous maker retained.',
422:'Elonora Gonzaga Guastalla,inventory4997,1709. Preserve source spelling and exact year; named sitter differs from the other court women.',
423:'CosimoIII de Medici,inventory5000,1709. Different ruler and dated object from large CosimoII4506.',
424:'Spanish prince,inventory4562,seventeenth-century small canvas. Identity remains generic; no specific royal name invented.',
425:'Princess Sofia Dorotea,inventory4535,seventeenth-century small canvas. Source named female sitter distinguishes the Spanish-prince painting.',
426:'Lady with walking stick,inventory308,eighteenth century. Attribute-specific subject and independent national inventory distinguish it from fruit/flower portraits and Ceci woman1803.',
429:'Marie Louise of Austria,inventory32,1835. Source explicitly a copy after Callegari; not the original or his returned male Cornacchia/Sanvitale portraits. Literal Austrian title retained despite broader search translations.',
432:'Giuria FerdinandIV of Bourbon,inventory907,1776–1800. Existing Tempesti FerdinandIII of Lorraine is a different ruler. Preserve range rather than infer1791 from another Giuria work.',
435:'Alessandro Del Testa,inventory305,seventeenth century. Different named sitter from Jacopo Giuseppe307 and eighteenth-century FrancescoMaria4548.',
436:'Jacopo Giuseppe Del Testa,inventory307,1693,oval. Separate from Alessandro305; retain explicit manufacture year.',
437:'Caravaggesque apostle,inventory309,seventeenth-century canvas. Saint identity and named maker unknown; no matching physical identity returned.',
438:'FerdinandII Medici coat of arms,inventory914,seventeenth-century oval canvas. This is an armorial painting, not a portrait of FerdinandI/II.',
440:'Giuria MariaLuisa,wife of PeterLeopold,inventory923,1791. Distinct dated portrait from later Pisan-school Bourbon woman4455; no inferred identity merger from their similar names.',
441:'Pietro Angeli called Bargeo,sixteenth-century tempera panel,inventory2133 among historical numbers.1796 Zucchetti donation is acquisition evidence. The companion Sebastian4452 is explicitly another work.',
442:'Dominican friar,sixteenth-century tempera panel,inventory2147 among historical numbers. Probable fragment is counted as one surviving physical panel. Bronzino-like style is not firm authorship; named secular Bronzino sitters differ.',
444:'Cleopatra,inventory2166/D85,sixteenth-century oil panel. Preserve Florentine-school qualification; no matching physical identity returned.',
447:'Girl dressed as Diana,inventory2189,eighteenth century. One portrait in mythological costume; no named sitter or extra mythological work invented.',
448:'Woman with fruit and flowers,inventory2190,eighteenth century. Independent from seventeenth-century Lady with fruit4972; literal subjects and periods retained.',
449:'Pecheux Baptism of Nazaradeol,inventory2213,1777–1784. Explicitly one of two preparatory sketches; other at Galleria Sabauda and final Pisa Cathedral painting are separate physical works.',
450:'Ferdinando,son of CosimoIII,inventory2233,1709. Source calls him GranPrincipe; not FerdinandIII of Lorraine or Cardinal FerdinandI.',
451:'Francesco Maria de Medici,inventory2236,1709. Different named sitter from FrancescoMaria del Testa4548 and other Medici portraits.',
452:'Genoese-school prophet,inventory2243,seventeenth-century oil canvas. Nolde1912 woodcut Prophet is different period,medium and maker.',
453:'John drawing water at a spring,inventory4418,eighteenth-century oil canvas. Catalogue identifies Baptist explicitly; retain literal event instead of the loose search translation.',
454:'Female monastic saint,inventory4421,sixteenth century. Unknown saint and author remain unknown; one separately inventoried canvas.',
455:'Central-Italian Holy Family with John,inventory4422,eighteenth-century canvas,including Joseph. Related Ceci Brueghel Holy Family is a seventeenth-century separately inventoried work; no source identity overlap.',
459:'Crucifixion with Mary,John and Magdalene,inventory4430,eighteenth century. One multi-figure canvas; no matching physical identity returned.',
460:'Saint writing,inventory4433,eighteenth century,with Christ and angels. Preserve unnamed saint and unknown painter; independent from prophet2243.',
462:'Conception,inventory4436,eighteenth century,Father,Virgin,angels and crescent. Source subject and inventory retained; no matching identity returned.',
464:'Flemish-school sorrowing Virgin,inventory4438,sixteenth-century canvas. Not the eighteenth-century Conception4436 or another collective Virgin scene.',
465:'Elizabeth with crown,inventory4440,eighteenth century. Preserve literal subject without adding a specific royal identity or an unsupported crowning event.',
467:'Sebastian,sixteenth-century oil panel,inventory4452 among historical numbers,from Zucchetti1796. Former Vasari attribution retained as history. Separate from canvas5751 and named Vasari Blaise/Eustace works.',
468:'Pisan-school MariaLuisa of Bourbon,inventory4455,nineteenth century. Independent period/inventory from Giuria1791portrait923. Do not invent which Bourbon woman beyond the source label.',
471:'Female martyr with palm,inventory4461,seventeenth century. Unknown saint identity retained; one canvas.',
474:'Young woman with blue hair ribbon,inventory4471,eighteenth century. Attribute-specific subject and inventory distinguish her from seated woman4478 and dress-colour variants.',
475:'Young man,inventory4472,eighteenth-century oil canvas. Returned Hokusai works are Japanese prints; Cawen/Heckel/Williams/Zoellner are twentieth-century works. No matching local object returned.',
476:'Court dwarf,inventory4476,seventeenth century. History proposes dwarf of Duke of Crequit; retain catalogue title and attribution unknown, not an invented personal name.',
477:'Seated young woman,inventory4478,eighteenth-century canvas. Berckheyde chalk and Elsheimer gouache are different supports/periods. Separate from standing/attribute-specific women.',
482:'Mr and Mrs Del Testa,inventory4501,circa1765,Sicilian-school arched canvas. Two people form one artwork; distinct from single male portrait4548.',
488:'Woman in red dress,inventory4515,eighteenth century. Romako1889same English title has different maker/period; distinguish the girl4557 and sixteenth-century red-cloak oval4980.',
489:'Stanislao Iablonowsky,inventory4956,eighteenth century. Existing Secchi Francesco Rau is a different named sitter.',
490:'Venetian canal,inventory4958,eighteenth century. Distinct named view from PiazzaSanMarco4959; no matching identity returned.',
491:'PiazzaSanMarco,inventory4959,eighteenth century. Separate place-specific painting from canal4958; not an extra count of one Venice ensemble.',
493:'Anna Quaratesi Dazzi,inventory4964,eighteenth century. Named sitter and national inventory distinguish modern Griselli and Costetti women.',
497:'Young man as Ganymede,inventory4968,seventeenth-century oval. Mythological costume is the portrait subject; one painting.',
504:'Court lady in white dress,inventory4978,eighteenth century. Separate clothing-specific canvas from blue-dress4985 and red-dress4515; no named artist inferred from court-portrait series.',
505:'Army general,inventory4979,seventeenth century. Preserve unknown sitter/artist; related Ceci eighteenth-century gentleman1791 has a different inventory and catalogue identity.',
508:'Woman in blue dress,inventory4985,eighteenth century. Independent from white-dress4978 and sixteenth-century blue-cloak4981; source date and clothing distinction retained.',
519:'Sebastian,inventory5751,sixteenth-century oil canvas. Source support separates it from Zucchetti oil panel4452; both remain anonymous-school records.',
520:'Saint Andrea Diogene,inventory5754,eighteenth century. Preserve the unusual literal label and unknown artist, without inventing a corrected saint identity.',
522:'Susanna bathing,inventory24(allegato7),1550–1599,large relined canvas. Architectural balustrade/elders and foreground vessels described; Vasari/Salviati/Sarto are stylistic comparisons, not asserted authors.'}
NOTES.update(PISA_NOTES)
DEFERRED={242:'Generic Madonna needs comparison with existing eighteenth-century Giaquinto Immacolata and other Virgin records.',288:'Navarro portrait requires physical comparison with sparse contemporaneous Lucca portraits.',297:'Anonymous female portrait needs physical comparison with sparse same-century named portraits.',312:'Vasari/Andrea del Sarto Holy Family versions require additional support/composition reconciliation.',318:'Same-sitter Allori Bianca Cappello versions need individual physical comparison.',326:'Old male head needs comparison with sparse Sustermans/Van Dyck study-head records.',328:'Sodoma Christ and unresolved National Gallery Head of Christ lead need further physical identity review.',338:'Early-seventeenth-century header conflicts with historical attribution to late Van Uden production.',340:'Breenbergh/Schrieck landscape versions and sparse contemporary Panfi landscape remain unresolved.',343:'TerBorch/Kamper musician needs physical comparison with the sparse NG1399 portrait.',348:'Sweerts boy needs physical comparison with sparse same-maker male portrait.',360:'Cigoli/Allori Francis versions require physical reconciliation.',370:'Generic Massoni female pendant needs comparison with sparse existing nineteenth-century portraits.',371:'Generic Massoni male pendant needs comparison with sparse existing nineteenth-century portraits.',377:'Schiavone marriage versions require object-level physical comparison.',406:'Franchi circle generic oval comparator requires further version check.',407:'Franchi circle generic oval comparator requires further version check.',427:'Lady with flowers needs comparison with the sparse Dance-Holland1765 painting.',431:'MariaCarolina portraits by Giuria,VigeeLeBrun and Meytens need physical version comparison.',439:'PeterLeopold same-sitter Tempesti record needs physical reconciliation.',461:'Anonymous eighteenth-century Baptist needs comparison with unidentified1791source record.',478:'Armoured male portrait needs comparison with Nattier and other sparse versions.',483:'MariaMaddalena widow portraits need version comparison.',485:'CristinaLorena version must be distinguished from two widow portraits in this batch.',486:'Sustermans FerdinandII versions require individual physical comparison.',496:'Generic Burgundian gentleman needs physical comparison with Ceci Ferrari gentleman.'}
DEFERRED.update({int(k):v for k,v in working.get('holds',{}).items()})
DEFERRED.update({222:'Shared inventory1557 with Gargiulo Sebastian214: reconcile historic numbering before adding this DeCaro Addolorata.',241:'Shared inventory526 with Carella Healing240 and existing Isaac record: reconcile, do not duplicate.',303:'Mansi family tree appears recatalogued as354; resolve physical identity and revised dating.',354:'Mansi family tree likely same support as303; no second tree counted.',296:'Shared inventory7(5012) with302 and existing Parensi identity requires reconciliation.',302:'Shared inventory7(5012) with296 and existing GirolamoParensi record; not a new object.',363:'Broader mythological wall/ceiling suite overlaps selected Minerva362; do not count ensemble and component.',433:'Inventory4456 shared with differently identified Ludovico469; possible sitter reidentification.',469:'Inventory4456 shared with CarloIII433; reconcile before adding either.',434:'Malformed source range171–1710 is not a valid reviewed creation chronology; do not invent1710.',521:'Generic/empty source title remains a source hold.'})
def values():
 x=m.load(RUN/'measurement-values-002.json.gz');assert not x['failures'] and not x['stopped'];rows=[]
 for part in x['components']:
  raw=f.body(part['receipt_reference'],part['body_reference']);vs=[{k:v['value'] for k,v in r.items()} for r in json.loads(raw)['results']['bindings']];assert len(vs)==part['rows'] and all(v['s'] in part['subjects'] for v in vs);rows+=vs
 assert rows==x['triples'];g=collections.defaultdict(lambda:collections.defaultdict(set))
 for v in rows:g[v['s']][v['p']].add(v['o'])
 return g
dimensions=f.d.prior.r.dimensions
def build(reparse=False):
 original=m.load(RUN/'native-candidates-002.json.gz')['rows'];x=m.load(RUN/'selected-identity-004.json.gz');comps={v['number']:v for v in x['comparisons']};assert x['rows']==s.rows();checked(x['script_reference']);checked(x['base_script_reference']);g=values()
 if reparse:
  fresh,_=f.build();assert fresh==original
 assert set(NOTES)<=set(s.SELECTED) and not(set(NOTES)&set(DEFERRED));ds=[]
 for row in original:
  n=row['number']
  if n not in NOTES:
   ds.append(dict(number=n,institution_id=row['institution_id'],museum=row['museum'],source_id=row['index_record']['source_record_id'],state='editorial_hold' if row['state']!='candidate' or n in [434,303,354,296,302,363,433,469] else 'deferred_identity_review',basis=DEFERRED.get(n,'Source issues: '+', '.join(row['issues']) if row['issues'] else 'Physical version/source-note identity review pending; no new artwork approved.')));continue
  assert row['state']=='candidate' and not row['issues'];v=copy.deepcopy(row['facts']);cmp=comps[n];assert not cmp['source_hits'] and v['last']<=1970
  history=v['source_fields'].get('NOTIZIE STORICO CRITICHE','') or ''
  if n==330:history=history.replace('restituita intatta al marito una giovane sposa','')
  assert not re.search(r'deposito esterno|prestito|rubat|furt|restitu',history,re.I)
  derived=dimensions(v,g);v['dimensions_text']=derived
  ds.append(dict(row,facts=v,state='approved_review_only_addition',confidence=.88,existing_artwork_id=None,basis=NOTES[n],comparison=cmp,derived_fields=dict(dimensions_text=dict(value=derived,basis='Literal object measurement values, explicit units only, frame notes preserved. No inferred units.',source_reference=ref(RUN/'measurement-values-002.json.gz'))),limitation='Editorial confidence, not a calibrated probability. Qualified/unnamed makers, uncertain titles, date ranges and source rights labels retained. Some comparisons have sparse metadata; individual catalogue inventories, descriptions, subjects and supports support physical identity. Museum holding is not current display or independently observed presence. All additions remain in review, without images or painter links.'))
 return ds
def main():
 dest=RUN/'editorial-reviewed-001.json.gz';assert not dest.exists();ds=build(True)
 m.save(dest,dict(at=m.now(),decisions=ds,reviewer_reference=ref(Path(__file__).resolve()),dependencies=[ref(RUN/n) for n in ['native-candidates-001.json.gz','native-candidates-002.json.gz','native-identity-002.json.gz','identity-citations-002.json.gz','selected-identity-003.json.gz','selected-citations-003.json.gz','selected-identity-004.json.gz','selected-citations-004.json.gz','measurement-values-002.json.gz','comparison-source-context-001.json.gz','oderzo-editorial-working-001.json']],policy='Individually inventoried physical works, preserving school and qualified maker labels. Ambiguous recatalogues, versions, shared supports and source contradictions remain outside this release.',reparsed_candidates=len(ds)))
 print(json.dumps(dict(states=collections.Counter(v['state'] for v in ds),approved_by_museum=collections.Counter(v['museum']['name'] for v in ds if v['state']=='approved_review_only_addition'))),flush=True)
if __name__=='__main__':main()
