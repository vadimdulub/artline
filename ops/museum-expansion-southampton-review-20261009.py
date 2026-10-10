"""Explicit physical-object dispositions of 80 selected Southampton highlights."""
import collections,gzip,hashlib,importlib.util,json
from pathlib import Path
def module(name,file):
 z=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(z);z.loader.exec_module(v);return v
f=module('f','museum-expansion-southampton-facts-v2-20261009.py');ctx=module('ctx','museum-expansion-southampton-context-v4-20261009.py');m=f.m;RUN=f.RUN;ref=f.ref;checked=f.checked;IID=f.IID
LINKS={1:'ec91a002-096e-5e8f-8daa-671103cf9190',5:'f27c3140-379d-5ee5-a6db-b4351c65fa90',12:'252b9a5e-ec0a-5286-ace7-7e182bdb1017',16:'f50eacc5-2857-540c-95df-a7c966db4d98',38:'fc08cb95-7d01-55d9-9212-a136c0645eb1',62:'2dfb55ef-9b8f-5906-aca2-8a3f7dc7b918'}
EXISTING={17:'7512f465-4464-5f47-8300-54772857f85e',19:'a585b3a5-7762-5cfc-8d53-ee1c772bed90',24:'32a6a8dc-8085-5e09-9a07-50fb8e55620d',26:'e995968a-7faa-58ad-b886-e8966ca7bc9e'}
HOLDS={4:'Blank creation field and conflicting chronology: purchased1946 versus narrative Portland works1948–55. Neither is a safe creation date.',10:'Native date blank;1936 wreck sketches do not establish painting creation.',20:'Prior held Bigge1930 object, inventory28/2005; unresolved1933 CSV record and prior width conflict. Neither add nor relink.',23:'Native date blank;1936 found-object story dates a precursor, not this object.',25:'Explicit1981 outside pre1971 artwork scope.',32:'Prior held Wells inventory56/2006 conflicts with native2006/57. Same-title1955 work unresolved; no duplicate addition.',39:'Native date blank. Undated relative age about650 years is not a supported creation date. Altarpiece ensemble not split into inferred panels.',41:'Native date blank;1562 appointment and other Summer versions1563/1573 do not establish this object date.',44:'1513 engraving design is not a documented date of this physical impression; edition unresolved.',47:'Native date blank; gouache version cannot inherit a print or watercolour date.',49:'Native date blank;1820 commission does not date the impressions. Aggregate set not expanded into invented individual works.',54:'Native date blank;1858 travel/biography is not creation.',56:'Native date blank; general1850s stylistic discussion is not object date. Preserve literal creator Camile spelling pending identity research.',61:'Native date blank; related late1860s/early1870s versions do not date this physical version.',78:'Native date blank; smaller340x572mm work differs from Tate570x762mm Clarence Gardens1912. Tate date not transferred.'}
APPROVE={2,3,6,7,8,9,11,13,14,15,18,21,22,27,28,29,30,31,33,34,35,36,37,40,42,43,45,46,48,50,51,52,53,55,57,58,59,60,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,79,80}
NOTES={
1:'Secure creator and distinctive Red Landscape1942 title/date match to retained WikiArt source; Black Landscape1939–40 is different. Native inventory1369 supplies direct museum collection credit. Preserve existing WikiArt metadata.',
2:'Mere Poussepin1920 is86.7x51.2cm, inventory1456. Retained WikiArt Barber Mother Marie Poussepin c1915–20 is60.5x45.3cm, a different version. Unrelated inventory1456 at another museum is not identity.',
3:'Rotherhithe from Wapping1946 is91.5x122cm, oil on board; IWM Wapping1941,ART17174 is25x40.8cm. Separate painting, also corroborated by PDF oil on plywood and1950 gift.',
5:'Retained WikiArt Canal Bridge1949 matches exact creator,title,date. Native71x91.2cm and PDF same dimensions,signed dated1949,purchased1951 corroborate Southampton holding; other inventories1397 are unrelated makers.',
6:'PDF exact Floating Bridge1956 title,maker,signed date,50.8x76.3cm and acquisition1956 resolve blank native date. Native describes another floating-bridge version; only inventory1483 is selected.',
7:'1913 double portrait, inventory1968/6,508x459mm. Native credit and PDF both say purchased1954; accession components are not acquisition dates. Source explains sitters unrelated; do not invent kinship.',
11:'1947 Resurrection: The Raising of Jairus Daughter is one source-catalogued triptych, inventory1383,768x1890mm. Count one ensemble. Other inventory1383 works have different makers and subjects.',
12:'Retained WikiArt Portrait of Patricia Preece1933 matches native maker and distinctive sitter/title/date; PDF83.9x73.6cm and1954 acquisition corroborate inventory1444. Other inventory1444 works are unrelated.',
16:'Highly distinctive March7,1937-4(Sandbumptious) title,Grace Pailthorpe and1937 date agree with retained WikiArt record. Native2003/14 provides direct collection evidence. Do not duplicate.',
21:'Tunnard1944 plein-air abstraction is gouache on board507x758mm. Tate Composition1942 is oil on board454x705mm: different physical painting and medium.',
27:'Object Lesson1940 is collage and bodycolour. Work type remains unknown rather than forcing painting; exact material retained. No duplicate found in bounded object scope.',
29:'Native title1940-42(two forms) retained; explicit Date field1942 is source date. Tate1943–45 St Ives406x502mm and MoMA1940–43 gouache24.1x24.8cm differ from native oil canvas910x917mm. Hepworth forms are a different creator.',
30:'1966(greystone),oil board565x439mm, is distinct from Tate1966 Parthenon graphite paper375x486mm and the larger1967/1969 carved panels.',
34:'Zennor1955 gouache473x367mm differs from Tate Zennor Storm1958 oil board1219x1829mm.',
38:'Retained WikiArt Kitchen Still Life1948 exact title,maker,date. Native579x660mm inventory2006/17 supplies museum evidence. William Scott Ochre1958/Winter1956 have different titles/dates; generic Still Life lead is Bernard Scott.',
40:'Native narrative qualifies1520 as around1520; retain circa. Native St Jerome contrasts head against a tree with landscape. Exact ArCo0300097740 Brera history describes the unique chest-beating version and dark ground among three versions. No transfer of Brera title/date/holding; retain native803x607mm and1958/2.',
42:'Explicit native narrative dates whole triptych around1510. One ensemble, no inferred panel count. Rogier van der Weyden Saint Catherine1445 is different creator and object.',
43:'Native creator Sofonisba Anguissola,Date1551,inventory literally SOTAG:3. URL197914-3 is not the accession. Historical Titian attribution remains in source narrative; no false current maker qualification. Other museum inventory3 records are unrelated.',
45:'Native circa1790 Wright view,1051x1285mm. Source acknowledges other versions; none matched in creator/title/inventory scope. Select only1416.',
50:'Native Sisley1867 canvas95.5x122.2cm differs from WikiArt1865 versions50x65 and125x205cm,1866 Bremen45x59.5cm,Met1878 50.2x61cm and exact Joconde000PE013733 Saint Cloud1877 50.5x65.5cm.',
51:'Native Pissarro1870 oil canvas45.8x55.7cm differs from NGA c1872 watercolour19x25.2cm,1879 print, and exact LondonPID0GGD-0001-0000-0000 oil52.7x81.9cm. No related-work dates transferred.',
52:'Native church1880 oil50.5x61cm differs from OrsayRF1973181879 vertical65.5x50.5cm; Met Seine1880 60.3x100.3cm; Thyssen Thaw680(1977.86)1880 60x100cm;1901 Vetheuil versions and1881 garden. Primary Thyssen evidence corrects an earlier research-only mistaken Barnes label.',
53:'Vuillard Manicure1897 is a different subject from The Avenue1899,The Square1910 and La Cheminee1905. Same creator alone is not object identity.',
55:'Native Captain’s Daughter1873 explicitly distinguishes The Last Evening, although2017 PDF includes that confused alias. Alias searched for duplicates only; not imported as alternate title. Preserve723x1048mm,580 and1934 acquisition.',
58:'Native Deux Chiens1891 oil canvas370x397mm,also narrative Deux Chiens Jouant, differs from NGA Two Dogs in a Deserted Street c1894 oil pressed board35.1x27cm and1914 woman holding dog. Exact French-title lead Denon is a different creator. Furniture design is precursor, not another selected artwork.',
59:'Renoir Wilhelm Muhlfeld1910 is a named male sitter, not Marie Murer1877 or Camille Monet c1874. No unresolved same-sitter version hit.',
60:'Launcelot/Lancelot1896 oil painting1385x1698mm is based on earlier tapestry design; do not date by1890 commission or count tapestry as this canvas.',
62:'Retained WikiArt Frank Dicksee Romeo and Juliet1884 exact creator,title,date matches native171x118cm,1006. Thomas Francis Dicksee Juliet1877 is a different maker and work.',
63:'Native Turner1802 title/date and inventory1396. Other inventory1396 pine-road painting has different creator/subject. Creation from explicit Date field, not maritime event.',
64:'Native Martin1812 Sadak76.2x63.5cm,1367. Prior museum leaflet acknowledges two versions; only this smaller source-catalogued canvas selected. No database same-title version found; unrelated inventories1367 excluded.',
65:'Sargent1887 portrait of Cecil/EC Harrison,1728x836mm, differs from Tate Mrs Robert Harrison1886T07693,1578x803mm. Source former title retained in narrative; no incorrect female-sitter reconciliation.',
67:'Native Afterglow in Egypt1854,inventory1280,1854x863mm. Narrative says painting begun1854. No other same-maker version found in bounded database scope. Do not infer completion year from travel or dimensions.',
68:'Visual comparison: Southampton PDF shows frontal seated sitter with clasped hands and door on right; Cleveland1982.125 turns right in three-quarter view with cabinet edge. Different physical paintings. Native1912 versus PDFcirca1912–14 and67x51 versus67x49cm retained explicitly; no Cleveland date/dimensions transferred.',
69:'Native In the Park1911 versus museum PDF1912 dates retained as explicit1911 or1912 uncertainty. Same title,maker,72.5x90cm and1953 acquisition corroborate object; no invented resolution.',
74:'Native View from a Window1909,508x403mm vertical, differs from Tate Cambrian Road1913N03558,559x686mm horizontal.',
76:'Native Mantelpiece1907; PDF Mantlepiece spelling checked as comparison alias. Same painting dimensions76x50.8cm and1932 acquisition; no second record for spelling variant.',
78:HOLDS[78]}
def source_guards():
 for r in m.load(RUN/'comparison-source-context-004.json.gz')['rows']:
  if not r.get('body_reference'):continue
  p=checked(r['body_reference']);raw=gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_bytes();assert hashlib.sha256(raw).hexdigest()==r['raw_sha256']
  if r['format']=='json':assert json.loads(raw)==r['data']
  if r['format']=='wikiart_html':assert ctx.wikiart(raw)==r['parsed']
 img=m.load(RUN/'gilman-identity-image-001.json');assert hashlib.sha256(Path(img['path']).read_bytes()).hexdigest()==img['sha256'];pdf=m.load(RUN/'exhibition-catalogue-001.json');checked(pdf['pdf_reference']);checked(pdf['receipt_reference'])
def build():
 rows=m.load(RUN/'native-candidates-002.json.gz')['rows'];assert rows==f.rows();source_guards();ident=m.load(RUN/'native-identity-002.json.gz');assert ident['rows']==rows and not ident['within_batch'];cs={v['number']:v for v in ident['comparisons']};groups=[set(LINKS),set(EXISTING),set(HOLDS),APPROVE];assert sum(map(len,groups))==80 and set.union(*groups)==set(range(1,81));out=[]
 for row in rows:
  n=row['number'];v=row['facts'];c=cs[n];state='approved_review_only_addition' if n in APPROVE else 'approved_existing_holding' if n in LINKS else 'already_catalogued' if n in EXISTING else 'editorial_hold';basis=NOTES.get(n)
  if n in APPROVE|set(LINKS):assert row['state']=='candidate' and not c['source_hits'] and 100<=v['first']<=v['last']<=1970
  if n in LINKS:
   h=next(h for h in c['hits'] if h['id']==LINKS[n]);assert h['current_institution_id'] is None;proof=[r for r in m.load(RUN/'comparison-source-context-004.json.gz')['rows'] if r['artwork_id']==h['id'] and r.get('format')=='wikiart_html'];assert proof
  if n in EXISTING:assert next(h for h in c['hits'] if h['id']==EXISTING[n])['current_institution_id']==IID;basis='Exact native work already linked in wave87; preserve existing record and do not count a second object.'
  if n in HOLDS:basis=HOLDS[n]
  if not basis:
   assert n in APPROVE;basis='Reviewed native '+v['creator_label']+' / '+v['title']+' / '+v['date_display']+', '+v['inventory']+'. Explicit creation date and acquisition credit. Compared full museum and bounded creator/title/inventory/source scope; no same physical work identified. Other-maker title or inventory similarities are not duplicates.'
  out.append(dict(number=n,source_id=row['source_id'],institution_id=IID,facts=v,source_reference=row['source_reference'],comparison=c,state=state,confidence=.85 if n in LINKS else .95 if n in APPROVE else None,basis=basis,existing_artwork_id=LINKS.get(n) or EXISTING.get(n),retrieved_at=row['retrieved_at'],limitation='Editorial confidence,not calibrated probability. Collection evidence does not establish current display,custody or legal ownership. Native labels,qualified dates and source disagreements remain explicit. Existing artwork metadata,images,artist links and statuses are preserved. No new media attachment.'))
 return out
def main():
 dest=RUN/'editorial-reviewed-001.json.gz';assert not dest.exists();decisions=build();deps=['native-candidates-002.json.gz','native-identity-002.json.gz','identity-citations-002.json.gz','comparison-source-context-004.json.gz','exhibition-catalogue-001.json','gilman-identity-image-001.json','primary-version-web-001.json','thyssen-comparison-001.json','version-search-002.json'];m.save(dest,dict(at=m.now(),decisions=decisions,reviewer_reference=ref(Path(__file__).resolve()),dependencies=[ref(RUN/x) for x in deps],policy='Explicitly selected55 new review objects and6 existing-object holdings;4 prior objects and15 unresolved/out-of-scope leads excluded. Native accession spelling preserved. Holding-only matches do not authorize metadata enrichment.'))
 print(json.dumps(dict(states=dict(collections.Counter(d['state'] for d in decisions)))),flush=True)
if __name__=='__main__':main()
