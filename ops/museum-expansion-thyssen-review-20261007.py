#!/usr/bin/env python3
"""Explicit editorial decisions on267selected Thyssen public catalogue pages."""
import collections,gzip,hashlib,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('p',Path(__file__).with_name('museum-expansion-thyssen-proof-20261007.py'));p=importlib.util.module_from_spec(s);s.loader.exec_module(p);m=p.m;f=p.f;RUN=f.RUN
s=importlib.util.spec_from_file_location('i',Path(__file__).with_name('museum-expansion-thyssen-identity-20261007.py'));i=importlib.util.module_from_spec(s);s.loader.exec_module(i)
checked_reference=p.checked_reference
HOLD_TEXT='''
2|existing_reconciliation|Giovanna Tornabuoni already represented by9fb9b023-1957-4181-914d-07b55bd2d75d and legacy portrait leads. Preserve dates and reconcile; no second object.
8|existing_reconciliation|Inventory172/1975.35 agrees with58fa398f-555b-4dab-94c0-a036c2563665; other Annunciation versions do not justify another record of this canvas.
9|existing_reconciliation|Inventory81/1934.37 identifies existingCaravaggio Catherine d2cefb32-d380-44b5-b767-50b840b38e9e.
14|existing_reconciliation|Fragonard See-Saw c41810a9-46be-590f-b84e-b4552ee10b5c has incomplete dates/inventory. Reconcile that entry before considering an addition.
19|version_hold|Seated Man versus Seated Peasant9f673e19-3ad7-46eb-b0b9-39cbec058c17: date and size differ, but preserve generic portrait/version uncertainty pending fuller comparison.
29|existing_reconciliation|Dalí dream18119436-15f2-58c5-8f48-9a599d238449 has the older1944date and translated title. Official1947date alone is not a new object; preserve both sources without rewriting.
36|version_hold|Antonello small male portraits include21492147-c4bf-4c62-b123-2c6a477493f2 with incomplete physical fields. Met/Louvre comparisons in the native essay do not resolve every legacy portrait.
38|existing_reconciliation|Cranach Virgin and Child with Grapes5c0aeb72-eb05-5a1f-827e-9f94e977060e needs reconciliation despite unknown creation date.
41|existing_reconciliation|Gentile Bellini Annunciation74801601-0437-509d-89b5-427b14ca4ef3 may be this work with a conflicting1465date. No duplicate or silent date correction.
44|existing_reconciliation|Holbein Elder female portrait2f5ab4d9-6c91-50cd-b8e5-4d1b0ad70e71,1518–20, must be reconciled before any addition.
45|existing_reconciliation|Holbein Elder male portrait120ce25a-4603-52d2-980a-d6a06a8f9769,1518–20, must be reconciled before any addition.
47|version_hold|Bruyn female portrait versus white-headdress portraitffa37cc9-6b06-45e2-8926-e931de2f403a,33x24cm: measurements are too close to decide without fuller version evidence.
48|existing_reconciliation|Inventory171/1954.1 identifies b93d32e7-38f8-4e08-8fe2-11832ba5d60a; El Greco Annunciation variants retained separately.
49|existing_reconciliation|Inventory169/1930.28 identifies63f6d289-b988-4ccb-aa30-ec72aab6a705; no duplicate Christ with Cross.
59|version_hold|Attributed Hals violinist versus incomplete Fisher Boy bb59bc2b-cfeb-5bb8-bb90-47f3041d3503 requires physical comparison. Current qualification remains explicit.
67|version_hold|Degas Milliner pastel versusMet436126/4f7e76f8-bded-4363-bbf5-367630b9eb68: same1882date and very similar dimensions75.5x85.5vs76.2x86.4cm. Resolve composition/provenance before addition.
69|existing_reconciliation|Van Gogh Evening Landscape/ Landscape at Dusk9299181c-8f2f-55a0-8730-02e7db217fb3 is an existing native-source identity.
116|version_hold|Daddi Crucifixion versusNGA6e436731-cf33-410e-9c1f-f6adbe5ac7e1: close panel/frame dimensions and repetitive composition; do not distinguish on date alone.
124|version_hold|Rogier Virgin: legacy Madonna76c4b71e-d06c-5965-92de-60478be0d7e2 unresolved; source also proposes original recto/verso relationship with NGA Saint George. Preserve physical-object uncertainty.
131|version_hold|Canaletto Piazza San Marco includes incomplete Italian/legacy versions043d6011-2bae-4224-a242-3314d11fa255 and5739c435-b502-590e-829a-aacfc0908ac6. Distinctive source paving evidence retained; no automatic version separation.
133|version_hold|Tintoretto senator versus incomplete white-bearded portrait5275fc4b-6ce5-592e-b969-00e515719b81: resolve anonymous sitter/version.
134|version_hold|Titian Saint Jerome fed9198b-8686-5ec8-9100-3c543eb209b4 lacks physical facts; different late versions discussed in native essay require fuller identification.
138|version_hold|Fetti Weeds versus Royal CollectionSower6cb9cceb-9efa-5213-b08d-bf3a53e466da,60.4x44.4cm, is too close to distinguish solely on date/measurements.
139|version_hold|Strozzi workshop Cecilia versus ItalianSanta Cecilia c046b8bc-8cee-456b-ad35-e090f7a1eb5a: current attribution differs and legacy dimensions are absent. Reconcile version first.
141|version_hold|Neeffs church interior versus9dd57cd4-0dc9-44f5-b31a-c8ea6d2e21bb and incomplete6b67600e-98c0-4c9a-87f8-1ef743068bd3; source dual dates1615/1616 retained, physical comparison incomplete.
144|version_hold|Heda fruit-pie still life versus generic incompleteGilt Cup/Broken Glass records. Native essay notes replica/versions; require physical comparison.
150|version_hold|Van Goyen frozen Dordrecht view versus Winter Landscape with Horse Drawn Sleigh9f30aada-d8e0-5cca-986a-8a16b77cfc93, with no dimensions. Scene/date differences alone are insufficient.
151|version_hold|Van der Ast vase versus cb342aaa-a512-42b7-8608-428cb7160ef8 and b2f104b1-98bf-43cf-b80e-53e75958d958: similar translated subject, incomplete physical identifiers.
153|version_hold|Dou candle/window versusSMK8974fa92-3097-42d9-9bd2-e678fe4598d9,27.5x20cm: very close to26.7x19.5cm. Preserve version uncertainty.
155|version_hold|De Hooch mother/child domestic interiors include incomplete aeb8b6d4-95d6-5194-b39a-95bd2f08fda3; source records later repainting/removal. Resolve composition history before addition.
156|version_hold|Maes female portrait versus4d4fb90b-2d92-467b-b4d7-ff14d6a38706,95.5x72cm: close size and anonymous sitter need version evidence. Male pendant separately identified.
158|existing_reconciliation|Ruisdael Stormy Sea06855aa0-dca6-5256-9bcf-e341eaf786ee is an exact creator/title/date lead requiring reconciliation, not another entry.
160|version_hold|Ricci Bacchus/Ariadne versus471c2d71-b1bc-4ecb-a430-83fdfa173415: incomplete earlier record and translated versions need comparison beyond date.
164|version_hold|Robert Foot-Bridge versusOld Bridge1c8d115e-2a0a-5a4c-beb4-c4bfd29e6c3b,1775: incomplete physical fields and synonymous subject remain unresolved.
193|existing_reconciliation|Schwitters Merzbild1A already67c0ec9e-bbf8-5092-b3c8-5cdf8839f674 with native source identity.
204|existing_reconciliation|Tanguy Death Watching/Awaiting his Family1b10488e-990d-5d05-a8f0-c5bc086530d6: translated title does not establish a new object.
207|version_hold|Ernst Flower-Shell versus legacyFleurs e03c5e2b-7559-4008-abf4-7ed64d5a0a57; native essay describes a1927–29series, so date alone does not identify the version.
'''
HOLDS={int(n):(state,note) for n,state,note in (line.split('|',2) for line in HOLD_TEXT.strip().splitlines())}
# Explicitly selected row numbers in the pinned209-row candidate sequence.
APPROVED=[1,3,4,5,6,7,10,11,12,13,15,16,17,18,20,21,22,23,24,25,26,27,28,30,31,32,33,34,35,37,39,40,42,43,46,50,51,52,53,54,55,56,57,58,60,61,62,63,64,65,66,68,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95,96,97,98,99,100,101,102,103,104,105,106,107,108,109,110,111,112,113,114,115,117,118,119,120,121,122,123,125,126,127,128,129,130,132,135,136,137,140,142,143,145,146,147,148,149,152,154,157,159,161,162,163,165,166,167,168,169,170,171,172,173,174,175,176,177,178,179,180,181,182,183,184,185,186,187,188,189,190,191,192,194,195,196,197,198,199,200,201,202,203,205,206,208,209]
NOTES={
1:'One separately dispersed Maestà predella panel; do not count the entire altarpiece. Three Marys at Tomb is a different subject.',
3:'Dürer1506oil panel64.3x80.3cm differs from the1503/04Christ Among Doctors print29.4x20.9cm.',
4:'Use actual detail-page dimensions218.5x151.5cm and circa1505date; older dates or other contextual measurements remain source evidence, not automatic new versions.',
5:'Elder Nymph75x120cm is distinct from Younger Nymph Spring15.2x20.3cm and Elder Fountain of Youth composition.',
6:'Native essay identifies former Liechtenstein series and San Vio viewpoint; NGA Molo entrance114.5x153.5cm and other canal viewpoints differ.',
10:'Rubens Venus/Cupid137x111cm: Adonis, fur-coat and Mars compositions have different subjects and physical formats.',
11:'Rembrandt72x54.8cm oil panel; the closest cap/window self-portrait leads are small prints, not this painting.',
12:'Hals family202x285cm differs from the National Gallery family148.5x251cm.',
13:'Saenredam exterior west facade differs from the Hamburg1638interior and interiors of other named churches.',
15:'Met334344has71x37.9cm sheet and1976.201.7Payson bequest; native64x36cmSwaying Dancer has a separately documented Sickert/Unwin history and green/orange performance composition. Web-tool summary supplements prior catalogue citations; direct Met capture was rate-limited.',
17:'Toledo54772describes Chaponval/Rue de Gré,60x73cm; nativeLes Vessenots55x65cm describes Gachet-area fields. Distinct documented place,composition,size and object history. Toledo comparison uses saved web-tool primary text; direct capture denied.',
20:'Native essay explicitly identifies oldWaterloo Bridge/Victoria Embankment and Baltic Wharf; MoMA79463is Charing Cross,81.7x100.7cm, and London Bridge is another named structure. Source objects are distinct views.',
24:'Source artform is Work on paper, retained literally with unknown database work_type; do not narrow to drawing or painting.',
28:'Oil portrait105x73cm differs from Quappi cigarette/cowboy drawings49x37.5and60x45.2cm.',
32:'Conventional Master of the Pomposa Chapterhouse label is preserved at object level; no invented person or biography.',
34:'Attributed Piero78cmtondo with two angels and bird differs from75cmCleveland work with SaintJohn/SaintCecilia. Historical Maestro Allegro/Foschi leads reviewed; retain tentative attribution.',
37:'Separately catalogued predella panel with Jerome and Bartolo; other Gozzoli Herod/John panels depict different episodes.',
43:'Warwick south facade75x120.5cm differs from existing42.9x71.8cmWarwick painting and Palazzo Ducale print.',
50:'Joint El Greco and Jorge Manuel attribution retained as one source label. Immaculate Conception108x82cm is not one of the separate Annunciation or Christ/Cross records.',
53:'Workshop qualification retained. Museum distinguishes Getty prototype,Berlin,Ottawa,Bilbao and other copies; localArtemisia Lot record is a different creator, not interchangeable.',
55:'Native essay explicitly contrasts this monochrome37.5x58.5cm oil sketch with ChicagoCapture50.4x66.4cm and CincinnatiSamson. Prior Van Dyck attribution remains in narrative.',
58:'Flinck male67.1x55.1cmpanel differs from85.73x70.49cmcanvas and70.5x59cmFrench male portrait.',
63:'V&A O17800saved primary response verifies70x89cmlandscape-formatSwing,515-1882,versus65.5x54.5cmhere; Cleveland150.8x89.7cmalso different. Prior raw V&A body hash rechecked.',
68:'One Thyssen impression of the1885lithograph; native essay explicitly distinguishes two canvases and identifies this print among the surviving impressions. NGA print has a different accession and31.7x40.6cmsheet. Do not count all editions.',
75:'44.5x60cmwatercolour bottles/carafe/jug/lemons differs from oil still-life leads; literal source medium retained.',
78:'Retain complete1914–1925creation/reworking range; do not reduce it to the first year.',
81:'Square view16.5x26.3cmgouache/chalk/wax is distinct fromLooking onto a River print19.8x28.5cm.',
87:'Recto and verso are catalogued together as1973.65.a/b. Create one record for the sheet, not a separate record for its study side.',
91:'106x69cmoil canvas differs from1911Man with Clarinet30.9x19.6cmdrawing.',
92:'Native essay identifies RicciottoCanudo dedicated impression,second state of first edition; existing1913impressions are a later edition. One physical print, with source1904date retained.',
93:'31x24.5cmpaperstudy differs from61.4x47.6cmoilHead of Sleeping Woman study. Preserve preparatory-work title.',
94:'Source Relief and18x25x2.2cmwood/collage retained; database type remains unknown.',
114:'Sitter name remains [Rita](?) exactly as qualified; other named sitters and smallerAnnette portraits are different.',
117:'Master of the Magdalen is a conventional source label, not an invented named artist. SaintDominic/Martin composition177x86.5cm separately catalogued.',
118:'One complete triptych1934.30.1-3,not three additions. Anonymous Venetian label and explicit Byzantine iconography retained. Former Vigoroso/MasterSantaChiara names were included in historical-attribution search.',
120:'Native essay identifies small49.5x36.5cmversion omitting saints; other Costa enthroned altarpiece records include saints/angels. Do not count the larger ensemble.',
121:'Tura Patmos27x32cmpanel is a different saint/scene from AnthonyReading or FrancisStigmata; source single panel retained.',
123:'One catalogue record for the two-panel grisaille diptych,with both literal wing dimensions and source1933.11.2identifier. Do not create two wing records. NGA90.2x34.1cmAnnunciation is a different composition.',
126:'One dispersed Catherine-before-Pope scene; same-series CatherineBeggar andStigmata are different episodes, not duplicates of this panel.',
127:'Conventional Master of the Lüneburg Last Judgement creator label retained without invented authority.',
129:'One physical portrait panel entered under its recto catalogue identity. Narrative describes wild-man reverse; no second reverse record. MasterWB historical identity searched; sitter question mark retained.',
130:'One independently catalogued panel from dismantled polyptych. Alvise/Bartolomeo attribution history retained; other Vivarini John records and dated Italian altarpieces are comparison leads, not the complete ensemble imported here.',
135:'Native174.5x494cmParadise is a separate proposed/modello composition, explicitly distinguished from the finalDoge Palace painting and Louvre sketch. Existingbb2781a9sourceWikiArt reportsPalazzoDucale; raw old body hash rechecked. Do not conflate model and finished work.',
137:'WorkshopGoodSamaritan59.6x43.7cmpanel retained as qualified version; native essay distinguishes Dresden horizontal prototype and other autograph/copy versions. Weeds companion remains held separately.',
143:'Stom/Stomer spelling variants reviewed. Native111.8x152.4cmEmmaus differs from French130x164cmversion; Adoration112x150cmis a different scene despite similar size.',
145:'Attributed-to qualification retained; Village Men Drinking63x95.9cm is separately inventoried from generic Scene at Inn lead.',
146:'Jordaens and Workshop qualification retained. Source discusses replica history. ExistingNationalmuseumHolyFamilyNM1768citation explicitly says oil on oak, versus89.7x103cmcanvas here; Met1616Shepherds is another subject/format.',
147:'39.4x37.3cmsmokers differs from Cleveland37.2x26.3cmpanel andNGA31.8x40.5cm. SecondaryFrench titleLeBonnetVert used only as duplicate-search lead.',
157:'Male pendant91.4x72.7cm and1930.57 independently inventoried from female1930.58. Native essay establishes two signed canvases. Existing maleMaes44x31/43.5x30.5cmworks are different.',
162:'Native essay explicitly identifies the MetConcertChampêtre as this painting’s separate pendant,split in1913. Similar title/date/size therefore do not imply a duplicate.',
166:'CourbetBrème114x89cmportrait-formatcanvas differs from73x92.2cmFrenchlandscape-formatBrème version.',
171:'Native swimming deer/dog scene andHooper ownership through1978differ fromAIC16785fisherman-at-sunset/Ryerson1933provenance. AIC original public text independently captured despite nearly identical sheet sizes.',
173:'Small44.4x54.6cmoilpanel differs from86.6x100.4cmMetShinnecock canvas and76.2x122.2cmNearBeach.',
180:'Native essay explicitly describes two large versionsIandIIshown in1913. NGAIIshares200x194cmsize but has another composition; one record forThyssenI.',
191:'65x46cmoilHead of Man differs from1912drawing62.2x48.3cm and female heads/prints; medium and subject considered together.',
208:'Exact1970creation is eligible. PriorWhitney48268rawresponse verifies15.7x21.7cmmixed-mediaNudeCollage2015.321,distinct from63.5x114.5cmoilNudeNo.1. No cutoff inferred from acquisition1974.',
}
def supplementary():
 refs=[f.ref(RUN/name) for name in ['identity-scope-003.json.gz','identity-comparisons-003.json.gz','identity-expanded-comparisons-001.json.gz','historical-creator-identity-001.json.gz','version-scope-001.json.gz','version-prior-bodies-001.json.gz','version-public-capture-001.json.gz','web-discovery-004.json','web-discovery-005.json']]
 for ref in refs:checked_reference(ref)
 for row in m.load(RUN/'version-prior-bodies-001.json.gz')['records']:
  raw=gzip.decompress(checked_reference(row['body_reference']).read_bytes());assert hashlib.sha256(raw).hexdigest()==row['raw_sha256'];refs.append(row['body_reference'])
 for ref in m.load(RUN/'version-public-capture-001.json.gz')['pages']:
  row=m.load(checked_reference(ref));refs.append(ref)
  if 'capture' in row:
   raw=f.n.body(row['capture']);assert f.d.d.BeautifulSoup(raw,'html.parser').get_text(' ',strip=True)==row['text']
   if row['source_url'].endswith('/16785'):assert '1933.1238' in row['text'] and 'fisherman' in row['text'] and 'Ryerson' in row['text']
 return refs
def build():
 source=RUN/'native-candidates-002.json.gz';candidate=m.load(source);assert candidate['counts']=={'candidate':209,'source_hold':58}
 for ref in candidate['parser_references']:checked_reference(ref)
 rows=[r for r in candidate['rows'] if r['state']=='candidate'];cm={r['source_id']:r for r in m.load(RUN/'identity-comparisons-003.json.gz')['records']};expanded={r['source_id']:r for r in m.load(RUN/'identity-expanded-comparisons-001.json.gz')['records']}
 assert len(APPROVED)==len(set(APPROVED))==172 and not set(APPROVED)&set(HOLDS) and set(APPROVED)|set(HOLDS)==set(range(1,210))
 supplements=supplementary();decisions=[];holds=[]
 for num,row in enumerate(rows,1):
  v=p.facts(row['source_reference']);assert v==row['facts'];x,parsed=p.checked_record(row['source_reference']['path'],row['source_reference']['sha256']);assert not f.source_holds(v,x,parsed)
  if num in HOLDS:
   state,note=HOLDS[num];holds.append(dict(row,state=state,number=num,review_note=note,comparison=cm[row['source_id']],expanded_comparison=expanded[row['source_id']]));continue
  c=cm[row['source_id']];assert not c['source_hits'] and not c['native_url_hits'] and not c['institution_native_id_hits'] and not any(a['relevant'] for a in c['inventory_component_hits']),v['source_id']
  note=NOTES.get(num,'Specific creator,subject,accession and physical medium/dimensions were reviewed against the retained focused and broader creator/title comparisons; no unresolved same-object lead was found for this selection.')
  basis=f"Official catalogue {v['inventory']} identifies {v['title']} by {v['creator_label']}, {v['date_display']}; {v['medium']} {v['dimensions_text']}. Exact museum credit: {v['credit_line']}. "+note
  decisions.append(dict(source_id=row['source_id'],number=num,state='approved_review_only_addition',confidence=.9,basis=basis,limitation='Editorial confidence, not a calibrated probability. Museum connection is not legal title, current physical custody or current display. Source qualifications,unknown fields,rights and narrative remain evidence; no images,artist links,publication or existing metadata edits.',facts=v,index=row['index'],source_reference=row['source_reference'],comparison=c,expanded_comparison=expanded[row['source_id']],supplement_references=supplements))
 for row in candidate['rows']:
  if row['state']!='candidate':holds.append(dict(row,review_note='Preserve source triage hold; no museum assignment or addition from this source record.'))
 assert len(decisions)==172 and len(holds)==95
 return decisions,holds
def main():
 decisions,holds=build();m.save(RUN/'editorial-reviewed-001.json.gz',dict(at=m.now(),decisions=decisions,holds=holds,candidate_reference=f.ref(RUN/'native-candidates-002.json.gz'),reviewer_reference=f.ref(Path(__file__).resolve()),policy='Explicit selection172of267captured objects;95source/existing/version holds. One record per reviewed physical artwork or catalogued ensemble. Original museum facts and known unknowns retained.'))
 print(json.dumps(dict(approved=len(decisions),holds=dict(collections.Counter(r['state'] for r in holds)))),flush=True)
if __name__=='__main__':main()
