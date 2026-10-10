#!/usr/bin/env python3
"""Verify public artist artwork routes; preserve museum member-access results."""
import importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('v',Path(__file__).with_name('verify-random-country-collections-20261010.py'));v=importlib.util.module_from_spec(s);s.loader.exec_module(v);m=v.m
old=m.load(m.RUN/'verification.json');checked=m.load(m.RUN/'database-verification.json.gz');states=checked['states'];records=[r for c in ('BE','LV','HR') for r in m.pinned(c)[0]['records']]
selected=[]
for iid in checked['institutions']:
 works=[r for r in records if r['institution_id']==iid and states[r['artwork_id']]['creators']]
 selected.append(next((r for r in works if states[r['artwork_id']]['artwork']['primary_media_id']),works[0]))
artist_ids={states[r['artwork_id']]['creators'][0]['artist_id'] for r in selected}
with m.connect() as db:artists={x['id']:x for x in db.execute('SELECT id::text,slug,display_name FROM artists WHERE id=ANY(%s::uuid[])',(list(artist_ids),))}
checks=[]
for r in selected:
 aid=r['artwork_id'];st=states[aid];artist=artists[st['creators'][0]['artist_id']];url='https://artlines.org/api/backend/v1/artists/'+artist['slug']+'/works/'+aid
 cache=m.RUN/'public-artist-artwork-checks'/(aid+'.json')
 if cache.exists():out=m.load(cache)
 else:
  response=v.public_get(url,timeout=45);out=dict(artwork_id=aid,institution=r['museum'],url=url,status=response.status_code,at=m.now(),verified=False)
  if response.ok:
   x=response.json();assert x['title']==st['artwork']['title'],(aid,x['title']);out.update(title=x['title'],media_url=x.get('media_url'),verified=True)
   if st['artwork']['primary_media_id']:
    media=next(z for z in st['media'] if z['id']==st['artwork']['primary_media_id']) if 'media' in st else None
    if media:assert x['media_url']==media['storage_path']
    receipt=m.RUN/'BE/images'/(aid+'.json')
    if receipt.exists():assert x['media_url']==m.load(receipt)['path']
  else:out['error']=response.text[:200]
  m.save(cache,out)
 checks.append(out);print('Public artwork',r['museum'],out['verified'],flush=True)
assert all(x['verified'] for x in checks),'Public artwork check failed; inspect retained evidence'
# Keep original observations; these routes now deliberately require member login.
assert all(x.get('status')==401 for x in old['public_artwork_checks'])
assert all('401 Client Error' in x.get('error','') for x in old['country_browse_checks'])
revision=dict(old,at=m.now(),public_artist_artwork_checks=checks,expected_member_access_checks=old['public_artwork_checks']+old['country_browse_checks'],public_api_failures=[x for x in old['public_artist_checks']+checks if not x['verified']],member_browse_content_verified=False,access_policy_note='AGENTS.md Member access and bookmarks (10 October 2026): museum browsing requires login. Museum HTTP 401 outcomes are expected signed-out access checks, not import failures. Content verified in production database; artist artwork routes verified publicly.')
archive=m.RUN/'verification-before-access-policy-reconciliation.json';assert not archive.exists();(m.RUN/'verification.json').rename(archive);m.save(m.RUN/'verification.json',revision)
print('Public artist artwork checks passed',len(checks),'expected museum member gates',len(revision['expected_member_access_checks']),flush=True)
