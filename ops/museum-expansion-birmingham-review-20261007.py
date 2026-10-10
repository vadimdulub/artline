#!/usr/bin/env python3
"""Explicit review of bounded native Birmingham objects; no database writes."""
import importlib.util,collections
from pathlib import Path
s=importlib.util.spec_from_file_location('i',Path(__file__).with_name('museum-expansion-birmingham-identity-20261007.py'));i=importlib.util.module_from_spec(s);s.loader.exec_module(i);w=i.w;m=w.m;RUN=w.RUN
HOLDS={
'george-iii':'Existing63138f48-6eb4-5b71-81e6-6f472a47a17d shares title, creator and1959.116 accession. Preserve pending existing record; do not duplicate.',
'moroccan-scene':'Existingf0a50066-8744-5ff8-bcd7-0018ea9a7b53 shares Tanner identity and1971.30 accession. Source About1912 versus imported1912 preserved; no duplicate or date rewrite.',
'a-race-meeting-at-jacksonville-alabama':'Existing9836d94f-ffac-5553-b8ed-d7500cfa7309 shares Hedges identity and1985.278 accession. Retain existing pending record.',
'the-gardener':'Existing56605203-6736-564c-b20c-902ca317a69a shares Parrish title,1906 and1981.27 accession. No duplicate.',
'sierra-storm':'Existing9bb6066d-ed85-5d63-a52f-00b02870793d shares Keith title and1993.36 accession. Keep existing pending record and source About1880 versus imported1880.',
'the-judgment-of-paris':'Existing36b02aef-c38c-5526-b82d-3d6f5fbdb99c comes from WikiArt1588; retained WikiArt page explicitly names Birmingham Alabama. Native1590 copper27.9x37.8cm is a probable same-work identity despite date discrepancy. Reconcile existing object separately; source precedence does not justify a duplicate. Larger French canvas versions are separate leads.',
'madonna-and-christ-child-2':'Existing2985b8f1-291f-4ce1-9811-307248b44ffd Madonna and Child1492-1498 attributed to Agnolo has insufficient version detail. Native attributed workshop of Agnolo and Donnino1490s and former Graffione attribution remain literal. Resolve before insertion.',
'hercules-freeing-prometheus':'Existing0e552818-3457-4f9d-806d-a3d0e73b1f42 and30f9e690-50cd-451c-bb9c-14169c215ea0 Hercule delivrant Promethee1703 by Bertin require reconciliation. Native60x49.4cm versus62.5x52cm is too close to exclude measurement differences.',
'les-baigneuses-female-bathers-in-a-landscape':'Pater bathers variants include f4acc876-d4b8-4ee8-88bb-2faa54764218,0f73afbf-4e47-48af-93b5-916c7c4151ab and26b3cc56-07c5-4b68-9ad2-5d45066ef10b. Overlapping dates and generic translated titles need physical-version resolution.',
'the-cascade-at-tivoli':'Vernet cascade variants include509d8316-00ac-49c2-aa90-cb824cecb263 with insufficient physical detail. Date discrepancy1740-48 versusc1750 alone does not exclude identity.',
'portrait-of-a-gentleman-self-portrait':'Perronneau oil52.1x41.3cm may overlap Tours821d17bf-26d0-4cd4-b091-0bdd4b8a19f6 Autoportrait54x45.5cm. NGA1757 pastel is distinct, but unresolved oil identity remains; preserve self-portrait question.',
'saint-augustine':'Sano di Pietro sourcec1470 panel118.1x41cm versus aca7e651-c0dc-4041-bef5-8f51c187f823 Sant Agostino ca1441-1460 lacks enough version detail. ArCo page unavailable; hold without inventing evidence.',
'sarah-rowlls-chad':'Native title names Sarah but narrative/provenance uses Sir George as sitter and describes Sarah as companion. Retain source inconsistency for portrait-level review.',
'portrait-of-a-lady':'Native Cornelis Jonson1649 panel is physically distinct from Met and Tate canvases, but exact-title0eabd26b-5df3-4675-a1dc-b062e8017d7a under alias Cornelius Johnson1655 lacks physical detail. Date discrepancy alone cannot exclude same object; resolve alias/version first.'}
SPECIAL={
'still-life-of-flowers-fruit-shells-and-insects':'Balthasar nativec1629 AFI.3.2002 is horizontal43.5x74.3cm. Retained official National Gallery page identifies existingcb342aaa-a512-42b7-8608-428cb7160ef8 as NG6593, vertical47x36.8cm, about1630, with separate Percy Meyer provenance and2003 allocation. Dimensions, orientation, title and provenance distinguish the objects, not date alone.',
'last-judgment':'Museum explicitly distinguishes nearly identical Tokyo P.1999-0003. Native copper71.1x48.3cm,1961.114 is the Birmingham object. Potential shared early provenance before1803 remains uncertain; later provenance applies to this object.',
'saint-bartholomew':'One surviving separately accessioned Perugino altarpiece panel. Preserve narrative of Napoleonic removal and corrected former Louvre provenance. Do not add the reconstructed altarpiece or other panels.',
'seven-virtues':'One surviving painted cassone panel. The pendant Seven Liberal Arts is discussed but is not an additional record. Pesellino and Workshop attribution remains qualified.',
'gilles-du-faing':'Current attribution is Unknown artist, Flemish. Native Artist field preserves Formerly attributed to Otto Van Veen. Search former attribution for duplicates; do not assign it as current creator.',
'judith':'Possibly School of Guido Reni remains a qualified object label; no definite Reni artist link.',
'madonna-and-christ-child-with-infant-saint-john-the-baptist-and-three-angels':'Current Workshop of Domenico Ghirlandaio preserved; former Mainardi attribution remains evidence and identity lead, not a current artist link.',
'copy-of-lansdowne-portrait-of-george-washington-by-gilbert-stuart':'Theodore Ramos About1965 copy is dated as its own physical object, distinct from Stuart original. Copy qualifier remains in title.',
'adoration-of-the-magi':'Vignon1624/1626 oil canvas81.9x99.1cm differs from1619 Met/Chicago etchings and large French1630 composition. Both explicit slash-year endpoints retained without asserting uninterrupted creation.',
'still-life-with-onions':'Vollon oil24.1x30.5cm differs from Met Still Life with Cheese84.8x89.9cm. About1875/80 is the literal source date.',
'paysage-montagneux-pastoral-landscape':'Pillement1770s oil14.6x18.9cm differs from1792 graphite/wash work and French Paysage au berger24.3x39.7cm.',
'la-vielle-tour-pastoral-landscape':'Pillement1789 painting,1991.259.1, is distinct from1792 graphite-and-wash Landscape; keep native title spelling.',
'the-barricade':'Bellows1918 painting differs from existing First Stone, Second Stone and No.2 lithographs. Physical medium/version governs, not subject alone.',
'tragedy-at-sea':'Source traces Butler1919 gift and1929 deaccession/exchange, then Ingalls descent and1975 Birmingham gift. Preserve full history; historical Butler deaccession is not Birmingham disposal.',
'rainbow-recto-burst-verso':'Two painted sides form one object1972.23 created1970. Count once; retain literal copyright credit.',
'ornette':'Source1960-1961 creation is distinct from2002.129 accession. Copyright suffix retained in credit and excluded from accession parsing.',
'margaret-george-mcglathery-died-about-1830':'About1817 is source creation; sitter death1830 in title is not creation.',
'the-pure-land-of-amitabha-front-the-miracles-of-wen-shu-manjusri-back':'One combined two-panel object1987.34.1-.2, with front/back subjects, source Ming About1450. Count once; unidentified temple origin remains unknown.',
'album-of-bird-and-flower-paintings-10-leaves':'One combined album1991.752.1-.10; do not invent ten separately catalogued artworks. Manner of Hua Yan qualification and whole18th/19th-century envelope retained.',
'palden-lhamo-remati-with-retinue':'Tibet cultural label and title question mark retained. The question mark is not a useful exact-title search alias. No invented artist identity.',
'landscape':'Qing dynasty bounds are context; explicit1882 suffix is creation. Li Ruwei biography is separate.',
'view-of-the-grand-canal':'Museum identifies view toward Palazzo Vendramin-Calergi and Deposito del Megio,1961.121 Kress gift. Existing Women s Regaton the Grand Canal is a differently specified event view; shared canal subject alone is not identity.',
'le-village-deragny-the-village-of-eragny':'Specific1885 village painting,1979.353, with catalogue raisonne790 and retained acquisition history; existing sunrise, snow and hay-harvest subjects at Eragny are separate named compositions.',
'nativity':'Bicci di Lorenzo tempera panel17.5x32.4cm differs from anonymous Byzantine museum Nativity accessionBXM02021,52.5x40.5cm, and Lorenzo Monaco works. Shared forename or subject does not identify the same physical painting.'}
def main():
 rows=m.load(RUN/'native-candidates-002.json.gz')['rows'];cm={r['source_id']:r for r in m.load(RUN/'native-comparisons-002.json.gz')['records']};fm={r['source_id']:r for r in m.load(RUN/'native-filtered-comparisons-002.json.gz')['records']};decisions=[];queue=[]
 for row in rows:
  sid=row['source_id'];f=row['facts'];x,p=w.checked_record(m.ROOT/row['source_reference']['path']);assert f==w.facts(x,p)
  if row['state']!='candidate':queue.append(dict(**row,review_state='source_hold'));continue
  cmp=cm[sid]
  if sid in HOLDS:queue.append(dict(**row,comparison=cmp,filtered_comparison=fm[sid],review_state='editorial_hold',editorial_reason=HOLDS[sid]));continue
  assert not cmp['source_hits'] and not cmp['native_url_hits'] and not [v for v in cmp['inventory_hits'] if v['relevant']]
  basis=f"Native Birmingham Alabama index and object page agree on {f['title']}, {f['creator_label']}, {f['date_display']} and accession {f['inventory']}; WordPress object {f['native_object_id']} is a separate identifier. Retained creator/alias/former-attribution, title, accession and native-URL comparisons reviewed. "
  basis+=SPECIAL.get(sid,'Other named subjects or unrelated creators in the saved comparisons do not establish same-work identity. Source physical object, literal qualified attribution and collection credit retained.')
  if 'tale-of-genji' in sid:basis+=' This is a separately catalogued and accessioned leaf; preserve its distinct chapter and accession, without adding a parent album.'
  if f['provenance']:basis+=' Full provenance retained, including uncertainties, former institutions and historical loans; collection credit is not a legal-title conclusion.'
  basis+=' Literal collection credit: '+f['credit_line']
  limitation='Editorial confidence0.90 is not a calibrated probability. Museum catalogue establishes documented collection connection only; no current display, physical custody or legal title claim. No image permission inferred or image fetched. Preserve source wording, unknowns and research status.'
  decisions.append(dict(source_id=sid,state='approved_review_only_addition',confidence=.9,basis=basis,limitation=limitation,facts=f,index=row['index'],source_reference=row['source_reference'],comparison=cmp,filtered_comparison=fm[sid]))
 assert len(decisions)==134 and len(queue)==46 and len({r['facts']['inventory'] for r in decisions})==134
 m.save(RUN/'native-editorial-reviewed-001.json.gz',dict(at=m.now(),decisions=decisions,supplements=[w.ref(RUN/'web-discovery-002.json.gz'),w.ref(RUN/'native-filtered-comparisons-002.json.gz')],candidate_reference=w.ref(RUN/'native-candidates-002.json.gz'),comparison_reference=w.ref(RUN/'native-comparisons-002.json.gz')))
 m.save(RUN/'native-followup-queue-001.json.gz',dict(at=m.now(),rows=queue,counts=dict(collections.Counter(r['review_state'] for r in queue)),policy='Retained32source holds and14identity/source-inconsistency holds; no new records or altered holdings from this queue. Resolve existing records separately.'))
 print('Approved',len(decisions),'Follow-up',len(queue),flush=True)
if __name__=='__main__':main()
