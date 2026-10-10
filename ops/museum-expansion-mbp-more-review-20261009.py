"""Further MBP object-by-object decisions; physical supports and attribution qualifiers retained."""
import collections,copy,importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('i',Path(__file__).with_name('museum-expansion-mbp-more-identity-20261009.py'));i=importlib.util.module_from_spec(z);z.loader.exec_module(i);s=i.s;m=i.m;RUN=i.RUN;ref=s.ref;checked=s.checked
QUALIFIED={
227:'Anonymous; Mount Athos workshop (museum attribution)',229:'Anonymous; Cretan workshop (museum attribution)',232:'Anonymous; northern Greek workshop (museum attribution)',234:'Anonymous; northern Greek workshop (museum attribution)',235:'Anonymous; Macedonian workshop, possibly Veroia (museum attribution)',236:'Anonymous; Greek workshop (museum attribution)',240:'Anonymous; Sinai monastery workshop (museum attribution)',249:'Anonymous; Macedonian, specifically Mount Athos workshop (museum attribution)',256:'Anonymous; northern Greek workshop (museum attribution)',257:'Anonymous; Serbian workshop (museum attribution)',258:'Anonymous; northern Greek workshop (museum attribution)',260:'Anonymous; Greek workshop (museum attribution)',261:'Anonymous; northern Greek workshop (museum attribution)',262:'Anonymous; workshop influenced by Western models (museum attribution)',263:'Anonymous; probably Mount Athos workshop (museum attribution)',264:'Anonymous; eastern Macedonian workshop (museum attribution)',265:'Anonymous; workshop using Italian engraving models (museum attribution)',266:'Anonymous; Mount Athos workshop (museum attribution)',267:'Anonymous; workshop associated with Meteora (museum attribution)',270:'Attributed to the workshop of Georgios Chrysoloras (museum attribution)',272:'Anonymous; Cretan workshop (museum attribution)',273:'Anonymous; Macedonian workshop (museum attribution)',282:'Anonymous; Greek workshop (museum attribution)',284:'Anonymous; northern Greek folk workshop (museum attribution)',285:'Anonymous; Greek folk workshop (museum attribution)',287:'Anonymous; northern Greek workshop (museum attribution)',295:'Anonymous; Macedonian workshop (museum attribution)',297:'Anonymous; Cretan workshop (museum attribution)',299:'Anonymous; Ionian workshop (museum attribution)',307:'Anonymous; Constantinople workshop (museum attribution)',308:'Anonymous; Macedonian workshop, probably Mount Athos (museum attribution)',314:'Anonymous; Macedonian workshop (museum attribution)',317:'Anonymous; northern Greek workshop (museum attribution)',319:'Anonymous; eastern Macedonian workshop (museum attribution)',328:'Anonymous; attributed to Mount Athos workshop, familiar with Russian icons (museum attribution)',331:'Anonymous; provincial workshop (museum attribution)',345:'Anonymous; provincial workshop (museum attribution)',349:'Anonymous; northern Greek workshop (museum attribution)',350:'Anonymous; Ionian workshop and Cretan painter close to Poulakis (museum attribution)',351:'Anonymous; attributed to a Macedonian workshop',352:'Anonymous; Ionian workshop (museum attribution)',353:'Anonymous; provincial workshop with Western influences (museum attribution)',355:'Anonymous; Macedonian workshop (museum attribution)',362:'Anonymous; northern Greek workshop (museum attribution)',363:'Anonymous; Macedonian workshop (museum attribution)',364:'Anonymous; provincial Greek workshop (museum attribution)',372:'Anonymous; provincial Macedonian workshop (museum attribution)',375:'Unidentified painter; inscription possibly names Constantine and Sergius from Epirus (museum attribution)',376:'Anonymous; provincial workshop with Western influences (museum attribution)',377:'Anonymous; provincial workshop with Western influences (museum attribution)',378:'Anonymous; Cretan workshop (museum attribution)',379:'Anonymous; early eighteenth-century workshop; Poulakis signature not genuine (museum assessment)',380:'Anonymous; provincial workshop, possibly Wallachia (museum attribution)',389:'Anonymous; Macedonian workshop (museum attribution)',
}
NOTES={
203:'One inventoried triclinium mosaic BΨ38,10.35x7.45m,with Eusebius/Markia/Helladitis/Clementi inscription; not other residential floor inventories.',
204:'One combined residential-floor inventory BΨ20; reception hall and three further rooms count together once, not four separate objects.',
207:'Detached devotional mosaic BΨ29/α,83x98cm,from northern colonnade of Saint Demetrius; do not equate it to other donor mosaics remaining in the church.',
208:'One detached peacock/basin mosaic BΨ27,82x105cm; destroyed symmetric counterpart is not a second record.',
219:'Single inventoried small monogram fragment BT124/2,4.7x4cm. No speculative whole inscription or church-decoration parent added.',
224:'Independent surviving cut panel BEI957,Potiphar-wife/trial scenes,53x45.5cm; distinct from BEI956,958,959,which depict different episodes. Earlier single parent painting not added.',
229:'Two pictorial zones remain one wooden icon BEI164; no separate records for its saint figures.',
230:'Paper icon50 has ten prophet medallions and32.3x48cm dimensions; distinct from Parthenios124 with fifteen medallions,35x48.3cm.',
231:'Parthenios124 has fifteen prophet medallions and35x48.3cm dimensions; distinct from anonymous50 with ten medallions.',
235:'Inventory26 belongs to the explicit MBP registry in this record, not a universal object identifier. Creator remains qualified Macedonian/possibly Veroia workshop.',
242:'Physical recent print175 retains1900–1999; stays in review and is not date-eligible. Small9.1x10.5cm sheet differs from older Catherine impressions.',
243:'Nikodimos1698sheet176,34.5x45.5cm,seated Catherine; distinct from1698–1699sheet177,63.4x61.6cm,standing Catherine and life scenes.',
244:'Sheet177 includes life scenes and1698/1699 inscriptions; one print, distinct from sheet176.',
247:'Ca.1820 in narrative takes precedence over unqualified exact-year representation; original structured date preserved in evidence.',
252:'The physical impression213 is printed on cloth, not paper; material retained literally.',
254:'Source structured1767 retained; broader second-half-eighteenth-century narrative is compatible. Skete229 is distinct from Demetrios105/213/220.',
268:'1853lithograph printed on silk for Vienna Greek community; not a painted wooden Saint George icon.',
269:'1767engraving223: A.B. identifies printer Antonio Bortoli, not a securely named engraver; creator remains anonymous.',
270:'Source narrative attributes the icon to Chrysoloras workshop; do not convert structured named creator into autograph authorship.',
275:'1798NikiforosXenophontosprint58,43x53.7cm,is a distinct inventoried impression from already catalogued1833print127,34.5x48.5cm.',
280:'Source explicitly identifies1700Leopoliswoodcut by Dionysios; no modern reprint date asserted for this sheet179.',
299:'One painted oval heraldic shield within a carved coat of arms,BEI421; surrounding figures do not create further artwork records.',
338:'One detached Acheiropoietos fountain mosaic fragment40,63x185cm; different church and inventory from peacock27.',
351:'Two surviving side leaves of a triptych,BEI323,are catalogued together once; no whole triptych or missing central panel invented.',
360:'Conservation uncovered Emmanouil Langadis signature and1624date; retain corrected source date,not earlier obsolete18th-century attribution.',
361:'Surviving central triptych panel178,30.5x32.5cm; side leaves and complete parent not added.',
370:'One Russian icon412 containing four scenes around a painted cross; count once.',
375:'Illegible inscription only possibly names Constantine and Sergius; retain uncertain creator label without authority links.',
379:'Source explicitly says Poulakis signature is not genuine. Anonymous early18th-century workshop; no Poulakis artist link.',
}
def build():
 x=m.load(RUN/'production-identity-001.json.gz');extra=m.load(RUN/'subject-comparators-001.json.gz');assert x['rows']==i.f.rows()[0];out=[]
 for row,c in zip(x['rows'],x['comparisons']):
  d=copy.deepcopy(row);d['comparison']=copy.deepcopy(c);f=d['facts'];n=d['number'];assert not c['source_hits']
  ids={h['id']for h in d['comparison']['hits']};keys={m.norm(q).removeprefix('the ').replace('saint ','st ').replace('demetrios','demetrius')for q in f['titles']}
  for h in x['state']['artworks']:
   same=m.norm(h['title']).removeprefix('the ').replace('saint ','st ').replace('demetrios','demetrius')in keys
   manual=n==224 and h['id']=='a5d1275c-f630-5bd9-a16e-aee4ab6cf54d' or n in[349,350,351,352,353,355]and h['id']=='9603d4e3-ef53-524d-ada0-b735012f5992'
   if(same or manual)and h['id']not in ids:d['comparison']['hits'].append(dict(h,hit_types=['translated_title_or_creator_comparator'],same_museum=h['id']in x['state']['scoped_ids']));ids.add(h['id'])
  if n in QUALIFIED:f['creator_label']=QUALIFIED[n]
  if n==224:f['description_md']='Surviving cut panel from Theodoros Poulakis’s Joseph cycle, inventory ΒΕΙ957. The historic single parent painting is not represented by a further record.'
  if n==351:f['description_md']='Two surviving side leaves of a triptych, catalogued together under ΒΕΙ323. The missing central panel and complete triptych are not additional records.'
  if n==361:f['description_md']='Surviving central panel of a triptych. The missing leaves and complete triptych are not additional records.'
  if n==350:NOTES[n]='Small17x14.2cm anonymous Ionian/Cretan icon67,close in style to Poulakis. Existing9603d4e3 Annunciation is Q113051424,1672,30x22.5cm,inventoryCl.I n.0533 in its captured Wikidata concordance; distinct object and dimensions,not an attribution rewrite.'
  if n==379:f['description_md']='The museum identifies the inscribed signature of Theodoros Poulakis as not genuine and dates the work to an early eighteenth-century workshop.'
  if n in [203,204,207,208,337,338]:f['description_md']=('Floor mosaic'if n in[203,204,337]else'Wall mosaic')+': one museum-inventoried fragment or assembly, '+f['inventory']+'. Combined sections count once; source mosaic classification is retained.'
  basis='Museum provider274 and storeLocation6051 explicitly identify MBP. Object '+f['source_id']+', inventory '+f['inventory']+'. '+NOTES.get(n,'Independent inventoried physical object. Title,subject,material,dimensions,period and inventory distinguish its support from the120existing museum objects and bounded source/title/creator comparators; repeated saint subjects alone do not establish identity.')
  d.update(state='approved_review_only_addition',basis=basis,confidence=.95,limitation='Editorial confidence, not calibrated probability. Holding only; no fresh display, custody or ownership claim. Review status and original source qualifications preserved. No image or artist-authority attachment.');out.append(d)
 assert len(out)==107;return out
if __name__=='__main__':
 ds=build();deps=[RUN/v for v in ['candidate-facts-001.json.gz','production-identity-001.json.gz','production-identity-citations-001.json.gz','production-initial-scope-001.json.gz','national-details-001.json.gz','subject-comparators-001.json.gz','captures/poulakis-annunciation-qid-001.json','captures/poulakis-annunciation-qid-001.body.gz']];m.save(RUN/'editorial-reviewed-001.json.gz',dict(at=m.now(),decisions=ds,dependencies=[ref(v)for v in deps],reviewer_reference=ref(Path(__file__).resolve()),policy='Selected physical MBP objects with source,edition,assembly and creator review; local database read-only.'))
 print(json.dumps(dict(states=dict(collections.Counter(v['state']for v in ds)),eligible=sum(v['state']=='approved_review_only_addition'and v['facts']['first']is not None and v['facts']['last']<=1970 for v in ds))),flush=True)
