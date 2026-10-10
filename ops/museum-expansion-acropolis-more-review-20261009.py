"""Further Acropolis physical-object decisions with fragment and prototype boundaries."""
import collections,copy,importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('i',Path(__file__).with_name('museum-expansion-acropolis-more-identity-20261009.py'));i=importlib.util.module_from_spec(z);z.loader.exec_module(i);s=i.s;m=i.m;RUN=i.RUN;ref=s.ref;checked=s.checked
HOLDS={
67:'Athena head Acr.661 is associated with torso Acr.159 and possibly shield hand Acr.338. Hold for parent/component reconciliation, without making a further whole-statue record.',
146:'Blonde Boy head Acr.689 has a disputed association with torso Acr.6478. Preserve the disagreement and reconcile the physical version before adding.',
185:'Rampin Rider Acr.590 display includes a plaster head whose original is at the Louvre. Cross-museum original/component identity needs reconciliation.',
188:'Scribe Acr.629 display includes a large plaster head portion whose original, the Fauvel head, is at the Louvre. Cross-museum original/component identity needs reconciliation.',
190:'Seated goddess lower body Acr.618 was formerly associated with head Acr.659, already catalogued in wave107. The wording does not conclusively resolve the past association; hold pending parent reconciliation.',
215:'Plinth Acr.431 and Herakles torso Acr.638 are mutually associated as a possible Herakles/Cerberus group. Hold both rather than count the possible same sculpture twice.',
230:'Unassigned hand Acr.4330 may belong to a rider. Its parent is unresolved among rider records; defer this detached component.',
231:'Arm Acr.4246 is ascribed to selected Kouros Acr.665. It must not become a second record for the same sculpture.',
241:'Herakles torso Acr.638 and plinth Acr.431 may belong to the same Herakles/Cerberus group. Their possible union remains unresolved; both held.'}
NOTES={
63:'Small Aphrodite head, NA1957 NAG99, height 5 cm, tilting right. Different from the 7 cm head NA1956 NAG38α, tilting left.',
64:'Small Aphrodite head, NA1956 NAG38α, height 7 cm, tilting left. The probable second-century AD date remains approximate; separate from NA1957 NAG99.',
65:'Athena head Acr.635 is an ancient small copy of the Athena Parthenos type, not the lost chryselephantine original or an autograph work of Pheidias.',
66:'Asklepios head NMA95, height 14.3 cm, is a separately inventoried Roman head. Distinct from complete statue NMA350 and statuette M1123.',
69:'Hermes head Acr.14877 is a second-century AD version, distinct from existing first-century BC head Acr.2281α. Alcamenes is associated with the earlier model, not asserted as maker of this Roman copy.',
108:'Plato portrait head M163 is a first-century AD object for insertion in a herm. The philosopher is the sitter, not the sculptor; his lifetime does not date the surviving object.',
180:'Surviving original Kouros Acr.665 and inscribed base count once. Display reconstruction height is retained separately in literal dimensions. Ketios is the dedicator. Related arm Acr.4246 is held from separate addition.',
181:'Rider and horse Acr.700 form one sculpture; distinct from separately inventoried riders Acr.1359,597,606 and590.',
182:'Rider and horse Acr.1359 form one surviving sculpture, later reused in a fortification. Neither figure becomes an additional record.',
183:'Hippalektryon and rider Acr.597 are one reassembled sculptural group; the creature body and rider torso are not separate artworks here.',
184:'Persian or Scythian Rider Acr.606 is one reassembled sculpture. Its conventional name and possible Miltiades identification remain qualified.',
186:'Headless scribe Acr.144 is one surviving statue, distinct from scribe Acr.146 and the held Acr.629. Existing Solomko Scribe is a different artwork evidenced by its artist and WikiArt source.',
187:'Lower portion of scribe Acr.146 is a separate inventoried statue, distinct from Acr.144 and held Acr.629. Interpretations of the scribes duties remain uncertain.',
189:'Seated goddess Acr.7795 is reassembled from original fragments once stored in two Athens museums. Subject is probably Aphrodite Pandemos; neither a certain cult function nor a current-display claim is inferred.',
191:'Seated goddess lower portion Acr.620, probably Athena, differs from held Acr.618 in inventory, date, dimensions and throne details.',
192:'Youth Acr.633 combines original body and surviving front of the head. Modern back-of-head and neck restorations are not separate artworks.',
193:'Youth Acr.692 comprises three joined ancient fragments, one statue; possible athlete identification remains qualified.',
194:'Owl Acr.1347 is one reassembled ancient sculpture. Possible association with a column does not justify an extra complete-monument record.',
195:'Headless Artemis NMA5052 is a Roman Colonna-type variant. Surviving statue and original shoulder count once; the fourth-century BC prototype does not replace the AD150–200 object date.',
196:'Asklepios NMA350 comprises nine joined pieces, one Roman statue. Distinct from head NMA95 and statuette M1123; the modern excavation date is not a creation date.',
197:'This record represents surviving Athena torso Acr.293, assembled from two original pieces. Associated head Acr.658 and leg Acr.162 are not added separately; the previously held head needs reconciliation with this record before any future import.',
198:'Headless Athena Acr.1336 and plinth are one Roman copy of the Ince type. Retain the physical first-century AD date, not the older prototype date.',
199:'Headless Athena Acr.1337 and plinth are one probable Roman copy. Approximate mid-first-century AD source wording remains explicit.',
200:'Athena Acr.2161 comprises four joined pieces, one Roman-period variation of an older statuary type. Literal cross-BC/AD source dating retained.',
201:'Athena Acr.3029 is separately inventoried from the later Roman copies Acr.1336/1337/2161. Its source gives end of fifth century BC; do not normalize all copies of the Ince type to one date.',
202:'Athena torso Acr.142 is a distinct figure from previously added horse Acr.697. Possible membership of the same pedimental group is retained without adding a hypothetical complete pediment or its other fragments.',
203:'Athena Parthenos Acr.1362 is a surviving headless Roman marble replica, AD150–200, not the lost fifth-century BC original or an autograph work of Pheidias.',
204:'Angelitos Athena Acr.140 and column base count together once. The inscription names Euenor as maker and Angelitos as dedicator.',
205:'Endoios Athena Acr.625 retains the museum attribution to Endoios based on Pausanias. It is not treated as an unqualified signed sculpture.',
206:'Surviving seated Hermes Acr.1346 lacks head, arm and legs. No complete missing statue, tortoise or separate lyre is invented.',
207:'Hygeia NMA201 comprises four joined pieces, one Roman statue. Different from the existing separately inventoried head M1122.',
208:'Kybele NMA125 is a headless statue reused in the same later wall as Selene NMA127. Shared reuse does not make them one artwork.',
209:'Osiris-Dionysos Chronokrator NMA282, base and possibly replaced feet form one inventoried marble statue. Different from ivory Osiris-Dionysos M2862; interpretation of this syncretic deity remains source-qualified.',
210:'Papposilenus carrying infant Dionysos EAM257 is one second-century BC sculptural group copying an older model. Existing Piranesi Silenus with Bacchus is a separate artwork, not this ancient sculpture.',
211:'Prokne and Itys Acr.1358 are one sculptural group, not two additions. Museum attribution to Alcamenes follows Pausanias and remains labelled as such.',
212:'Selene NMA127 and the yoked oxen form one sculpture. Shared later reuse with Kybele NMA125 does not merge the objects; hypothetical restoration details are not supplied.',
213:'Acr.145 preserves one figure and the other figures hand from a group, probably Theseus and Procrustes. Related fragment Acr.370 is not added separately, nor is a second complete figure invented.',
214:'Zeus Heliopolitanus NMA96 is one statue with a separately carved original head. Its relief deities and symbols do not become additional records.',
216:'Small Kore Acr.667, height22.5cm, is a separate original from Kore Acr.668. Its separately carved original arm belongs to the same sculpture.',
217:'Kore Acr.668, height27cm, is one statue joined from two fragments, with an ancient head repair; distinct from Acr.667.',
218:'Nearly finished workshop statuette NMA3447 probably depicts Alexander. Possible inspiration from a lost Leochares/Lysippos hunting group does not establish their authorship or the date of this physical Roman-period object.',
219:'Aphrodite and accompanying Eros NMA294 count once, as one Roman copy in the Louvre-Naples/Frejus type. The fifth-century BC model does not replace the second-century AD creation date.',
220:'Aphrodite NMA85 is a separate second-century BC statuette, height19.6cm, with missing inserted head and hand; not NMA294,414,91 or263.',
221:'Aphrodite NMA414 is an unfinished ancient study, possibly by an apprentice. Its incomplete state is preserved, not described as a finished modern replica.',
222:'Aphrodite NMA91 is an ancient Capitoline-type statuette with plinth and support, one object. The source first-century BC date is retained.',
223:'Aphrodite and child NMA263 comprise two joined fragments of one group. Distinct from previously added Eros/Aphrodite M1578; both retain their respective physical-object inventories.',
224:'Asklepios M1123 is a third-century AD statuette in the earlier Este type. The fourth-century BC prototype does not replace its physical date.',
225:'Athena NMA286 is one headless statuette with olive branch. Its stated first-century BC to second-century AD range is not collapsed to the date of an older model.',
226:'Kybele NMA1869 is a separate small statuette, not relief NMA1868 with a near-identical inventory number, nor statuette NMA284.',
227:'NMA1807 is a headless marble boy, probably Harpocrates. Cleveland Harpocrates1972.6,1940.668 and1942.777 are differently sized bronze objects; title similarity does not establish identity.',
228:'Hekate NMA166 contains three adjoining forms and a common plinth, one sculpture, not three artworks.',
229:'Kybele NMA284 is a distinct small statue found in deposit NMA1, not NMA1869, NMA125 or the separately inventoried reliefs.',
232:'Nike Acr.690 and inscribed column are one dedication reassembled from28fragments. Kallimachos is the dedicator, not the sculptor. The stated4.85m height describes reconstruction; open after490BC date retained.',
233:'Potter Relief Acr.1332 is one reassembled votive relief with a reconstructed inscription naming Endoios as maker. The potter is the dedicator, not securely identified as sculptor. Different namespace from Physicians Relief EAM1332.',
234:'Cart Driver Relief EAM1341 is joined from three fragments, one object. Antimedon is the dedicator; the identities of accompanying goddesses remain qualified.',
235:'Gigantomachy Relief Acr.120 is one reassembled votive relief. Its older identification as an Old Temple metope is not asserted as current.',
236:'Graces Relief Acr.702 comprises two joined fragments, one object. Alternative interpretation as the daughters of Kekrops remains explicit.',
237:'Physicians Relief EAM1332 comprises two joined pieces, one object; the named physicians are dedicators, not artists. Distinct from Potter Relief Acr.1332.',
238:'Kore torso Acr.588 comprises three joined original fragments, one surviving sculpture. Missing separately made arm and complete parent are not invented.',
239:'Archer torso Acr.599 is a surviving figure with separately made original attachments, not a complete victory monument. Possible monument membership remains qualified.',
240:'Artemis Ephesia NMA214 is a separate Roman torso variant. Missing parts and the original cult statue in Ephesus are not additional records.',
242:'Ivory Tyche M2861 and the separately surviving rudder fragment belong to one figurine. The combined attributes of several deities do not create multiple works.',
243:'NMA5555 is an unfinished ancient female sculpture from a marble workshop; intended identity remains unknown. It is not a modern mock-up or a completed figure.',
244:'NA1957 NAG77 is an unfinished ancient Aphrodite figurine, with missing head and legs. Different physical support from the completed and unfinished Makrygianni Aphrodite statuettes.',
245:'NA1957 NAG135 is a small unfinished Pan figurine retaining the head and upper torso. No missing lower body or parent sculpture is invented.',
246:'NMA2517 is an unfinished life-size right female hand from the marble workshop, retaining pointing-machine marks. Record the documented ancient workshop piece only; no completed parent statue asserted.',
247:'NMA160 is an unfinished oversized left male hand, not the right hands NMA2517/3593. Only the original workshop component is recorded, without an invented parent.',
248:'NMA3593 is an unfinished right hand with a sleeve-like marble mass, found above the marble workshop. Its different handedness, size and configuration distinguish it from NMA160 and NMA2517.',
249:'NA1960 NAM20 is a separately inventoried unfinished veiled female head from the south slope, not one of the Makrygianni heads.',
250:'NMA3345 is an unfinished bearded herm head from a marble workshop; the missing column is not another record.',
251:'NMA98 is an unfinished child head with a pointing-machine mark, not a finished portrait or a modern cast.',
252:'NA1957 NAG97 is an unfinished Dionysos head, distinct from Aphrodite head NA1957 NAG99 and Pan figurine NA1957 NAG135.',
253:'Unfinished female head NMA93, height7.5cm, is distinct from NMA4624, height17.4cm, with an insertion tenon.',
254:'Unfinished female head NMA4624 has an insertion tenon for a statuette; record the surviving original head without inventing its complete parent. Distinct from NMA93.',
255:'Kritios Boy Acr.698 consists of the reunited original torso and head, one statue. Attribution to Kritios is based on stylistic comparison and remains qualified. Open after480BC source date retained.'}
QUALIFIED={205:'Attributed to Endoios (museum attribution based on Pausanias)',211:'Attributed to Alcamenes (museum attribution based on Pausanias)',255:'Attributed to Kritios (museum stylistic attribution)'}
def build():
 x=m.load(RUN/'production-identity-001.json.gz');extra=m.load(RUN/'subject-comparators-001.json.gz');narr={v['number']:v for v in m.load(RUN/'native-narratives-001.json.gz')['rows']};assert x['rows']==i.f.rows()[0];out=[]
 for row,c in zip(x['rows'],x['comparisons']):
  d=copy.deepcopy(row);d['comparison']=copy.deepcopy(c);f=d['facts'];n=d['number'];assert not c['source_hits'];d['narrative_evidence']=narr[n];f['creator_label']=QUALIFIED.get(n,f['creator_label'])
  if 'workshop'in f['creator_label'].lower():f['creator_label']='Anonymous; '+f['creator_label']+' (museum attribution)'
  if n in NOTES:f['description_md']=NOTES[n]
  state='editorial_component_hold'if n in HOLDS else'approved_review_only_addition';assert n in HOLDS or n in NOTES
  d.update(state=state,basis=HOLDS.get(n,'Official Acropolis object page, inventory '+f['inventory']+'. '+NOTES.get(n,'')),confidence=None if n in HOLDS else .95,limitation='Editorial confidence, not calibrated probability. Museum holding only; no fresh display, custody or ownership claim. Literal dates, qualifiers and surviving portions retained. No image or artist-authority attachment.');out.append(d)
 assert len(out)==84 and sum(v['state']=='approved_review_only_addition'for v in out)==75;return out
if __name__=='__main__':
 ds=build();deps=[RUN/v for v in ['candidate-facts-001.json.gz','production-identity-001.json.gz','production-identity-citations-001.json.gz','production-initial-scope-001.json.gz','native-details-001.json.gz','native-narratives-001.json.gz','subject-comparators-001.json.gz']];m.save(RUN/'editorial-reviewed-001.json.gz',dict(at=m.now(),decisions=ds,dependencies=[ref(v)for v in deps],reviewer_reference=ref(Path(__file__).resolve()),policy='75selected original physical sculptures, nine component/cast holds, qualified ancient models and attributions; local DB read-only.'))
 print(json.dumps(dict(states=dict(collections.Counter(v['state']for v in ds)),date_eligible=sum(v['state']=='approved_review_only_addition'and v['facts']['last']is not None for v in ds))),flush=True)
