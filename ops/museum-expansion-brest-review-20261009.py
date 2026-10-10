"""Individual Brest objects, conservative handling of folded supports and close comparators."""
import collections,copy,importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('i',Path(__file__).with_name('museum-expansion-brest-identity-20261009.py'));i=importlib.util.module_from_spec(z);z.loader.exec_module(i);s=i.f.s;m=i.m;RUN=i.RUN;ref=s.ref;checked=s.checked
NOTES={
7:'One Jean-Haffen SNCF lithographic poster, inventory979.12.1, dated1930–1940. The broad Jean token retrieved unrelated Ingres Caesar studies and a Laboureur painting979.12.1.P; their creators,media and subjects differ. The artist-specific pool has no matching Provins poster. Missing dimensions remain unknown.',
10:'Schuffenecker pastel Le pont,30.8x41.7cm,963.6.1. Exact-title works are by Ventrillon,Boucher,Luntz,Delplanque,Frélaut,Schnetz and Laboureur, not this artist or object.',
11:'Schuffenecker pastel963.6.2,24x15.4cm; the equal-title VanRysselberghe object is oil on wood32.6x42cm, a different creator/support.',
12:'Pastel963.6.3 depicts dawn at a shore and cliff; distinct title and inventory from the Normandie coast963.6.8 despite equal14x20.8cm paper sizes. No source indication of recto/verso or shared support.',
13:'Pastel963.6.4,12.7x18.5cm, distinct from museum oil landscapes by Delavallée and Chamaillard.',
14:'Pastel963.6.5,14x20.5cm,red foliage subject; distinct from the coastal sheets in the same accession series.',
15:'Pastel963.6.6,24.5x16cm,Breton rocks; not Chamaillard oil Paysage breton(Vitré),81.2x65.2cm.',
16:'Pastel963.6.7,10.8x17cm,Etretat. The same artist oil Les Rochers à Etretat is64x82cm, so a separate object; not the oil Rochers à Yport either.',
17:'Pastel963.6.8,14x20.8cm,Normandy coast; separate inventory and subject designation from dawn sheet963.6.3. Equal paper size alone is not a duplicate or verso assertion.',
19:'One24x19cm oil on cardboard,969.5.1,painted on both faces; preserve both titles and count once. Jourdan Pluie à Pont-Aven59.5x73cm and Chapelle de Trémalo74x78cm are oils on canvas with different subjects.',
26:'Bernard Les remparts,979.13.1,29.6x23.1cm walnut ink drawing. Same-title Pellerin work is a1958oil on wood; other Bernard-token hits are different creators. Other architectural Bernard drawings were inspected for translated titles and have different media/dimensions/subjects.',
27:'Schuffenecker33.7x23.7cm boy pastel979.8.1; independent inventoried portrait, not the girl portrait983.3.2.',
32:'Lacombe mahogany high relief982.3.1,275x218.6cm,1898. Separate from the documentary photograph2013.0.69 and existing paper Calvaire993.5.1. Preserve the museum title as a catalogue label; do not resolve the debated self-portrait interpretation by inventing biography.',
33:'Amiet watercolor on paper984.16.1,39x31cm,monogramCA; same-title Laboureur,Darien,Ruisdael,Michel works and the held Sérusier folded support are different creators/objects.',
34:'Moret984.17.2,22.6x32.8cm,atelier numbersHM250a/HM250b refer to two faces of one sheet; full recto/verso title retained and one object counted.',
35:'Moret984.17.3,23.7x32.7cm,atelierHM340; independently numbered from adjacent wave drawingsHM341–343.',
36:'Moret984.17.4,24.3x32.7cm,atelierHM341; distinct inventory,studio number and dimensions fromHM340/342/343.',
37:'Moret984.17.5,23.2x32.9cm,atelierHM342,agitated inlet; different from calm inletHM343,984.17.6.',
38:'Moret984.17.6,23.2x32.8cm,atelierHM343,calm inlet; independent sheet rather than a second title forHM342.',
40:'Sérusier984.21.1,25x32.5cm,three-pencil drawing of river rocks,PSsignature. Different from oil river scenes,watercolor Trieux and the held folded cardboard984.20.1/2.',
43:'Moret984.8.1,23.3x32.6cm,atelierHM200,seaweed/rocks; no same object in creator pool.',
44:'Moret984.8.2,22.4x28.1cm,atelierHM202. PointeII differs from PointeI984.8.7,21.1x31.5cm,HM336.',
45:'Moret984.8.3,23.8x32.7cm,atelierHM236,colour annotations retained as source evidence; distinct from the other coastal sheets.',
46:'Moret984.8.6,24x32.4cm charcoal,HM331; not oil Falaises à Ouessant66x81cm.',
47:'Moret984.8.7,21.1x31.5cm,atelierHM336; separate from smaller PointeII984.8.2,HM202.',
48:'Moret984.8.8,22.5x31.7cm,atelierHM362,high broken cliff; distinct studio/inventory number from other coastal sheets.',
57:'Bernard995.4.1,27x21cm ink drawing,saint figures against religious architecture with Cul de Lampe annotation. Comparator A L EGLISE,INV78.5.1 is charcoal on blue paper27x20cm and carries different title/inventory; existing evidence retained. Neither Bellotto etching nor another creator sharing Bernard is the same work.',
61:'Schuffenecker charcoal2001.16.1,39x31cm; source also retains a former label saying pencil38x31cm. Do not replace current object measurements with that label. Same-title Corot oils100x134cm and Dumas oil89.5x106.2cm are different.',
67:'Schuffenecker pastel983.3.2,19.6x28.8cm; not his oil-on-wood Tête de jeune fille45x37.4cm.',
68:'Schuffenecker charcoal963.6.9,31x24cm,people at a fishing port; not Jourdan oil Brigneau984.19.1,46.2x55cm.',
69:'Schuffenecker pencil963.6.10,25x16cm,named sitterMarieGrandcerre and colour annotations; independent sheet in963.6series.',
92:'Schuffenecker original pastel poster design983.3.1,65.2x49.7cm; neither a printed poster nor Fautrier oil still life with coincident inventory983.3.1 at another institution.',
99:'Delavallée etching/aquatint2013.0.65,27x21.7cmimage/39x33.9cmsheet; two sets of dimensions refer to one print. Coincident inventory at Bourbon-Lancy belongs to Galimard GeorgeSand portrait and is provider-scoped.'}
def build():
 x=m.load(RUN/'production-identity-001.json.gz');assert x['rows']==i.f.rows()[0] and not x['within_batch'];by={v['id']:v for v in x['state']['artworks']};out=[]
 for row,c in zip(x['rows'],x['comparisons']):
  d=copy.deepcopy(row);d['comparison']=copy.deepcopy(c);f=d['facts'];n=row['number'];assert not c['source_hits'];assert f['first'] is not None and f['last']<=1950
  if n==70:
   other=copy.deepcopy(by['dc8655e7-91c6-4bb5-b2ee-880df83a2cc1']);other.update(hit_types=['editorial_alternate_title'],same_creator=True,same_museum=False);d['comparison']['hits'].append(other)
   d.update(state='held_editorial_review',basis='Maisons flamandes2013.0.67(32.2x24.2cm,walnut ink) is close to existing Bernard Les vieilles maisons505(32.5x24.8cm,pen/black ink/grey wash). Historical citations differ but do not conclusively resolve physical identity. Exact national-reference query for000DE006792 returned zero records; limited suffix searches did not resolve it. Hold pending image or stronger object/provenance comparison; do not change either museum link.');out.append(d);continue
  assert n in NOTES
  if n==19:f['description_md']='One oil painting on cardboard, with Moulins à Pont-Aven on one face and Chaumières en Cornouaille on the reverse.'
  if n==34:f['description_md']='One charcoal drawing sheet with a coastal view on one face and a lightly sketched wave on the reverse.'
  d.update(state='approved_review_only_addition',basis=NOTES[n],confidence=.94,limitation='Museum holding, not current display, ownership or custody. Literal creator labels,period ranges,materials and inventories preserved; no lifespan-derived date precision. Mechanical same_creator flags denote discovery token overlap, not verified authority identity. One physical object per record. No images,publication or artist-authority links. Editorial confidence is not calibrated.');out.append(d)
 assert len(out)==34 and sum(v['state']=='approved_review_only_addition' for v in out)==33;return out
if __name__=='__main__':
 ds=build();deps=[RUN/v for v in ['candidate-facts-001.json.gz','production-identity-001.json.gz','production-identity-citations-001.json.gz','production-initial-scope-001.json.gz','joconde-selected-001.json.gz','additional-comparator-evidence-001.json.gz']];m.save(RUN/'editorial-reviewed-001.json.gz',dict(at=m.now(),decisions=ds,dependencies=[ref(v) for v in deps],reviewer_reference=ref(Path(__file__).resolve()),policy='33 selected individual Brest artworks,one close Bernard alternate-title comparison held;66known sources and3fact/group holds separate.'))
 print(json.dumps(dict(states=dict(collections.Counter(v['state'] for v in ds)),types=dict(collections.Counter(v['facts']['work_type'] for v in ds if v['state']=='approved_review_only_addition')),dates=dict(collections.Counter(v['facts']['date_precision'] for v in ds if v['state']=='approved_review_only_addition')))),flush=True)
