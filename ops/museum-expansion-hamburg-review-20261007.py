#!/usr/bin/env python3
"""Explicit object-level Hamburg editorial selection; offline evidence, no DB writes."""
import collections,copy,gzip,hashlib,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('x',Path(__file__).with_name('museum-expansion-hamburg-identity-20261007.py'));x=importlib.util.module_from_spec(s);s.loader.exec_module(x);f=x.f;m=f.m;RUN=f.RUN
# An explicit whitelist. All unlisted candidates remain in the follow-up queue.
APPROVAL_TEXT='''
Q102425731|Schmidt family,130x125cm,inventory300248; distinct from Christa/Wolfi and Woman with Beachball. Medium remains unknown.
Q106489355|Nölken well scene,185x240cm,2742; exact English-title lead is by Hébert, a different creator and period.
Q107539673|Van Mieris escaped-bird subject,1687,21x17cm; no same-object creator or exact-title lead. Inventory and support remain unknown.
Q108718081|Liebermann Jesus in the Temple,149.6x130.8cm,HK-5424; other exact titles are different creators and physical objects.
Q110016333|Ahlborn Palermo/Monte Pellegrino,53x77.6cm,1080; distinguished by named location, artist and physical object.
Q110406866|Runge blue-coat self-portrait,40.3x28.9cm,on oak,2034; separate from his Pauline portraits and Morning compositions.
Q110407115|Runge Pauline in green dress,72x53cm,1006; separate from49.5x38.2cm1810Pauline inventory1013.
Q110407150|Runge1810Pauline,49.5x38.2cm,1013; separate from larger green-dress portrait1006.
Q110627503|Trübner carpenter place at Wesslinger See,45x69cm,1557; no same-object lead in scoped creator works.
Q110763254|Achenbach rocky coast,48.5x63cm,1304; separate physical dimensions and scene from Sicilian coast83x107cm and later storm compositions.
Q110768897|Puteani dancing couple in tavern,1874,24x28cm panel; explicit named scene, creator and dimensions, inventory unknown.
Q110819342|Koch Bernese Oberland waterfall,99x75cm,HK-1046; separate from Serpentara landscape and biblical compositions.
Q110819656|Alma del Banco portrait of Georg Ludwig Wendemuth,70x70cm,1432; named sitter resolves identity.
Q110934782|Anita Rée1930self-portrait,66x60.8cm,HK-2543; exact generic titles with other named creators are not this portrait.
Q110949007|Burgkmair Agony in the Garden1505,119.5x91.5cm panel,HK-394; similarly titled Dürer prints have different creator and medium.
Q110949126|Kandinsky White Point Composition248,1923,HK-5094; separate from CompositionsIV,VIandX. Dimensions remain unknown.
Q110973073|Heilbuth Reader,40.5x32cm,2047; no same-object creator lead.
Q110973302|Heilbuth named Hudtwalcker portrait,119.5x105.5cm,1791; different from his Reader.
Q111033776|Rebell Atrani/Amalfi1817oil on canvas; creator and specifically named view have no same-object lead. Inventory and dimensions remain unknown.
Q111155667|Thoma woodland meadow,45.9x37.1cm panel,1546; distinct from Kronberg landscape and Sunday Peace.
Q111156552|Thoma1871self-portrait,105.5x77.5cm,1544; existing1898/1909prints are different physical objects.
Q111411571|Thoma Kronberg view,78x106cm,1539; named location and inventory separate his other landscapes.
Q111416494|Schirmer path at woodland edge,97x128.5cm,1312; no same-object creator lead.
Q111479587|Klee Revolution des Viaductes1937,60x50cm,cotton,HK-2899; official modern-collection caption19 independently agrees. Cosmic Revolutionary is a different work.
Q111494779|Vollmer Holstein landscape1827,22x30.8cm,1159; named region and physical size distinguish his Sachsenwald/Elbe works; medium unknown.
Q111509919|Vollmer Stangenmühlengrund/Sachsenwald1852,112x151cm; distinct named place and size from other Vollmer landscapes. Inventory unknown.
Q111821566|Thoma Sunday Peace,79.5x107cm,1538; separately inventoried subject from Kronberg1539and woodland meadow1546.
Q112294976|Oppenheim Heinrich Heine portrait1831,43x34cm,1162; named sitter and oil/paper/canvas physical evidence.
Q112913573|Claesz salmon,berkemeyers,fruit and oysters,57x85cm panel,508; specific composition and inventory distinguish generic still-life leads.
Q112913765|Heda1638portrait-format still life,102.5x84.7cm,71; Budapest1637work45x65cm and French1638Ham Lunch43x60cm differ physically; generic incomplete legacy leads retained in comparisons.
Q112913960|Hennekyn still life circa1660,oil/canvas; existing same-creator scope contains portraits of Anna van der Does,Meulenaer and a man, not this subject. Inventory/dimensions unknown.
Q112947488|Hackert Tivoli waterfalls1785,122.5x171cm,731; Terni1776print is a different location and physical medium.
Q112960554|Georg Hinz beer-glass-and-roll still life1665,oil/canvas; separate subject from1666cabinet composition in official caption3. Inventory/dimensions unknown.
Q113600461|Koch Serpentara landscape with herdsmen/cattle,76x103.7cm,1045; separate from Magi scene and Berner waterfall1046.
Q113818622|Habermann self-portrait circa1900,oil/canvas; no same-creator self-portrait identity lead. Inventory/dimensions remain unknown.
Q113915789|Savery woods after a storm circa1630,HK-163; specific subject and inventory; support and dimensions unknown.
Q113964282|Caullery Carnival circa1615,55.3x99cm panel,413; separate from same-creator religious compositions.
Q114027423|Spitzweg Stargazer circa1863,48x27.5cm,HK-1448; different subject and dimensions from Old Man and Hermit.
Q114035772|Spitzweg Old Man on Terrace circa1875,21.1x11.9cm oak,HK-1446; different physical work from Stargazer1448and Hermit1447.
Q114036113|Spitzweg Hermit in Mountains1870–1875,27.5x58.7cm,HK-1447; explicit pre1971range, distinct physical composition.
Q114037299|Cranach Elder Man of Sorrows with Mary/John,circa1540,56.5x76.5cm lime panel,HK-708;1502Crucifixion woodcuts are different medium/subject. Julian source calendar retained.
Q114050212|Gurlitt house on Sorrento beach circa1843,26x36.6cm,HK-1153; oil/paper physical record and named place.
Q114051018|Faber Sorrento gorge1823,31x21.9cm oil/paper,HK-1137; NGA graphite drawing41.9x28.5cm is a different physical object.
Q114051114|Liebermann hotel Louis C.Jacob terrace1902,70x100cm,HK-1597; official caption17 independently agrees.
Q114053246|Beckmann reclining woman by sea1950,46x61cm,HK-200915; Vienna1931Book and Irises72.5x116cm and1947drawings differ.
Q114053439|Beckmann Odysseus/Kalypso1943,HK-2887; catalogue raisonné646 explicitly identifies Hamburg inventory2887and150x115.5cm. Retain Wikidata150x1155cm and official caption50x115.5cm as conflicting evidence.
Q114053582|Feininger Vollersroda Spring1936,100x80cm,HK-200602; named location differs from Gelmeroda series.
Q114054398|Maetzel-Johannsen Two Nudes with Crescent1919,129.2x76.7cm,HK-5748; creator,physical dimensions and specific composition.
Q114064934|Dix Mother and Child1924,75.5x71cm,HK-2831; existing Hamburg Mother and Child is by Paula Modersohn-Becker circa1903. Public museum press caption independently identifies the Dix painting.
Q114065058|Anita Rée Half-nude before Prickly Pear1922–1925,HK-5692; Kulturstiftung identifies66x53.5cm andHamburg; museum press describes2007gift. Preserve Wikidata535cm width as conflicting evidence.
Q114065149|Ernst Beautiful Morning1965,92x73cm,HK-5109; Beautiful Season1925has a different title/date and composition; no same-object lead.
Q114065390|Radziwill Canal with Yellow Bridge1928,80.3x98cm,HK-2601; specific named composition and physical record.
Q114065530|Heckel Two Men at a Table1912,97x120cm painting,HK-2948; Met1913woodcut23.5x26.2cm is a different medium and object.
Q114065608|Grosz John the Woman Slayer1918,86.5x81.2cm,HK-5112; public Hamburg press caption independently identifies this work.
Q114355092|Götzloff View of Naples circa1850,oil/canvas; artist/place/source identity without a same-object lead; inventory/dimensions remain unknown.
Q114805267|Tischbein self-portrait circa1810,54.1x46.3cm; explicit artist and physical record, inventory unknown.
Q115215781|Cornelis van Haarlem Fall of Man1622,87x64cm; Rijksmuseum1592version273x220cm and French1625Adam/Eve44.5x32cm are distinct physical versions.
Q115309387|Magritte Swift Hope1927,49.5x64cm,HK-5156; specific composition and inventory, no same-object lead.
Q115535231|Barthel Beham Vanitas1540,58.5x42cm panel,HK-328; Sebald Beham prints are a different creator and medium.
Q115568494|Beckmann Large Fish Still Life1927,96x140.5cm,HK-2932; separate named composition and physical record.
Q115633284|Kirchner Painter and Model,HK-2940,150.4x100cm; official caption23states1910overworked1926. Preserve both creation and later reworking explicitly.
Q115858838|Beckmann Minna Beckmann-Tube1906,100x60cm,HK-2901; named sitter separates other portraits.
Q116446148|Vollmer self-portrait circa1826–1830,25.5x20.3cm panel,HK-5582; complete explicit source date range retained.
Q116446162|Vollmer Elbe at Blankenese1844,93x139.5cm; named view and dimensions separate otherVollmer scenes; inventory unknown.
Q116446180|Vollmer Kleine Alster before1842,sourcecreation1842,oil/panel; title describes represented scene, not a before-creation bound. Original title/date kept together; inventory/dimensions unknown.
Q116446758|Vollmer Aumühle circa1830,27.5x38.1cm cardboard,1161; named place and physical medium distinguish other landscapes.
Q116753157|Uhde Nursery1889,110.7x138.5cm,1637; separately inventoried from Morning1638.
Q116753297|Uhde Morning1889,91x110cm,1638; different size and subject from Nursery1637.
Q116908783|Liebermann wagon in Katwijk dunes1889,49.5x64.6cm,1588; named scene and physical record.
Q116909011|Liebermann Dutch Lacemaker1881,62.5x47.5cm,1585; separately inventoried subject from net-menders.
Q116909052|Liebermann Gerhart Hauptmann1912,118.5x92cm,1594; Aura Hertwig photograph is a different creator and medium.
Q117460670|Böcklin Roman Landscape with Bridge1863,44.5x35cm,2402; no same-object creator lead.
Q117538994|Hofner Fox and Hare1866,71x98cm,3455; specific animal subject and physical record.
Q117662172|Menzel Frederick the Great and Zieten in Camp1852,27.3x24.5cm gouache/paper; separate from Frederick travelling1850. Inventory unknown.
Q117706328|Jordaens Lamentation1648–1652,207.5x191cm; Cleveland Betrayal225.5x246.3cm differs in subject/physical size. Source complete four-year range retained.
Q117878369|Corinth Leonid Pasternak1923,80x60cm,HK-2941; named sitter distinguishes Otto Eckmann portrait.
Q117881516|Corinth terrace in Klobenstein1910,81x101cm,HK-2766; named view distinguishes other terrace scenes.
Q118047494|Corinth Otto Eckmann1897,110x55cm,HK-1640; named sitter and dimensions distinguish Pasternak portrait.
Q119778013|Osias Beert imperial-crown flowers in glass vase circa1615,74x53cm oak; specific composition/medium and artist, no same-object lead. Inventory unknown.
Q1215843|Runge Rest on Flight into Egypt1805,96.5x129.5cm,1004; separate from Morning compositions and other-creator exact-title objects.
Q123014396|Graff portrait of Karl Ludwig Kaaz1809; named sitter and creator support distinct identity. Inventory,medium and dimensions remain unknown.
Q123130399|Kalckreuth Hamburg mayor Max Predöhl1915,200x151cm,1817; named sitter and physical painting differ from sister Marie print.
Q123307549|Saenredam Saint Mary Church Utrecht1638,HK-412; other named church interiors are StBavo,Haarlem,Assendelft and Buurkerk. Medium/dimensions remain unknown.
Q123510926|Liebermann zoologist Hermann Strebel1905,112x86cm,HK-1593; distinct sitter from Richard Strauss,Wilhelm Bode and Otto Gerstenberg prints.
'''
APPROVED=dict(line.split('|',1) for line in APPROVAL_TEXT.strip().splitlines())
HOLDS={
'Q106646286':'Amalfi mill versus Capuchin Convent lead a13433ed-206e-4340-83d8-522a27fd6018: translated place/version and incomplete physical comparison.',
'Q107363247':'Generic flower/fruit versions include e3493458-9369-42ec-8bf4-9becabbeac56; no source inventory/dimensions to separate.',
'Q110653136':'Dordrecht city-gate versus Shipping Before Dordrecht01c5dd0a-fddb-5e71-9297-effd771fb9cc; incomplete physical identifiers.',
'Q110792226':'Storm at Dutch coast may overlap legacy1840storm version; dates alone do not resolve translated scene.',
'Q111165249':'Cleveland Prater df390e3f-d179-4770-a3c4-0473451ad488 has similar swapped dimensions; resolve physical version.',
'Q114036745':'Cranach Younger Caritas1537versus Elder Caritas/Charity attributions; resolve version and attribution history.',
'Q114065108':'Ernst Grätenblumen versus Fleurs circa1928–29 e03c5e2b-7559-4008-abf4-7ed64d5a0a57; unresolved physical identity.',
'Q114065635':'Wikidata1930–31conflicts with artist1805–1886lifespan confirmed in official Wasmann exhibition page; source also has differing dimensions. Do not silently correct date.',
'Q116313643':'SMK Niels Klim8f6879ab-978b-4f01-839f-2d3518f69790 is41.5x34cm versus42x35.5cm; too close to distinguish without further object evidence.',
'Q116764113':'Annunciation panel,111x138cm; source has no inventory and potential altarpiece/component identity needs confirmation.',
'Q116963188':'Cranach children-blessing versions and unresolved legacy f7c94d3e-c182-5f24-b9cd-7b45e95267f4; no physical measurements.',
'Q118352035':'Fearnley waterfall versus Danish1833Marumfoss scene; translated subject and incomplete existing size need reconciliation.',
'Q118435998':'Existing Master Francke Entombment bd51f1b7-220b-5fe2-8be2-d15bde6f6fd3; resolve panel before addition.',
'Q119566360':'Near-identical Bredael1680–1725flower/fruit pairs,68x51.2/51.4cm; confirm pendant versus duplicate and object-date basis.',
'Q119566362':'Near-identical Bredael1680–1725flower/fruit pairs,68x51.2/51.4cm; confirm pendant versus duplicate and object-date basis.',
'Q1195869':'Runge Morning already represented by d08da529-273f-5130-8f3e-66262f7ad394 and detail72bf197f-3810-5c99-a42b-de353dabd02c; no duplicate addition.',
'Q119718584':'Van Beijeren fish/shellfish version may overlap Liechtenstein generic mussels scene; resolve physical version.',
'Q121547676':'Stumme narrow StChristopher panel121.2x42.2cm; component/altarpiece identity requires review.',
'Q121547698':'Francke Man of Sorrows: establish independently catalogued panel and relationship to altar ensemble before counting.',
'Q121547699':'Existing Francke Adoration f7685095-fe8e-5af4-aad2-ac6fcfca8be7; resolve panel and date discrepancy without duplication.',
'Q121547700':'Existing Francke Martyrdom8baf10f9-1118-5bb2-b495-a6c648108030; resolve panel without duplicate.',
'Q121547701':'Existing Francke Resurrection65584214-3cdb-5234-858c-3815e766fd7e and aa715364-b7b1-5149-b39c-e3768d036d34; duplicate/version reconciliation required.',
'Q121692307':'Avercamp winter landscapes18.2/18.5cm and existing Vienna d84e91bd-d85d-5f2c-a571-a5f7bb378a46; nearly identical sizes and missing inventories require version review.',
'Q121692311':'Avercamp winter landscapes18.2/18.5cm and existing Vienna d84e91bd-d85d-5f2c-a571-a5f7bb378a46; nearly identical sizes and missing inventories require version review.',
'Q123385248':'Degas mirror pastel: translation and multiple toilette compositions need broader version comparison; no inventory/dimensions.',
}
CAPTION_OVERLAPS={17:'Q114051114',18:'Q114053439',19:'Q111479587',23:'Q115633284'}

def checked_reference(ref):
 p=m.ROOT/ref['path'];assert hashlib.sha256(p.read_bytes()).hexdigest()==ref['sha256'];return p

def supplementary():
 pages=m.load(RUN/'supplemental-public-pages-003.json.gz')['pages'];assert len(pages)==4 and not any('error' in p for p in pages)
 for p in pages:
  cap=p['capture'];raw=gzip.decompress((m.ROOT/cap['body_path']).read_bytes());assert hashlib.sha256(raw).hexdigest()==cap['receipt']['sha256'] and cap['receipt']['status']==200
  assert f.d.BeautifulSoup(raw,'html.parser').get_text(' ',strip=True)==p['text']
 assert '150' in pages[0]['text'] and '115,5' in pages[0]['text'] and '2887' in pages[0]['text'] and 'HAMBURG Kunsthalle' in pages[0]['text']
 assert '66 x 53,5 cm' in pages[2]['text'] and '1922–1925' in pages[2]['text']
 assert '1805-1886' in pages[3]['text']
 return pages

def rendered(facts,labels):
 v=copy.deepcopy(facts)
 def role(qs):
  assert not set(qs)-{'P518','P1706'},'Unreviewed physical qualifier'
  vals=[]
  for p,snaks in qs.items():
   for snak in snaks:
    q=snak['datavalue']['value']['id'];assert q in {'Q861259','Q860792','Q107105674'},q
    vals.append(f.label(labels[q]['entity'],('en','mul','de')))
  return ' ('+', '.join(vals)+')' if vals else ''
 v['medium']='; '.join(c['label']+role(c['qualifiers']) for c in v['material_claims']) or None
 parts=[]
 for c in v['dimension_claims']:
  assert c['unit_label'] and c['value'].get('lowerBound') is None and c['value'].get('upperBound') is None
  amount=c['value']['amount'].lstrip('+');assert float(amount)>0
  parts.append(c['label']+': '+amount+' '+c['unit_label']+role(c['qualifiers']))
 v['dimensions_text']='; '.join(parts) or None
 if v['source_id']=='Q114053439':v['dimensions_text']='150 × 115.5 cm';v['dimension_resolution']='Use catalogue raisonné646and Hamburg press caption; retain two conflicting source dimensions in evidence.'
 if v['source_id']=='Q114065058':v['dimensions_text']='66 × 53.5 cm';v['dimension_resolution']='Use Kulturstiftung artwork caption; retain implausible Wikidata535cm width in evidence.'
 if v['source_id']=='Q115633284':v.update(date_display='1910 (überarbeitet 1926)',first=1910,last=1926,date_precision='range',creation_interpretation='Creation1910and documented reworking1926are both preserved; this envelope does not imply continuous production.')
 return v

def build():
 supplementary();candidates=m.load(RUN/'wikidata-candidates-002.json.gz');checked_reference(candidates['parser_reference'])
 labels=f.f.sources('wikidata-creator-capture-001.json.gz')|f.f.sources('wikidata-extra-label-capture-002.json.gz');objects=f.f.sources('wikidata-selected-capture-001.json.gz')|f.f.sources('wikidata-selected-capture-002.json.gz')
 cm={c['source_id']:c for c in m.load(RUN/'identity-comparisons-001.json.gz')['records']};fm={c['source_id']:c for c in m.load(RUN/'identity-focused-comparisons-001.json.gz')['records']};decisions=[];queue=[]
 for row in candidates['rows']:
  sid=row['source_id']
  if row['state']=='source_hold':queue.append(dict(row,review_state='source_hold'));continue
  v=row['facts'];assert f.facts(objects[sid]['entity'],labels)==v;cmp=cm[sid]
  if cmp['source_hits'] or cmp['native_url_hits'] or any(c['relevant'] for c in cmp['inventory_hits']):
   assert sid not in APPROVED
   queue.append(dict(row,review_state='existing_identity_reconciliation',reason='Existing source identifier/native reference/relevant inventory. No duplicate addition.',comparison=cmp));continue
  if sid not in APPROVED:
   reason=HOLDS.get(sid)
   if not reason:
    assert v['last']-v['first']>=20,sid
    reason='Broad source creation range may reflect artist activity/lifespan. Verify object-specific dating and version before eligible addition; original values retained.'
   queue.append(dict(row,review_state='editorial_hold',reason=reason,comparison=cmp,focused_comparison=fm[sid]));continue
  facts=rendered(v,labels)
  basis='Wikidata object '+sid+' has one non-deprecated current collection Q169542, one unqualified creator, explicit pre1971creation and no conflicting owner/location/component claims. Source IDs, museum inventories and creator-scoped/alias/title comparisons retained. '+APPROVED[sid]
  limitation='Editorial museum confidence0.80 is not a calibrated probability. Wikidata is secondary evidence; its unfetched native catalogue URLs are references, not native verification. Museum connection does not establish current display, custody or legal title. Unknowns and original claims/ranks/qualifiers/references retained. No image permission or painter-authority link inferred.'
  decisions.append(dict(source_id=sid,state='approved_review_only_addition',confidence=.8,basis=basis,limitation=limitation,facts=facts,source_facts=v,source_reference=row['source_reference'],source_entity=objects[sid]['entity'],comparison=cmp,focused_comparison=fm[sid],supplement_references=[f.ref(RUN/'supplemental-public-pages-003.json.gz'),f.ref(RUN/'main-site-leads-001.json.gz')]))
 assert set(APPROVED)=={r['source_id'] for r in decisions}
 for row in m.load(RUN/'main-site-leads-001.json.gz')['rows']:
  n=row['lead_number'];reason='Official caption retained for separate object/version and authority review; not counted in this Wikidata selection.'
  if n in CAPTION_OVERLAPS:reason='Same-work corroboration for '+CAPTION_OVERLAPS[n]+'; one object counted once.'
  if n==7:reason='Existing Claude Lorrain Aeneas/Dido d420ed83-7efe-58e0-89a6-1bfa76e42fa2; reconcile without duplicate.'
  if n==13:reason='Whole Grabow altar title paired with80x51cm component-size dimensions; resolve counting unit.'
  if n==14:reason='Existing HK-5161and separate unlinked English-title record; preserve explicit permanent-loan credit.'
  if n==21:reason='Artificial-stone sculpture: cast/version and creator identity review needed; do not classify as painting.'
  queue.append(dict(source_id='caption-%03d'%n,review_state='corroborating_caption' if n in CAPTION_OVERLAPS else 'caption_followup',reason=reason,source=row))
 return decisions,queue

def main():
 decisions,queue=build();m.save(RUN/'editorial-reviewed-001.json.gz',dict(at=m.now(),decisions=decisions,reviewer_reference=f.ref(Path(__file__).resolve()),candidate_reference=f.ref(RUN/'wikidata-candidates-002.json.gz'),policy='Explicit individually assessed secondary-source selection; review status only. Official captions and independent references corroborate selected objects. No museum-native catalogue access bypass.'))
 m.save(RUN/'followup-queue-001.json.gz',dict(at=m.now(),rows=queue,counts=dict(collections.Counter(r['review_state'] for r in queue)),policy='Source holds, existing identities, versions, dates and unselected official captions retained for follow-up. Nothing deleted or published.'))
 print(json.dumps(dict(approved=len(decisions),queued=len(queue),queue_counts=dict(collections.Counter(r['review_state'] for r in queue)),known_inventories=sum(bool(r['facts']['inventory']) for r in decisions))))
if __name__=='__main__':main()
