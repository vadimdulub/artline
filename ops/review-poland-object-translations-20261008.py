#!/usr/bin/env python3
"""Reviewed translation/version decisions; retain original catalogue metadata."""
import importlib.util
from pathlib import Path
s=importlib.util.spec_from_file_location('m',Path(__file__).with_name('import-poland-collections-20261008.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
folder=m.RUN/'poland';path=folder/'source-identity-crosswalk.json.gz'
original=folder/'source-identity-crosswalk-exact.json.gz'
assert not original.exists();path.rename(original);cross=m.load(original)
links={
 'warsaw/446665':'b46b910d-41e7-512d-96fa-81ab7729a722',
 'warsaw/446221':'0d5da395-0c59-5d36-b81d-74f2de2f382b',
 'warsaw/446753':'ef9f8c55-a6f6-58eb-b886-cca52a181cf6',
 'warsaw/446830':'d7318471-dc42-57b3-b491-e71a52916c16',
 'krakow/270807':'5751e1d1-6e50-5764-a435-03ea15fd1083',
 'krakow/368340':'ef250c0b-a08e-5f59-a957-763ca00109c7',
 'krakow/269717':'23171eb8-aa7a-528c-a18a-d7e0ba0cf853',
 'krakow/35369':'991b35f8-89b0-5e35-985c-2cf7f21307fb',
 'krakow/161479':'85dea941-bc48-53c9-842a-7bae3fad3955',
 'krakow/330685':'3335c1cd-e75d-5925-88a4-9177c6e3d14b',
 'krakow/161259':'b335f9a7-a7be-5758-9a34-8083f3d979ee',
 'wroclaw/wypadek-w-podrozy':'3c2d5df5-1aeb-56ed-8160-fcac2c817828',
 'lodz/46':'c5829a6c-3b9c-5c10-9ec6-a0370ae6e2d0',
 'lodz/262':'4d9cbe29-1b75-54a5-9914-a4c61d4c9314',
 'krakow/157417':'c9468bb3-37c4-5f33-af3c-05427d54c809',
}
holds={
 'warsaw/442453':'Holy Family titles may omit additional figures; existing physical version not securely distinguished.',
 'lodz/104':'Composition I versus generic Spatial Sculpture: multiple existing 1925 candidates; reconstruction/version identity unresolved.',
 'krakow/37432':'Repeated 1904 views of Kościuszko Mound require composition-level comparison.',
 'wroclaw/helenka':'Two existing 1900 child/Helenka portraits require composition-level comparison.',
 'lodz/18':'Numbered Composition III and generic Spatial Sculpture require version-level comparison.',
 'lodz/20':'Generic Composition versus descriptive Two Circles, Planes and Crosses requires image-level reconciliation.',
 'wroclaw/autoportret-1':'Generic self-portrait title/date candidate requires composition-level comparison.',
}
candidates={r['key']:r for r in m.load(folder/'translation-candidates.json')}
rows={r['provider']+'/'+r['source_id']:r for r in m.load(folder/'source-records.json.gz')}
with m.connect() as db:
 states=m.snapshot(db,list(links.values()))
 for key,aid in links.items():
  r=rows[key];a=states[aid]['artwork'];assert not a['accession_number']
  assert a['current_institution_id'] in [None,m.uid('museum/'+m.museums()[r['museum']][0]),'6c8ae01a-f6a5-5591-9635-a4af407cd2dc','05e061a0-727a-567f-bd69-a4a7af2174d6']
  assert key=='krakow/157417' or (r['year_start'],r['year_end'])==(a['creation_year_start'],a['creation_year_end'])
  basis='Reviewed Polish/English title translation, same creator, matching distinctive subject and creation date; numbered sculpture II remains distinct from I, III and IV. No conflicting accession or holding. Existing metadata retained.'
  if key=='krakow/157417':basis='Same Leonardo portrait of Cecilia Gallerani, Lady with an Ermine; museum circa 1490 is compatible with existing 1489–1490. Existing date range retained.'
  cross[key]=dict(verified_existing_id=aid,crosswalk_basis=basis,crosswalk_before=states[aid],crosswalk_editorial_confidence=.97)
 for key,reason in holds.items():cross[key]=dict(editorial_hold=reason,crosswalk_candidates=candidates.get(key,{}).get('matches',[]))
m.save(path,cross)
for p in [folder/'plan.json.gz',folder/'plan-pin.json',folder/'input-records.json.gz',m.BACKUP/'poland/plan-preimages.json.gz']:
 if p.exists():
  archive=p.parent/'draft-before-creators';archive.mkdir(exist_ok=True);assert not(archive/p.name).exists();p.rename(archive/p.name)
print('Reviewed links',len(links),'version holds',len(holds),flush=True)
