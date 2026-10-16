#!/usr/bin/env python3
"""Human-reviewed object decisions for the sequential Streeton selection."""
import importlib.util,copy,json,re
from pathlib import Path
spec=importlib.util.spec_from_file_location('campaign',Path(__file__).with_name('creators-deep-4h-20261010.py'))
x=importlib.util.module_from_spec(spec);spec.loader.exec_module(x);x.configure('arthur-streeton')
plan=x.r.load(x.RUN/'research-selection.json.gz');rows=plan['rows']
NGV='10f88aa8-da2e-58a1-99f1-dc7c360f55b7';NGA='8a40bd5a-e130-57ee-af68-0c921b602c95';NSW='d3524dc2-2672-582f-be42-4bf3c8ace210'
pdf=x.r.load(x.RUN/'exhibition-pdf-receipt.json')
selected=[1,4,5,8,9,10,11,12,13,15,16,18,19,22,23,24]
held={
 2:('a403720f-64e6-547e-8b36-50dac74b86ca','Existing Sandridge; museum qualifies c1888 and inscription 1884. Do not duplicate or silently rewrite.'),
 3:('c2f35a3a-a1ac-512b-bf65-15f0066db4db','Exact visual match to NGA Pastoral in yellow and grey: a colour impression of Templestowe, despite different WikiArt title. Google comparison sheet 1 reviewed. AGSA comparison image was a black placeholder and was not used as identity evidence.'),
 6:('56b1d8de-fbd1-50d9-8fb3-a2a30ecaf3e3','Existing Golden Summer, Eaglemont, same 1889 title and NGA credit.'),
 7:('ac8f5fe6-fe14-5884-a9df-3f884f43ac9c','Hoddle St., 10 p.m. is the existing spelling variant of Hoddle Street, 10 p.m.; 1889.'),
 14:('58e9eb7f-4402-5228-916d-c0723660bd3c','Existing selector hut, exact distinctive title and date.'),
 17:('56cd0b38-a0d9-587b-8a8f-3cd404803dc2','The three liners is shortened from existing The three liners, Circular Quay, 1893.'),
 20:('34dcd2b6-adbd-5ee6-be23-4adfd654ee34','Existing The spirit of the drought; museum date c1895 remains qualified.'),
 21:('dad47e18-8c25-55aa-95b1-6fe3aa57c169','Existing exact title and 1895 source date.'),
 25:('2b68a165-eee7-5c06-81f7-ad2317fa1936','Existing exact WikiArt object URL.'),
 26:('161e0fac-5301-570e-82b1-6c8b987d8573','Existing exact WikiArt object URL.')}
notes={
 1:'Vertical woodland Pastoral 1888. Distinct from the existing 1889 cardboard Pastoral in yellow and grey and later 1894 decorative Pastoral. The direct source omits medium and dimensions; preserve those unknowns.',
 4:'Autumn 1889 shows a woman in white beside washing and an orchard. No existing Streeton counterpart was found. Ballarat source leads are recorded as further research; no unsupported museum link or dimensions are introduced.',
 5:'Evening Game 1889 is the park at sunset with figures, distinct from the football field in The National Game. Exhibition label page 23 records private collection, Sydney; the host museum is not the owner.',
 8:'Exact distinctive title and 1889 date agree with NGV object 77367, accession 2005.61. The source image shows the Princess theatre and Burke/Wills monument. NGV image server denied the comparison request; no claim of paired native-image inspection is made.',
 9:'Same football field composition, posts and figures as the museum-provided Google Arts & Culture object. Board and frame measurements are distinguished.',
 10:'The vertical moonlit landscape with a couple matches the distinctive 1890 title and NGA collection credit in exhibition label page 36. Separate from the smaller disputed romantic couple sketch described by NGV.',
 11:'Distinctive portrait-format golden landscape and gum tree agree with the 1890 NGV object 3055. Native metadata and exhibition label 33 corroborate the object; the NGV image server denial is retained.',
 12:'NGV identifies Spring as 1890 while recording inscriptions referring to Spring of 1889 and Streeton 1890. Retain the explicit catalogue date 1890 and both inscription facts in evidence.',
 13:'Exact same broad moonrise and winding river composition as the museum-provided image. Visually distinct from the existing QAGOMA upright sketch, object 1241. The 2020 museum label specifies later hardboard mounting; preserve that material history.',
 15:'Vertical ferry-wharf painting with golden reflections and smoke; the 2020 NGA collection credit and detailed catalogue description (page 58) agree with the composition. The private ownership in older descriptions predates the documented 2017 acquisition.',
 16:'Rain-soaked elevated view of railway buildings and pedestrians matches the distinctive Redfern title and the museum description on page 55; source date 1893.',
 18:'Direct visual comparison with the existing NERAM 1933_26 reproduction proves these are different 1894 paintings: this broad mountain panorama lacks the foreground road, red carriage and tall line of trees of the NERAM work. The 2020 AGNSW label page 68 corroborates its title, date, medium and holding. Do not merge by title.',
 19:'Small beach scene with figures and boats agrees with the Manly Beach 1895 exhibition label page 46. That label credits Bendigo Art Gallery, not the exhibition host. Preserve the credit as evidence without inventing an institution record.',
 22:'Exact image match to AGNSW From my camp (Sirius Cove), 1896. Visually different from the existing very narrow NGA Sirius Cove c1895; title similarity alone does not make them duplicates.',
 23:'Square Hawkesbury panorama agrees with NGV title, 1896 date and accession 33-2. Native object metadata and exhibition label 76 corroborate the work; no native-image download was available.',
 24:'Square harbour panorama agrees with NGV Sydney Harbour (1907), accession 491-2. Keep museum parentheses in evidence; WikiArt supplies explicit 1907. Do not conflate with the distinct Sydney Harbour from Penshurst (Cremorne) in NSW.'}
ngv={8:(77367,'2005.61','oil on wood panel','21.5 × 16.5 cm'),11:(3055,'1223-4','oil on canvas','53.7 × 43.3 cm'),12:(3067,'A14-1978','oil on canvas on plywood','81.4 × 152.6 cm'),23:(3060,'33-2','oil on canvas','123.0 × 123.0 cm'),24:(3068,'491-2','oil on canvas on plywood','122.2 × 122.0 cm')}
pdf_rows={5:(23,'oil on cardboard',None,'Private collection, Sydney'),9:(24,'oil on cardboard',NSW,'Art Gallery of New South Wales; purchased 1963'),10:(36,'oil on canvas',NGA,'National Gallery of Australia; purchased 1978'),13:(37,'oil on canvas, later mounted on hardboard',NSW,'Art Gallery of New South Wales; purchased 1890'),15:(58,'oil on canvas',NGA,'National Gallery of Australia; purchased 2017 with named donor assistance'),16:(55,'oil on canvas',NSW,'Art Gallery of New South Wales; gift of Lady Denison 1942'),18:(68,'oil on canvas',NSW,'Art Gallery of New South Wales; purchased 1918'),19:(46,'oil on wood',None,'Bendigo Art Gallery; gift of Mr Bert Levy 1900'),22:(61,'oil on plywood',NSW,'Art Gallery of New South Wales; bequest of Mrs Elizabeth Finley 1979')}
google={9:('https://artsandculture.google.com/asset/the-national-game-arthur-streeton/-QHfizPdLA5gYA','11.8 × 22.9 cm (board)'),13:('https://artsandculture.google.com/asset/still-glides-the-stream-and-shall-for-ever-glide-arthur-streeton/ygERI3uJlLij5w','82.6 × 153.0 cm (stretcher); 79.5 × 150.5 cm (sight edge); 118.0 × 189.0 × 9.5 cm (frame)'),22:('https://artsandculture.google.com/asset/from-my-camp-sirius-cove-0108/9wF89eYN3qivBw','28.0 × 21.5 cm (board); 47.0 × 39.4 × 3.5 cm (frame)')}
result=[]
for n in selected:
 row=copy.deepcopy(rows[n-1]);row['selection_index']=n;row['native_sources']=[]
 row['confidence']=.98 if n not in [1,4] else .96
 row['editorial_review']=notes[n]
 row['identity_basis']+=' '+notes[n]
 row['image_identity_review']='Viewed full selected WikiArt reproduction on wikiart-candidates contact sheets 1 and 2. Exact creator page, canonical/legacy object IDs, title, creation date and image URL agree. '+notes[n]
 if n in ngv:
  oid,acc,medium,dims=ngv[n];u='https://www.ngv.vic.gov.au/explore/collection/work/'+str(oid)+'/'
  native=x.r.load(x.RUN/'native-objects'/(x.r.sha(u.encode())+'.json'))
  src=dict(url=u,publisher='National Gallery of Victoria: collection catalogue',receipt=native['receipt'],record_id=str(oid),facts=dict(title=row['work']['title'],date=row['work']['date_display'],medium=medium,dimensions=dims,accession=acc,collection='National Gallery of Victoria'),review=notes[n],confidence=.98)
  row['native_sources'].append(src);row['work'].update(medium_text=medium,dimensions_text=dims,work_type='painting')
  row['museum_research']=dict(institution_id=NGV,accession_number=acc,native_source_index=0,confidence=.98,basis=notes[n]+' Explicit native collection credit; no current-display assertion.')
 if n in pdf_rows:
  p,medium,iid,credit=pdf_rows[n]
  src=dict(url=pdf['source_url'],publisher='Art Gallery of New South Wales: Streeton exhibition labels, 2020',receipt=pdf['receipt'],record_id='Streeton2020-page-'+str(p),locator='PDF page '+str(p),facts=dict(title=row['work']['title'],date=row['work']['date_display'],medium=medium,collection_credit=credit),review=notes[n]+' Label visually reviewed in research-documents/label-review contact sheets.',confidence=.97)
  row['native_sources'].append(src);row['work'].update(medium_text=medium,work_type='painting')
  if iid:row['museum_research']=dict(institution_id=iid,accession_number=None,native_source_index=0,confidence=.96,basis=notes[n]+' Dated 2020 collection credit; retained as holdings evidence, not a fresh display claim.')
 if n in google:
  u,dims=google[n];native=x.r.load(x.RUN/'native-objects'/(x.r.sha(u.encode())+'.json'))
  row['native_sources'].append(dict(url=u,publisher='Art Gallery of New South Wales via Google Arts & Culture',receipt=native['receipt'],record_id=u.rsplit('/',1)[-1],facts=dict(title=row['work']['title'],date=row['work']['date_display'],dimensions=dims,collection='Art Gallery of New South Wales'),review=notes[n]+' Museum-provided object page, not a user-created gallery. Paired images visually inspected.',confidence=.99))
  row['work']['dimensions_text']=dims
 result.append(row)
plan['rows']=result
plan['held']+=[dict(source_url=rows[n-1]['source_url'],title=rows[n-1]['work']['title'],existing_artwork_id=wid,reason=reason) for n,(wid,reason) in held.items()]
plan['reviewed_at']=x.r.now();plan['reviewer']='Codex editorial research and visual review'
plan['additional_identity_inventory']=dict(path=str((x.RUN/'expanded-existing-records.json.gz').relative_to(x.ROOT)),sha256=x.r.sha((x.RUN/'expanded-existing-records.json.gz').read_bytes()),records=25)
plan['research_limitations']=['Two entries (Pastoral and Autumn) retain medium/type/dimensions unknown where the selected direct source is silent.','Native source collection credits are preserved separately from image-provider rights.','NGV native image host denied requests; no bypass and no claim of native visual comparison.','NGA Google Arts & Culture dimensions for existing Templestowe/Sirius Cove appear scaled incorrectly; do not import those dimensional claims.','The AGSA thumbnail response is black; it was rejected as comparison evidence.','Public exhibitions do not transfer ownership: Evening Game remains private collection evidence and Manly Beach credits Bendigo, not NSW.']
x.c.validate(plan)
x.r.save_gz(x.RUN/'reviewed-plan.json.gz',plan)
x.r.save_gz(x.RUN/'image-selection.json.gz',plan)
x.r.save(x.RECOVERY/x.SLUG/'cloud-backup.json',x.r.load(x.RECOVERY/'cloud-backup.json'))
print(json.dumps(dict(new=len(result),excluded=len(held),native_sources=sum(len(v['native_sources']) for v in result),holdings=sum(bool(v.get('museum_research')) for v in result),source_bodies=x.c.validate(plan))))
