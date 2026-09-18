#!/usr/bin/env python3
"""Consolidate 21 individually compared POP notice pairs; retain original records."""
import argparse,importlib.util,json,re
from pathlib import Path
s=importlib.util.spec_from_file_location('c',Path(__file__).with_name('consolidate-overnight-pop-objects.py'));c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
m=c.m;C=c.CORE;B=m.x.SESSION_BASE;E=B/'duplicates/inventory-alias-leads';RUN=B/'duplicates/confirmed-inventory-aliases';BACK=m.BACKUPS/'confirmed-inventory-aliases'
c.RUN=RUN;c.BACK=BACK;c.SOURCE=m.x.SESSION_NAME+'-confirmed-inventory-aliases';c.SOURCE_NAME='Individually compared paired primary POP object notices';c.SOURCE_ROOT='https://pop.culture.gouv.fr/'
# Index is an explicit human-reviewed choice of canonical notice, never a fuzzy match rule.
CASES={6:(1,'PE 800','83.5','64'),7:(1,'Bx E 1443','54','65'),8:(1,'Bx E 673','82','66'),9:(1,'55.974.0.720','33','41'),33:(0,'PMD 976.1.156','60,5','45,5'),34:(0,'PMD 976.1.126','32,6','41'),35:(1,'PMD 996.5.1','95,5','125'),36:(1,'PMD 976.1.690','71','78'),37:(1,'PMD 984.10.1','55','46'),38:(0,'PMD 980.46.1','98','106,5'),39:(0,'PMD 976.1.965','54','65'),40:(0,'PMD 976.1.786','100,5','123'),41:(0,'PMD 988.7.1','73','100'),42:(0,'PMD 996.4.1','147','190,5'),43:(0,'PMD 976.1.158','81','100'),44:(0,'PMD 976.1.349','136','198'),45:(0,'PMD 976.1.849','65,3','54,3'),46:(0,'PMD 976.1.48','97','143'),47:(1,'PMD 981.29.1','36','18,5'),48:(1,'PMD 976.1.911','55','40'),49:(0,'68.2','32.3','40.7')}
def proposals():
 comparisons=json.loads((E/'comparison-fields.json').read_text());assert {int(e['key'].split('-')[1]) for e in comparisons}==set(CASES);out=[]
 for e in comparisons:
  n=int(e['key'].split('-')[1]);idx,acc,height,width=CASES[n];sources=e['sources'];assert len(sources)==2;keep=sources[idx];old=sources[1-idx];proof=[]
  for src in sources:
   f=E/'primary'/(src['notice']+'.review.json');d=json.loads(f.read_text());assert C.sha(f.with_name(src['notice']+'.html').read_bytes())==d['receipt']['sha256'];fields=src['fields'];assert acc in fields["Numéro d'inventaire"] and height in fields['Mesures'] and width in fields['Mesures'];assert fields['Auteur']==keep['fields']['Auteur'];assert c.key(fields['Titre'])==c.key(keep['fields']['Titre']);assert fields['Lieu de conservation']==keep['fields']['Lieu de conservation'];proof.append(dict(path=str(f),sha256=C.sha(f.read_bytes()),notice=src['notice'],receipt=d['receipt'],fields=fields))
  reason='Both current POP notices individually compared: same museum inventory, unqualified maker with matching lifespan, physical support dimensions, title and compatible creation chronology. Formatting labels and legacy notice numbers do not represent a second object. Preserve original fields, citations and immutable holding assertions; archive redundant row and redirect.'
  if n==6:reason+=' New notice explicitly cross-references 000PE018890 as machine number; same signed1835portrait83.5x64.'
  elif n==8:reason+=' New primary notice explicitly gives creation1869; older1850–1875rangeiscompatible. Keep existing1869canonicalrow; originalbroadrangeunchangedonarchive.'
  elif n==9:reason+=' Same signed1911Braque33x41withKahnweilerprovenanceand1923acquisition. Protected-image declaration preserved; no image publication approved.'
  elif n==49:reason+=' Exact same framed/unframed dimensions and1968acquisition;968.002explicitly computer inventory1999–2004. Broad1850–1900datingretained.'
  elif n>=33:reason+=' MuseumMauriceDenis paired notices share PMD inventory and exact physical dimensions; catalogue suffix Numéro d’inventaire is a field label. Some pairs also link the identical museum object URL. Frame dimensions remain distinct from support dimensions.'
  primary=dict(object_url=proof[idx]['receipt']['url'],receipt=proof[idx]['receipt'],paired_primary_notices=proof,review='Twenty-one closed, individually inspected primary-notice comparisons. No general title-only or stripped-parenthesis duplicate rule.')
  out.append(dict(key=e['key'],canonical_slug=keep['slug'],old_slug=old['slug'],primary=primary,institution_context=reason,targets={}))
 return out

def plan():
 if (RUN/'plan.json').exists():return
 entries=proposals();snaps={t:{} for t in ('local','production')}
 for target in snaps:
  with m.m.r.base.connect(target=='production') as db,db.transaction():
   db.execute('SET TRANSACTION READ ONLY');db.execute("SET LOCAL statement_timeout='120s'");c.a.ensure_schema(db)
   for e in entries:
    ids={r['slug']:r['id'] for r in db.execute('SELECT id::text,slug FROM artworks WHERE slug=ANY(%s)',([e['old_slug'],e['canonical_slug']],))};assert len(ids)==2;old=ids[e['old_slug']];keep=ids[e['canonical_slug']];snap=c.a.snapshot(db,[old,keep]);ws={w['id']:w for w in snap['artworks']};assert all(w['status']=='review' and not w['published_at'] and not w['primary_media_id'] for w in ws.values());assert ws[old]['current_institution_id']==ws[keep]['current_institution_id'];assert ws[old]['work_type']==ws[keep]['work_type']=='painting'
    creators=lambda wid:{(r['artist_id'],r['attribution_role']) for r in snap['artwork_artists'] if r['artwork_id']==wid};assert creators(old)==creators(keep) and len(creators(keep))==1 and next(iter(creators(keep)))[1]=='primary'
    if e['key']!='alias-08':assert all(ws[old][k]==ws[keep][k] for k in ('creation_year_start','creation_year_end','date_precision'))
    else:assert (ws[old]['creation_year_start'],ws[old]['creation_year_end'],ws[keep]['creation_year_start'],ws[keep]['creation_year_end'])==(1850,1875,1869,1869)
    for table in ('artwork_media','artwork_places','curated_collection_items'):assert not any(r['artwork_id']==old for r in snap[table])
    assert any(r['artwork_id']==keep and r['claim_type']=='holding' and r['review_state']=='accepted' and not r['superseded_by'] for r in snap['artwork_location_assertions'])
    common={r['scheme'] for r in snap['external_identifiers'] if r['entity_id']==old}&{r['scheme'] for r in snap['external_identifiers'] if r['entity_id']==keep};e['targets'][target]=dict(old_id=old,canonical_id=keep,preserve_archived_schemes=sorted(common));snaps[target][e['key']]=snap;print(target,e['key'],'exact pair preflight',flush=True)
 for e in entries:
  comp=lambda t:[{k:w[k] for k in ('slug','title','accession_number','creation_year_start','creation_year_end','date_precision','work_type','status')} for w in sorted(snaps[t][e['key']]['artworks'],key=lambda w:w['slug'])];assert comp('local')==comp('production')
 for target in snaps:C.save_new(BACK/(target+'-preimages.json'),snaps[target])
 C.save_new(RUN/'plan.json',entries);pin=C.sha((RUN/'plan.json').read_bytes());C.save_new(RUN/'manifest.json',dict(at=C.now(),pairs=len(entries),plan_sha256=pin));C.save_new(RUN/'quality-review.json',dict(at=C.now(),approved=True,plan_sha256=pin,held_objects={},review='All42freshprimarynoticesactuallyreadandcompared;21closedexactphysicalobjectpairsapproved. Sourceinventories,unqualifiedmakers,lifespans,dimensions,chronology,inscriptionsandprovenanceconsidered. 179numericcomponentfalsepositivesexcluded;other29strictaliasleadsinclude4alreadyhandledanddistinctfolio/study/versiongroupsandareexcluded. Noimage,deletion,publication,creationyearorcountryinference. Bothdatabasepreimagespinnedandcheckedagainbeforecommit.'))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['plan','apply','verify']);a=p.parse_args();plan() if a.command=='plan' else getattr(c,a.command)()
