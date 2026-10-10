#!/usr/bin/env python3
"""Explicit editorial decisions on186selected Nelson-Atkins physical objects."""
import collections,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('i',Path(__file__).with_name('museum-expansion-nelson-identity-20261007.py'));i=importlib.util.module_from_spec(s);s.loader.exec_module(i);f=i.f;m=i.m;RUN=i.RUN;IID=i.IID;checked_reference=f.checked_reference;reference=f.ref
HOLD_TEXT='''
48|version_hold|Anonymous Backer lady versus incompletely described Sara de Bie and Machtelt Bas portraits needs physical/version evidence, not a decision from differing dates.
49|version_hold|Claesz Still Life616e35f8-b8a6-4448-b357-fc6bf558f362 has no physical facts. Cleveland landscape-format panel differs, but does not resolve that legacy record.
50|version_hold|Dou self-portrait e6b183f3-fdea-4103-9862-063ca798caf1 is close in size and date. The newly separated signature verifies inventory32-77, but composition/version review remains required.
52|version_hold|Hals male portraits include several incomplete identities and close-sized SMK and Met canvases. Generic title and dates cannot safely select a version.
54|version_hold|Hobbema Road in the Woods versus incomplete Cottages in a Wood72f2da34-855a-4c09-a2d9-89a3ed4cf583 and related woodland subjects remains unresolved.
55|version_hold|Huysum panel78.74x59.69cm is close to SMK79x60.5cmKMS441 and Rijksmuseum81x61cmSK-A-188. Require composition/provenance comparison.
57|version_hold|Ruysch flower still-life leads93f63c40,2cbef719,bd784288 and7364a9f0 lack physical facts; differing dates alone do not resolve versions.
58|version_hold|Ruysdael1644signature and native inventoryF61-72 retained. Incomplete Ferry53237c4a-54e9-47d5-8da5-b4ffde8e7da4 needs reconciliation even though other fully measured ferry canvases differ.
64|existing_reconciliation|Wtewael Martyrdom of Saint Sebastian1600 already represented by5c5b1b46-2143-580a-8b76-6c95889c27e0 with WikiArt identity. Reconcile its holding separately; do not create another record.
65|version_hold|Constable Helmingham Dell9b2d0a67-1539-4020-ada7-7571007b7de9 has an unverified1823date and absent physical facts. Compare with the native1830canvas before addition.
67|version_hold|Former Cotes attribution broadens comparison. Tate lady0caec9a8-2242-4a39-b361-a1c1ba01ee53 is126.7x101.6cm versus127x101.6cm here; close physical formats require sitter/provenance resolution.
70|version_hold|Gainsborough Repose has a broad woodland/figural subject; incomplete Rocky Wooded Landscape with Rustic Lovers bb4e07dc-d498-5887-9648-6bb125bb2c84 remains a physical-version lead.
71|version_hold|Guy Head Iris4b72ef8f-0c3c-5a7b-8dd6-bf143a5890cb lacks physical dimensions and may use a shortened title. Native1793versus circa1800alone is insufficient.
80|version_hold|Sisley Lock and legacy Dam/Loing Canal c990de06-dc77-55bb-9557-70c9aef9bf01 require version comparison; nearby Saint-Mammes views are not interchangeable.
93|version_hold|Rubens Sacrifice of Isaac and Le Sacrifice d'Abraham2ab7a9a2-fe4e-4641-8a69-b063a840b0ff may be translated versions; the older record lacks physical facts.
108|version_hold|Boudin flagged boats versus incomplete Le bassin de Deauville9cf1b6d1-d4b7-4351-958b-d937da73a880 requires composition review. Prior MuMa connection is retained, not used alone to distinguish.
112|version_hold|Caillebotte moored boat65.41x54.29cm is close to Voiliers a Argenteuil964cb31c-0c60-4f76-a9f7-24f98f72fbc8 at65x55.5cm. Related Bayeux/deposit leads remain evidence.
115|version_hold|Cezanne Bibemus versus c606e7e8-f602-4e47-96c5-9e8549016532 needs exact quarry/version evidence; dates differ but physical facts of the old record are absent.
116|version_hold|Champaigne Crucifixion includes incompletely measured Le Christ en croix records9e1f5662,b17367ae,09717e30. The larger227x202cmcanvas is distinct but does not resolve those leads.
120|version_hold|Couture Pierrot malade a80e9893-4610-4bc3-834d-377d8b402a6c is35x39.6cm versus35.08x43.02cm. Close size and translated title need fuller comparison.
121|version_hold|Daubigny Oise panel39.07x66.83cm is close to Met37.5x67cmpanel and incomplete3498f9d2. Do not separate solely by source dates.
127|version_hold|Cranach Younger portrait includes incomplete e9f2d9b8-a485-4bbd-9dbb-a232ef967a0f under Lucas Cranach(II); father/son and anonymous sitter versions remain unresolved.
136|source_hold|The native1510-1592creation field repeats Jacopo Bassano's lifespan. Preserve source value as evidence; it is not approved creation dating.
138|version_hold|Bellini Madonna versions include close-sized NGA71.7x52.8cm and several incomplete Virgin/Child records. Source transfer from panel to canvas does not by itself prove another object.
140|version_hold|Canaletto San Marco views include incomplete043d6011,0981dae8,5739c435. Establish exact clock-tower viewpoint before addition.
141|version_hold|Carpi Magi versus National Gallery Kings d92c17e6-b855-44e5-9a67-6e687ec90a1a has compatible dates and translated subject but absent physical facts in the old record.
148|version_hold|Asola Shepherds939bc4cc-802f-4cd3-8bbc-62e3a89e22a8 uses qualified attribution and matching1525-30date. Resolve native object identity before addition.
149|version_hold|Daddi workshop enthroned Madonna includes incomplete3a88119d-1069-4d00-835e-2d15c4a1d660. Smaller fully measured NGA panel is distinct, but not every legacy version is resolved.
155|group_version_hold|Giaquinto Adoration must be compared with existing S.Croce modelli group db27ca01-8f57-46e0-a4db-2aa3b10ddd66. Preserve the existing group/research-record safeguard.
156|version_hold|Guardi Dogana/Salute and incomplete7e560fc3-0606-4c64-90a1-cb44e79cc699 require exact view/version comparison, irrespective of its unverified19th-century date.
158|version_hold|Bosch small temptation panel versus Lisbon triptych1498Pint/e7aa7158 and incompletec9f64b03 needs component/version review. Do not infer distinctness from a group title alone.
159|version_hold|Bouts Christ Crowned with Thorns may overlap Albrecht/Dirk attribution histories and recto/verso6359aee0. Resolve physical panel identity first.
165|version_hold|Gossaert Carondelet43.02x34.93cm and Met unnamed man47x34.9cm are close enough to require sitter/provenance comparison; preserve both identities.
168|version_hold|Memling enthroned Madonna, two-angels27185c9d and historical Rogier76c4b71e leads have incomplete physical facts. Current attribution does not resolve the version.
171|version_hold|Raeburn Sir George Abercromby76.2x63.5cm versus SMK anonymous male75.5x63.5cmKMS2085 requires physical/sitter review.
177|version_hold|Attributed Herrera Penitent Peter versus4816aef2-6ce6-5102-9f2d-be40e7664146 Saint Peter1630-1640 lacks dimensions; qualification and dates alone do not prove another version.
178|version_hold|Murillo Immaculate Conception2f82b6b0 and3937e045 lack physical facts; several known distinct versions do not resolve these incomplete identities.
'''
HOLDS={int(n):(state,note) for n,state,note in (line.split('|',2) for line in HOLD_TEXT.strip().splitlines())}
APPROVED=[n for n in range(1,187) if n not in HOLDS]
NOTES={
13:'Large72.07x91.12cm tempera/oil Masonite differs from the Met Minstrel Show lithograph22.9x29.2cmimage. One painted object, not all print impressions.',
14:'One separately catalogued panel of American Historical Epic, inventoryF75-21/10; do not import the complete mural ensemble again.',
15:'One separately inventoried American Historical Epic panel F75-21/4; retain native literal1923-24date.',
18:'One separately inventoried American Historical Epic panel F75-21/2; related panel references in the shared bibliography do not become additional records.',
19:'One separately inventoried American Historical Epic panel F75-21/6, marked Chapter2Panel1 in source inscription. Shared bibliography is retained without counting the whole ensemble.',
25:'Preserve the distinct series title Red Brass and oil/canvas/pressed-wood support. Yes uses casein on hardboard; other Homage variants have distinct subtitles and source objects.',
38:'Museum classification is painting; literal gouache on paper remains unchanged. No unsupported oil or canvas medium is inferred.',
43:'Retain literal native title Paysage au cid Sombre, including its unusual spelling; do not silently correct catalogue text.',
47:'Native numbered WomanIV differs from MoMAI192.7x147.3cm,II149.9x109.3cm, and small NGA paper drawing. IV remains its own numbered149.86x117.48cmcomposition.',
51:'Restaurant Rispal73.33x60.02cmportrait format differs from Sirene restaurant54.5x65.5cmlandscape format and other named places.',
53:'Nobleman differs from the female portraits despite similar standard canvas sizes; retain native anonymous male sitter.',
56:'Black Beret81.6x64.45cmcanvas differs from the comparable-size Plumed Hat oil/wood panel, and tiny1637etching. Support and subject are reviewed together.',
62:'Source describes a saluting man-of-war under sail beside a dock. Native62.87x78.11cmlandscape canvas differs from the vertical NGA saluting ship66.4x52.9cm and Rijksmuseum cannon-shot78.5x67cm; other retained leads are battles,storms or drawings.',
63:'Nieuwe Kerk is the New Church; retained Oude Kerk records describe the Old Church. Preserve the named building distinction, not just the shared Delft location.',
69:'Anonymous English School portrait retains unknown sitter. Current native narrative and earlier Circle of Arthur Devis sale label are both preserved; supplemental historical scope does not invent an artist link.',
72:'One independently catalogued Rose Tavern painting. Existing Rake Gaming House depicts another scene, while Harlot Bridewell/Funeral belong to a different cycle. Do not count the complete Rake series.',
74:'One copper portrait with its ivory/brass case,51-12A,B. Case is not counted as another artwork; sitter remains Possibly William Herbert.',
87:'Younger Brueghel43.66x58.9cmpanel differs from Elder Harvesters116.5x159.5cmpainted surface; retain the creator distinction.',
90:'Van Dyck115.57x90.33cmcanvas differs from Rijksmuseum75x59cmcanvas and Met106x72.7cmwood panel. Historical creator scope included.',
91:'Named sitter Joannes de Marschalck appears in the native inscription; current Flemish School stays unassigned. Historical van Dyck attribution from narrative was included in the supplemental search.',
95:'31.43x53.34cmpanel differs from NGA31.8x40.5cm and Thyssen39.4x37.3cm interiors. Distinct physical proportions considered with accession/source description.',
96:'Unknown; After Albrecht Durer is the current explicit maker statement. This44.15x31.55cmoak painting is not one of Durer Saint Eustace engraved impressions.',
100:'1773 or1775 remains literal source wording. Endpoint envelope is not a claim of continuous work between those dates.',
102:'Creation1892and reworking1929are both retained; no reduction to the first date.',
104:'Water Mill130.33x163.2cmcanvas differs from National Gallery57.2x73cmcanvas and small chalk drawings.',
105:'Jupiter/Callisto57.79x69.85cmlandscape canvas differs from Met oval64.8x54.9cmportrait format and Hermitage98x72cmversion.',
106:'Small25.72x34.93cmDeauville panel differs from Cleveland46.7x37.8cmDock and the separately described beach scene; other Trouville works name another port.',
107:'Trouville20.64x41.28cmpanel differs from Cleveland34.7x57.7cm,NGA31.2x47.5cmpanels and small Metpastel. Original beach-scene narrative retained.',
110:'Keep Attributed to Sebastien Bourdon from detailed catalogue, despite unqualified index card. Magi oil canvas differs from Shepherds chalk drawing.',
111:'Richard Gallo97.31x116.68cmlandscape-formatcanvas differs from Cleveland male portrait81.3x65.6cm and other named sitters.',
113:'Les Lauves63.82x81.6cm differs from Basel59.9x72.2cmcanvas, Met57.2x97.2cmlandscape and paper versions. Literal date retained without inferring a unique version from year alone.',
114:'Man with Pipe43.18x34.29cmcanvas differs from NGA26.1x20.2cmversion.',
118:'Preserve explicitly identified Lake Garda view; named Nemi,Albano,Genoa and Naples locations remain separate comparison subjects.',
119:'Native long catalogue/provenance text describes Jo and her multiple painted versions; this accession32-30has its own physical54.31x63.5cmcanvas and history. Only this selected physical object is added.',
122:'Erhard120.65x77.15cmpanel differs from Albrecht Altdorfer89.5x76.8cmpanel; current creator and physical support history remain explicit.',
123:'One separately inventoried male panel46-9/1of a betrothal pair; the source Diptych medium is retained. No additional record for the whole pair. Former Holbein Younger attribution is identity evidence only.',
124:'One separately inventoried female panel46-9/2; native description explicitly says one of a pair. Its companion has another sourceIDand accession; no group record added.',
128:'Question mark in Self-portrait(?) stays. Denner wood panel38.89x31.27cm differs from SMK52x40.5cmcanvas and36.5x32cmcopper portrait.',
129:'One panel from the dispersed Monis altarpiece, not the complete ensemble. Conventional unidentified-master label and former Housebook attribution remain evidence.',
131:'Unknown remains the current creator. Former Justus Englehardt Kuhn name is retained in source fields and searched for identity; no invented named authority.',
133:'Detached fresco support132.72x65.72cm remains literal. Guercino short-name scope reviewed independently from unrelated Barbieri creators.',
139:'Round125.73cmMadonna/InfantJohn differs from the Met rectangular193.7x165.7cmMadonna with adult SaintsMaryMagdalenandJohn.',
144:'Joint qualified Bernardo Cavallino and follower(Johann Heinrich Schonfeld?) source label remains intact, including uncertainty and biographical suffix. No unqualified creator link.',
150:'One workshop Saint John panel95.89x44.45cm; four-Evangelist altar-panel records and other individual saints remain different subjects. Do not import an entire polyptych.',
153:'Retain Attributed to Agnolo Gaddi from detail page. Annunciation differs in subject from similarly sized MetTrinity; size alone is not the identity basis.',
157:'Herri met de Bles and Workshop retained. Native GoodSamaritan70.01x101.28cmdiffers from FlightintoEgypt,ParadiseandDiana subjects in the short-name scope.',
160:'Anonymous School of Bruges and former Bellegambe/MasterofDouai labels retained. JanPolack57.3x41cmAbbot differs from27.62x21.11cmpanelhere; no authority invented.',
161:'One triptych38-4A-C,with all three panel dimensions retained; do not create three separate artwork rows.',
162:'Joos carnation61.28x46.36cmversion is separately inventoried from the small qualified workshop Madonna31-115selected here.',
163:'Workshop qualification is explicit on the detailed page. Small25.24x18.42cmoak panel differs from larger carnation61.28x46.36cmversion and HolyFamily compositions.',
164:'Circle of Jan Wellens de Cock retained. Oil wood panel28.58x38.89cm differs from NGA1522woodcut26.3x38.2cmeven though the subject and proportions are close.',
166:'Native narrative explicitly documents a Hayne de Bruxelles version inspired by the Cambrai Madonna. It is a separately described62.23x36.04cmpanel with RousseldeMedavy heraldry and Latin inscription, not the cult-image prototype.',
167:'Small35.24x48.74cmpanel differs from Patinir large triptych117.5x81.3cmcentral panel. Preserve conventional anonymous-master label and historical search names.',
169:'One separately catalogued Knighting of Saint Martin panel, not the complete altarpiece; Martyrdom of John is a different narrative episode.',
173:'Lady Abercromby105.25x84.3cm differs from Walters anonymousLady91.4x68.7cm. SirGeorge companion remains held, without blocking this independently inventoried panel.',
179:'One entire altarpiece32-207A-P,including painted scenes,predella and frame pieces. GoncalPerisSarria plus Workshop stays literal; formerGonzaloPerez/PedroNicolau preserved. Do not multiply the ensemble into16records.',
180:'Workshop of Ribera remains qualified. SaintLawrence is not SaintPhilip or SaintBartholomew; source120.17x134.3cmcanvas and accession88-9 identify this object.',
182:'NativeTrinitarianFriar92.39x85.41cm differs from MetOldMan52.7x46.7cm and portraits of separately named officials. Greek creator remains explicit at object level.',
183:'Rehashed existing WikiArt body states157x121cm for MaryMagdaleneinPenitence; native101.6x81.92cmcanvas is a distinct smaller version. Source dates1577andcirca1580-1585both preserved; date difference alone is not the distinction.',
184:'Workshop of ElGreco retained despite indexplainartist. Small43.51x28.58cmebony panel differs from Cleveland193x116cmcanvas and full-size carrying-cross paintings; crucifixion and carrying the cross remain distinct subjects.',
185:'MoscowSchool label and ca1490-1510date retained. Small37.47x29.21x3.81cmtempera/gold panel depicts John dictating to a scribe. Similar JoosPatmosrecord is oil on wood; other Patmos works have distinct creators/supports/formats. Gift provenance records Istanbul purchase1958andIrwiggift1996; no named painter invented.',
186:'Unknown Russian creator retained.30.48x27.31x3.49cmtempera/gold panel with Abraham,Sarah,three angels and calf differs from the wide38.7x84.5cmOldTestamentTrinity,Cretan97x71.5cmand23.5x13cmpanels,and NewTestamentTrinities. Rehashed Cypriot comparison sources explicitly describe wall paintings. IrwigIstanbulpurchase1958and1996gift are provenance, not creation dates.',
}
def build():
 candidate=m.load(RUN/'native-candidates-003.json.gz')
 for ref in candidate['parser_references']:checked_reference(ref)
 refs=[reference(RUN/name) for name in ['identity-scope-002.json.gz','identity-comparisons-002.json.gz','supplemental-identity-001.json.gz','expanded-comparisons-001.json.gz','version-citations-002.json.gz','prior-body-verification-001.json.gz']]
 for r in m.load(RUN/'prior-body-verification-001.json.gz')['rows']:checked_reference(r['body_reference']);refs.append(r['body_reference'])
 cm={r['source_id']:r for r in m.load(RUN/'identity-comparisons-002.json.gz')['records']};expanded={r['number']:r for r in m.load(RUN/'expanded-comparisons-001.json.gz')['rows']}
 assert len(HOLDS)==37 and len(APPROVED)==149 and set(APPROVED)|set(HOLDS)==set(range(1,187))
 decisions=[];holds=[]
 for row in candidate['rows']:
  num=row['number'];v=row['facts'];capture,index,page,source_refs=f.page(num);assert page['complete'] and f.facts(page)==v and source_refs==row['source_references']
  c=cm[row['source_id']]
  if num in HOLDS:
   state,note=HOLDS[num];holds.append(dict(row,state=state,review_note=note,comparison=c,expanded_comparison=expanded.get(num)));continue
  assert v['date_issue'] is None and v['last']<=1970 and v['inventory']==index['inventory']
  assert not c['source_hits'] and not c['native_url_hits'] and not c['institution_native_id_hits'] and not any(a['relevant'] for a in c['inventory_hits'])
  assert not row['reasons'] or row['reasons']==['Index/detail creator_label differs']
  note=NOTES.get(num,'Reviewed the native subject, creator label, accession, physical medium/dimensions and retained broad/focused title comparisons. No unresolved same-object lead was found for this selected catalogue object.')
  if row['reasons']:assert num in NOTES;note+=' Detailed native attribution takes precedence over the shortened index label; the qualification is preserved without naming a new artist authority.'
  basis=f"Official Nelson-Atkins object{v['source_id']}, inventory{v['inventory']}: {v['title']}; {v['creator_label']}; {v['date_display']}; {v['medium']}; {v['dimensions_text']}. Collection credit: {v['credit_line']}. "+note
  decisions.append(dict(source_id=v['source_id'],number=num,state='approved_review_only_addition',confidence=.9,basis=basis,limitation='Editorial confidence, not a calibrated probability. Source facts, qualified/anonymous labels, rights and unknowns retained. Museum connection does not establish legal title,current custody,current display or publication eligibility. Web-tool extracts are complete but are not original object HTTP bytes.',facts=v,index=index,source_references=source_refs,source_reference=source_refs[0],retrieved_at=row['retrieved_at'],source_discrepancies=row['reasons'],comparison=c,expanded_comparison=expanded.get(num),supplement_references=refs))
 assert len(decisions)==149 and len(holds)==37;return decisions,holds
if __name__=='__main__':
 decisions,holds=build();m.save(RUN/'editorial-reviewed-001.json.gz',dict(at=m.now(),decisions=decisions,holds=holds,candidate_reference=reference(RUN/'native-candidates-003.json.gz'),reviewer_reference=reference(Path(__file__).resolve()),policy='149individually reviewed additions selected from186complete official object extracts;37existing/version/date/group holds. All additions remain review-only,one record per selected physical object or explicitly catalogued ensemble. No new painter authorities,images or current-display claims.'));print(json.dumps(dict(approved=len(decisions),holds=dict(collections.Counter(r['state'] for r in holds)))),flush=True)
