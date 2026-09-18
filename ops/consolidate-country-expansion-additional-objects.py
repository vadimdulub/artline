#!/usr/bin/env python3
"""Four individually reviewed physical-object duplicates, with redirects and preimages."""
import argparse,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('c',Path(__file__).with_name('consolidate-overnight-pop-objects.py'));c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
m=c.m;C=c.CORE;B=m.x.SESSION_BASE;RUN=B/'duplicates/additional-physical-objects';BACK=m.BACKUPS/'additional-physical-objects';E=B/'duplicates/seven-additional-objects/primary'
c.RUN=RUN;c.BACK=BACK;c.SOURCE=m.x.SESSION_NAME+'-additional-reviewed-objects';c.SOURCE_NAME='Four individually researched primary museum object reconciliations';c.SOURCE_ROOT='https://github.com/vadimdulub/artline'
CASES=[('Flandrin','europe-joconde-m0703-54a541c1602e-la-florentine','wikimedia-artwork-q112056883','7943',['7943 ; 3048','Flandrin Hippolyte (1809-1864)','1840','60.5','50.2'], 'Current POP exact inventory7943/old3048 identifies the same Flandrin painting at Evreux,1840,oilcanvas60.5x50.2. Related study8192 is explicitly different and excluded.'),('Leroux','europe-joconde-m0525-bfe738393cdb-l-attente','wikimedia-artwork-q121791025','81.1.58',['81.1.58 ; BA2.25; D13; 54.21.20','Leroux-Revault Laura (1872-1936)','150','130','Salon de 1896'],'Current POP exact inventory81.1.58 and aliases confirms same LauraLeroux painting at Verdun. Canonicalc1896 uncertainty retained, compatible with primary1890–1903 and Salon1896; original broader dating remains on archived row.'),('Charnay','europe-joconde-m1011-aba5bd9c11e8-chateau-de-chateau-renard-loiret','wikimedia-artwork-q135902845','MC_CC 97.01.119',['MC_CC 97.01.119 ; 59 ; 84','Charnay Armand (1844-1915)','H. 20 ; l. 29,4','1997'],'Current POP inventoryMC_CC97.01.119 and aliases identifies same Charlieu painting,oilcanvas20x29.4,1997gift. Canonical unknown chronology retained; broad primary period not converted into invented exact date.'),('Polenov','wikimedia-artwork-q124079130','europe-russian-session-museum-8d47a54b21c3-record','Ж-2682',['Ж-2682','Поленов В. Д.','43,5 х 30','1890–1900-е'],'Current RussianMuseum exact Ж2682 and actual side-by-side primary/Commons comparison establish same painting: matching brushwork, figures, stairs, pot, architecture and signature. Keep enriched primary museum record canonical; transfer Wiki authority and redirect duplicate placeholder. No inference solely from title. Unknown bounded chronology retained.')]
def proposals():
 out=[]
 for key,old,keep,acc,need,reason in CASES:
  f=E/(key+'.review.json');ev=json.loads(f.read_text());assert C.sha(f.with_name(key+'.html').read_bytes())==ev['receipt']['sha256'];assert all(x in ev['text'] for x in need)
  primary={**ev,'evidence_file':str(f),'evidence_sha256':C.sha(f.read_bytes())}
  if key=='Polenov':
   cf=E/'Polenov-commons.json';sheet=E/'Polenov-identity-comparison.jpg';primary['visual_review']=dict(approved=True,comparison_path=str(sheet),comparison_sha256=C.sha(sheet.read_bytes()),commons_metadata_path=str(cf),commons_metadata_sha256=C.sha(cf.read_bytes()),review='Actually viewed both images side by side: same individual paint strokes and physical scene. Different color balance/resolution does not establish another object. Museum reference image is only research evidence, not approved for publication.')
  out.append(dict(key=key,old_slug=old,canonical_slug=keep,accession=acc,primary=primary,institution_context=reason,targets={}))
 return out

def plan():
 if (RUN/'plan.json').exists():return
 assert (B/'duplicates/russian-primary-inventory-enrichment/verification.json').exists(),'Plan after500 inventory fills'
 entries=proposals();snaps={t:{} for t in ('local','production')}
 for target in snaps:
  with m.m.r.base.connect(target=='production') as db,db.transaction():
   db.execute('SET TRANSACTION READ ONLY');db.execute("SET LOCAL statement_timeout='120s'");c.a.ensure_schema(db)
   for e in entries:
    ids={r['slug']:r['id'] for r in db.execute('SELECT id::text,slug FROM artworks WHERE slug=ANY(%s)',([e['old_slug'],e['canonical_slug']],))};assert len(ids)==2;old=ids[e['old_slug']];keep=ids[e['canonical_slug']];snap=c.a.snapshot(db,[old,keep]);ws={w['id']:w for w in snap['artworks']};assert all(w['status']=='review' and not w['published_at'] for w in ws.values());assert not ws[old]['primary_media_id'];assert ws[old]['current_institution_id']==ws[keep]['current_institution_id'];assert m.m.accession_key(ws[keep]['accession_number'])==m.m.accession_key(e['accession'])
    creators=lambda wid:{(r['artist_id'],r['attribution_role']) for r in snap['artwork_artists'] if r['artwork_id']==wid};assert creators(old)==creators(keep) and len(creators(keep))==1 and next(iter(creators(keep)))[1]=='primary'
    for table in ('artwork_media','artwork_places','curated_collection_items'):assert not any(r['artwork_id']==old for r in snap[table])
    assert any(r['artwork_id']==keep and r['claim_type']=='holding' and r['review_state']=='accepted' and not r['superseded_by'] for r in snap['artwork_location_assertions'])
    common={r['scheme'] for r in snap['external_identifiers'] if r['entity_id']==old}&{r['scheme'] for r in snap['external_identifiers'] if r['entity_id']==keep};e['targets'][target]=dict(old_id=old,canonical_id=keep,preserve_archived_schemes=sorted(common));snaps[target][e['key']]=snap;print(target,e['key'],'pair planned',flush=True)
 for e in entries:
  comp=lambda t:[{k:w[k] for k in ('slug','title','accession_number','creation_year_start','creation_year_end','date_precision','work_type','status')} for w in sorted(snaps[t][e['key']]['artworks'],key=lambda w:w['slug'])];assert comp('local')==comp('production')
 for t in snaps:C.save_new(BACK/(t+'-preimages.json'),snaps[t])
 C.save_new(RUN/'plan.json',entries);pin=C.sha((RUN/'plan.json').read_bytes());C.save_new(RUN/'manifest.json',dict(at=C.now(),pairs=4,plan_sha256=pin));C.save_new(RUN/'quality-review.json',dict(at=C.now(),approved=True,plan_sha256=pin,held_objects={},review='Four specific primary-source decisions actually reviewed: exact POP inventory aliases and canonical creator links; Polenov primary/Commons physical image comparison and museum inventory. Cartailhac/Bruges distinct objects excluded; Walsall alias evidence unresolved and excluded. Preserve all original rows,media,citations,dating,country,holdingassertions and reviewstatus; archive duplicate and redirect.'))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['plan','apply','verify']);a=p.parse_args();plan() if a.command=='plan' else getattr(c,a.command)()
