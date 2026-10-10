"""Retain strict live guards using the reviewed eight-image comparison refresh."""
import argparse
import importlib.util
from pathlib import Path

spec=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-larissa-apply-20261010.py'))
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
c,m,RUN=a.c,a.m,a.RUN
REFRESH=RUN/'production-identity-refresh-001.json.gz'

def reviewed_state():
    old=m.load(RUN/'production-identity-001.json.gz')['state'];new=m.load(REFRESH)
    for pin in new['old_references']:c.checked(pin)
    assert new['artwork_ids']==old['artwork_ids'] and new['creator_links']==old['creator_links']
    assert new['citations']==m.load(RUN/'production-identity-citations-001.json.gz')['citations'] and not new['added_citations']
    observation=m.load(RUN/'comparison-drift-observation-001.json')
    assert new['changes']==observation['changes'] and len(new['changes'])==8
    protected=set(m.load(RUN/'focused-comparators-001.json.gz')['ids'])|set(m.load(RUN/'production-initial-scope-001.json.gz')['scoped_ids'])|set(m.load(RUN/'baseline-verification-001.json')['prior_production_ids'])
    replacements={x['id']:x for x in new['changes']}
    for before,after in zip(old['artworks'],new['artworks']):
        if before!=after:
            change=replacements[before['id']]
            assert change['before']==before and change['after']==after and change['fields']==['primary_media_id']
            assert before['primary_media_id'] is None and after['primary_media_id'] and before['id'] not in protected
            assert {k:v for k,v in before.items() if k!='primary_media_id'}=={k:v for k,v in after.items() if k!='primary_media_id'}
    assert len(old['artworks'])==len(new['artworks'])==6086
    return new

def global_identity_unchanged(db):
    state=reviewed_state();ids=state['artwork_ids']
    current=db.execute('SELECT '+a.identity.ARTCOLS+' FROM artworks a WHERE a.id=ANY(%s::uuid[]) ORDER BY a.id',(ids,)).fetchall();assert current==state['artworks'],'Comparison artwork metadata changed after reviewed refresh'
    links=db.execute('SELECT aa.artwork_id::text,aa.artist_id::text,aa.attribution_role,ar.display_name FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=ANY(%s::uuid[]) ORDER BY aa.artwork_id,aa.artist_id,aa.attribution_role',(ids,)).fetchall();assert links==state['creator_links']
    cites=[v['row'] for v in db.execute("SELECT to_jsonb(x) row FROM citations x WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id",(ids,))];assert cites==state['citations']
    titles=m.load(RUN/'production-identity-001.json.gz')['params']['titles'];current_ids={v['id'] for v in db.execute('SELECT id::text FROM artworks WHERE normalized_title=ANY(%s)',(titles,))};assert current_ids<=set(ids),'Unreviewed exact-title candidate appeared'
    review=m.load(a.REVIEW);units=review['records']+review['holdings'];urls=sorted({u for v in units for u in v['facts']['source_urls']+v['facts']['native_urls']});sids=sorted({x for v in units for x in v['facts']['source_ids']})
    assert not db.execute("SELECT 1 FROM external_identifiers WHERE entity_type='artwork' AND (canonical_url=ANY(%s) OR (scheme='searchculture-edm' AND external_id=ANY(%s))) LIMIT 1",(urls,sids)).fetchone()
    assert not db.execute("SELECT 1 FROM citations WHERE entity_type='artwork' AND (source_url=ANY(%s) OR (source_record_id=ANY(%s) AND source_url LIKE 'https://www.searchculture.gr/%%')) LIMIT 1",(urls,sids)).fetchone()

a.global_identity_unchanged=global_identity_unchanged

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['prepare','apply']);parser.add_argument('--plan-sha');args=parser.parse_args()
    if args.command=='prepare':a.prepare()
    else:assert args.plan_sha;a.apply(args.plan_sha)
