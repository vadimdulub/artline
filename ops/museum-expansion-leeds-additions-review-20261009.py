"""Selected Cotmania physical-object review, including curatorial corrections to table labels."""
import collections,copy,gzip,hashlib,importlib.util,json,re
from pathlib import Path
def module(name,file):
 z=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(z);z.loader.exec_module(v);return v
s=module('s','museum-expansion-leeds-additions-common-20261009.py');f=module('f','museum-expansion-leeds-additions-facts-v2-20261009.py');i=module('i','museum-expansion-leeds-additions-identity-v3-20261009.py');m=s.m;RUN=s.RUN;ref=s.ref;checked=s.checked
OVERRIDES={
 10:('Almost certainly Edward William Cooke; formerly attributed to John Sell Cotman with Miles Edmund Cotman','The object title and David Hill catalogue essay reject the older composite attribution and identify Cooke by comparison with his dated 1864 watercolour. Preserve almost certainly and source c.1864.'),
 19:('John Sell Cotman (recto); probably an unidentified pupil (verso)','One sheet: white-jacket musketeer with musket over right shoulder; verso upright waterside building with C Watson sign. Current curator retains John Sell for recto despite historical Miles Edmund suggestion; verso is probably pupil work.'),
 22:('John Sell Cotman (recto); probably an unidentified pupil (verso)','One sheet: pikeman and landscape with trees on verso. The native 114 x 267 mm dimension is retained literally, not silently corrected. Historical Miles Edmund proposal retained as evidence.'),
 27:('John Sell Cotman (recto); probably an unidentified pupil (verso)','One sheet: green-jacket musketeer with musket over left shoulder; castle on reverse. Different from candidate19 with the same former Spanish Arquebusier title. Current attribution follows the catalogue essay while retaining earlier debate.'),
 33:('Possibly by John Thirtle; authorship of recto and verso unresolved; formerly attributed to John Sell Cotman','One physical sheet with tomb recto and three reverse sketches. The essay leaves open whether the Thirtle inscription applies to the whole sheet,one side,one sketch or a recorded model. No definite maker assigned to either side.'),
 36:('Circle of John Sell Cotman (attribution unresolved)','The catalogue essay explicitly leaves John Sell participation unresolved and says the work comes from his circle. Distinct Leeds sheet from Walker153 and from Leeds cattle composition candidate20; no unqualified Cotman attribution copied from the table.'),
 37:('Unidentified artist, after John Sell Cotman; formerly attributed to John Sell Cotman','The native essay says the watercolour cannot be by Cotman. It derives from a separate Norwich pencil drawing dated 26 July1800. Preserve the watercolour source date c.1803, not the model date.'),
 39:('Unidentified artist, formerly attributed to John Sell Cotman','The native essay explicitly rejects Cotman authorship and only suggests a possible copy of a lost composition. Do not assert definite copy or transfer identity from Yale B1975.2.506.'),
}
NOTES={
 1:'The word copy in the essay describes a demonstration model for pupils, not an attribution to a copyist.',
 7:'Current1804 sheet differs from the related Norwich c.1807 watercolour,1811 print and later copied version.',
 8:'Fourth soldier drawing gifted by Robert Hawthorn Kitson1945,315x249mm; separate accession and provenance from the three Sydney Kitson sheets. Datec1825 is creation,1607 is the source engraving publication.',
 9:'One physical sheet with two portrait studies on reverse; different from Cley Church and from copies by MrsTurner. Both sides retained in title.',
 14:'Cotman composition incorporating a Poussin-derived figure motif, not a Poussin original or an additional physical item.',
 16:'Current essay identifies a preliminary Cotman version despite historical copy doubts. Other full-size1823,1829 and collection versions are explicitly distinct; native qualifications and criticism retained.',
 17:'Preserve native John Sell and previously Miles Edmund attribution. No artist link or invented certainty.',
 18:'Native credit and provenance say scheduled as missing in December1973 following a collections audit. Retain research evidence; no new accepted holding or artwork row in this pass.',
 20:'Sepia cattle-watercolour is a distinct Leeds sheet from candidate36 horses/reed-cart composition. Unknown dimensions retained.',
 25:'Paul Sandby Munn1803, not Cotman. Native gallery catalogue and exact Kitson1939 credit establish gallery association despite absent separate provenance section.',
 26:'42x74mm sight-size cloud/ship fragment,c1824, is different from British Museum1902,0514.32 dismasted-brig watercolour1808,19.5cm high in retained source. Other exact titles have different creators and media.',
 28:'Native credit gives Kitson1939 bequest although the provenance subsection stops at Boswell purchase1927. Exact gallery catalogue allocation retained; no invented intermediate provenance.',
 31:'Native watercolourc1825 differs from etchings of Tan y Bwlch. Exact gallery catalogue and Kitson1939 credit support holding despite absent separate provenance subsection.',
 32:'Copy criticism concerns the second Norwich version, not this Leeds sheet. Current curator calls Leeds the prime version; pencil/wash, sepia watercolour and1823 exhibition versions stay separate.',
 34:'Sometimes attributed to John Sell Cotman remains qualified; Miles Edmund discussion is not converted into a definite maker.',
 35:'John Joseph Cotman1873, not John Sell. Creation is eligible; do not use John Sell lifespan as a date rule.',
 38:'Current rocky-pool sheet1802 has separate accession and image/paper dimensions; not the conduit or Brecon subjects.',
 40:'Creation1804 is separate from source credit1937 and accession1938. Both acquisition statements preserved without altering creation.',
 41:'Native studio attribution and associated sons preserved; drawing305x238mm,c1835, reverses earlier watercolours and differs from1837/1838 etchings. The associated sons are not definitive joint authors.',
 44:'No Artist table field; Cotman is only Associated Person. Essay rejects his hand and proposes a Hovingham pupil, probably Worsley family. Preserve uncertainty, no new painter authority.',
 45:'Small98x172mm man-of-war and fishing-smack drawingc1830 differs from BM1808 dismasted brig and the tiny Leeds cloud/ship fragment.',
 46:'Edingthorpe screen1816 is a different church/interior subject from Cley1818; retain uncertain spelling.',
 47:'Repeated Associated Person fields do not imply multiple creators. Keep ?Dover subject and c1799 date.',
 48:'John Joseph uncertainty in the essay concerns a related sawmill drawing, not this eroded-gulley sheet. Preserve current attribution and source c1829.',
 49:'Cotman sketch after David Cox, not the Cox painting YaleB1977.14.135. Preserve after relationship and own c1810 date.',
 50:'Source c1830 is distinct from the paper watermark date1828; no invented exact creation year.',
}
COMPARISON={
 2:'Different Lowcock park painting1872; subject words do not identify the physical object.',
 5:'Frank Dean Windmill1896 differs in creator,date and accession.',
 9:'Cley Church2013.340 depicts a different named church with different dimensions; this is the KingsLynn west door.',
 16:'Falaise1821 etching,Normandy graphite castle,Caen house and Beccles view differ in subject/medium/dimensions/accession from this small street watercolour.',
 18:'Florence Hess beach painting is a different creator/accession; current candidate separately held as missing.',
 20:'Tan y Bwlch softground etching1995.7.1 differs in subject and medium from lake-and-cattle watercolour.',
 23:'William Burgess1785 exact-title work is a different artist; Cotman Tan y Bwlch prints are different subjects/media.',
 24:'Cley Church graphite/wash2013.340 differs from Blakeney/Wiveton171x283mm even though both are dated1818.',
 26:NOTES[26],
 29:'NGA1995.52.30 wooded landscape is chalk,heightenedwhite28.7x37.3cm,probably1841; Leeds16x23.5cm watercolourc1835 differs. Lowcock park1872 also different.',
 31:'NGA Tan y Bwlch is a softground etchingc1810/15. Butterfield and FrederickGeorgeCotman works have different makers and dates.',
 32:'Beccles view2017.348 depicts another town and differs in date,dimensions and inventory.',
 33:'Frank Dean Windmill1896 is a different artist,century and medium context from the tomb recto/multiple verso sheet.',
 34:'Daubigny1875,KarlDaubigny1885 and MacArthur chateau works are distinct makers/objects. Shared place title does not imply identity.',
 36:'Tan y Bwlch1838/c1810-15 etchings differ in medium and subject from this reed-cart lake watercolour.',
 37:'Tan y Bwlch etching differs in medium and subject from the derivative conduit watercolour.',
 41:NOTES[41],
 42:'WilliamChristianSymons On the Shore1884 is a different maker,date and accession.',
 44:'All exact Study of Trees hits have different creators/inventories. MilesEdmund Trees on Yare1846 is a separate later work; this Hovingham pupil sheet is c1804,286x165mm.',
 45:NOTES[45],
 46:NOTES[46],
 48:'Lowcock In the Park1872 is a different artist,date and object from Cotman gulley c1829.',
 49:'Kenyon Cox1912 sketch sheets are a different maker/century. DavidCox1844 BoltonAbbey and Altrincham are different subjects; derivative relationship does not establish object identity.',
 50:'John Selby-Bigge Composition1940 is a different maker,century and accession.',
}
def source_rows():
 return [v for name in ['cotmania-objects-001.json.gz','cotmania-extra-objects-001.json.gz'] for v in m.load(RUN/name)['rows']]
def verified_raw(cap):
 raw=gzip.decompress((m.ROOT/cap['body_path']).read_bytes());assert cap['receipt']['status']==200 and hashlib.sha256(raw).hexdigest()==cap['receipt']['sha256'];return raw
def validate_sources(rows):
 assert len(rows)==50 and len({r['source_id'] for r in rows})==50
 for r in rows:
  verified_raw(r['capture']);assert r['index']['url']=='https://cotmania.org/works-of-art/'+r['source_id'];fs=r['parsed']['fields'];assert fs['Reference'].startswith('LEEAG.') and fs.get('Credit Line');assert 100<=r['date'][0]<=r['date'][1]<=1970
 probes=m.load(RUN/'native-probes-001.json')
 for r in probes['rows']:verified_raw(r['capture'])
 assert 'Leeds Art Gallery' in probes['rows'][0]['parsed']['text'] and 'commission' in probes['rows'][0]['parsed']['text']
def corrected(facts,number,text):
 v=copy.deepcopy(facts)
 if number in OVERRIDES:
  label,basis=OVERRIDES[number];v['original_creator_label']=v['creator_label'];v['creator_label']=label;v['creator_editorial_basis']=basis
  if 'qualified_creator' not in v['issues']:v['issues'].append('qualified_creator')
 if number==10:assert 'almost certainly by Edward William Cooke' in text
 if number==36:assert 'well within Cotman' in text and 'awaits the opportunity of proper comparison' in text
 if number==37:assert 'watercolour cannot be by Cotman' in text
 if number==39:assert 'the hand is not his' in text
 if number==33:assert 'Thirtle' in text and 'authorship of any of them open to doubt' in text
 return v
def build():
 rows=source_rows();validate_sources(rows);facts=m.load(RUN/'candidate-facts-002.json.gz');identity=m.load(RUN/'identity-003.json.gz');assert facts['rows']==i.rows()==identity['rows'];assert not facts['source_fact_holds'];comps=i.comparisons(identity['rows'],identity['state']);assert comps==identity['comparisons'];batch=i.within_batch(identity['rows']);assert batch==identity['within_batch'];assert all(v['numbers']==[19,27] and v['kind']=='title' for v in batch);assert len(batch)==2;out=[]
 by={r['number']:r for r in rows};context=m.load(RUN/'comparison-source-context-001.json.gz')
 for dep in context['body_references']:checked(dep)
 for r,c in zip(facts['rows'],comps):
  n=r['number'];src=by[n];v=corrected(r['facts'],n,src['parsed']['text']);assert not c['source_hits'];assert not any('inventory' in h['hit_types'] for h in c['hits']);assert bool(c['hits'])==(n in COMPARISON)
  # Numeric identifiers from other collections are different namespaces, never exact matches.
  for h in c['other_source_numeric_id_collisions']:assert not (h.get('source_url') or h.get('canonical_url') or '').startswith('https://cotmania.org/') and h.get('scheme')!='cotmania-object'
  held=n==18
  if held:assert 'scheduled as missing' in src['parsed']['text'].lower()
  else:assert 'scheduled as missing' not in v['source_fields']['Credit Line'].lower()
  review=dict(number=n,source_id=r['source_id'],institution_id=s.IID,state='editorial_hold' if held else 'approved_review_only_addition',facts=v,comparison=c,comparison_basis=COMPARISON.get(n,'No identity candidate in the bounded creator,title,inventory,source and full gallery scope.'),version_note=NOTES.get(n,'Exact native accession denotes one physical object; titles,source creation date,medium and unknown fields retained.'),confidence=None if held else .97,confidence_kind='editorial assessment, not calibrated probability',basis='Museum-commissioned Cotmania catalogue gives exact Leeds Art Gallery accession, object description and collection credit. '+OVERRIDES.get(n,('', ''))[1],limitation='Documented collection association only; no current display, current custody or legal ownership claim. Uncertain maker,subject,date and version descriptions retained. No image bytes or painter-authority links.',retrieved_at=src['capture']['receipt']['retrieved_at'],source_capture=src['capture'],source_record_reference=ref(RUN/'selected-objects-001'/('%03d.json'%n)),physical_object_count=0 if held else 1)
  out.append(review)
 assert collections.Counter(d['state'] for d in out)=={'approved_review_only_addition':49,'editorial_hold':1};assert len({d['facts']['inventory'] for d in out})==50
 return out
def main():
 out=build();paths={Path(__file__).resolve(),Path(f.__file__),Path(i.__file__),Path(s.__file__)}|{p for p in RUN.rglob('*') if p.is_file()};ctx=m.load(RUN/'comparison-source-context-001.json.gz');paths|={checked(d) for d in ctx['body_references']};m.save(RUN/'editorial-reviewed-001.json.gz',dict(at=m.now(),decisions=out,dependencies=[ref(p) for p in sorted(paths)],reviewer_reference=ref(Path(__file__).resolve()),identity_artworks=len(m.load(RUN/'identity-003.json.gz')['state']['artworks']),identity_citations=len(m.load(RUN/'identity-citations-003.json.gz')['citations']),policy='Selected49 physical objects,not archive pages,with one missing-object hold. Source-table attributions explicitly qualified using the same object catalogue essay. All existing data preserved; additions stay review.'))
 print(json.dumps(dict(reviewed=50,new_records=49,held=1,creator_refinements=len(OVERRIDES),verified_native_bodies=54,comparison_raw_bodies=len(ctx['body_references']))),flush=True)
if __name__=='__main__':main()
