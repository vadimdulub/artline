"""Selected individual Moulin drawings; repeated crowd sheets remain unresolved."""
import collections,copy,importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('i',Path(__file__).with_name('museum-expansion-beziers-more-identity-20261009.py'));i=importlib.util.module_from_spec(z);z.loader.exec_module(i);s=i.f.s;m=i.m;RUN=i.RUN;ref=s.ref;checked=s.checked
HOLDS={76:'Inventories75.9.166 and75.9.167 have identical titles,23x14.8cm dimensions,medium and subject labels. Distinct inventories alone do not resolve whether these are separate sheets,faces or duplicate notices; hold both pending image/object comparison.',77:'Same unresolved physical identity as75.9.166; do not add a second crowd drawing from duplicated descriptive fields.'}
NOTES={
1:'MontparnasseIV75.9.60,34.1x41.2cm,1930 bar scene; source inscriptionIV differs from existingII75.9.61 Salon1929 andV/III75.9.62 art-dealer scene. One original watercolour/ink drawing, not another edition of those scenes.',
2:'49.8x34.3cm view of the Maison-forte du Noyer75.9.58; separate from smaller21.1x15.5cm Conflans church tower75.9.130. Source1925–1930 retained.',
3:'MontparnasseI75.9.72,39.2x28.3cm; inscriptionI,orientation and dimensions distinguish it fromIV75.9.60,II75.9.61 andV/III75.9.62.',
4:'Original cartoon75.9.76 with title variants and LeRire11October1930 publication. The printed reproduction is not another physical record.',
5:'75.9.77 inscription says vers1931; preserve circa qualification although the catalogue year field says1931.',
7:'Signed JeanMoulin17 drawing75.9.57; source explicitly dates1917. No confusion with CharlesMoulin or PieterMolijn.',
9:'75.9.75 original drawing published LeRire4January1930. Foujita is mentioned in its caption, not its creator; different from held PortraitOfFoujita sketchbook leaf75.9.99.',
20:'75.9.103 is one sheet with two figure studies on opposite faces; retain full recto/verso title and one record.',
23:'75.9.106 is one drawn sheet reused from an Aix-les-Bains concert programme. Six portraits count once; source1924–1930 retained without inventing a day.',
34:'75.9.117 is a27.4x22.2cm series of masks on one printed subscription form; distinct from small7.9x10.6cm single mask75.9.118 and mountain landscape75.9.121.',
35:'75.9.118 is one7.9x10.6cm mask drawing; not the27.4x22.2cm series75.9.117.',
38:'75.9.121 depicts mountains, on a separate subscription-form sheet with its own inventory; matching standard paper size does not make it the mask-series75.9.117.',
43:'75.9.127 depicts a picador and arena staff behind a barrier; separately inventoried from75.9.128 and smaller75.9.131. Current and former subject labels preserved.',
44:'75.9.128 is separately inventoried charcoal drawing of two men; source does not identify it as a verso of75.9.127 despite equal dimensions. After1920 remains open.',
46:'75.9.130 is a21.1x15.5cm church-tower view on a prefecture form; distinct from49.8x34.3cm roofs view75.9.58.',
47:'75.9.131 is31.8x33.6cm arena drawing, distinct from47.8x32.1cm75.9.127/128.',
65:'75.9.150 has ten female heads and another verso sketch; one reused identity-form sheet. Different recorded composition from75.9.151/152 despite standard form dimensions.',
66:'75.9.151 is one sheet with31female-head studies and3male heads; title preserves older20-study count. Do not create34artwork records. Different composition from75.9.150/152.',
67:'75.9.152 depicts women and three cancan dancers on an identity form; different subject from head-study forms75.9.150/151.',
69:'75.9.156 is one13.5x10.9cm sheet with seven recto and eight verso heads, not15objects.',
70:'75.9.159 is a15.2x11.4cm pencil café interior; not CharlesMoulin IntérieurFlamand121x96cm oilpainting.',
72:'75.9.161 is one folded printed refugee document with drawing studies. Title retains revised35-study count; no per-head,per-face or per-panel multiplication. Its2025Arles exhibition is historical, not current display.',
73:'75.9.162 has different counts of caricatures on the two faces; one physical sheet, older catalogue count retained in title.',
75:'75.9.164 one sheet of19caricatures; old18count retained as title evidence. No multiplication.',
85:'75.9.175 retains the questioned1925lower endpoint and1939upper endpoint as an approximate range; no precise1925date invented.',
93:'75.9.186 artwork creation1932, not1900from the depicted costumes. Recto figures and verso draft captions remain one physical sheet.',
96:'75.9.191 is a14.8x7.3cm dancer drawing; distinct from13.1x5.7cm skirt-and-legs study75.9.192 and explicitly rejoined fragments75.9.189/190 held separately.',
97:'75.9.192 is a13.1x5.7cm skirt-and-legs study with its own inventory; source does not identify it as a part of75.9.191. Explicitly rejoined75.9.189/190 remain held.',
99:'75.9.195 is one48.7x25.3cm sheet with café figures on recto and figures on verso; no separate verso addition.'}
def build():
 x=m.load(RUN/'production-identity-001.json.gz');assert x['rows']==i.f.rows()[0];out=[]
 for row,c in zip(x['rows'],x['comparisons']):
  n=row['number'];d=copy.deepcopy(row);d['comparison']=c;f=d['facts'];assert not c['source_hits']
  if n in HOLDS:d.update(state='held_editorial_review',basis=HOLDS[n]);out.append(d);continue
  assert f['creator_label']=='Moulin Jean (1899-1943)' and f['work_type']=='drawing'
  basis=NOTES.get(n,'Distinct original drawing with its own75.9inventory,subject,medium and dimensions. Full museum scope and relevant creator pool compared; no same physical object found. Multiple figures and recto/verso faces count as one object.')
  if n==5:
   assert f['first']==f['last']==1931 and 'vers 1931' in f['source_fields']['Precisions_inscriptions'];f['date_precision']='circa';f['date_display']='vers 1931'
  if f['date_precision']=='after':f['description_md']='The museum catalogue dates this drawing only as '+f['date_display']+'. No upper year has been inferred.'
  if n==72:f['description_md']='Studies on one folded printed refugee document, with further studies on the reverse.'
  if n==85:f['description_md']='The catalogue gives a creation range of 1925 to 1939, with the 1925 endpoint questioned.'
  d.update(state='approved_review_only_addition',basis=basis,confidence=.94,limitation='Documented museum holding, not current display, ownership or custody. Source creator label,qualified dates and unknown upper bounds retained. One physical sheet per record; no sketchbook or joined-fragment multiplication. No publication,images or artist-authority links. Confidence is editorial,not calibrated.');out.append(d)
 assert len(out)==70 and sum(v['state']=='approved_review_only_addition' for v in out)==68;return out
if __name__=='__main__':
 ds=build();deps=[RUN/v for v in ['candidate-facts-001.json.gz','production-identity-001.json.gz','production-identity-citations-001.json.gz','production-initial-scope-001.json.gz','joconde-selected-001.json.gz']]+[m.RUN/'native/beziers-20261009/native-context-001.json.gz'];m.save(RUN/'editorial-reviewed-001.json.gz',dict(at=m.now(),decisions=ds,dependencies=[ref(v) for v in deps],reviewer_reference=ref(Path(__file__).resolve()),policy='68 selected original drawings and two unresolved crowd notices held;30 additional source/group holds tracked separately.'))
 print(json.dumps(dict(states=dict(collections.Counter(v['state'] for v in ds)),dates=dict(collections.Counter(v['facts']['date_precision'] for v in ds if v['state']=='approved_review_only_addition')),eligible=sum(v['facts']['last'] is not None and v['facts']['last']<=1970 for v in ds if v['state']=='approved_review_only_addition'))),flush=True)
