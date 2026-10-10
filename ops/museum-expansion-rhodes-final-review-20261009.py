"""Individually reviewed Rhodes physical artworks, with one existing-work link."""
import collections,copy,importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('i',Path(__file__).with_name('museum-expansion-rhodes-final-identity-20261009.py'));i=importlib.util.module_from_spec(z);z.loader.exec_module(i);s=i.s;m=i.m;RUN=i.RUN;ref=s.ref;checked=s.checked
NOTES={
280:'Vasiliou1060 is one1941 egg-tempera painted manuscript double page,35.8x50.7cm, with a shepherd playing a flute and weapons hanging in a tree. The older folk song and1945 exhibition do not date this physical artwork; no album parent added.',
281:'Vasiliou1061 is one1941 painted manuscript double page,35.8x50.6cm, illustrating the prison song. Its precise medium remains unknown; no type or technique invented from adjacent sheets.',
282:'Vasiliou1062 is one1941 painted Greek funeral-feast manuscript,36x25.9cm, with eight figures. The narrative calls it tempera but the dedicated medium field is empty; both facts retained without silently filling the field.',
283:'Vasilikiotis1063 is the1958 oil-on-canvas Harbour,76.5x114.5cm, with boats and a watermelon market. Distinct from Angelidou1006 and other artists harbour views; no exact city inferred.',
286:'Vitsoris1066 is the circa1927 Paris street oil,35x47cm, showing a lit shop and cars at night. Depicted Paris does not establish whether painted in Paris or Athens.',
287:'Vitsoris1067 is the circa1936–1940 Piraeus harbour oil on wood,44x59cm, with coal barges and workers. Different physical support from his undated watercolour1077; range and uncertainty retained.',
288:'Vitsoris1068 is the circa1936–1940 portrait of playwright Pantelis Horn,oil on canvas69.2x43.5cm. The sitter is not his son Dimitris Horn; no portrait or creator conflation.',
289:'Vitsoris1069 is the circa1936–1940 oil tavern scene,38.5x49cm. Workers and interior form one painting, separate from his harbour and portrait works.',
290:'Vourloumis1070 is the1960 oil-on-cardboard Athens Houses,68.5x81cm. The narrative records an Education Ministry purchase and museum collection association; no inference of present legal ownership or display.',
291:'Vyzantios1071 is the same physical Boat with Sails as existing8a26fdd2-c1a7-5f9e-a234-d67bb658891e. Matching reproductions show the identical sailboat,sails,ropes,cabin and reflections. Add only the documented Rhodes holding; preserve existing unknown creation date and all other metadata. Native1962,oil91x72cm and inventory1071 remain cited evidence, not an overwrite.',
292:'Vyzantios1072 is the1957 oil Hydra landscape,69.5x105cm, with pale hills,cypresses and houses. Visual comparison distinguishes it from the existing dense1959 Ydra townscape and the boat compositions Summer in Hydra,Boats Hydra and Port. Source1957 is retained.',
298:'Inventory1078 is a1917 charcoal-on-paper still-life drawing,39.5x48cm. Preserve the literal qualified creator label Σπυρίδων Βικάτος(;); proposed student-demonstration context does not remove the question mark or establish a new artist authority.',
300:'Gaitis1100 is the1946 oil Horses,50.5x43.5cm. The1947 exhibition mentioned in the narrative is not its creation date; no conflation with the artists later repeated-figure constructions.',
301:'Galanis1101 is the circa1910 Seine work on cardboard,38x51cm. The dedicated field says tempera while the narrative calls it oil; literal field retained with this explicit unresolved material discrepancy.',
302:'Germenis1102 is the circa1940 oil Schooner in a Storm,51x63cm. The subject is a single boat composition, not a dated maritime event.',
310:'Giannako1109 is the1961 oil-on-cardboard Medieval City,114x55cm. Chalkis is only a tentative depicted location; medieval architectural subject does not date the painting. Full supplied creator name and alias preserved.',
311:'Gioldasis1110 is the1921 oil-on-cardboard Patissia landscape,25.5x30cm. The historical Athens suburb is a depicted place, not a separate object or a present museum venue.',
312:'Ginis1111 is the1970 oil-on-canvas The Precipitous Infant,79x40cm. Exact1970 is eligible. Painting type follows explicit oil-on-canvas medium despite the empty category; apparent1863–1966 biography typo is not used for creation or artist metadata.',
314:'Gounaropoulos1113 is the1952 oil Archaic Figures,79.7x98.7cm, with three veiled female profiles. Distinct documented title,dimensions and creation date from Goulandris Prometheus circa1948,89x116cm. The archaic subject does not imply ancient creation.',
320:'Giallinas1119 is the1929 Corfu-Pontikonisi watercolour,39x73cm. Image shows a causeway and islet buildings, unlike the National Gallery Landscape with sailboats and bare mountains; National Gallery Corfu also has different12x28.4cm support dimensions.',
324:'Chalepas1123 is one1930–1938 pencil sheet,24x25cm, containing two Eros studies. Count one physical drawing, not two figures. Existing Chalepas sculpture records are different objects; narrative identifications remain tentative.',
326:'Chalepas1125 is one1930–1938 double-sided pencil sheet,24x25cm: two horsemen on the front and a female nude on the reverse. Count one physical artwork, not two sides or separate hypothetical sculptures. Possible Medea identification and source biography typo do not date or rename the object.',
339:'Davis1150 is the1961 oil-on-cardboard Meltemi,51x69cm, with an Aegean harbour. Mykonos is tentative, not asserted. Distinct from his1951 Lindos oil5055 and works by unrelated Davis artists.',
340:'Daniil1151 is the1963 oil Spanish Woman,99x79cm. Literal creator Δανιήλ Δανιήλ retained; no unsupported sitter identity or artist-authority merge.',
343:'Diamantopoulos1155 is the1930 tempera-on-paper Roofs,33.2x24.8cm. The1931 exhibition is distinct from creation; one urban composition.',
344:'Engonopoulos1201 is the1952 oil Oath of the Filiki Eteria (Conspiracy),89x70.5cm. Its1954 Venice exhibition and historical revolutionary subject do not date the artwork. Different from existing1939 divine-couple watercolour and1957 Orpheus.',
348:'Eleftheriadis1205 is the1959 oil Composition with Boat,66x79cm, with foreground chair,table and sea urchins and a small background boat. Not a generic harbour-title duplicate.',
349:'Zepos1206 is the1952 oil Yellow Jug,71x91cm, a still life. Dedicated1952 creation retained; no second exhibition-based date invented.',
352:'Zidianakis1210 is the1961 Portrait,73.5x60.5cm, of a bearded older man in a white blouse. Medium is unstated and remains unknown; generic title does not establish the same sitter as another portrait.',
358:'Zepos1216 is the circa1930 pencil drawing,28x20.8cm, of a clothed woman leaning at a table with a hand to her head. Possible identification as the artists mother remains tentative and does not replace Untitled.',
359:'Zepos1217 is the circa1920 charcoal drawing of a plaster bust of Euripides,36x46cm. The ancient model does not date this student drawing. Distinct from existing1243 full-statue drawing120x69cm.',
360:'Zepos1218 is the circa1925 charcoal life drawing,51x35.5cm, of an older mustached man sitting upright and looking left, both hands beside the seat. Visually distinct from1222 and1223 despite similar dates and near-equal dimensions.',
361:'Zepos1219 is the circa1925 charcoal drawing,57.8x33cm, of a standing female nude in contrapposto with a hand covering her breast. Different pose and support from the seated male studies.',
362:'Zepos1221 is the circa1950 landscape,34.4x43cm, associated with the Ilissos area. The narrative allows late1940s or later; dedicated circa1950 retained, not narrowed to an exact year. Medium remains unknown.',
363:'Zepos1222 is the circa1925 charcoal drawing,52x35cm, of a younger seated man looking down in three-quarter profile with a hand on his thigh. Image confirms a different model and pose from1218 and1223.',
364:'Zepos1223 is the circa1925 charcoal drawing,60x45.6cm, of a frontal seated man with an arm diagonally across his torso. Different pose and support from1218 and1222; not another crop of the same drawing.',
365:'Zepos1224 is the circa1965 pencil-and-pastel Patmos drawing,28x20cm, a vertical hill-village and monastery view. Different from the horizontal Skala harbour view1228.',
366:'Zepos1225 is the1931 pencil drawing Woman Kneading,20x16.1cm. Individually inventoried support; no complete sketchbook or extra study parent added.',
367:'Zepos1226 is the circa1931 pencil drawing Goat,16.1x20cm, showing a goat by tree roots. Separate title and inventory from Woman Kneading; reversed dimensions alone do not establish a recto-verso relationship.',
369:'Zepos1228 is the circa1965 horizontal Kato Patmos harbour drawing,22.5x32.8cm. Dedicated pencil-and-pastel medium retained while the narrative mentions blue ink; discrepancy explicit. Distinct from the vertical hill view1224.',
374:'Zepos1233 is the circa1948 oil Coral Violin still life,57.3x26.1cm. Possible identification with a1948 exhibition does not remove circa. The adjacent undated young-woman portrait1232 repeats these dimensions but has a different subject and inventory; dimensions may need source correction and are retained literally.',
376:'Zepos1235 is the1961 oil Mother,13x11cm. The museum explicitly identifies a preparatory work for the National Gallery painting; one separate physical study, not another record for the finished canvas. Small stated dimensions retained without speculative correction.',
377:'Zepos1236 is the circa1952 oil Peasant Woman of Rhodes,59.8x49.8cm. The1952 exhibition context does not turn the qualified creation date into an exact year.',
378:'Zepos1237 is the1952 oil The House,47x57.5cm, an Athens house view. No precise address or current building identification inferred.'}
DRAWINGS={298,324,326,358,359,360,361,363,364,365,366,367,369};WATERCOLOURS={320}
def build():
 x=m.load(RUN/'production-identity-001.json.gz');assert x['rows']==i.f.rows();out=[]
 for row,c in zip(x['rows'],x['comparisons']):
  d=copy.deepcopy(row);d['comparison']=copy.deepcopy(c);f=d['facts'];n=d['number'];state=d['metadata_state'];note=''
  if c['source_hits']:state='already_catalogued';note='Existing exact native object identity; no duplicate or metadata rewrite.'
  elif state=='outside_creation_scope':note='Explicit physical creation after1970; excluded from this addition.'
  elif state=='unknown_date_review_deferred':note='Dedicated creation date unknown. Retain source lead for individual scope/version review; no inferred year or quota placeholder.'
  elif state=='cutoff_date_review_hold':note='Qualified creation may cross1970; no automatic addition.'
  else:
   assert n in NOTES,n;note=NOTES[n]
   if n==291:state='approved_existing_holding';d['existing_artwork_id']='8a26fdd2-c1a7-5f9e-a234-d67bb658891e'
   else:state='approved_review_only_addition';f['description_md']=note
   if n in DRAWINGS:f['work_type']='drawing'
   if n in WATERCOLOURS:f['work_type']='watercolor'
   if n==312:f['work_type']='painting'
  d['comparison_assessment']='Protected creator and title comparators, translated titles, physical supports and selected visual references reviewed; see subject-comparators and visual-assessment.';d.update(state=state,institution_id=s.IID,basis=note,confidence=.99 if n==291 else .95 if state=='approved_review_only_addition'else None,limitation='Editorial confidence, not calibrated probability. Collection holding only; no current display,venue,custody or ownership claim. Source qualifications,conflicts and unknowns retained. No image attachment or artist-authority merge.');out.append(d)
 assert len([v for v in out if v['state']=='approved_review_only_addition'])==43 and len([v for v in out if v['state']=='approved_existing_holding'])==1
 return out
if __name__=='__main__':
 ds=build();deps=[RUN/v for v in ['candidate-facts-001.json.gz','production-identity-001.json.gz','production-identity-citations-001.json.gz','production-initial-scope-001.json.gz','native-selection-001.json.gz','native-selection-002.json.gz','subject-comparators-001.json.gz','visual-assessment-001.json','visual-reference-captures-001.json','ydra-reference-001.json']]+[m.RUN/'native/rhodes-20261009/institution-reconciliation-001.json'];m.save(RUN/'editorial-reviewed-001.json.gz',dict(at=m.now(),decisions=ds,dependencies=[ref(v)for v in deps],reviewer_reference=ref(Path(__file__).resolve()),policy='43 individually reviewed date-eligible physical artworks,one existing-work holding link preserving its unknown date.41 unknown-date leads and15 post1970 exclusions retained. Real local catalogue read-only.'));print(json.dumps(dict(states=dict(collections.Counter(v['state']for v in ds)))),flush=True)
