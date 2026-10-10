"""Final individual two-museum release; preserve deferred five-museum research."""
import collections,copy,importlib.util,json,re
from pathlib import Path
z=importlib.util.spec_from_file_location('s',Path(__file__).with_name('museum-expansion-italy-fourth-release-identity-20261008.py'));s=importlib.util.module_from_spec(z);z.loader.exec_module(s)
i=s.i;f=s.f;m=s.m;RUN=s.RUN;ref=s.ref;checked=s.checked
working=m.load(RUN/'source-editorial-working-002.json');NOTES={int(k):v for k,v in m.load(RUN/'vicenza-editorial-working-001.json')['notes'].items()}
COMPARISONS={
236:'Conca Crucifixion depicts a different event from Finoglio Virgin Queen of Angels.',
237:'Batoni Diana and Endymion: the source distinguishes the Eton drawing. No competing physical identity returned.',
239:'Criscuolo Dormition/Assumption with Michael is a later copy of the Gaeta original. No same-work hit returned.',
240:'Woman carrying an egg basket is a different composition from Spadarino David and Goliath.',
241:'Roman fruit, pumpkin and bird still life: no competing physical identity returned.',
242:'Neri circle still life with artichoke, lettuce and asparagus: no competing identity returned.',
244:'Rivalta kitchen still life: no competing physical identity returned.',
246:'Travi circle landscape: no competing physical identity returned; retain circle qualifier.',
250:'Habert circle carp, cauliflower and peeled lemon differ from Recco fish and mushrooms, de Heem flowers/fruit and Fyt game.',
252:'Melendez boy with basket: no competing physical identity returned.',
254:'Miracle at Soriano, Puglia school,1626–1650,inventory80. Barletta altar provenance is oral source history, not a current holding.',
257:'Dutch-school Venus and Mars surprised by Cupid. Mieris is hypothetical in history; extra Mieris and English-title comparisons returned no same-work conflict. Keep the school attribution.',
258:'Verdier Temptation,1690s. Source explicitly distinguishes another Louvre version. Retain historical attribution qualifier; no competing same-maker identity returned.',
259:'Chrestien Peter freed,1675–1699: source cartiglio and partly obscured signature. No competing same-maker identity returned.',
260:'Champaigne workshop Christ falls,1640–1660,inventory182. Former Le Brun/Bourdon suggestions checked; retain workshop attribution.',
261:'Le Sueur Laurence sketch is distinct from the Boughton finished altarpiece. Preti female martyr depicts a different saint.',
262:'Procne and Philomela,1630–1640,attributed to Artemisia. Historical attribution remains qualified.',
263:'Attributed Regnier Sebastian,1625. No competing physical identity returned.',
265:'Bourdon bacchanal,1634–1637. The Medici Vase is depicted inside this painting, not a second artwork or the vase itself.',
267:'Master of the Announcement to the Shepherds circle reader,1640–1660,inventory70. Source distinguishes a larger Lecce replica. Vivarini Jerome1476, Weyden Magdalene1435, Lawless1861 and Sarkisian1938 differ by period/subject/support.',
268:'Nome Sebastian on copper,1620–1630. No competing physical identity returned.',
271:'Neapolitan Francis,1651–1675,copy after Reni at the Gerolamini. NGI118 Virgin with multiple patrons is a different composition.',
272:'Ottino circle Borromeo during plague,1600–1624,inventory216: bozzetto distinct from the finished church painting.',
274:'Spinelli Mercury and Argus has an independent subject and inventory; not the Pan and Syrinx painting.',
275:'Altobello Presentation, literal1675/1685 date range agrees with structured endpoints; no invented single year.',
276:'Spinelli Pan and Syrinx(?), question mark retained. Independent composition from Mercury and Argus.',
277:'Castello Benedetto Giustiniani portrait:1997 Rome private collection is historical provenance. Current catalogue location is verified Devanna.',
278:'De Lione unidentified mythological/biblical scene. Preserve uncertainty over subject; no invented identification.',
279:'De Bellis Sacrifice of Isaac,1640–1650: no competing physical identity returned.',
280:'Calling of Peter, attributed to Bonzi in source history. Keep this qualification.',
281:'Coppola glory of an unnamed saint,1650–1659. Different composition from Preti martyrdom and D Anna Christ in Glory; saint stays unnamed.',
282:'Rosa circle Mercury and Argus: source distinguishes the Sydney version. Preserve circle attribution.',
283:'Fracanzano Anthony Abbot and Paul with raven differs from De Rosa Anthony of Padua in ecstasy.',
284:'Spanish-school Crucifixion,1600–1649. Preserve unnamed maker; no competing physical identity returned.',
286:'Stomer prophet/evangelist: retain uncertain subject; former Caracciolo, Finoglia and Vitale suggestions checked.',
287:'Attributed Cerano Virgin head,1600–1624. Verified existing Giaquinto1753–1762 and Giordano1692–1702 sources are later works.',
288:'Bizamano workshop Redeemer with Francis and Bernardino,1540s. Different composition from Bari Virgin with Catherine. Preserve workshop attribution and Greek/Venetian tradition.',
290:'Attributed Bathas Virgin without archangels. Source distinguishes Barletta version with archangels; existing799e version has archangels. Giaquinto/Giordano records are later periods.',
291:'Gaulli Borromeo with cross,1675–1699. Helena and Francis cross compositions represent different saints.',
292:'Attributed Tommaso Conca Rest on the Flight,1760–1770. No competing physical identity returned.',
293:'Vouet school Margaret,1630–1640: source calls this a copy of the Hartford original, not a preparatory sketch.',
295:'Iberian Francis,1540–1549. Distinct period from the seventeenth-century Neapolitan copy271.',
296:'Pino school Shepherds,1568–1577. Louvre drawing22474, Cort print and Magi altarpieces are distinct objects. Benefial Crowning depicts another event.',
297:'Farinelli portrait,1740–1760: no competing named-sitter identity returned.',
299:'Attributed El Greco Dominican friar,1567–1577,oil on panel. Distinct from the Longhi copper; qualification retained.',
300:'Flemish Christ with thorns,1626–1650,painted on the back of an engraved copper plate. One physical object, not two records.',
301:'Attributed Bagozzo Venantius,1550–1599. No competing physical identity returned.',
303:'Sweerts Woman at her Toilet,1646–1654. Source distinguishes San Luca version; pinned source dates existing Schiavoni87ec portrait1820–1830.',
304:'Velazquez manner man,1640–1660. Existing Ciseri blue-cravat portrait dates1850–1874 in pinned source. Preserve manner qualification.',
305:'Attributed Corona Ecce Homo,1580–1590. No competing physical identity returned.',
306:'Adriatic saint head,1300–1349,fragment; former Rimini label preserved. Boccioni Milano hit is unrelated.',
307:'Marche Flagellation,1590s,copy after Zuccari. No competing physical identity returned.',
310:'Hercules, Nessus and Deianira,1700–1749,small monochrome panel,inventory217. One composition.',
313:'Winterhalter reclining nude with book,1850–1870,signed with initials. Speranza comparison is a different named maker.',
315:'Attributed Comerio Virgin and Child with Dominic and another saint,1780–1790. No competing physical identity returned.',
318:'Attributed Gericault Red Sea sketch,1815–1824. History death-year1924 typo is not a creation date.',
319:'Jerome,1776–1800,inventory222. Source identifies a signed Tischbein Magdalene pendant, not this same physical work.',
320:'Della Gatta woman with Capuchin,1800–1824,gouache. No competing physical identity returned.',
321:'Roman Francis Xavier and saints,1751–1775,inventory101. No competing physical identity returned.',
322:'Attributed Fuseli King Lear,1770s,inventory112,oil canvas. Fuseli/Fuessli/Fussli and King Lear aliases returned only unrelated Pearson Denman, Moroni woman and Beresford Rose portraits.',
323:'English-school Assumption,1790–1799. Benjamin West/American school is a historical possibility, not firm authorship. Returned Assumptions name other makers, including Unterberger, or have different periods; no competing West identity returned.',
324:'Attributed Lanfranco Holy Face,1620–1640,oil on panel. Existing7d3a Santo1637–1639 is a mural painting in its pinned source; different physical support.',
325:'Attributed Toma Ophelia(?),1870–1880. Oral attribution and questioned subject remain qualified.',
326:'Southern Italian putti,1741–1760,inventory172. Different composition/maker from De Wit putti before Dionysus herm; former Gimignani suggestion rejected in source.',
327:'Bertuzzi Clare, Catherine and Laurence,1740–1760,inventory170. No competing physical identity returned.',
329:'Roman Lamentation, literal1590/1610 agrees with structured endpoints. Giulio Mancini remains historical context.',
330:'Roman Christ with thorns,1700–1724,copy after Reni,inventory98. Different period/object from Flemish copper300.',
331:'French Teresa in ecstasy,1725–1749,inventory168. No competing physical identity returned.',
332:'Neapolitan Pieta,1740–1760,inventory227. Solimena/De Caro influence stays qualified, not a firm maker.',
333:'De Mura circle Vincent Ferrer,1750–1799,inventory82. No competing physical identity returned.',
334:'Southern Italian workshop Ecce Homo,1701–1750,inventory177. Distinct from sixteenth-century Corona305.',
335:'Bazzani circle Pieta,1725–1749,inventory203. Distinct school and inventory from Neapolitan332.'}
assert set(COMPARISONS)==set(s.DEVANNA)
for n,note in COMPARISONS.items():NOTES[n]=working['observations'].get(str(n),{}).get('note','')+' '+note
NOTES[135]+=' Additional Mountain Landscape title matches name other artists, periods and media; no competing Picutti object returned.'
DEFERRED={int(k):v for k,v in working['holds'].items()};DEFERRED.update(s.UNCERTAIN);DEFERRED.update({int(k):v for k,v in m.load(RUN/'vicenza-editorial-working-001.json')['deferred'].items()})
QUALIFIED={258,262,280,287,299}
def values():
 x=m.load(RUN/'measurement-values-002.json.gz');assert not x['failures'] and not x['stopped'];rows=[]
 for part in x['components']:
  raw=f.body(part['receipt_reference'],part['body_reference']);vs=[{k:v['value'] for k,v in r.items()} for r in json.loads(raw)['results']['bindings']];assert len(vs)==part['rows'] and all(v['s'] in part['subjects'] for v in vs);rows+=vs
 assert rows==x['triples'];g=collections.defaultdict(lambda:collections.defaultdict(set))
 for v in rows:g[v['s']][v['p']].add(v['o'])
 return g
dimensions=f.d.prior.r.dimensions
def build(reparse=False):
 original=m.load(RUN/'native-candidates-002.json.gz')['rows'];x=m.load(RUN/'selected-identity-005.json.gz');comps={v['number']:v for v in x['comparisons']};assert x['rows']==s.rows();checked(x['script_reference']);checked(x['base_script_reference']);g=values()
 if reparse:
  fresh,_=f.build();assert fresh==original
 assert set(NOTES)==set(s.SELECTED) and len(NOTES)==135 and not(set(NOTES)&set(DEFERRED));ds=[]
 context=m.load(RUN/'comparison-source-context-001.json.gz');assert not {v['number'] for v in context['museum_local_inventory_hits']}&set(NOTES)
 for row in original:
  n=row['number']
  if n not in NOTES:
   ds.append(dict(number=n,institution_id=row['institution_id'],museum=row['museum'],source_id=row['index_record']['source_record_id'],state='editorial_hold' if row['state']!='candidate' or n in DEFERRED else 'deferred_identity_review',basis=DEFERRED.get(n,'Source issues: '+', '.join(row['issues']) if row['issues'] else 'Physical version/source-note identity review pending; no new artwork approved.')));continue
  assert row['state']=='candidate' and not row['issues'];v=copy.deepcopy(row['facts']);cmp=comps[n];assert not cmp['source_hits'] and v['last']<=1970
  derived=dimensions(v,g);v['dimensions_text']=derived;derived_fields=dict(dimensions_text=dict(value=derived,basis='Literal measurements, explicit units only; frame notes preserved.',source_reference=ref(RUN/'measurement-values-002.json.gz')))
  if n in QUALIFIED:
   history=v['source_fields']['NOTIZIE STORICO CRITICHE'];assert re.match(r'(?:Dipinto |Piccola tavola )?attribuit[oa]',history,re.I)
   original_label=v['creator_label'];v['creator_label']=original_label+'; attribuito (NOTIZIE STORICO CRITICHE)';derived_fields['creator_label']=dict(value=v['creator_label'],original_header=original_label,basis='Historical note explicitly qualifies attribution; preserve literal header separately and prevent unqualified authorship.',source_field='NOTIZIE STORICO CRITICHE',source_text=history)
  ds.append(dict(row,facts=v,state='approved_review_only_addition',confidence=.88,existing_artwork_id=None,basis=NOTES[n].strip(),comparison=cmp,derived_fields=derived_fields,limitation='Editorial confidence, not calibrated probability. Qualified/unnamed makers, uncertain titles, ranges and rights labels retained. Sparse comparisons evaluated using subjects, supports, periods and inventories. Holding is not current display or independently observed presence. Review only, no images or painter authority links.'))
 assert not [v for v in i.within_batch([v for v in ds if v['state']=='approved_review_only_addition']) if v['kind']=='inventory'];return ds
def main():
 dest=RUN/'editorial-reviewed-001.json.gz';assert not dest.exists();ds=build(True)
 names=['native-candidates-002.json.gz','selected-identity-005.json.gz','selected-citations-005.json.gz','measurement-values-002.json.gz','comparison-source-context-001.json.gz','source-editorial-working-002.json','vicenza-editorial-working-001.json']
 m.save(dest,dict(at=m.now(),decisions=ds,reviewer_reference=ref(Path(__file__).resolve()),dependencies=[ref(RUN/n) for n in names],policy='135 individually reviewed works at Vicenza and Devanna. Remaining563 notices stay in research, including three underfilled museums. No quota-based approval.',reparsed_candidates=len(ds)))
 print(json.dumps(dict(states=collections.Counter(v['state'] for v in ds),approved_by_museum=collections.Counter(v['museum']['name'] for v in ds if v['state']=='approved_review_only_addition'))),flush=True)
if __name__=='__main__':main()
