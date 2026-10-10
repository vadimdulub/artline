#!/usr/bin/env python3
"""Independent read-only validation and reproducible final research register."""
import argparse,collections,csv,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('m',Path(__file__).with_name('museums-exactly-one-deep-20261008.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
d=m.d;RUN=m.RUN;ROOT=m.ROOT
def verify():
 records={};waves=[];plans={}
 for folder in sorted((RUN/'waves').iterdir()):
  if not (folder/'applied.json').exists():continue
  p=d.load(folder/'plan.json.gz');receipt=d.load(folder/'applied.json');assert receipt['plan_sha256']==d.sha((folder/'plan.json.gz').read_bytes())
  for r in p['records']:assert r['artwork_id']not in records;records[r['artwork_id']]=r;plans[r['artwork_id']]=receipt['plan_sha256']
  waves.append(dict(wave=folder.name,created=receipt['new_artworks'],museums=len({r['museum']['id']for r in p['records']})))
 links=[]
 for name in ['deep-existing','extra-existing']:
  folder=RUN/'links'/name/'delivery/verified';p=d.load(folder/'plan.json.gz');v=d.load(folder/'verification.json')
  assert not v['errors'] and v['targets']=={'production':len(p['claims'])} and v['plan_sha256']==d.sha((folder/'plan.json.gz').read_bytes());links+=p['claims']
 aliases=d.load(RUN/'aliases/verification.json');aliasapi=d.load(RUN/'aliases/api-verification.json');assert aliases['verified_aliases']==aliasapi['passed']==3 and not aliasapi['failed']
 baseline=d.load(RUN/'baseline.json.gz');base={x['institution']['id']:x for x in baseline['selected']};assert all(r['museum']['id']in base for r in records.values())
 with d.connect()as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
  arts=db.execute('SELECT to_jsonb(a) artwork,artline_creation_scope(creation_year_start,creation_year_end,date_precision) scope,artline_has_selection_evidence(id) selected FROM artworks a WHERE id=ANY(%s::uuid[])',(list(records),)).fetchall();assert len(arts)==len(records)
  for x in arts:
   ar=x['artwork'];r=records[ar['id']];f=r['facts'];assert ar['current_institution_id']==r['museum']['id'] and x['scope']=='eligible' and x['selected']
   assert ar['status']=='review' and ar['published_at']is None and ar['primary_media_id']is None
   for col,key in [('title','title'),('unlinked_creator_label','creator_label'),('creation_year_start','first'),('creation_year_end','last'),('date_precision','date_precision'),('date_display','date_display'),('accession_number','accession'),('medium_text','medium'),('dimensions_text','dimensions'),('work_type','work_type'),('object_form','object_form')]:assert ar[col]==f.get(key),(ar['id'],col)
  cites=db.execute("SELECT entity_id::text,source_record_id,source_url,evidence_note FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND field_name='museum_source_metadata_and_holding'",(list(records),)).fetchall();assert len(cites)==len(records)
  for c in cites:
   r=records[c['entity_id']];ev=json.loads(c['evidence_note']);assert c['source_record_id']==r['source_record_id'] and c['source_url']==r['facts']['source_url'] and ev['plan_sha256']==plans[c['entity_id']] and ev['raw_source_record']==r['raw_source_record'] and ev['remaining_uncertainty']==r['remaining_uncertainty']
  identifiers=db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(list(records),)).fetchall();assert len(identifiers)==len(records)
  for x in identifiers:
   r=records[x['entity_id']];assert x['external_id']==r['source_record_id'] and x['canonical_url']==r['facts']['source_url'];assert x['scheme']=={'artefact-native':'artefact-object','qagoma-native':'qagoma-object','wikidata-catalogue':'wikidata'}[r['provider']]
  holds=db.execute('SELECT to_jsonb(h) v FROM artwork_location_assertions h WHERE artwork_id=ANY(%s::uuid[])',(list(records),)).fetchall();assert len(holds)==len(records)
  for x in holds:
   h=x['v'];assert h['institution_id']==records[h['artwork_id']]['museum']['id'] and h['claim_type']=='holding' and h['review_state']=='accepted' and h['display_state']is None and h['superseded_by']is None
  assert not db.execute('SELECT 1 FROM artwork_artists WHERE artwork_id=ANY(%s::uuid[]) LIMIT 1',(list(records),)).fetchone()
  secondary=d.load(RUN/'waves/artefact-delivery/secondary-source-applied.json')['citation'];actual=db.execute('SELECT entity_id::text,source_record_id,source_url,evidence_note FROM citations WHERE id=%s',(secondary['id'],)).fetchone();assert all(actual[k]==secondary[k]for k in actual)
  for r in aliases['rows']:
   assert db.execute('SELECT canonical_institution_id::text id FROM institutions WHERE id=%s',(r['alias_id'],)).fetchone()['id']==r['canonical_id']
   assert not db.execute('SELECT 1 FROM artworks WHERE current_institution_id=%s LIMIT 1',(r['alias_id'],)).fetchone()
  mids=set(base)|{r['canonical_id']for r in aliases['rows']};counts={}
  for part in d.chunks(sorted(mids),100):counts.update({x['id']:x['n']for x in db.execute("SELECT current_institution_id::text id,count(*) n FROM artworks WHERE current_institution_id=ANY(%s::uuid[]) AND status<>'archived' GROUP BY 1",(part,))})
  remaining=[x['v']for x in db.execute("""SELECT to_jsonb(i) v FROM institutions i CROSS JOIN LATERAL
   (SELECT count(*) n FROM (SELECT 1 FROM artworks a WHERE a.current_institution_id=i.id AND a.status<>'archived' LIMIT 2) q)c
   WHERE i.kind='museum' AND i.status<>'archived' AND i.canonical_institution_id IS NULL AND c.n=1 ORDER BY i.name,i.id""")]
 additions=collections.Counter(r['museum']['id']for r in records.values());linked=collections.Counter(r['target_institutions']['production']['id']for r in links);rows=[]
 for iid in sorted(set(additions)|set(linked)):
  i=base[iid]['institution'];assert counts[iid]>=1+additions[iid]+linked[iid];rows.append(dict(id=iid,name=i['name'],slug=i['slug'],before=1,added=additions[iid],linked_existing=linked[iid],after=counts[iid]))
 result=dict(at=d.now(),target='production',fresh_baseline_at=baseline['at'],baseline_exactly_one=len(base),new_artworks=len(records),existing_artworks_linked=len(links),museums_expanded=len(rows),museum_aliases_reconciled=len(aliases['rows']),current_global_exactly_one=len(remaining),new_icons=sum(r['facts'].get('object_form')=='icon'for r in records.values()),new_publications=0,new_images=0,new_display_claims=0,local_database_writes=0,waves=waves,museums=rows,aliases=aliases['rows'])
 d.save(RUN/'verification.json',result);d.save(RUN/'remaining-one-artwork-museums.json.gz',dict(at=result['at'],museums=remaining))
 arts=[dict(artwork_id=aid,museum=r['museum']['name'],slug=r['museum']['slug'],title=r['facts']['title'],action='create',source_url=r['facts']['source_url'])for aid,r in records.items()]
 arts +=[dict(artwork_id=r['target_ids']['production'],museum=r['institution']['name'],slug=r['institution']['slug'],title=r['title'],action='link_existing',source_url=r['source_url'])for r in links]
 for filename,data in [('artwork-results.csv',arts),('museum-results.csv',rows),('museum-alias-results.csv',aliases['rows'])]:
  with (RUN/filename).open('x',newline='')as fp:w=csv.DictWriter(fp,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
 print(json.dumps({k:v for k,v in result.items()if k not in ['museums','aliases']}),flush=True)

def api_verify():
 m.m.api_verify()
 v=d.load(RUN/'verification.json');checks=[]
 targets=[dict(name=r['name'],slug=r['slug'],expected=r['after'])for r in v['museums']]
 targets +=[dict(name=r['alias_name'],slug=r['alias_slug'],expected=r['after'])for r in v['aliases']]
 for r in targets:
  url='https://artlines.org/api/backend/v1/museums/'+r['slug'];response=d.requests.get(url,timeout=(15,45));body=response.json()if response.status_code==200 else {}
  value=body.get('work_count');ok=response.status_code==200 and value is not None and value>=r['expected'];checks.append(dict(**r,url=url,status=response.status_code,work_count=value,verified=ok));print('Overview',r['name'],value,ok,flush=True)
 d.save(RUN/'overview-api-verification.json',dict(at=d.now(),passed=sum(r['verified']for r in checks),failed=sum(not r['verified']for r in checks),checks=checks));assert all(r['verified']for r in checks)

def register():
 v=d.load(RUN/'verification.json');base=d.load(RUN/'baseline.json.gz')['selected'];expanded={r['id']for r in v['museums']};aliases={r['alias_id']for r in v['aliases']};remaining={r['id']for r in d.load(RUN/'remaining-one-artwork-museums.json.gz')['museums']};evidence=collections.defaultdict(list)
 for r in d.load(RUN/'artefact/selected-museum-catalogues.json.gz'):evidence[r['museum']['id']].append('Official Artefact: selected museum-scoped native objects')
 for r in d.load(RUN/'arco/italian-native/selection.json.gz')['museums']:evidence[r['museum']['id']].append('Italian ArCo: bounded native collection candidates; identity holds retained')
 for r in d.load(RUN/'waves/qagoma-corrected/source-verified.json.gz')['records']:evidence[r['museum']['id']].append('Official QAGOMA: selected native objects')
 indexed={r['museum']['id']for r in d.load(RUN/'wikidata-catalogue/missing-authorities/index-evidence.json.gz')['evidence']}
 for r in d.load(RUN/'reviewed-museum-authorities.json.gz'):evidence[r['museum']['id']].append('Reviewed Wikidata museum authority; '+('captured bounded object index'if r['museum']['id']in indexed else'object index deferred after service throttling'))
 rows=[]
 for b in base:
  i=b['institution'];iid=i['id'];status='expanded'if iid in expanded else'museum_alias_reconciled'if iid in aliases else'researched_no_mutation'if iid in evidence else'not_individually_researched_in_this_round'
  rows.append(dict(museum_id=iid,name=i['name'],status=status,still_exactly_one=iid in remaining,research='; '.join(sorted(set(evidence[iid])))or'Fresh production and preserved local candidate audit only; no claim of exhaustive source research.'))
 with (RUN/'cohort-research-register.csv').open('x',newline='')as fp:w=csv.DictWriter(fp,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 d.save(RUN/'research-summary.json',dict(at=d.now(),cohort=len(rows),statuses=collections.Counter(r['status']for r in rows),artefact_native_objects=sum(len(r['candidates'])for r in d.load(RUN/'artefact/selected-museum-catalogues.json.gz')),qagoma_native_objects=17,arco_native_objects=21,wikidata_selected_new_entities=len(d.load(RUN/'wikidata-catalogue/saved-index-metadata/selected-new-object-ids.json')),wikidata_reviewed_authorities=25,wikidata_successful_indexes=len(indexed),limitation='Bounded selected metadata research, not exhaustive downloading or proof of absent museum holdings. Unvisited objects and unresolved identity leads remain documented.'))
 print(collections.Counter(r['status']for r in rows),flush=True)

def report():
 v=d.load(RUN/'verification.json');api=d.load(RUN/'api-verification.json');overview=d.load(RUN/'overview-api-verification.json');research=d.load(RUN/'research-summary.json')
 assert api['failed']==overview['failed']==0
 native=d.load(RUN/'native-tests.json');wd=d.load(RUN/'wikidata-tests.json');assert native['failures']==native['errors']==wd['failures']==wd['errors']==0
 backup=d.load(RUN/'backups.json')['production'];assert backup['status']=='SUCCESSFUL'
 md=f"# Deep production museum research — 8 October 2026\n\nFresh production audit: **{v['baseline_exactly_one']}** active canonical museums with exactly one non-archived linked artwork at {v['fresh_baseline_at']}. Final independent database verification at {v['at']}: **{v['current_global_exactly_one']}**. Counts include review records and use the actual current production database.\n\n"
 md+=f"Applied **{v['new_artworks']} new artworks**, including **{v['new_icons']} icons**, and **{v['existing_artworks_linked']} existing-artwork museum links** across **{v['museums_expanded']} museums**. Reconciled **{v['museum_aliases_reconciled']} additional duplicate museum identities**, preserving their records, old routes and existing artworks. This round reduced the one-artwork count by **{v['baseline_exactly_one']-v['current_global_exactly_one']}**. All newly created artworks remain in review.\n\n"
 md+='[Database verification](verification.json) · [99 artwork additions/links and their sources](artwork-results.csv) · [Museum counts](museum-results.csv) · [Museum aliases](museum-alias-results.csv) · [All 228 cohort research statuses](cohort-research-register.csv) · [211 remaining one-artwork museums](remaining-one-artwork-museums.json.gz).\n\n'
 md+='## Research coverage and decisions\n\n'
 md+='Reviewed **849 selected source candidates and entity records**: 456 official Artefact museum objects, 17 QAGOMA objects, 21 Italian ArCo objects, and 355 selected Wikidata artwork candidates, with 171 associated creator entities. Also captured 25 exact existing WikiArt artwork pages for identity/link review. These counts are source records, not a claim of 849 distinct physical artworks. Museum-scoped catalogue selection preceded any enrichment; this round downloaded no artwork images.\n\n'
 md+='- **Official Artefact:** reviewed two bounded catalogue index pages per museum, capped at 48 candidates across each of ten museums. Accepted 74 new records after native-ID, collection, date, type, creator/date, title-translation and version checks. Museum-scoped catalogue membership and each object’s explicit Collection field are retained with captured page hashes. Source Russian labels and anonymous icon creators remain explicit; uncertain dates retain their intervals.\n'
 md+='- **Official QAGOMA:** 16 new records from 17 selected native pages. Preserved object numbers, accessions, own-object creator labels, original dates and acquisition credits. A discovered related-artists parsing problem was corrected before planning/delivery. The collection relationship is to the Queensland Art Gallery Board of Trustees catalogue; it does not assert display in a particular QAG building.\n'
 md+='- **Referenced Wikidata:** 25 museum authorities reviewed by full museum name, location and official website; no institution authority metadata overwritten. Fifteen bounded object indexes were captured successfully. The SPARQL endpoint throttled further indexing, including a later retry after backoff, so it was stopped. Previously saved successful indexes supplied candidates for the separately available public entity API. Eight records met the strict referenced-collection/type/date checks; three were added and one existing Manessier work was subsequently linked with primary-source corroboration. Unreferenced or conflicting holdings remain held.\n'
 md+='- **Italian ArCo:** 21 native candidates across five museums; six passed source checks but remained held because generic titles lacked sufficient distinct-object identity against existing records. No ArCo additions were forced through.\n\n'
 md+='This round individually investigated or reconciled 44 of the 228 starting museums; the register explicitly marks **184 without individual source research this round**. Twenty-seven investigated museum entries produced no mutation, including authority-only cases whose object indexes were deferred. The remaining 211 museums are an open research backlog, not a conclusion that they lack additional eligible holdings. The preserved local catalogue audit supplied no additional approved candidates.\n\n'
 md+='## Existing works linked\n\n'
 md+='The six links preserve all existing creator relationships, dates, images and publication states. Three use exact WikiArt artwork IDs and explicit Location fields: Roerich’s *Beda the Preacher* and *Nastasia Mikulichna* at Novosibirsk, and Levitan’s *Dandelions* at Chuvash. The Chuvash English museum-label variant was independently reconciled with the official museum catalogue.\n\n'
 md+='Mashkov’s *Cypress in the cathedral walls. Italy* (1913, 59 × 67 cm) and Grabar’s *Dugino. Sunrise* (1904, 66.5 × 88.5 cm) were matched using exact creator/date, translated titles and distinctive dimensions. Their WikiArt pages have no Location field: the actual holding evidence is the official Artefact catalogue, for Vladimir-Suzdal and Chuvash respectively. Editorial confidence is 0.90.\n\n'
 md+='Manessier’s *La Passion de Notre Seigneur Jésus-Christ* (1952) was matched by the exact WikiArt URL referenced in Wikidata. The underlying [official Alfred Manessier public-collections catalogue](https://www.alfredmanessier.com/collections-publiques/) was independently opened and confirms that title, date and La Chaux-de-Fonds museum. The existing unknown dimensions were preserved. Confidence is 0.95; the other exact WikiArt Location links also use 0.95. All confidence values are editorial assessments, not calibrated probabilities.\n\n'
 md+='## Identity and source limitations retained\n\n'
 md+='Two Artefact records describe the same Zhukovsky *Summer Morning. Rozhdestveno Estate* (1918): identical creator, museum and 91.3 × 122.6 cm dimensions. Only one artwork was created. Its citation preserves both source records, and a separately verified secondary-source citation indexes the other exact native URL to prevent a later duplicate. The catalogue permits one external identifier per provider scheme; the additional source is correctly represented as a citation.\n\n'
 md+='Fechin’s *A Bad Joke* remains explicitly identified as a study, and Myasoyedov’s *The Flight of Grigory Otrepyev* is the museum’s 1867 replica rather than the 1862 original. These version notes are saved in both source and holding evidence. New source creator labels remain object-level labels; this pass does not infer painter links.\n\n'
 md+='Held cases include an illustrated-album author/creator ambiguity, conflicting Abram Yefimov/Arkhipov labels, incompatible Fechin dimensions, a Raffaelli study needing existing-version comparison, the Nicholas Mas/Nicolaes Maes portrait identity, unresolved Braque still-life identity, two-sided/version ambiguities, unsupported date intervals and works outside the creation cutoff. A Petrov-Vodkin source with an impossible early date was excluded. Every accepted creation range falls wholly in or before 1970; no unknown creation year was invented.\n\n'
 md+='Hopper’s *Hotel By A Railroad* remains unlinked in this round: WikiArt says Private Collection, while referenced museum evidence names Hirshhorn. Official Smithsonian results support Hirshhorn, but direct catalogue captures returned 403; retained the discrepancy and source-access evidence for follow-up. Other sources returning throttling/security responses were not repeatedly queried. No held case is evidence that a museum lacks additional works. Full candidate decisions remain in the immutable source and final plans under `waves/`.\n\n'
 md+='## Museum results\n\n| Museum | Before | New works | Existing linked | After |\n|---|---:|---:|---:|---:|\n'
 for r in sorted(v['museums'],key=lambda r:(-r['after'],r['name'])):md+=f"| {r['name']} | 1 | {r['added']} | {r['linked_existing']} | {r['after']} |\n"
 md+='\n## Duplicate museum identities resolved\n\n| Former one-work record | Canonical collection before | After |\n|---|---:|---:|\n'
 for r in v['aliases']:md+=f"| {r['alias_name']} | {r['before_canonical']} | {r['after']} |\n"
 md+='\nThe Rome modern-art spelling error, English Rome ancient-art collection name and English Perugia museum name were each reconciled against retained official museum pages. Separate venues and storage/deposit institutions were not merged. Existing artwork metadata, source IDs, images and publication states were verified preserved.\n\n'
 md+='## Validation and recovery\n\n'
 md+=f"**25 source-guard tests passed** ([12 native-source guards](native-tests.json), [13 Wikidata guards](wikidata-tests.json)). Independent read-only SQL verified every new record’s exact source facts, source identifiers, citation body, eligible creation interval, review state, museum holding and absence of publication/display mutations. The existing-artwork link verifier checked all six complete preimages and relationships. Alias verification preserved all three existing objects and their source/media relationships.\n\n"
 md+=f"[Live artwork API checks](api-verification.json): **{api['passed']} passed**, covering one new work in every expanded museum and every existing-artwork link. [Live museum overviews](overview-api-verification.json): **{overview['passed']} passed**, including all three former one-work alias routes. Both old and canonical artwork URLs also passed the [three alias comparisons](aliases/api-verification.json).\n\n"
 md+=f"Production writes used the shared curated-ingestion advisory lock, row/preimage/source checks and guarded transactions. Recovery evidence includes successful Cloud SQL backup **{backup['id']}** and exact transaction preimages under `~/Library/Application Support/Artline/backups/{m.OP}/`. No local database writes, image changes, automatic publication, current-display claims, commits or deployments. Baseline `snapshot-comparison.json` is retained as inherited historical bookkeeping against round 2; the fresh baseline and final verification above are the authoritative counts for this round.\n"
 (RUN/'README.md').write_text(md)
 print('Report saved',str(RUN/'README.md'),flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase');x=p.parse_args();globals()[x.phase]()
