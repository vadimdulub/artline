#!/usr/bin/env python3
"""Twenty individually reviewed POP physical identities excluded by strict matching.

No title, date, maker or inventory is changed. Archived placeholders retain
their original fields; the complete canonical object remains in review.
"""
import argparse,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('p',Path(__file__).with_name('consolidate-overnight-pop-objects.py'));p=importlib.util.module_from_spec(s);s.loader.exec_module(p)
m=p.m;CORE=p.CORE;ORIGINAL=p.RUN;p.RUN=m.x.BASE/'duplicates/pop-individual-followup';p.BACK=m.BACKUPS/'pop-individual-followup';p.SOURCE='overnight-pop-individual-objects-20260913'
CONTEXT={
 '00000055502':'RouenI965.7(1963), same exact museum object and maker; sourceMariaElena and canonicalMariaHelena are name variants. Distinct fromRouenII.',
 '00000055503':'RouenII974.1(1968), same exact museum object and maker; sourceMariaElena and canonicalMariaHelena are name variants. Distinct fromRouenI.',
 '00000058395':'InteriorChurch975.4.200(1855); sourceJohanBartholdJongkind and canonicalJohanJongkind identify the same maker and physical object.',
 '07290020397':'StRemyDieppe1923.1.47(1900); sourceWalterRichardSickert and canonicalWalterSickert. Primary biographical death1886 is erroneous and is not imported or validated.',
 '07290020416':'Grassini1842.3(1805); sourceLouiseElisabethVigeeLeBrun and canonicalElisabethVigeeLeBrun. The1806engraving mentioned in title is not this1805painting.',
 '07290021362':'HorseStudy1893.7(1891); sourceJeanLouisErnestMeissonier and canonicalErnestMeissonier, same exact notice and study.',
 '07290021847':'ScandinavianLandscape1850.2(1670); Allart/Allaertv anEverdingen spelling variant, same exact object.',
 '07290022457':'CleopatraAntony1907.1.64; sourceCharlesNatoire and canonicalCharlesJosephNatoire. This drawing study is not the related Nimescartoon or Gobelinstapestry. Primary1740(?) uncertainty retained in citation; date fields unchanged pending chronology review.',
 '07300000009':'SaintJerome1975.4.14; JanMassys/JanMatsys same maker, same notice and16thcenturyobject. Broad original century preserved.',
 '09940008604':'LandonWomanMG2003-5(1793); French/English title equivalents. Separate primary person reconciliation unifies oldLandon and canonicalLandon before this merge.',
 '00000104722':'HallaliPE399(1780); aux/dans and repeatedle are title variants.13September1776 in title is depicted event, not creation. SourceNicolasAnneDubois/duBoisdeBeauchesne same exact museum object.',
 '01370035091':'DufresnoyAllegory2006-4-1; same notice,title,maker,1650context. Canonicalcirca1650 preserved against placeholderexact1650; no invented precision.',
 '04450000125':'CourdouanZouaves865.1.1(1855); candidate title includes the creator prefix, same exactNarbonneobject. Related source duplicateQ139792095 stays held.',
 '09940005550':'LandonBourcetFamilyMG1388(1791); shortened title versus full title plus historical title. Sourcepersonalias separately reconciled first.',
 '00000077216':'SanteulPE638; sameChantillyportrait and17thcenturyquarter. CurrentCondeprimary identifiesLeChevalierDumee, oldPOP containsDUMKETCHEVALIERde transcription. ExactToussaintname remains review; reducedCarnavaletversion explicitly different and excluded.',
 '07290021368':'SunriseApolloRouen exactPOP07290021368 is an explicit candidate authority crosswalk; canonicalWikiinventory822.1.2 conflicts with primary1822.1.2. Preserve both original fields and cited discrepancy, not silently correct. Rouenstudy distinct fromVersaillesceilingMV8486 andMarseillestudy.',
 '04450000382':'MorereRabat2004.1.1; translated/prefixed title same exactobject. Primaryfirsthalf20c versus canonicalunknown stays documented; no automatic date fill. Distinct fromMarrakech2004.1.2.',
 '04450000383':'MorereMarrakech2004.1.2; titleprefixvariation same exactobject. Primaryfirsthalf20c versus canonicalunknown preserved. Distinct fromRabat2004.1.1.',
 '04400000569':'ThomireFabredEglantine985.13.1158(1793); source title adds sitterlife1750–1794, not creationdates or another portrait.',
 '01370026890':'LignierLaBascule2900bis(1891); primary additionally lists740historicalcataloguenumber. Canonical maininventory2900bis unchanged.'}

def plan():
 if (p.RUN/'plan.json').exists():return
 holds=json.loads((ORIGINAL/'holds.json').read_text());assert set(h['key'] for h in holds)==set(CONTEXT)
 entries=[];snapshots={t:{} for t in ('local','production')}
 for h in holds:
  oid=h['key'];primary=json.loads((ORIGINAL/'captures'/(oid+'.json')).read_text());assert CORE.sha((ORIGINAL/'captures'/(oid+'.html')).read_bytes())==primary['receipt']['sha256']
  e=dict(key=oid,canonical_slug=h['canonical_slug'],old_slug=h['old_slug'],primary=primary,institution_context=CONTEXT[oid]+' Every original assertion and asset remains on its original physical row; archive duplicate with redirect, preserve canonical review.',targets={})
  if oid=='00000077216':
   f=m.x.BASE/'france/primary-objects/followup/conde-santeul.html';receipt=json.loads(f.with_suffix('.receipt.json').read_text());assert CORE.sha(f.read_bytes())==receipt['sha256'];e['primary']['current_museum_followup']=receipt
  for target in snapshots:
   with m.m.r.base.connect(target=='production') as db,db.transaction():
    db.execute('SET TRANSACTION READ ONLY');p.a.ensure_schema(db);rows={r['slug']:r['id'] for r in db.execute('SELECT id::text,slug FROM artworks WHERE slug=ANY(%s)',([e['old_slug'],e['canonical_slug']],))};assert len(rows)==2
    old=rows[e['old_slug']];keep=rows[e['canonical_slug']];snap=p.a.snapshot(db,[old,keep]);works={r['id']:r for r in snap['artworks']};assert all(w['status']=='review' and w['published_at'] is None for w in works.values())
    creators=lambda aid:{(r['artist_id'],r['attribution_role']) for r in snap['artwork_artists'] if r['artwork_id']==aid};assert creators(old)<=creators(keep) and creators(keep),(oid,'unreconciledmaker')
    assert works[keep]['current_institution_id'] and works[keep]['accession_number'];assert not works[old]['primary_media_id']
    for table in ('artwork_places','curated_collection_items','artwork_media'):assert not any(r['artwork_id']==old for r in snap[table]),(oid,table)
    assert any(r['artwork_id']==keep and r['claim_type']=='holding' and r['review_state']=='accepted' and not r['superseded_by'] for r in snap['artwork_location_assertions'])
    # Both existing records must themselves cite this exact primary notice.
    for aid in (old,keep):assert any(r['entity_id']==aid and (r['source_url'] or '').rstrip('/').endswith('/'+oid) for r in snap['citations']),(oid,'missingprimarycrosswalk')
    if works[old]['current_institution_id'] and works[old]['current_institution_id']!=works[keep]['current_institution_id']:
     inst={r['slug'] for r in db.execute('SELECT slug FROM institutions WHERE id=ANY(%s::uuid[])',([works[old]['current_institution_id'],works[keep]['current_institution_id']],))};assert inst=={'joconde-m0729','musee-beaux-arts-rouen'} and 'Rouen' in primary['fields']['Lieu de conservation']
    common={r['scheme'] for r in snap['external_identifiers'] if r['entity_id']==old}&{r['scheme'] for r in snap['external_identifiers'] if r['entity_id']==keep};e['targets'][target]=dict(old_id=old,canonical_id=keep,preserve_archived_schemes=sorted(common),issues=[]);snapshots[target][oid]=snap
  fields=('slug','title','creation_year_start','creation_year_end','date_precision','status','accession_number','work_type')
  comparable=lambda t:[{k:w[k] for k in fields} for w in sorted(snapshots[t][oid]['artworks'],key=lambda w:w['slug'])]
  assert comparable('local')==comparable('production');entries.append(e)
 for t in snapshots:CORE.save_new(p.BACK/(t+'-preimages.json'),snapshots[t])
 CORE.save_new(p.RUN/'plan.json',entries);CORE.save_new(p.RUN/'manifest.json',dict(at=CORE.now(),plan_sha256=CORE.sha((p.RUN/'plan.json').read_bytes()),pairs=len(entries)));print('Individually reviewed POP plan',len(entries),flush=True)

if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('command',choices=['plan','apply','verify']);args=a.parse_args();(plan if args.command=='plan' else getattr(p,args.command))()
