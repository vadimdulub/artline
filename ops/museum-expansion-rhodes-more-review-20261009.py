"""Individually reviewed next Rhodes objects with physical-support and date checks."""
import collections,copy,importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('i',Path(__file__).with_name('museum-expansion-rhodes-more-identity-20261009.py'));i=importlib.util.module_from_spec(z);z.loader.exec_module(i);s=i.s;m=i.m;RUN=i.RUN;ref=s.ref;checked=s.checked
NOTES={
127:'Zepos1243 is a charcoal-on-paper student drawing of an ancient statue, circa1920,120x69cm. The ancient model does not date the physical drawing. Different from the ASFA orphan abstract painting and Lekakis/Zongolopoulos works sharing Untitled.',
129:'Semertzidis5000 is the1956 oil-tempera portrait of an elderly Skyrian woman,70x50cm; one physical portrait, not the whole Skyros series.',
130:'Semertzidis5001 is the1956 Attica landscape,tempera on cardboard54x74cm, with flowering foreground and a rocky hill. Different from Asteriadis landscapes bearing the same place title.',
131:'Semertzidis5002 is the1957 charcoal-and-pastel drawing of the man with blue shirt,headscarf and goggles above his cap. Distinct from5003 and the finished threshing-machine painting; one separate50x35cm support.',
132:'Semertzidis5003 is the1957 charcoal-and-pastel drawing of the man in an open white shirt and cap against a yellow-black field. Different figure from5002 despite equal title,year and dimensions. Not the finished painting.',
133:'Semertzidis5004 is the1955 oil-on-cardboard portrait of Rouli in a light sleeveless dress,70x50cm. The circa1970 portrait5010 with dark pullover remains separately held at the cutoff.',
134:'Semertzidis5005 is the circa1966 acrylic-on-hardboard study of a demonstration participant,125x86cm. Different from his1946 demonstration prints and the finished1966 canvas;1944/1965 events in the narrative do not date this support.',
135:'Semertzidis5006 is the circa1961 oil-on-hardboard fishermen-at-Styra landscape,39x68cm. Figures are small at the left of the shore; not the monumental1962 Fishermen.',
136:'Semertzidis5007 is one1968 tempera sheet containing two fishermen movement studies,50x70cm. Count one physical artwork, not each study or the finished1962 canvas.',
137:'Semertzidis5008 is the circa1968 tempera Fisherman,93x70cm, a single figure in a blue shirt before the sea. The1961 visit in the narrative is background, not this object date.',
139:'Semertzidis5009 is the1967 oil-on-hardboard portrait of publisher Giannis Goudelis,120x70cm, standing before a landscape. The sitters lifespan is not the creation date.',
141:'Semertzidis5011 is the1966 mixed-technique Weaver,70x50cm. Separate from the1970s Weaver5012; historical book illustration context does not turn it into a printed book or a series parent.',
143:'Semertzidis5013 is the1966 mixed-technique Dance before the Firing Squad,130x230cm. May1944 is the depicted event. The museum explicitly identifies a smaller reversed preparatory version of the National Gallery composition, not the same physical canvas.',
148:'Semertzidis5020 is the1966 mixed-technique Rhodes landscape,73x125cm, showing Attavyros and its foothills. Distinct from existing5037,the1967 ink-marker drawing50x70cm, and from later1970s landscapes.',
150:'Semertzidis5021 is the1964 tempera-on-paper right-hand fragment of the final mural study,255x120cm, showing musicians and a dancer. One physical study fragment; not a crop record or the300x450cm mural. Historical town-hall placement of the mural is not a display claim for this study.',
153:'Semertzidis5024 is the1964 oil-tempera Attavyros,50x70cm, with a foreground slope,fields and triangular mountain. Distinct from5036,the red-sky western-Rhodes mountain view, and5020,the larger1966 composition.',
154:'Semertzidis5025 is the1968 tempera-on-paper Last Supper,100x180cm, inspired by a post-Byzantine mural at Paradisi. The modern physical painting is separate from that church mural; not dated to the biblical event or the prototype.',
155:'Semertzidis5026 is the1935 oil-on-canvas male nude study,89.5x113cm, from his student examination work. Separate from the1951 female nude drawing5042.',
156:'Semertzidis5027 is the1935–1936 oil still life,65x75cm, with fabrics,fruit and a clay jug on a small table. Different from the existing Ghika and Oikonomou still lifes; source abbreviated range1935-36 expanded without narrowing.',
157:'Semertzidis5028 is the1938 coloured-pencil drawing of his sister Nadia,40x33cm, a separate preparatory portrait. Not the finished double portrait5030.',
159:'Semertzidis5030 is the1938 oil-on-hardboard Two Sisters,95x67cm, with seated Liouba and Nadia and a cat. One double portrait, distinct from the single-figure Nadia drawing5028 and its preparatory sketches.',
160:'Semertzidis5031 is the1946 tempera-and-coloured-pencil partisan study on paper,142x89cm. Separate physical support from the existing small1946 etching4131 and the finished monumental painting.',
161:'Semertzidis5032 is the1945 tempera-on-paper full-length Vlacha study,87x49cm, standing before pointed mountains. Distinct from existing1947 etched head study4140 and the monumental painting mentioned in its narrative.',
165:'Semertzidis5036 is the1964 oil-tempera western-Rhodes mountain,50x70cm, with a single pyramidal mass and red sky. Distinct from5024 with fields and blue-grey tones; equal dimensions do not make the compositions identical.',
169:'Semertzidis5041 is the1965 oil-tempera study on paper of fishermen eating on shore,130x230cm. Its seated meal scene differs from the fishermen carrying nets studies; one physical sheet.',
170:'Semertzidis5042 is the1951 charcoal-on-paper seated female nude study,106x72cm. Museum narrative distinguishes it from the finished painting in the artists family collection.',
171:'Semertzidis5043 is the1956 pastel landscape at Styra with a pine-covered hill. Dimensions remain unknown. Distinct from the circa1961 fishermen-at-Styra oil5006.',
177:'Afro5057 is the1938 oil-on-wood Winter panel,180x350cm, depicting hunting. One of four separately inventoried season panels made for Grande Albergo delle Rose; no complete-cycle parent added.',
178:'Afro5058 is the1938 oil-on-wood Spring panel,220x280cm, with a bathing woman and flute player beside a stream. Separate support from the other three seasons; later artist biography does not date this panel.',
179:'Afro5059 is the1938 oil-on-wood Summer panel,220x250cm, with shade,seated figures and sunflowers. Separate from equal-sized Autumn5060. Historical council-hall placement is not current display evidence.',
180:'Afro5060 is the1938 oil-on-wood Autumn panel,220x250cm, with grape treading and basket carriers. Literal source title Autumno retained; one panel rather than the four-season cycle.',
192:'Kontopoulos1323 is the1958 oil-on-canvas A Country,110.5x158cm. Visual comparison distinguishes its dense cream,black,red and blue painted fields from the existing1959 red-green One country drawing on pale paper. Related composition,different physical version; both dates preserved.',
193:'Pentzikis1605 is the1961 tempera landscape on paper,22.8x32.5cm. Chalkidiki is only a tentative depicted location. Different from Zongolopoulos Landscape and Pentzikis1962 seaside hut1606.',
208:'Lagana1400 is the circa1960 Syros landscape watercolour,23x31cm, with sea and a barren mountain. Distinct from the larger urban harbour watercolour1401.',
209:'Lagana1401 is the circa1960 Syros harbour watercolour,31.5x43.5cm, showing waterfront houses near Asteria. Separate support and composition from1400.',
211:'Parthenis1603 is the1930–1934 oil still life with porcelain lidded dish and pomegranate,44x44cm. Visual comparison confirms a different composition from the existing wide WikiArt Still Life with pears,basket,bottles and glass; no date or holding rewrite to that record.',
213:'Pentzikis1606 is the1962 watercolour Seaside Hut,32.5x23cm. The1963 exhibition date is not its creation date. The depicted Chalkidiki location remains tentative.',
215:'Grammatopoulos2118 is the1957 Siren woodcut,34x26.5cm, depicting one bird-bodied female with a lyre. Its possible preparatory relationship to In the Island of the Sirens is explicitly tentative; a separate physical print, not a cropped detail.',
222:'Bekiari5053 is the circa1950 oil-on-wood Flowers,36x47cm. Different from existing undated Miliadis Flowers on cardboard and the post1970 Kampanis material.',
223:'Bekiari5054 is the Forest oil,70x80cm, dated to the1950s. Preserve the full1950–1959 decade and do not infer an exact year from its woodland subject.',
224:'Davis5055 is the1951 oil-on-canvas Lindos,60x90cm, with a black-clad woman before the town and acropolis. The source explicitly records the family donation to this museum; no present-display assertion.',
232:'Bartlett/Treacher4009 is the coloured copper engraving of the ruined StJohn loggia at the head of Knights Street,18x22cm. Catalogue1841 and narrative1841–1842 publication retained as an interval. Distinct from Bartlett/Wilmor1851 street view4055 and Witdoeck1828 plate4072.',
235:'Ajmone1029 is the circa1939–1941 oil view of Leros,50.5x60.5cm, with port,castle hill and foreground prickly pear. Not the nineteenth-century engraved Leros views already catalogued.',
237:'Ajmone1031 is the circa1939–1941 oil view of Rhodes Castello,48x69cm. Its foreground walls and distant palace differ from the gate-specific views1020 and1023; palace construction/restoration dates do not date the painting.',
240:'Angelidou1006 is the1960 oil Harbour,54x73cm, showing boats,workers and waterfront buildings. No city is inferred from the generic title.',
245:'Asteriadis1012 is the watercolour Ploughing,31x45cm, explicitly before1948. Lower date bound stays unknown;1948 is an exclusive upper endpoint. Separate physical preparatory sheet for an exhibited landscape,not Semertzidis1946 linocut4132.',
249:'Arlioti1017 is the1969 oil-on-paper Figure in Black,93x71.5cm. Distinct from existing1959 Erotic Couple1003; one figure composition, not a portrait identity inference.',
250:'Asteriadis1018 is the1948 oil-on-canvas Attica Landscape,63x90cm, with cultivated fields and workers. Different physical support and dimensions from existing1002,1948 tempera-on-paper23x34.5cm. Maroussi as depicted place remains tentative.',
252:'Ajmone1020 is the circa1939–1941 oil DAmboise Gate view,48x65.5cm, with the dry moat and gate towers. Separate from the Castello and StAthanasius views; medieval construction dates refer to the subject.',
253:'Ajmone1021 is the circa1939–1941 oil Hippocrates Plane Tree at Kos,52x67.5cm, with square,fountain and tree. The ancient teaching tradition does not date the painting or verify the trees historical identity.',
254:'Ajmone1022 is the circa1939–1941 oil Archangelos Rhodes,50x70cm, showing village houses below the ruined hilltop castle. One painted view,not the castle itself.',
255:'Ajmone1023 is the circa1939–1941 oil StAthanasius Gate view,51x66cm, with bridge,moat and walls. Distinct from DAmboise Gate1020;1522/1922 gate-history dates are not artwork creation dates.',
256:'Ajmone1024 is the circa1939–1941 oil Prophet Elijah Rhodes,51x61cm, showing a wooded slope and mountain. Not a historical hotel or topographic photograph.',
261:'Ajmone1038 is the circa1939–1941 oil Landscape with Church,48.2x58.2cm. Rhodes is a probable depicted location, not certain. No relation to a vanDyck portrait with the same accession number at another museum.',
264:'Grammatopoulos2117 is the1957 Centaurs I woodcut,33x52.3cm, depicting a female centaur and hybrid child. Not Centaurs II,the entire mythology series or the Siren2118.',
270:'Vakalo1050 is the1963 oil-on-canvas Tree Bark,100x75cm. An abstract painted composition,not a natural-history bark specimen or the full tree series.',
271:'Vakalo1051 is the1957 painting on cardboard Birds,48x69cm, two birds inside a fenced garden. Literal medium label retained; different subject from Shells and Fish1052.',
272:'Vakalo1052 is the1956 tempera-on-hardboard Shells and Fish,53x76.5cm, an underwater composition. Its formal relationship to Birds1051 does not make them a single work.',
273:'Vakirtzis1053 is the1962 crayon-on-cardboard Perama harbour view,67x94.8cm. Classified as drawing from its dedicated medium; the broader portal painting category and narrative brushwork wording are retained in evidence.',
274:'Valata-Pappa1054 is the1970 Mykonos watercolour,27.5x50cm. Exact1970 is within scope,unlike circa1970 leads. Two chapel-topped hills remain one physical watercolour.',
275:'Vasiliou1055 is the1950 oil-on-wood Clean Monday Table,125x75.5cm, historically exhibited as The View. Table,foods,kite and Athens view form one painting,not separate records.',
276:'Vasiliou1056 is the1957 egg-tempera-on-wood Monastiraki,95.5x128.8cm. Old Objects is an alternative title for this same work; depicted antiques do not supply an earlier creation date.',
277:'Vasiliou1057 is the1954 oil-on-cardboard Captain Vangelis,90.6x63.2cm. Distinct from Kontoglous Aivali Captain mentioned as a comparison; the sitter is not a creator attribution.',
278:'Vasiliou1058 is one1941 painted manuscript double page,35.8x50.8cm, illustrating the Daskalogiannis song. The1771 event and1787 song do not date the artwork. Count one object,not two pages or a complete album.',
279:'Vasiliou1059 is one1941 egg-tempera manuscript double page,35.8x50.7cm, illustrating Solomoss Free Besieged. Different poem and composition from1058; no complete-album parent added.'}
DRAWINGS={127,131,132,157,170,171,273};WATERCOLOURS={208,209,213,245,274}
def build():
 x=m.load(RUN/'production-identity-001.json.gz');assert x['rows']==i.f.rows();out=[]
 for row,c in zip(x['rows'],x['comparisons']):
  d=copy.deepcopy(row);d['comparison']=copy.deepcopy(c);f=d['facts'];n=d['number'];state=d['metadata_state'];note=''
  if c['source_hits']:state='already_catalogued';note='Existing exact native/SearchCulture object identity; no duplicate or metadata rewrite.'
  elif state=='outside_creation_scope':note='Explicit physical creation after1970; excluded from this addition.'
  elif state=='unknown_date_review_deferred':note='Dedicated creation date unknown. Retain source lead for individual scope/version review; no inferred year or quota placeholder.'
  elif state=='cutoff_date_review_hold':note='Circa1970 or the1970s can extend beyond the cutoff; source qualifier retained and no automatic eligibility or catalogue addition.'
  else:
   assert n in NOTES,n;state='approved_review_only_addition';note=NOTES[n];f['description_md']=note
   if n in DRAWINGS:f['work_type']='drawing'
   if n in WATERCOLOURS:f['work_type']='watercolor'
   if n==232:f.update(first=1841,last=1842,date_precision='range',date_display='1841–1842 (museum catalogue1841; cited publication1841–1842)')
  d['comparison_assessment']='Protected creator and subject comparators, exact source IDs and translated-title visual comparisons reviewed; see subject-comparators and visual-assessment receipts.';d.update(state=state,institution_id=s.IID,basis=note,confidence=.95 if state=='approved_review_only_addition'else None,limitation='Editorial confidence, not calibrated probability. Collection holding only; no current display,venue,custody or ownership claim. Source labels,qualifications and unknowns retained. No image attachment or artist-authority merge.');out.append(d)
 assert len([v for v in out if v['state']=='approved_review_only_addition'])==65
 return out
if __name__=='__main__':
 ds=build();deps=[RUN/v for v in ['candidate-facts-001.json.gz','production-identity-001.json.gz','production-identity-citations-001.json.gz','production-initial-scope-001.json.gz','native-selection-001.json.gz','subject-comparators-001.json.gz','visual-assessment-001.json','visual-reference-captures-001.json']]+[m.RUN/'native/rhodes-20261009/institution-reconciliation-001.json'];m.save(RUN/'editorial-reviewed-001.json.gz',dict(at=m.now(),decisions=ds,dependencies=[ref(v)for v in deps],reviewer_reference=ref(Path(__file__).resolve()),policy='65 individually reviewed physical artworks, all date eligible including one before1948 record with unknown lower bound. One existing object skipped.3 cutoff holds,27 unknown-date leads and64 post1970 exclusions. Local catalogue read-only.'));print(json.dumps(dict(states=dict(collections.Counter(v['state']for v in ds)))),flush=True)
