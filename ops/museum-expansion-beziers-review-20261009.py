"""Individual object decisions with copy, physical-sheet and dating qualifications."""
import collections,copy,importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('i',Path(__file__).with_name('museum-expansion-beziers-identity-20261009.py'));i=importlib.util.module_from_spec(z);z.loader.exec_module(i);s=i.f.s;m=i.m;RUN=i.RUN;ref=s.ref;checked=s.checked
EXISTING={23:'afc7c83a-00b4-51d5-9aa5-a8ae3c6cdb05'}
CIRCA={66:1928,79:1930,93:1930,94:1928,95:1928,96:1928,97:1934,164:1930}
NOTES={
11:'Attributed Niccolò Pisano panel869.8.1,59.3x45.3cm. Earlier Francia/Zaganelli attributions searched; Prado Francia SanFrancisco45.7x47.2cm and Rouen multi-figure panel200x112cm are different works. Attribution stays qualified.',
26:'Wood panel896.1.32,47.2x62.5cm. Source cannot resolve JanBruegel elder/younger and retains attributed label. Existing younger LandscapeAIII1788 is32.5x41.5cm copper; no same-object evidence in title/source/inventory search.',
27:'Panel896.1.36,44.1x36cm with verso RespiceFinem inscription. Museum comment allows Benson or his circle; retain broader qualification and old Holbein attribution in evidence. Known Holbein portraits have distinct sitters, dimensions or source identities.',
30:'Anonymous wood panel896.1.50,38.6x51.4cm. No named creator or inferred attribution added.',
54:'Bronze portrait of OliviaDanieli34.1.217,64.7cm high, signed Rome79; distinct from Injalbert other sculptures and later casts. Source1879 retained for this documented museum object.',
55:'Terracotta group34.1.248,26.2x42.6x19.8cm signed193[2], distinct from marble1923fountain and separately inventoried stone satyr busts.',
58:'Stone engained Bacchante34.1.1360,2.2metres high,1897. Distinct object, not a cast or extra face of another inventory.',
60:'Marble linked group34.1.1576,1.2metres high, signed1892. Count one sculptural object.',
103:'Vien fils charcoal/chalk drawing63.2.5,48.8x37.1cm; not anonymous ivory miniature77.1.222,5.5x4.6cm. Creator remains Joseph-MarieVien1761–1848, not his father1716–1809.',
104:'Vien fils charcoal/chalk drawing63.2.6,51.6x41.3cm, separately inventoried pendant to63.2.5. Other museum Matisse63.2.6 is unrelated; inventories are institution-scoped.',
123:'Anonymous attributed copy afterDurameau, oil canvas89.6.1,48.4x39.8cm. Questioned19thcentury remains date-under-review; do not turn the1859stretcher inscription into a creation date.',
135:'49cm limestone faun head34.1.1582,1898; distinct from82cm faun34.1.1580 and painting byJordaens.',
136:'46cm limestone satyr bust34.1.1584. Distinct dimensions and inventory from55cm34.1.1585 and existing55.5cm1895satyr34.1.1583. Source broad1876–1950period retained.',
137:'55cm limestone satyr bust34.1.1585,25.5x24cm footprint; existing34.1.1583 is55.5x30x31cm and dated1895. This source object is distinct; do not borrow1895.',
138:'One49cm two-faced limestone bust34.1.1593. Two faces do not create two records; separate from two-bust group34.1.1581 held for component reconciliation.',
141:'Original ink/gouache poster design75.9.1,1921; not a printed poster edition or later reproduction. Other museum Braque75.9.1 is unrelated.',
149:'Original ink drawing titled Cartespostales,75.9.18; source medium and inscription establish a drawn cartoon, not the documentary postcard collection.',
152:'One physical ink sheet75.9.30 with alternate caption on reverse; no extra record for second textual version.',
155:'Vertical BonnesAmies75.9.42,33.2x23.8cm, hairdresser caption and12April1930publication. Different drawing from horizontal75.9.47 with dress caption19April1930.',
157:'Horizontal LesBonnesAmies75.9.47,25.2x32.6cm, dress caption19April1930; distinct from75.9.42. Original drawing, not its LeRire reproduction.',
183:'Laurencin oil canvas77.4.5,61x50.2cm; no duplicate tulip still-life in creator/title/inventory source review. Broad1901–2000 date remains unresolved; do not narrow using artist lifespan.',
188:'Boussac watercolour79.4.191,70x103.2cm,1910,bequest1979. Distinct from nine FNAC state deposits with separate subjects/inventories. Artwork date is1910, not acquisition1979 or ancient Egyptian tomb date.',
189:'82cm limestone faun34.1.1580,1898,AI monogram; not49cm34.1.1582 or the two-face bust group.'}
def build():
 x=m.load(RUN/'production-identity-001.json.gz');assert x['rows']==i.f.rows()[0];out=[]
 for row,c in zip(x['rows'],x['comparisons']):
  d=copy.deepcopy(row);n=row['number'];d['comparison']=c;f=d['facts']
  if n in EXISTING:
   hit=next(h for h in c['hits'] if h['id']==EXISTING[n]);assert hit['same_museum'] and hit['accession_number']=='896.1.8';d.update(state='already_catalogued',existing_artwork_id=hit['id'],basis='Existing Wikidata-backed Delacroix1824copy with exact896.1.8inventory and museum. No duplicate and no metadata rewrite.');out.append(d);continue
  assert not c['source_hits'];basis=NOTES.get(n,'Individual original JeanMoulin/Romanin drawing: specific75.9inventory, dimensions, medium and inscription reviewed. Candidate creator pool contains unrelated Molijn/Moulin names; no existing same physical drawing found. One physical sheet, regardless of captions or figures.')
  if n in CIRCA:
   assert f['first']==f['last']==CIRCA[n] and ('vers '+str(CIRCA[n])) in f['source_fields']['Precisions_inscriptions'];f['date_precision']='circa';f['date_display']='vers '+str(CIRCA[n]);basis+=' Catalogue year field is unqualified, but the recorded inscription says vers; preserve that uncertainty.'
  if n==27:f['creator_label']='Ambrosius Benson ou son entourage (attribution proposée; ancienne attribution à Hans Holbein le Jeune)'
  if f['date_precision']=='after':f['description_md']='Creation dated by Joconde only as '+f['date_display']+'. The catalogue also gives a broad period; no upper year has been inferred.'
  if n==183:f['description_md']='Joconde dates this painting only to the twentieth century. The creation date remains under review.'
  if n==123:f['description_md']='Anonymous work attributed as a copy after Louis Durameau. The catalogue questions its nineteenth-century date.'
  if n in [135,189,136,137,138,155,157]:f['description_md']=basis
  d.update(state='approved_review_only_addition',basis=basis,confidence=.94,limitation='Source-backed museum collection connection, not current display, physical custody or legal ownership. Creator qualifications and unknown/broad/after dates preserved. No inferred lifespan dates, images, publication or artist authority links. Confidence is editorial, not calibrated.');out.append(d)
 assert len(out)==89 and sum(d['state']=='approved_review_only_addition' for d in out)==88
 return out
if __name__=='__main__':
 ds=build();deps=[RUN/v for v in ['candidate-facts-001.json.gz','production-identity-001.json.gz','production-identity-citations-001.json.gz','production-initial-scope-001.json.gz','native-context-001.json.gz','joconde-selected-001.json.gz']];m.save(RUN/'editorial-reviewed-001.json.gz',dict(at=m.now(),decisions=ds,dependencies=[ref(v) for v in deps],reviewer_reference=ref(Path(__file__).resolve()),policy='88 selected original physical objects. One additional exact existing Delacroix identity reconciled without writes. Scope/parent/lender holds kept in candidate facts.'))
 print(json.dumps(dict(states=dict(collections.Counter(d['state'] for d in ds)),eligible=sum(d['facts']['last'] is not None and d['facts']['last']<=1970 for d in ds if d['state']=='approved_review_only_addition'),dates=dict(collections.Counter(d['facts']['date_precision'] for d in ds if d['state']=='approved_review_only_addition')))),flush=True)
