"""Selected physical-object decisions; uncertain versions and sparse facts remain queued."""
import collections,copy,gzip,hashlib,importlib.util,json
from pathlib import Path
def module(name,file):
 z=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(z);z.loader.exec_module(v);return v
f=module('f','museum-expansion-harris-box-additions-facts-20261009.py');i=module('i','museum-expansion-harris-box-additions-identity-v2-20261009.py');s=f.s;m=f.m;RUN=f.RUN;ref=s.ref;checked=s.checked
HELD={
15569:'Sunset at Lands End needs composition/version comparison with existing Olsson Sunset Cornish Coast1915. Unknown date is not evidence of a different work.',
15579:'Dorelia portrait needs comparison with Augustus John landscape/fence versions and Gwen John portrait; Met chalk drawing is distinct but does not resolve all paintings.',
15591:'Native Ruysch narrative leaves authorship uncertain and discusses copies. Compare physical work with legacy Vase with Flowers before adding.',
15667:'Likely existing Laura Knight In for Repairs490e630b-e4d8-57af-b37d-8a27338d28b2. WikiArt title/date matches, but lacks inventory/dimensions; finish physical-version comparison before holding link. No duplicate.',
15730:'Family-level Galli Bibiena attribution and generic architecture title need comparison against all eight creator-pool works,including Decorative Drawing,stage designs and vaulted hall. No individual maker chosen.',
15748:'Four designs may be a grouped catalogue item or separate sheets; accession and relationship to other cupola designs need physical-object evidence.',
15751:'Cupola design needs comparison against Yale Conversion of St Paul12826 and Harris four-design group. Do not assume a distinct sheet from title alone.',
100011:'Cottonian Sarto Head of a Woman needs physical comparison with NGA1991.217.5 black-chalk drawing. NGA remains on access hold; no retry.',
100014:'Van Dyck drawing after Rubens needs exact catalogue format/subject and comparison of legacy portrait labels; qualified attribution alone does not resolve versions.',
100015:'Sirani drawing requires comparison with IrelandNGI.2021.67 and Pesaro1100131542. Do not assume the same title refers to different physical works.',
100018:'Green Devon1919 requires composition comparison with V&A Rosemary Devon1915; title/date differences alone insufficient for landscape version identity.',
100025:'Condy Barbican fish-market scene may relate to Yale The Market Place1846; native article has no inventory. Hold unresolved physical identity.',
100026:'Likely existing Cogle Sutton Pool and the Barbican98f175c4-06b4-5b1f-8d3c-000fe6b6dd82. Descriptor title missed similarity cutoff; full creator-pool review caught it. No duplicate or date overwrite.',
100028:'Mrs Hamar/Miss Limeburner article establishes exhibition presence,not an explicit permanent holding. Retain circa1748 and updated sitter title as leads pending collection confirmation.'}
ALREADY={15623:'576470ee-1cc4-57b9-bb90-52a0fa7f7e34',100002:'edc93dd1-f061-54bc-8ae3-5337430c0c6d',100019:'b422c807-9e2f-5c9f-888f-bbea2981fb38'}
NOTES={
1807:'Lewis Beys Garden1865 is not Mark Symons Molly in the Garden1930; different documented subjects and makers.',
1812:'Devis double portrait is a painting; Met officer-and-wife work43975e6e is a preparatory drawing on blue paper. Other Reverend title collisions have different named sitters/makers.',
1814:'Harris watercolour of Kidwelly gatehouse differs from Tate Turner oilcanvas Mountain Scene with Village and Castle. Painting versus watercolour format retained.',
14859:'Gilbert bronze1890s is not Girodet1814 paper/drawing Comedy and Tragedy; edition identity is this museum sculpture purchased1905,not an extra generic cast.',
15575:'Source explicitly distinguishes this independent1640s-influenced work from Snyders Hermitage Fruit Stall. Existing Game Stall and Woodbine Hinchliff1909 Fruit Stall differ in subject/maker. Preserve possible workshop relationship.',
15614:'Goodall Nile flood scene is not John Edward Goodall naval Battle of the Nile after Arnald; subject and maker context differ.',
15681:'Richards wartime church/resting soldiers is not Emmanuel Levy Red Shawl; lexical similarity has no object basis.',
15684:'Ralph William Daish naval engineer pastel is not George Briggs artillery portrait; named sitter and medium context differ.',
15689:'Hennell bomb-damaged Boulogne church differs from Hawthorne St John Baptist1934 and Assisi,Rouen,Vilna buildings; cities and subjects explicit.',
15733:'Reni sketch is not paintings by Caravaggio,Cesari,Guercino,Regnier,Giorgione or Castagno; Flatman miniature/copy and Bosse print remain separate maker/form evidence.',
15736:'Native describes a drawing; Chicago Martin1833 comparator is a mezzotint impression. Danby1825 painting separately selected as915736.',
15744:'Museum explicitly identifies reversed preparatory drawing; existing1746 Lovat etchings are printed impressions,not this drawing.',
15771:'Kauffman drawing P348 and Nollekens P441 are separate source inventory entries,not a double entry for ancient fresco.',
15774:'Nollekens drawing P441 and Kauffman P348 remain separate; ancient Vatican fresco is source subject,not this artwork.',
16791:'Native P1179 and Patti Mayor context identify self-portrait; generic-title matches by other named artists do not establish identity.',
100001:'Girardet Napoleon painting around1890 depicts1815; no existing same-maker/title candidate.',
100005:'Rogers is the print collector holding papers,not Frances Godde or Earl of Bellamont.1777 documented commission retained without assuming exact completion year.',
100006:'Young Frances Reynolds is artist sister,not Frances Godde1767; named sitter identity and companion father context distinguish portrait.',
100008:'Catherine Savery is young girl with dog,lace and coral pacifier,not adult male Comte de Roucy or Christopher Dimpfel; former Laroon attribution explicitly rejected.',
100010:'Morris portrait of music doctor Mrs E.B.Guard is not Samuel Cook Mrs Winsford; source early1900s wording retained without invented endpoints.',
100012:'Cottonian Boucher head study is explicitly a drawing; Cleveland comparator is oilcanvas portrait32.4x25.6cm.',
100013:'Mercier drawing after Watteau is not Watteau original head-and-hands drawing; after relationship retained.',
100020:'Museum Josef Herman reclining worker painting is not Moore sculpture or works by Matisse,Nonell,Mead,Brice,Coughtry,deKooning or Rock.',
100021:'One specifically described watercolour/ink image from naval album; literal ship/submarine title uncertainty retained;not whole album or separate vessel-count records.',
100022:'Daniell1825 storm lighthouse is not Luscombe1865 Russian Fleet; separate subject,artist and source account.',
100023:'Rogers Hooe Lake circa1814 is explicitly acquired for permanent collection1989. Sheep,boats and viewpoint retained;general panorama reference corroborates.',
100024:'Full Smart creator-pool review found no chemical-works subject; Cornish cliffs,St Ives,Ebb Tide and Implacable restoration are distinct named compositions.',
100027:'Ward1933 monumental gouache degree work is not Reynell View of Plymouth Dock; source gives artist,medium and creation year. Title clearly marked descriptive.',
100029:'Museum explicitly identifies its studio copy and distinguishes Tate original. Keep studio attribution and unknown copy date;do not conflate with original circa1788.',
100030:'Acquired2014 youthful1746 self-portrait differs from mature1773/1775 Reynolds self-portraits;underpainted portrait remains same canvas,not second record.',
100031:'One bound1750–1752Italian sketchbook acquired2014;121drawn sides counted as one object. Not1755sitters appointment book.',
915736:'Museum specifically identifies Danby Delivery of Israel1825 as separate painting from Martin drawing. No existing same-maker/title candidate.'}
def verified_raw(cap):
 raw=gzip.decompress((m.ROOT/cap['body_path']).read_bytes());assert cap['receipt']['status']==200 and hashlib.sha256(raw).hexdigest()==cap['receipt']['sha256'];return raw
def corrected(v,n):
 v=copy.deepcopy(v)
 if n in [1809,15675,15689,15696,15777]:
  v['source_taxonomy_inferred_work_type']=v['work_type'];v['work_type']='unknown';v['work_type_editorial_basis']='Works on paper taxonomy alone does not distinguish drawing,watercolour or print; narrative lacks explicit technique for this object.'
 if n==15684:v['medium']='Pastel'
 if n==100005:
  v['source_commission_year']=1777;v.update(first=None,last=None,date_precision='unknown',date_display='commissioned 1777; creation date unconfirmed')
 return v
def build():
 facts=m.load(RUN/'candidate-facts-001.json.gz');rs,errors=f.rows();assert facts['rows']==rs and facts['source_fact_holds']==errors;identity=m.load(RUN/'identity-002.json.gz');assert rs==identity['rows'];comps=i.comparisons(rs,identity['state']);assert comps==identity['comparisons'];ctx=m.load(RUN/'comparison-source-context-002.json.gz')
 for dep in ctx['body_references']:checked(dep)
 out=[]
 for row,c in zip(rs,comps):
  n=row['number'];v=corrected(row['facts'],n);verified_raw(row['source_capture']);assert not c['source_hits'];state='editorial_hold' if n in HELD else 'already_catalogued' if n in ALREADY else 'approved_review_only_addition';note=NOTES.get(n,row['version_note']);date_basis='Explicit source creation date retained with qualification.' if v['first'] is not None else 'Creation date unresolved;selected real collection work remains review-only and is not counted date-eligible. No lifespan/acquisition/publication year used.'
  out.append(dict(number=n,source_id=row['source_id'],institution_id=row['institution_id'],state=state,facts=v,comparison=c,comparison_basis=HELD.get(n,note+' Full institution and bounded creator/title/source/inventory candidates reviewed. Similarity is discovery only; no automatic deduplication or authority match.'),version_note=row['version_note'],hold_reason=HELD.get(n),existing_artwork_id=ALREADY.get(n),confidence=.94 if state=='approved_review_only_addition' else None,confidence_kind='editorial collection/identity assessment,not calibrated probability',basis='Current museum-authored collection narrative identifies this physical work. '+note+' '+date_basis,limitation='Documented collection association only,not current display,custody or legal ownership. Surname-only,qualified and missing creator/date/type fields remain explicit; no artist-authority or image attachment.',retrieved_at=row['retrieved_at'],source_capture=row['source_capture'],source_record_reference=row['source_record_reference'],supplementary_source=row.get('supplementary_source'),inventory_source_reference=row.get('inventory_source_reference'),physical_object_count=1 if state=='approved_review_only_addition' else 0))
 out+=errors;out.sort(key=lambda x:x['number']);assert collections.Counter(x['state'] for x in out)=={'approved_review_only_addition':71,'editorial_hold':14,'already_catalogued':3,'source_fact_hold':8};assert sum(x.get('facts',{}).get('first') is not None for x in out if x['state']=='approved_review_only_addition')==21
 return out
def main():
 out=build();paths={Path(__file__).resolve(),Path(f.__file__),Path(i.__file__),Path(s.__file__)}|{p for p in RUN.rglob('*') if p.is_file()};ctx=m.load(RUN/'comparison-source-context-002.json.gz');paths|={checked(d) for d in ctx['body_references']};m.save(RUN/'editorial-reviewed-001.json.gz',dict(at=m.now(),decisions=out,dependencies=[ref(p) for p in sorted(paths)],reviewer_reference=ref(Path(__file__).resolve()),policy='71selected new review records,21dated/50unknown;49Harris and22Box.3already represented works preserved,14version/holding holds and8source-fact/scope holds. No existing metadata change or holding reconciliation in this wave. Source surnames retained;maker identities need later enrichment. PDF text remains discovery-only after unavailable visuals. All earlier provider holds and museum queues remain.'))
 print(json.dumps(dict(new=71,dated=21,unknown_dates=50,already=3,holds=22,new_by_museum=dict(collections.Counter(x['institution_id'] for x in out if x['state']=='approved_review_only_addition')))),flush=True)
if __name__=='__main__':main()
