#!/usr/bin/env python3
"""Read-only Portuguese identity preview; never substitutes for both-DB plans."""
import collections,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('e',Path(__file__).with_name('export-overnight-research-handoff.py'));e=importlib.util.module_from_spec(s);s.loader.exec_module(e)
m=e.m;BASE=e.BASE;CORE=e.CORE;OUT=BASE/'chatgpt-handoff/final-20260914'
def main():
 rows=[]
 with m.m.r.base.connect(False) as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY');db.execute("SET LOCAL statement_timeout='120s'");matcher=m.f.Matcher(m.artist_inventory(db))
  for n in range(1,21):
   folder=BASE/'portugal/PT'/f'round-{n:02d}'/'delivery';qa=json.loads((folder/'quality-review.json').read_text())
   for path in sorted((folder/'ready').glob('*.json')):
    item=json.loads(path.read_text());r=item['record'];q=r['qid'];review=qa.get('held_records',{}).get(q);resolved,reason=m.resolve(r,matcher);artist=(resolved or {}).get('artist');reason=review or reason
    if artist and artist['countries'] and 'PT' not in artist['countries']:reason=reason or 'existing_country_context_requires_review'
    authorities=db.execute("SELECT w.slug,w.title,w.status FROM external_identifiers e JOIN artworks w ON w.id=e.entity_id WHERE e.entity_type='artwork' AND e.scheme='wikidata' AND e.external_id=%s",(q,)).fetchall()
    institutions=db.execute('SELECT id::text,slug,name FROM institutions WHERE slug=ANY(%s)',(r['collection'].get('related_institution_slugs',[r['collection']['institution']['slug']]),)).fetchall();acc=r.get('accession');objects=[]
    if acc and institutions:
     objects=db.execute("SELECT w.slug,w.title,w.status,w.accession_number FROM artworks w WHERE w.current_institution_id=ANY(%s::uuid[]) AND upper(regexp_replace(translate(w.accession_number,'ΒΧΜ','BXM'),'\\s','','g'))=%s LIMIT 6",([i['id'] for i in institutions],m.m.accession_key(acc))).fetchall()
    incomplete=[]
    if artist and acc:
     incomplete=db.execute("SELECT w.slug,w.title,w.status,w.accession_number FROM artwork_artists aa JOIN artworks w ON w.id=aa.artwork_id WHERE aa.artist_id=%s AND w.current_institution_id IS NULL AND w.status<>'archived' AND upper(regexp_replace(translate(w.accession_number,'ΒΧΜ','BXM'),'\\s','','g'))=%s LIMIT 6",(artist['id'],m.m.accession_key(acc))).fetchall()
    urls=m.vetted_object_urls(r);primary=r.get('primary_museum_review')
    if primary:urls.update(u for k,u in primary['receipt'].items() if k in ('url','final_url','original_source_url') and u)
    source_matches=db.execute("SELECT DISTINCT w.slug,w.title,w.status FROM citations c JOIN artworks w ON c.entity_type='artwork' AND w.id=c.entity_id WHERE c.source_url=ANY(%s) AND w.status<>'archived'",(sorted(urls),)).fetchall()
    known=authorities+objects+incomplete+source_matches
    state='held_for_source_or_creator_review' if reason else 'existing_object_evidence_requires_plan' if known else 'potential_new_object_pending_full_two_database_plan'
    rows.append(dict(round=n,artwork_wikidata=q,title=r['title'],creator_wikidata=r['creator_qid'],creator_name=r['creator_label'],existing_local_artist_slug=artist['slug'] if artist else None,creator_resolution_basis=(resolved or {}).get('basis'),existing_creator_countries=artist['countries'] if artist else [],preview_state=state,hold_reason=reason,exact_wikidata_matches=authorities,institution_accession_matches=objects,creator_accession_without_institution=incomplete,exact_source_url_matches=source_matches,accession_number=acc,primary_source_url=primary['receipt'].get('final_url') or primary['receipt'].get('url') if primary else None,scope='Read-only local preview. Production identity, attribution, dates, image rights and all pending guards still require the normal fresh application plan. No database/image upload performed.'))
 out=e.CSV(OUT,'portugal_local_identity_preview',list(rows[0]))
 for row in rows:out.add(row)
 result=dict(at=CORE.now(),records=len(rows),counts=dict(collections.Counter(r['preview_state'] for r in rows)),creator_profiles_matched=len({r['existing_local_artist_slug'] for r in rows if r['existing_local_artist_slug']}),csv=out.finish(),policy='Read-only preview only; no inferred production IDs, no import approval or mutation.');CORE.save_new(OUT/'portugal-local-preview-manifest.json',result);print('Portuguese local identity preview',result['counts'],flush=True)
if __name__=='__main__':main()
