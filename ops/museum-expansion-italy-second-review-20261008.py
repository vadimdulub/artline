"""Editorial review of 88 separate catalogue objects in four Italian museums."""
import collections,copy,gzip,hashlib,importlib.util,json,re
from pathlib import Path
s=importlib.util.spec_from_file_location('s',Path(__file__).with_name('museum-expansion-italy-second-supplement-20261008.py'));s=importlib.util.module_from_spec(s);s.__spec__.loader.exec_module(s)
i=s.i;f=i.f;m=i.m;RUN=i.RUN;ref=i.ref;checked=i.checked
DEFERRED={123:'Source history names Domenichino/Zampieri and Zoboli; expand former-maker identity comparison before release.',124:'Source history describes a Teniers copy formerly Helmont; supplemental Francken search does not resolve these identities.',163:'Sparse Wouwerman horsemen comparison remains a version question.',333:'Damaged attributed Vacca religious drawing needs physical comparison with sparse nineteenth-century Thomas records.',488:'Early Florentine generic allegory needs comparison with the sparse Filippino Lippi entry.'}
NOTES={
11:'Young scribe seated on steps with papers and hat, inventory215. Former Piazzetta/Longhi labels retained in history. Longhi Visit, Letter and Faint have different compositions and smaller documented formats.',
42:'Inventory72 depicts Aurora seizing Cephalus from the four-horse chariot. Native history rejects firm Albani authorship; retain Ambito Bolognese. Rubens oil-on-wood NG2598 is a different support and scale; nineteenth-century Guerin/Girodet versions remain separate.',
59:'Small canvas inventory107 records a Roman-school Mazarin portrait with explicit uncertainty over its relationship to the 1687 bequest and French models. Nanteuil comparisons are engravings; Mignard PE314 is a separately inventoried larger canvas. Do not equate a model or print with this copy/version.',
65:'Inventory116 is the damaged panel bust of Saint James of Galicia. Former Andrea del Sarto and Bastianino/Filippi opinions are explicitly insufficient in the source. Preserve the Ferrarese-school label.',
70:'Inventory123 shows Abraham leading Isaac to sacrifice in a pastoral landscape. It is a separate canvas from pendant137 and cited comparators130/2842; uncertain1624 inventory identification remains qualified.',
76:'Inventory134 is explicitly a late-sixteenth-century panel repetition of the Bronzino court-dress Cosimo type. The source distinguishes the several versions and Uffizi armoured prototype. Existing Lucca0900067695 and Uffizi0900021971 catalogue identities are retained separately; other Medici portraits depict different sitters.',
78:'Inventory137 is a small horizontal canvas with Elijah fed by angels. Candidate157 repeats a historical137 alongside434 but depicts Holy Family saints on a larger vertical panel. Source links123 as a pendant, not the same object; no combined ensemble counted.',
83:'Inventory152 reworks Bruegel with the tower relegated behind working figures. Native history explicitly distinguishes the composition from Vienna; neither Bruegel original nor later prints are this seventeenth-century canvas.',
84:'Inventory153 is a cattle fair on panel: cattle leave a stable while a man talks to a father and child. Former Saftleven/Camphuyzen and possible Teniers-copy opinions remain source history; the estaminet interior comparison depicts a different scene.',
87:'Inventory159 shows a picture seller exhibiting a Crucifixion at a fair. Source identifies151 as its separate pendant. Retain catalogue Schoevaerdts label and source history of earlier schools.',
94:'Inventory199 is a stable panel with animals and kitchen still life, a woman and child at rear left; the Potter signature is explicitly false. The Van Horstock window conversation and kitchen interior are different compositions.',
98:'Inventory231 has three tiers of saints over a gale and ship. Preserve1680–1689 and the source explanation that the third digit is probably8; do not import the formerly misread1694 or old Pesari attribution.',
104:'Inventory254 depicts Emanuele Filiberto, Prince of Carignano, in armour with lace cravat. The source dates this French-school portrait1660–1670; no returned identity match.',
110:'Inventory294 is a small round bay view on parchment/canvas with fortified palace and natural arch. Source explicitly distinguishes pendant2737, a bridge landscape. Preserve the literal mixed support and diameter without assuming a missing unit.',
125:'Inventory338 is explicitly an Estense copy after the Teniers/Beit inn-dance composition, bought1827, with apocryphal signature. It is not the1645 WikiArt original or other Teniers smoking/bowls/feasting compositions; preserve copy status in the source evidence and school label.',
127:'Inventory354 shows the Forum Boarium market with women washing vegetables. Mommers attribution, acquisition and characteristic carrot detail distinguish this canvas; retain source spelling.',
133:'Inventories1593/2820 identify one detached Scandiano fresco with Prasildo and the old adviser. The source names the other independently inventoried cycle scenes; this release counts only this detached physical panel, not the cycle.',
139:'Inventory4292 is a German-school panel derived in reverse from Vorsterman after the lost Rubens Job wing. The French INV.86-8 comparator is an89×66.5 canvas; prints, the lost wing and the Louvre model drawing are separate works.',
142:'Inventories1829/2861 identify one canvas attributed to Stringa after Guercino. Source explicitly contrasts its close framing and63×48 values with Dresden87.5×70.5 and a small copper copy; other Saint Mark paintings have independent catalogue identities.',
147:'Inventory7009 is the canvas portrait with a letter naming Calori Cesis,68.5×52 source values. The source explicitly identifies7010 as another portrait; never collapse these based on the same sitter/title.',
148:'Inventory7010 is the52×48 panel portrait, explicitly distinguished from canvas7009 in the Calori Cesis bequest. Different support, format and inventory establish a separate object.',
164:'Inventory4208 shows horsemen refreshed by peasants. The source identifies4207 as its separate pendant and describes an imitator of Wouwerman; retain Ambito Olandese and do not count the pair as an extra work.',
170:'Inventory2971 is explicitly a later copy of the Annibale Carracci San Prospero altarpiece. Source distinguishes the original removed1746; prints, Holy Families with other saints and individual Francis scenes are separate compositions and supports.',
174:'Inventory8342 is a large Clare canvas with monstrance and altar, circle of Crespi. The source records disputed Giuseppe/Luigi/Antonio roles; preserve the qualified circle label. Memmi panel, Court version and Betti record have separate periods/physical identities.',
175:'Inventory8347 depicts Bernardino praying with an angel pointing to the IHS disk, three mitres on a table. Retain Lombard-school seventeenth-century attribution and missing measurement units.',
176:'Inventory8349 combines Anthony of Padua, Child and an unidentified Capuchin. It is not Sirani Anthony alone or Vellani enthroned Madonna. The museum1958 acquisition is not its1790s manufacture date.',
177:'Inventory8350 depicts Vincent Ferrer and Francis of Paola, with flame and staff. Source distinguishes companion8349. The Stringa Vincent and Stern Francis embracing Christ show different subjects.',
331:'Separate245×346mm Vacca sheet: mosque and exotic palms seen from a cave; not the temple/Diana or central-plan woodland temple sheets already held.',
332:'Separate245×320mm1825 Oreste/Otello stage design with tomb, statues and sea. Existing Calderini/Bagetti/Bruegel landscapes are different artist/period/composition records.',
334:'Separate226×327mm stage design for La distruzione del regno delle Fate/Mose in Egitto, gothic building on an island. Existing Vacca temple drawings depict different architecture and composition.',
335:'312×196mm ink drawing of Virgin in a niche with two pilgrims. Preserve Piemontese-school label and probable Vacca opinion in history; earlier Madonna paintings are distinct supports/subjects.',
336:'234×321mm Vacca sheet shows a palace obliquely and a fountain with statues. Distinguished from frontal-palace337 by composition and paper format; no identified opera is invented.',
337:'252×323mm1833 sheet has frontal palace facade, trellis arches and statues, for Matrimonio dopo morte/Gabriella di Vergy. Separate from336 oblique view.',
338:'250×323mm1833 La straniera/Mose design has central lake and left shrine. Existing0100058692 has a right-hand hut in a mountain backdrop and252×334mm format; distinct captured compositions.',
339:'247×331mm1834 Fausta garden with stairs and paired statue pedestals; not the earlier central-plan temple or Diana temple. Individual stage-design sheet.',
340:'248×312mm1834 Guglielmo Tell/Fausta design with rocky caves, path and steep stairs; distinct from the architectural temple scenes.',
341:'246×325mm1828 Caritea design with urn tomb, equestrian statue and seated statue. Different from332 sea/tomb and344 many-gravestones compositions.',
342:'240×327mm Angelice e Medoro design with multiple huts among trees; different from existing right-hand mountain hut0100058692 and the single hill-house346.',
343:'244×323mm1830 Tancredi design with lake, terraced palace and beached boat. Separate from gothic island334 and337 palace facade.',
344:'235×345mm1833 Clato/Gabriella design with a clearing and numerous grave markers. Different composition and sheet from the other tomb scenes.',
346:'261×344mm1832 La straniera drawing shows a house atop a small hill among trees. Separate from338 central lake/left shrine and342 multiple huts.',
347:'290×390mm sheet depicts the Carmagnola thanksgiving procession with banners. One complete crowd drawing, not a count of its figures.',
348:'320×415mm Folto bosco is a separate densely wooded stage-design sheet. Remaining selected named designs have distinctive structures/compositions; the generic295×439mm Bosco352 and other forest-only candidates remain deferred.',
349:'310×420mm mountain/ruins drawing shows a gothic castle on the right and small figure lower left. Separate from lake, hut and temple compositions.',
350:'311×412mm village drawing with portico, houses, church and central well; different composition from the existing temple scenes.',
351:'308×407mm sea-cave view with hut against the rock and boat on the shore. Separate from331 mosque/palms and340 inland cave path.',
353:'350×525mm attributed Vacca sheet shows Virginia arrested outside a temple by soldiers; separate from354 dying Virginia and Apollo.',
354:'427×568mm attributed Vacca sheet shows dying Virginia supported by two men and Apollo above. Older Doyen/Caccianiga versions and the arrest drawing have separate artist/period/composition identities.',
355:'600×450mm1827 Gonin pencil drawing: sleeping Endymion seated on rock, Diana with arrow and putto. Separate physical drawing from the older Viani/Giordano/De Mura/Seyter mythological paintings and later Carnelli version.',
356:'585×394mm1805 Monticone Alfieri apotheosis, with Sophocles, Dante and allegories. Separate from same-sized1804 Filippo scene357.',
357:'585×394mm1804 Monticone sheet depicts Philip restraining Carlos beside Isabella in gothic interior. Not the unrelated Luti Saint Philip Neri healing subject.',
358:'550×440mm Monticone allegory shows Victor Emmanuel I confronting Rationalism with a crucifix. Distinct from the Grosso portrait of Victor Emmanuel III and359 court homage.',
359:'545×435mm1814 Monticone court homage with royal family and personifications of Piedmont, Religion, Public Happiness and Union; not358 or Grosso individual portrait.',
360:'515×725mm architectural facade elevation with porch and bell tower. Source calls it the unrealized1835 competition design; preserve1825–1849 range, no constructed-building artwork or1835 manufacture year inferred.',
361:'515×725mm transverse-section drawing, explicitly different view from360 facade despite equal sheet size. Floor plans362/365 and ambiguous structural sheets366/367 are not released.',
363:'520×730mm presbytery elevation, distinct object-specific drawing from the facade/section and floor-plan sheets.',
364:'510×740mm facade of a palace facing the church square, not the church facade itself. Native title/description establish distinct subject within the design group.',
422:'Inventory204 is the signed1660 daylight Antwerp cathedral on copper. Source and caption distinguish daytime from the V&A night scene. Aix and other French comparisons are wood panels, NGA1960.6.29 is a smaller copper, and the Ambrosiana/Brera notices have independent national objects; Brera is Reg.Cron.4833. Retain sparse comparator metadata as a limitation.',
428:'Inventory267 is the small Lucina/Norandino/Ogre landscape attributed to Barbalonga. Former Domenichino and Lanfranco opinions remain history, not definitive artist links; no matching physical work returned.',
443:'Inventory408 is the full-length Michele Peretti portrait with armour, helmet, sword, command baton and table. Retain source Fachetti spelling and older Commodi opinion in history; no identity conflict returned.',
480:'Inventory28 is a seventeenth-century Albani-school canvas with Rinaldo and Armida at the mirror, cupids and soldiers. No competing physical identity returned.',
504:'Inventory298 is a small sixteenth-century Florentine-school oil on copper showing a sculptor and other figures. Unknown named maker preserved; no comparison identity returned.',
533:'Individual canvas with kneeling Saul, shrouded Samuel rising from earth and the witch illuminating him. Preserve source circa1740 and Bertuzzi label; no matching physical identity returned.',
542:'Small Roman-school Finding of Moses canvas with Nile landscape, sister, princess and attendants. The fuzzy Fano male-portrait lead depicts a different subject.',
544:'Large Saint Clare canvas with Clarisses, Saracens and monstrance, catalogued1600–1649. No matching physical identity returned.',
557:'Portrait of Nicola Ferretti Gabuccini. Existing Claudio, Maddalena and Gian Ottavio portraits depict different named sitters; retain Luzzi executing-maker label.',
558:'Small Neapolitan-school Dominic canvas with angel, lily and book; source discusses but declines a firm Giaquinto match. Preserve school label; no matching physical identity returned after related-maker search.',
567:'Long horizontal imagined view of Novilara; different from the Pozzato landscape with a group of women and568 Pesaro view.',
568:'Long horizontal view of Pesaro from Colle San Bartolo. Same format as567 but explicit different site/composition and separate national object.',
570:'Large seventeenth-century Venetian-school allegory of Love; source notes Bellucci affinities. The Cardini/Fedi comparison is a later print on paper, not this canvas.',
573:'Double portrait of Gasparo and Francesco Maria Gabuccini in armour,225×145 source values. Existing Fortis, Claudio, Bagni, Amiani and Paolucci portraits identify other sitters.',
574:'Individual small capriccio with ruined arches, rustic houses and lagoon figures; not575 named Rialto bridge or590 Ducal Palace view.',
586:'Nineteenth-century small altar-boy canvas. Existing Fumagalli CHIERICHETTO is a1916–1920 oil on wood; distinct support/period/format.',
587:'Small nineteenth-century Chiaia waterfront canvas. No matching physical identity returned.',
589:'Nineteenth-century Naples harbour canvas, distinct named view from the Gulf painting588; separate national catalogue object, not an ensemble row.',
590:'Small piazzetta view toward the Ducal Palace, circa1790–1810. Different composition and size from lagoon capriccio574.',
599:'Large sixteenth-century city view of Fano attributed to Morganti. Attribution remains qualified; no matching physical identity returned.',
606:'One canvas of the twelve separately described theatrical paintings: heavenly palace in woodland. Source explicitly calls these free painted interpretations, not surviving scenery itself; retain maniera di Torelli.',
607:'One separately catalogued canvas: woodland with flying deities, distinct from606 heavenly palace. Shared series measurements do not merge distinct compositions.',
608:'Separate canvas with Bacchus temple, within the twelve theatrical interpretations. No whole-series record or represented theatre counted as an extra work.',
609:'Separate canvas of the Elysian Fields within the twelve theatrical interpretations; retain maniera di Torelli and source seventeenth-century date.',
610:'Separate canvas of the countryside of Naxos within the twelve theatrical interpretations; not the other woodland/courtyard views.',
611:'Separate royal-garden canvas within the twelve theatrical interpretations; not the physical garden or theatrical set.',
612:'Separate solitary-valley canvas within the twelve theatrical interpretations. Title, individual national notice and described series establish one painting.',
613:'Separate villa-courtyard canvas in the seventeenth-century twelve-picture group. Existing Albertini cortile regio is an1830 design with different creator/period and subject.',
615:'Portrait of Francesca de Suez with carefully painted lace sleeve and fabrics. Other returned portraits identify different male/female sitters; retain executing Torelli label.',
616:'One eighteenth-century painted hall with grand staircase, arches and columns; source says Bibiena-like scenic derivation, not a firm Galli attribution. No matching physical identity returned.',
621:'Profile blessing bishop with houses/palaces in the background. Source notes Giuseppe Ceccarini affinities but keeps Marchigian-school label; no matching physical identity returned.'}
assert set(NOTES)==set(s.SELECTED)-set(DEFERRED) and len(NOTES)==88
def values():
 x=m.load(RUN/'measurement-values-001.json.gz');rows=[]
 assert not x['failures'] and not x['stopped']
 for part in x['components']:
  raw=f.body(part['receipt_reference'],part['body_reference']);vs=[{k:v['value'] for k,v in r.items()} for r in json.loads(raw)['results']['bindings']]
  assert len(vs)==part['rows'] and all(v['s'] in part['subjects'] for v in vs);rows+=vs
 assert rows==x['triples'];g=collections.defaultdict(lambda:collections.defaultdict(set))
 for v in rows:g[v['s']][v['p']].add(v['o'])
 return g
def dimensions(facts,g):
 if facts['dimensions_text']:return facts['dimensions_text']
 parts=[];notes=set()
 for v in facts['measurements']:
  if len(v['types'])!=1 or len(v['value_nodes'])!=1:raise ValueError('Ambiguous measurement')
  node=g[v['value_nodes'][0]];numbers=node['https://w3id.org/italia/onto/MU/value'];units=node['https://w3id.org/italia/onto/MU/hasMeasurementUnit']
  assert len(numbers)==1 and len(units)<=1;unit=next(iter(units),'').split('/')[-1];assert unit in ['','cm','mm']
  parts.append(v['types'][0].split('/')[-1]+': '+next(iter(numbers))+(' '+unit if unit else ' (unit not stated)'));notes.update(v['collection_notes'])
 return '; '.join(parts+['Source measurement note: '+v for v in sorted(notes)]) or None
def build(reparse=False):
 original=m.load(RUN/'native-candidates-001.json.gz')['rows'];by={r['number']:r for r in original};x=m.load(RUN/'selected-identity-002.json.gz');comps={v['number']:v for v in x['comparisons']};assert x['rows']==s.rows();checked(x['script_reference']);g=values()
 if reparse:
  fresh,_=f.build();assert fresh==original
 ds=[]
 for row in original:
  n=row['number']
  if n not in NOTES:
   state='editorial_hold' if row['state']!='candidate' else 'deferred_identity_review'
   basis=DEFERRED.get(n,'Source issues: '+', '.join(row['issues']) if row['issues'] else 'Physical identity/source-note comparison is still pending; no addition approved.')
   if n==532:basis='Same-title Ceccarini1768 database record e6f4d956-c8e9-4344-abaf-317d6e8dc19e needs reconciliation, not a new duplicate.'
   if n in [603,604]:basis='Two same-title/same-size anatomical canvases lack distinguishing description; establish separate physical identities before adding either.'
   if n in [362,365,366,367]:basis='Related Vernier plan/structural sheets need further physical-unit comparison; do not infer separate leaves from orientation alone.'
   ds.append(dict(number=n,institution_id=row['institution_id'],museum=row['museum'],source_id=row['index_record']['source_record_id'],state=state,basis=basis));continue
  assert row['state']=='candidate' and not row['issues'];v=copy.deepcopy(row['facts']);cmp=comps[n];assert not cmp['source_hits'];assert v['last']<=1970
  history=v['source_fields'].get('NOTIZIE STORICO CRITICHE','')
  # These two literal usages concern attribution and painted rendering, not
  # restitution of a physical object; all other custody words still fail.
  for phrase in ["restituzione dell'opera al catalogo di Giuseppe Romani",'restituzione del paesaggio']:history=history.replace(phrase,'')
  assert not re.search(r'deposito esterno|prestito|rubat|furt|restitu',history,re.I)
  derived=dimensions(v,g);v['dimensions_text']=derived
  ds.append(dict(row,facts=v,state='approved_review_only_addition',confidence=.90,existing_artwork_id=None,basis=NOTES[n],comparison=cmp,derived_fields=dict(dimensions_text=dict(value=derived,basis='Explicit object measurement type/value nodes, literal unit only when present; original frame notes retained. HTML dimensions take precedence when supplied.',source_reference=ref(RUN/'measurement-values-001.json.gz'))),limitation='Editorial confidence, not a calibrated probability. Dates and qualified/unnamed creators retained. Some comparisons have sparse metadata; source descriptions, inventory/physical unit, support and independently catalogued identities underpin the decision. Recorded museum holding only, not present display or fresh physical observation. Review status; no images or painter links.'))
 return ds
def main():
 dest=RUN/'editorial-reviewed-001.json.gz';assert not dest.exists();ds=build(True)
 m.save(dest,dict(at=m.now(),decisions=ds,reviewer_reference=ref(Path(__file__).resolve()),dependencies=[ref(RUN/n) for n in ['native-candidates-001.json.gz','native-identity-001.json.gz','identity-citations-001.json.gz','selected-identity-002.json.gz','selected-citations-002.json.gz','measurement-values-001.json.gz','comparison-source-context-001.json.gz']],policy='88 individually reviewed records. Original source labels and unknowns preserved. Shared generic titles/series are not automatic duplicates: explicit separate physical units described in notes. Unresolved inventory/version/custody questions remain outside this release.',reparsed_candidates=893))
 print(json.dumps(dict(states=collections.Counter(v['state'] for v in ds),approved_by_museum=collections.Counter(v['museum']['name'] for v in ds if v['state']=='approved_review_only_addition'))),flush=True)
if __name__=='__main__':main()
