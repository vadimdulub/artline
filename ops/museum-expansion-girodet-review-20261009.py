"""Individual Girodet decisions: distinct physical objects and source uncertainty."""
import collections,copy,importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('i',Path(__file__).with_name('museum-expansion-girodet-identity-20261009.py'));i=importlib.util.module_from_spec(z);z.loader.exec_module(i);s=i.f.s;m=i.m;RUN=i.RUN;ref=s.ref;checked=s.checked
APPROVED={7,9,13,21,23,24,25,27,28,31,32,33,38,40,41,42,45,46,48,54,78,85,86,88,89,90,91,92,93,95,96,99,100,101,102,103,104,105,106,108,111,113,121,125,126,127,131,133,139,140}
HOLDS={58:'Two distinct Janssens pendants 874.62 and874.63 share this title; existing unlinked064e06fb-64e5-4823-acab-1a237f8467ff has no distinguishing inventory/source. Hold both to prevent duplication or arbitrary choice.',59:'Same unresolved pre-existing Janssens record as candidate58. Distinct dimensions confirm two source objects, but the old record cannot yet be assigned to one.',132:'Museum overview dates original full-size plaster1842; latestJoconde947.81 dates1844. Hold source/date reconciliation; the separately inventoried small1842study is not this object.',167:'Anonymous portrait: source material says oil on canvas but dimensions describe paper and cardboard. Hold physical support/type reconciliation without changing source data.'}
NOTES={
7:'Oil study for Father Aubry in the Funeral of Atala, inventory969.10; not the finished composition or prints after it. Unknown creation retained; purchase under usufruct retained as source legal evidence.',
9:'Specific oil-on-canvas oriental head, inventory987.1,53.2x45cm after restoration; distinct from Portrait of Mustapha988.28 and Un Indien988.2. No inferred year.',
13:'Small painted sketch988.26 for the eighth composition of Enlèvement d’Europe; not a finished literary illustration or another medium.',
23:'One separately inventoried Eneid VII drawing971.10; related composition971.11 and preparations971.12 are different sheets, not extra faces of this sheet.',
24:'One Eneid VII drawing971.11, separately mounted and inventoried from971.10 and971.12. Other museum71.11 is an unrelatedJordaenspainting; inventories are institution-scoped.',
25:'One separately inventoried Eneid VII drawing971.12 with its own mounting measurements; no count multiplier.',
27:'Separate22.5x18.5cm Ossian drawing971.14; not Fingal mourningMalvina atMet2006.412 or otherOssiancompositions.',
28:'Separate21.2x17.8cm Ossian drawing971.15; not the other characters/compositions in the series.',
31:'Small7.7x9.2cm drawing971.19 ofFingalgivingOssianthe spear, distinct from mourningMalvina andOssianreceivingFrenchheroes.',
32:'Specific18.8x25.9cm drawing971.20 ofMalvinaarriving atFingalpalace, notMet2006.412mourning her body.',
33:'1806mother-and-child study982.9,59.7x44.4cm; distinct from local firstthought989.12 andDijonD.2792,c1795,25.7x45.8cm, and finished flood paintings.',
38:'Presumed sitter qualification retained. Source points to related counterproof866.1.1.1; inventory982.16 is the selected1814drawing, not that separately numbered object.',
41:'Counterproof992.2.1 of theTomMassédrawing; source notes reversed inscription andBertin-Devauxoriginal. Retain counterproof identity, do not substitute original.',
45:'Preparatory drawing007.3.1,56.2x43.4cm, for a murderer in the1788DeathofTatius; source locates finished painting inAngers, not this sheet.',
46:'One1793LadyHamiltondrawing008.1.1. Source describes additional portraits on reverse; keep one physical sheet and original sitter title.',
48:'1783youthful drawing008.5.2,30.4x21.4cm; not1803oilportrait ofDrTrioson988.29 or portraits of youngTrioson/Ribes.',
54:'SaintMichel003.3.1,castcopperalloy signedDuretfecit andfounderE.Quesnel; distinct companionSaintGabriel003.3.2. No cast date inferred.',
78:'Pastel and coloured-pencil983.11, explicit1905–1907 creation. Historical donation underusufruct is retained, without claiming current physical display.',
86:'Single cardboard sheet983.19 with another boat drawing on reverse; source distinguishes related oilpaintings. No additional verso record.',
88:'Charcoal sheet983.21 of dockworkers; the source distinguishes an ink drawing used as a1938exhibitioncover. No substitution between these versions.',
91:'Three head studies on one inventoried sheet983.25, not three artwork records; distinct fromDijonD.5300singlehead.',
92:'Drawing983.26 on reverse of an exhibition-catalogue page; paper carrier is not a second artwork.',
93:'Charcoal/ink sheet983.27 with boat on reverse. CurrentWikiArtPastureinRolleboise1939 depicts a coloured pastoral painting, visually inspected; no merger with this drawing or title/date rewrite.',
95:'Wash/charcoal983.29 depicts female bather; source notes chequered paper. Separate from male bather983.30 and1930Baigneursoilpainting983.7.',
96:'Wash/charcoal983.30 male bather enteringwater; separate from female bather983.29 and other museums multipleBaigneuses.',
99:'Cardboard notebook leaf983.33 has its owninventory; source distinguishes companionboat983.19. PossibleDieppesubject retained.',
101:'Charcoal/ink983.35,1920–1940, notcrayon983.42,c1921. CurrentWikiArt1935BanksOfSeine is explicitlyoil, distinct from this drawing.',
102:'Pencil portrait983.36 ofPaulSignac; source mentions a related1930portrait but does not date this particular sheet1930. Preserve20thcentury range.',
111:'Museum-specific lithographic impression983.46 dated1907–1910, distinct from the painting exhibited1907 and other views ofIssy. No lifetime/state claim.',
113:'1891Charpentierplasterbas-relief983.48, notFrédéricLuce1947paintedportrait or the1892bronze mentioned atMonnaiedeParis.',
121:'54cm plastermaquette874.270,c1842, forFerdinandcenotaph afterArySchefferdrawing. Distinct from217cm fullsize947.81 held for dateconflict.',
125:'Terracottamaquette885.58,1871,45.6cm deep; not the completedPrinceAlbertmarbleatWindsor.',
127:'Large1874marbletarsia947.48,231.5x140.5cm; distinct from1872preparatorydrawing947.51 alreadycatalogued.',
131:'1845signed marble/cementtarsia947.49, preparatoryInvalidestombdecorproject, shownSalon1848; creationdate is1845, not exhibitionyear.',
133:'Plasterbustmedallion989.139,c1852,59.1x53.5cm; notSchwiter1843oilportrait2022.3.1 ofsame sitter.',
139:'Signed41.5x24.5cm marble018.2.1,c1867, acquiredbyGirodet; source relates it toWindsorSolomonborder, not an assignment ofWindsorcompletedmonument.',
140:'PlasterMonodbust2022.4.1 with formerdepositnumberD.008.1.1, donation2022, creationc1856. Exactoldinventoryquery returnsnone. Othermuseum2022.4.1inventories are differentobjects.'}
DESCRIPTIONS={7:'Preparatory oil study for Father Aubry in The Funeral of Atala. Creation date unknown.',41:'Counterproof of Girodet’s portrait drawing of Tom Massé, distinguished from the original in the museum catalogue.',45:'Preparatory drawing for a figure in The Death of Tatius. The finished painting is held in Angers.',46:'One drawing sheet; the catalogue also describes portraits on the reverse.',86:'One cardboard drawing sheet, with a further boat drawing on the reverse.',91:'Three studies of children’s heads on one drawing sheet.',93:'One drawing sheet with a further boat sketch on the reverse.',113:'Plaster bas-relief of Maximilien Luce by Alexandre Charpentier.',121:'Small plaster model for the effigy of Ferdinand d’Orléans, after a drawing by Ary Scheffer.',125:'Terracotta model for Prince Albert’s effigy at Windsor.',127:'Marble tarsia, distinct from the museum’s preparatory drawing of the same subject.',131:'Tarsia made as a project for the decoration of Napoleon’s tomb at Les Invalides.',133:'Plaster bust-medallion of Blanche de Triqueti, distinct from Ludwig August von Schwiter’s painted portrait.'}
def build():
 x=m.load(RUN/'production-identity-001.json.gz');assert x['rows']==i.f.rows()[0];base=m.load(RUN/'production-initial-scope-001.json.gz')['snapshot'];known={v['external_id'] for v in base['identifiers']}|{v['source_record_id'] for v in base['citations']};out=[]
 for row,c in zip(x['rows'],x['comparisons']):
  n=row['number'];d=copy.deepcopy(row);d['comparison']=c
  if n in APPROVED:
   assert not c['source_hits'] and row['source_id'] not in known;d.update(state='approved_review_only_addition',basis=NOTES.get(n,'Individually inventoried artwork with distinct title/subject, medium and source holding. Full relevant creator pool and all museum objects inspected; no same physical object found.'),confidence=.95)
   if n in DESCRIPTIONS:d['facts']['description_md']=DESCRIPTIONS[n]
   if d['facts']['date_precision']=='century' and d['facts']['last']>1970:d['facts']['description_md']=(d['facts'].get('description_md','')+' Joconde dates this work only to the twentieth century. Its creation date remains under review.').strip()
   d['limitation']='Documented museum holding, not current display, physical custody or legal ownership. Preserve literal source dates, unknown dates, broad periods, creator qualifications and historical usufruct wording. No artwork/artist image attachment or publication.'
  elif n in HOLDS:d.update(state='held_editorial_review',basis=HOLDS[n])
  else:assert row['source_id'] in known;d.update(state='already_catalogued',basis='Existing source identity in the production museum snapshot; no additional record or metadata rewrite.')
  out.append(d)
 assert len([d for d in out if d['state']=='approved_review_only_addition'])==50
 return out
if __name__=='__main__':
 ds=build();deps=[RUN/v for v in ['candidate-facts-001.json.gz','production-identity-001.json.gz','production-identity-citations-001.json.gz','production-initial-scope-001.json.gz','comparator-context-001.json.gz','wikiart-comparator-image-001.json','native-discovery-001.json.gz','joconde-current-003.json.gz']];m.save(RUN/'editorial-reviewed-001.json.gz',dict(at=m.now(),decisions=ds,dependencies=[ref(v) for v in deps],reviewer_reference=ref(Path(__file__).resolve()),policy='Full candidate creator pools and catalogue citations reviewed; 50 selected objects. No duplicate reconstruction of Janssenspair, no parent/child multiplication, no inferred creator-lifespan dates.'))
 print(json.dumps(dict(states=dict(collections.Counter(d['state'] for d in ds)),eligible=sum(d['facts']['last'] is not None and d['facts']['last']<=1970 for d in ds if d['state']=='approved_review_only_addition'))))
