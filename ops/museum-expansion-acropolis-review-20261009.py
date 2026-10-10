"""Acropolis sculpture decisions: physical versions, BC dates and fragment relationships."""
import collections,copy,importlib.util,json,re
from pathlib import Path
z=importlib.util.spec_from_file_location('i',Path(__file__).with_name('museum-expansion-acropolis-identity-20261009.py'));i=importlib.util.module_from_spec(z);z.loader.exec_module(i);s=i.s;m=i.m;RUN=i.RUN;ref=s.ref;checked=s.checked
HOLDS={
24:'Source explicitly describes a reconstruction of Telemachos stele. Reconcile original fragments and casts before assigning the ancient date to the displayed assembly.',
43:'The original left portion of the head is in Athens; the displayed right portion is a cast of the original in the Rodin Museum. Reconcile cross-museum component identities before adding.',
57:'Athena head Acr.658 is attributed to torso Acr.293 and foot Acr.162, within a possible group with warrior Acr.141. Resolve the parent/components before adding a further record.',
176:'Lyon Kore display combines original lower body and left-arm fragments in Athens with a plaster cast of the upper body held in Lyon. Reconcile the shared sculpture and component holdings first.'}
NOTES={
1:'One marble breast votive. Phile in its inscription is the dedicator, not a securely identified sculptor.',
2:'One marble leg votive. Sosibios is the dedicator, not a securely identified sculptor.',
3:'Ear relief Acr.18381 is a separate support from the Makrygianni ear plaque NMA1278.',
4:'One anatomical votive plaque depicting eyes, not one record per eye.',
9:'One two-sided decorated dedication base; its Demos and Aphrodite faces are not separate artworks.',
10:'One four-sided dedication base containing four gods; count the base once.',
14:'The surviving Homer bust dates to the beginning of the fourth century AD. The earlier Greek model does not supply the date of this physical copy.',
15:'Surviving child head, probably a girl; gender remains uncertain.',
18:'Surviving Eros and trace of Aphrodite belong to one inventoried group. No separate missing Aphrodite statue is invented.',
27:'Small girl head NMA129 is distinct from NMA130 and M413. A hairstyle related to Praxiteles does not establish autograph authorship.',
28:'The child may be a girl or boy; source title retained while narrative uncertainty remains explicit.',
33:'Head Acr.654 has an uncertain Rampin Master attribution and uncertain Kore/goddess/Sphinx interpretation.',
34:'NMA200 is a Hellenistic marble head, probably Aphrodite; it differs from existing Roman head EAM177 despite the identical generic title.',
36:'Acr.616 is not Cleveland Head of a Kore, inventory1924.538, height11.5cm, dated480–460BC. Museum inventory, dimensions and object evidence differ.',
37:'Earlier association of head Acr.659 with seated figure Acr.618 is not asserted as certain. No hypothetical parent is added.',
38:'Head Acr.643 comprises two joined ancient fragments and an ancient repair; count once.',
40:'Source workshop attribution remains Cycladic or Attic, without choosing one.',
42:'The ancient Kore head includes a modern plaster ear restoration; the record represents the original head, not an extra cast.',
44:'Head Acr.621 may belong with arm Acr.314. Only the documented head is added; the deferred arm must be reconciled with this record before later addition.',
45:'Head Acr.617 may represent a Kore, Sphinx, Kouros or rider; no certain gender or parent sculpture is invented.',
46:'Original dog head Acr.525 belongs with body Acr.550. Only this surviving head is represented here; the deferred body must not become a duplicate whole-animal record. It differs from hunting dog Acr.143.',
48:'Rider head Acr.663 is separately inventoried; it is not the Rampin Rider Acr.590.',
49:'Original woman head Acr.634, possibly Athena; its ancient repair to an earlier body does not establish another complete sculpture here.',
50:'Youth head Acr.699 has an open date after450BC. A possible relationship to Pheidias circle remains qualified; no Pheidias authority link.',
51:'Youth head Acr.657 may derive from a relief; no speculative complete relief is added.',
52:'Youth head Acr.644 was fitted to an older body; the source dates this surviving head.',
53:'Alexander head Acr.1331 is attributed to Leochares, with an alternative second-century-BC scholarly date retained. Open after338BC date is not made artificially closed. Cleveland head1927.209,26.5cm, is a separate inventoried sculpture.',
55:'Roman Athena head Acr.2338 copies an older Pheidias group. Physical Roman date retained; Pheidias is not asserted as its sculptor. Separate head from Miltiades Acr.2344.',
56:'Roman Athena head NMA5240 copies the Vescovali type; the older model date does not replace the physical AD100–150 date.',
58:'Agrippina head EAM3554 retains physical AD41–54 dating, not the lifespan of its sitter. EAM inventory namespace is preserved.',
59:'Plautilla head EAM358 retains the source late-second/early-third-century AD qualification, not the sitter lifespan.',
60:'Caracalla head Acr.1311 retains the physical circaAD215 date.',
61:'Lucius Verus head EAM350 is a marble portrait, distinct from the existing copper coin depicting the same emperor.',
62:'Roman Miltiades head Acr.2344 copies a figure from an older Pheidias group; separate from Athena head Acr.2338, with Roman-object date.',
76:'Kore, base, capital and column form one inventoried dedication. Thebades is named as maker; Lyson is the dedicator.',
78:'Calf-bearer Acr.624 and its base count once; Rhombos is the dedicator, not sculptor. The Chicago glazed-stone Egyptian relief1926.504 is a different object.',
79:'Small seated male statuette lacks the head; philosopher/poet/orator interpretation is uncertain.',
80:'Surviving left portion of a Dionysos mask, one original fragment; no missing other half or parent invented.',
81:'The museum Greek narrative identifies an unfinished marble bust sketch, perhaps an apprentice exercise. The mock-up title does not mean a modern reproduction.',
82:'Nike Acr.691 consists of three assembled fragments, counted once.',
83:'Nike Acr.694 consists of five assembled fragments, counted once. Earlier architectural attribution is not asserted as certain.',
84:'Ivory Osiris-Dionysos figurine comprises two joined fragments, one object.',
106:'Perirrhanterion base with six Korai is one carved base, not six artworks. Naxian workshop remains uncertain.',
107:'Praxias dedication is one pillar with a marble face; Praxias is a dedicator and only possibly a sculptor. No missing reliefs invented.',
109:'God relief NAM11 is a distinct older object reused in the Proclus house shrine, not the same object as Cybele NAM12 or existing funerary table NAM90.',
110:'Lenormant trireme relief comprises two joined fragments, counted once.',
111:'Makrygianni ear plaque NMA1278 is distinct from Acr.18381.',
112:'Apollo, Hermes, Nymphs and Pan form one relief with an open date after the middle of the second century BC.',
113:'Asklepios NMA126 consists of three joined fragments with plaster fills, one original relief.',
114:'Asklepios M1434 is a separate relief with worshippers, not NMA126 or EAM1388.',
115:'Asklepios and Hygeia EAM1388 is one relief assembled from two fragments.',
116:'Athena relief Acr.2605 differs from Acr.577 and the Pensive Athena Acr.695.',
117:'Athena relief Acr.577 has three joined fragments. Interpretation of the accompanying old man remains uncertain.',
118:'Acr.1329 is an Athena/Nike/Herakles-or-athlete relief; EAM1329 is a different inventory namespace and different Pan/Nymphs object.',
119:'Cybele NMA1868 is a separate small shrine relief; repeated goddess subject does not merge it with NAM12,NMA5612,NMA7364 or NMA89.',
120:'Cybele NAM12 is a separately inventoried relief reused with NAM11 and NAM90; possible Kallikrates/Kallikles inscription refers to a dedicator.',
121:'Surviving right portion of Demeter/Persephone relief Acr.1348; third figure may be Triptolemos, not certain.',
122:'Cybele NMA5612, found in house Y in2007, differs from the other inventoried Cybele reliefs.',
123:'Cybele NMA7364 is a surviving relief fragment missing its upper part; distinct from the complete NMA5612 relief.',
124:'Cybele NMA89 was found in wellNMA39 in1998; its probable dating remains approximate.',
125:'Nymph relief Acr.6464 copies an older model; physical125–100BC date retained. It is a different relief from Acr.1345.',
126:'Pan/Nymph relief Acr.1345 copies an older model; physical late-second/early-first-centuryBC date retained.',
127:'EAM1329 is one Pan/Nymph relief joined from five fragments. Archandros is dedicator, not sculptor; Acr.1329 is not the same inventory.',
128:'Surviving Pan relief EAM1443; the other figure may be Hermes. No missing left portion invented.',
129:'Sleeping Eros relief is one object joined from two pieces; missing face and limbs remain explicit.',
130:'Zeus-Sarapis ivory plaque may have ornamented a box; no complete box or additional parent is invented.',
131:'Temple-and-portico relief EAM1377 is reassembled from ancient fragments. Its front and narrow-side scenes count once.',
132:'Pensive Athena Acr.695 is one relief found in two pieces; interpretations of its stele remain uncertain.',
133:'Sacrifice relief Acr.581 is one reassembled plaque, distinct from Roman head EAM581 in another inventory namespace.',
134:'Dancer plaque EAM260 is a separate surviving slab from EAM259. Possible shared choragic-base origin is retained; no complete parent base added.',
135:'Dancer plaque EAM259 is a separate surviving slab from EAM260. Its physical late-first-centuryBC date is retained, not the fourth-century model date.',
136:'Dionysos EAM1489 is the right portion of a relief plaque, possibly from a statue base. No speculative parent added.',
137:'Theatre-mask plaque EAM382 consists of three fragments and six masks, one object. Physical second-centuryBC date retained, not older model date.',
138:'Silon stele and attached marble sandal form one dedication. Silon is the dedicator, not a named sculptor.',
139:'Palmyra Trinity NMA1825 is a single relief with two registers; probable fourth-centuryAD dating retained.',
141:'Ivory reclining Sarapis M2860 remains a separate figurine from the ivory plaque M2855 and Osiris-Dionysos M2862 found in the same well.',
142:'Alabaster Sarapis protome NMA3596 comprises two joined pieces, one object.',
143:'NMA281 is a marble footprint votive slab, not the actual foot of a statue.',
144:'Sphinx Acr.630 comprises joined wings, head and body, one object, distinct from Acr.632.',
145:'Sphinx Acr.632 lacks its lower body, and differs from earlier Sphinx Acr.630.',
147:'Bear cub Acr.3737 survives in fragments; possible Artemis connection remains qualified.',
148:'Headless female statue Acr.3020 is possibly Athena; subject remains qualified.',
149:'Goddess Acr.13641 and its plinth survive fragmentarily; no unsupported identity of the goddess is supplied.',
150:'Original front portion of horse Acr.697 has modern lower-leg restorations. Possible hoof/support associations Acr.572/573 and wider pediment group remain tentative; no further components or parent are added.',
151:'Hunting dog Acr.143 is a separate animal from head/body Acr.525/550. Rampin Master is a conventional attribution.',
152:'Kore Acr.589 consists of two joined fragments, one statue.',
153:'Kore Acr.602 comprises four non-joining ancient fragments. Suggested relationship to columnEM6249 and Endoios/Philergos signatures remains uncertain, with no definite named-artist link.',
154:'Headless Kore Acr.594 remains a fragmentary statue; missing head and limbs are not additional records.',
155:'Kore Acr.595 comprises two joined pieces, one statue.',
156:'Kore Acr.615 is reassembled from ancient fragments, one statue; separately carved original head and arms do not create additional records.',
157:'Kore Acr.619 has a source Naxian-workshop attribution; stylistic resemblance to Samos does not replace it.',
158:'Kore Acr.669 survives in two multi-fragment assemblies, together one statue. Possible Athena interpretation remains uncertain.',
159:'Kore Acr.670 is the ancient marble sculpture, distinct from the1911watercolour KAS1790 depicting it.',
160:'Kore Acr.671 was reused as building material; original separately carved hands belong to this one statue.',
161:'Kore Acr.672 and its integral plinth count once; possible Ionian workshop influence remains qualified.',
162:'Kore Acr.673 is reassembled from ancient fragments; hypothetical Athena interpretation remains uncertain.',
163:'Kore Acr.678 resembles the Peplos Kore in facial style but is a separately inventoried physical statue.',
164:'Kore Acr.165 is one surviving portion mended from two fragments.',
165:'Kore Acr.682 was reassembled from15fragments; its two original marble blocks form one statue.',
166:'Kore Acr.684 survives fragmentarily with original separate hand; no additional hand record.',
167:'Kore Acr.685 is the ancient statue, distinct from the1911watercolour KAS1793 depicting it.',
168:'Kore Acr.1360 is a reassembled headless statue; Parian workshop remains uncertain.',
169:'Antenor Kore Acr.681 and inscribed base form one dedication. Antenor is the sculptor; Nearchos the potter is the dedicator.',
170:'Eythidikos Kore Acr.686 survives in two parts counted together once. Euthidikos is the dedicator. The1911watercolour KAS1792 is a different artwork. Open480BC-or-shortly-after date retained.',
171:'Chios Kore Acr.675 is one statue reassembled from three pieces. Its conventional name does not establish a Chian sculptor; the former signed-base association is discredited. Watercolour KAS1796 is a different work.',
172:'Quince Kore Acr.680 and its separately carved original hand remain one statue.',
173:'Almond-Eyes Kore Acr.674 is one statue reassembled from four fragments, distinct from1911watercolour KAS1797.',
174:'Apple Kore Acr.677 is the surviving upper portion of one statue; no missing full-body record.',
175:'Pomegranate Kore Acr.593 is a separate statue, not the Apple Kore Acr.677 or Quince Kore Acr.680.',
177:'Peplos Kore Acr.679 and its reunited original parts are one statue. Possible Artemis identity and Rampin Master attribution remain uncertain.',
178:'Polos Kore Acr.696 and reunited fragments form one statue; its arm was formerly associated with Acr.701. The1911watercolour KAS1798 of its head is a different work.',
179:'Propylaia Kore Acr.688 is the surviving upper statue; open after480BC date retained. Watercolour KAS1791 depicts it but is a different artwork.'}
QUALIFIED={33:'Attributed to the "Rampin Master" (?)',45:'Attributed to the "Rampin Master" (?)',46:'Possibly the "Rampin Master" (museum narrative attribution)',53:'Attributed to Leochares (museum attribution; alternative date discussed)',151:'Attributed to the "Rampin Master" (conventional attribution)',177:'Attributed to the "Rampin Master" (?)'}
def build():
 x=m.load(RUN/'production-identity-001.json.gz');extra=m.load(RUN/'subject-comparators-001.json.gz');narr={v['number']:v for v in m.load(RUN/'native-narratives-001.json.gz')['rows']};assert x['rows']==i.f.rows()[0];out=[]
 for row,c in zip(x['rows'],x['comparisons']):
  d=copy.deepcopy(row);d['comparison']=copy.deepcopy(c);f=d['facts'];n=d['number'];assert not c['source_hits'];d['narrative_evidence']=narr[n]
  f['creator_label']=QUALIFIED.get(n,f['creator_label'])
  # Workshop labels are attributions, not named artist identities.
  if 'workshop'in f['creator_label'].lower():f['creator_label']='Anonymous; '+f['creator_label']+' (museum attribution)'
  if n in NOTES:f['description_md']=NOTES[n]
  # Preserve relevant version comparators, including drawings of ancient objects.
  tokens={w for w in i.q.tokens(f['title'])if len(w)>4};hits=[]
  for a in extra['artworks']:
   if tokens&i.q.tokens(a['title']) and (a['work_type']=='sculpture' or 'acropolis museum'in a['normalized_title']):hits.append(a)
  d['supplementary_comparators']=hits
  state='editorial_component_hold'if n in HOLDS else'approved_review_only_addition'
  basis=HOLDS.get(n,'Official Acropolis Museum object page, inventory '+f['inventory']+'. '+NOTES.get(n,'Separate inventoried physical sculpture. Title, material, dimensions, date and narrative reviewed against the scoped25museum records and bounded global comparators; no same-object concordance found.'))
  d.update(state=state,basis=basis,confidence=None if n in HOLDS else .95,limitation='Editorial confidence, not calibrated probability. Holding only; no fresh display, custody or ownership claim. Literal dates, surviving portions and qualified attributions preserved. No images or artist-authority attachments.');out.append(d)
 assert len(out)==120 and sum(v['state']=='approved_review_only_addition'for v in out)==116;return out
if __name__=='__main__':
 ds=build();deps=[RUN/v for v in ['candidate-facts-001.json.gz','production-identity-001.json.gz','production-identity-citations-001.json.gz','production-initial-scope-001.json.gz','native-details-001.json.gz','native-narratives-001.json.gz','subject-comparators-001.json.gz']];m.save(RUN/'editorial-reviewed-001.json.gz',dict(at=m.now(),decisions=ds,dependencies=[ref(v)for v in deps],reviewer_reference=ref(Path(__file__).resolve()),policy='Selected ancient physical sculptures; source and narrative version review; four cross-museum/parent component holds. Local database read-only.'))
 print(json.dumps(dict(states=dict(collections.Counter(v['state']for v in ds)),date_eligible=sum(v['state']=='approved_review_only_addition'and v['facts']['last']is not None and v['facts']['last']<=1970 for v in ds))),flush=True)
