#!/usr/bin/env python3
"""Read-only parity and provenance audit for this round's selected artwork facts."""
import argparse,collections,importlib.util,json
from pathlib import Path
import psycopg
from psycopg.rows import dict_row

s=importlib.util.spec_from_file_location('core',Path(__file__).with_name('enrich-artwork-images.py'));core=importlib.util.module_from_spec(s);s.loader.exec_module(core)
BATCHES={'nga-new-metadata':('european-nga-object','national-gallery-of-art','followup-nga-selected-primary-20260916'),
 'nga-original-date-metadata':('european-nga-object','national-gallery-of-art','followup-nga-original-artwork-dates-20260916'),
 'nationalmuseum':('nationalmuseum-object','nationalmuseum-stockholm','followup-nationalmuseum-current-20260916'),
 'nationalmuseum-native-creators':('nationalmuseum-object','nationalmuseum-stockholm','followup-nationalmuseum-current-20260916')}

def main():
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();expected={};counts=collections.Counter();errors=[]
    for batch,(scheme,institution,source) in BATCHES.items():
        path=a.run/batch/'plan.json';data=json.loads(path.read_text());assert core.sha(path.read_bytes())==json.loads((path.parent/'plan-manifest.json').read_text())['sha256']
        for r in data['records']:
            key=(scheme,r['external_id']);assert key not in expected
            targets={t:r['targets'][t]['artwork_id'] if 'targets' in r else r['artwork_id'] for t in ('local','cloud')}
            mode=r['targets']['local']['mode'] if 'targets' in r else 'new';counts[mode]+=1
            expected[key]=dict(r,scheme=scheme,institution=institution,source_slug=source,batch=batch,ids=targets,mode=mode)
    results={};snapshots={}
    for target,dsn in [('local','postgres://localhost/artline'),('cloud',core.cloud_dsn())]:
        ids=[r['ids'][target] for r in expected.values()];by_id={r['ids'][target]:r for r in expected.values()};found={};country=collections.Counter();missing_country=0
        with psycopg.connect(dsn,autocommit=True,row_factory=dict_row,options='-c default_transaction_read_only=on') as db:
            for start in range(0,len(ids),300):
                rows=db.execute("""SELECT a.id::text,a.title,a.accession_number,a.date_display,a.creation_year_start,a.creation_year_end,a.date_precision,a.work_type,a.medium_text,a.status,a.published_at,a.research_candidate,
                    artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision) scope,artline_has_selection_evidence(a.id) selected,
                    i.slug institution,coalesce(p.country_code,vc.country_code) institution_country,
                    ARRAY(SELECT ar.slug FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=a.id ORDER BY ar.slug) artist_slugs,
                    ARRAY(SELECT ar.display_name FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=a.id ORDER BY ar.slug) artist_names,
                    ARRAY(SELECT DISTINCT ac.country_code FROM artwork_artists aa JOIN artist_countries ac ON ac.artist_id=aa.artist_id WHERE aa.artwork_id=a.id ORDER BY ac.country_code) artist_countries,
                    ARRAY(SELECT e.scheme||':'||e.external_id FROM external_identifiers e WHERE e.entity_type='artwork' AND e.entity_id=a.id) identifiers,
                    ARRAY(SELECT DISTINCT s.slug FROM citations c JOIN sources s ON s.id=c.source_id WHERE c.entity_type='artwork' AND c.entity_id=a.id AND c.field_name='official_object_identity') identity_sources
                    FROM artworks a LEFT JOIN institutions i ON i.id=a.current_institution_id LEFT JOIN places p ON p.id=i.place_id
                    LEFT JOIN LATERAL(SELECT min(vp.country_code) country_code FROM institution_venues v JOIN places vp ON vp.id=v.place_id WHERE v.institution_id=i.id HAVING count(DISTINCT vp.country_code)=1 AND bool_and(vp.country_code IS NOT NULL)) vc ON true
                    WHERE a.id=ANY(%s::uuid[])""",(ids[start:start+300],)).fetchall()
                for row in rows:
                    r=by_id[row['id']];key=r['scheme']+':'+r['external_id']
                    try:
                        for f in ('title','accession_number','date_display','creation_year_start','creation_year_end','date_precision','work_type'):assert row[f]==r[f],f+' differs'
                        assert row['status']=='review' and row['published_at'] is None and row['scope']=='eligible' and row['selected'],'Review, scope or holding differs'
                        assert r['mode']!='new' or row['research_candidate'],'New research record is not flagged'
                        assert row['institution']==r['institution'] and row['institution_country']==('US' if r['scheme']=='european-nga-object' else 'SE'),'Institution country differs'
                        assert row['artist_slugs']==[r['artist_slug']] and row['artist_names']==[r['artist']],'Creator differs'
                        assert key in row['identifiers'] and r['source_slug'] in row['identity_sources'],'Native identity or official citation missing'
                        row.pop('id');row.pop('identifiers');row.pop('identity_sources');found[key]=row;country[row['institution_country']]+=1;missing_country+=not bool(row['artist_countries'])
                    except AssertionError as exc:errors.append({'target':target,'source_object':key,'error':str(exc)})
            artist_total=db.execute("SELECT count(*) n FROM artists WHERE status='review'").fetchone()['n']
        for key in expected:
            label=key[0]+':'+key[1]
            if label not in found and not any(e.get('source_object')==label and e['target']==target for e in errors):errors.append({'target':target,'source_object':label,'error':'Expected artwork absent'})
        snapshots[target]=found;results[target]={'verified':len(found),'holding_countries':country,'artworks_with_unmapped_existing_artist_country':missing_country,'review_artists_total':artist_total}
    for key in snapshots['local'].keys()&snapshots['cloud'].keys():
        if snapshots['local'][key]!=snapshots['cloud'][key]:errors.append({'target':'parity','source_object':key,'error':'Local and production facts or artist countries differ'})
    report={'at':core.now(),'metadata_records_expected':len(expected),'matching_metadata_records':len(snapshots['local'].keys()&snapshots['cloud'].keys()),'counts':counts,'targets':results,'errors':errors,'new_artists':0,
        'notes':'Current selected facts, exact source identifiers, review status, holding country and existing artist-country parity checked read-only. Country of the institution is not an inferred artist nationality. No artist biography or country was changed.'}
    core.save_new(a.output,report);summary={k:v for k,v in report.items() if k!='errors'};summary['error_counts']=dict(collections.Counter(e['error'] for e in errors));summary['error_examples']=errors[:5];print(json.dumps(summary,ensure_ascii=False,indent=2));raise SystemExit(bool(errors))

if __name__=='__main__':main()
