"""Literal15-object Kilkis research facts; periods remain non-numerical."""
import collections,gzip,importlib.util,json
from pathlib import Path
from bs4 import BeautifulSoup
z=importlib.util.spec_from_file_location('q',Path(__file__).with_name('museum-expansion-kazantzakis-selection-20261009.py'));q=importlib.util.module_from_spec(z);z.loader.exec_module(q);m=q.m;RUN=m.RUN/'native/kilkis-20261010'
source=m.load(RUN/'selected-object-discovery-001.json.gz')['rows'];native=m.load(RUN/'native-selected-001.json.gz')['rows'];out=[]
for r,n in zip(source,native):
 assert r['source_id']==n['source_id'];soup=BeautifulSoup(gzip.decompress((m.ROOT/n['receipt']['body_path']).read_bytes()),'html.parser');title=q.clean(soup.select_one('.CardTitle__title').get_text(' ',strip=True));period=q.clean(soup.select_one('.CardTitle__subtitle').get_text(' ',strip=True));attrs={}
 for el in soup.select('.pt-attribute'):
  parent=el.parent;label=parent.find('label');assert label is not None;key=q.clean(label.get_text(' ',strip=True));assert key not in attrs;attrs[key]=q.clean(el.get_text(' ',strip=True))
 descriptions=[q.clean(v.get_text(' ',strip=True))for v in soup.select('.ContentBlock__body-inner')];ss=BeautifulSoup(gzip.decompress((m.ROOT/r['receipt']['body_path']).read_bytes()),'html.parser');literal,enrich=q.fields(ss);assert attrs.get('Αριθμός Έργου');assert attrs.get('Είδος')in ['Ειδώλιο','Άγαλμα','Ανάγλυφο','Αγαλμάτιο'];num=r['number']
 note='Museum native page and collection-level statement identify the holding collection; findspot does not establish current display. Dedicated native label is a historical period,not a numeric creation interval; retain unknown numeric bounds and require date-scope review. No creator supplied.'
 if num in [6,10]:note+=' Bed-decoration fragments1594(hand)and1595(partialhead)need parent-object/physical-unit comparison with existing1593. Do not automatically count fragments of one furnishing as independent artworks.'
 if num in [13,14]:note+=' Two grape-cluster fragments5859 and5862 have distinct accession numbers and13mm/16mm reportedthickness; possiblejoining/parent-object identity stillrequiresvisualreview.'
 if num==8:note+=' Probable Aphrodite identification remains qualified. Two joinedpieces make onefigurine4460; compareexisting4461 ratherthanmergeontitle.'
 if num in [4,5]:note+=' Byzantineperiodlabel retained as stated,includinguncertainmaleidentificationfor1404; do not silently redate from stylistic assumptions.'
 out.append(dict(number=num,source_id=r['source_id'],source_url=r['index']['url'],native_url=n['native_url'],title=title,inventory_literal=attrs['Αριθμός Έργου'],work_type='sculpture',creator_label=None,date_display=period,first=None,last=None,date_precision='unknown',native_fields=attrs,native_description=descriptions,aggregator_literal=literal,aggregator_enrichment=enrich,source_receipt=r['receipt'],native_receipt=n['receipt'],review_state='candidate_pending_live_identity_and_physical_unit_review',note=note,images_downloaded=False,new_production_record=False))
m.save(RUN/'candidate-facts-001.json.gz',dict(at=m.now(),rows=out,native_reference=q.s.ref(RUN/'native-selected-001.json.gz'),source_reference=q.s.ref(RUN/'selected-object-discovery-001.json.gz'),script_reference=q.s.ref(Path(__file__).resolve()),policy='Literalmuseum inventorylabels,periods anddescription. SearchCulture enrichment notsilentlypromoted tosourcecreationdates orgeography. All15remaincandidates;no liveDBidentitycheck,imagesorwrites. Scopedmuseumartworksbaselineandcitationsneededafterauthentication.'))
print(json.dumps(dict(candidates=len(out),periods=dict(collections.Counter(v['date_display']for v in out)),numeric_date_bounds_invented=0)),flush=True)
