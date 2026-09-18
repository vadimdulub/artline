#!/usr/bin/env python3
"""Archive this bounded research pass and verify every archived member."""
import importlib.util,json,tarfile,hashlib
from pathlib import Path
spec=importlib.util.spec_from_file_location('b',Path(__file__).with_name('research-armenian-georgian-artworks.py'));b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
s=b.s;files={}
for p in s.RUN.rglob('*'):
 if p.is_file() and p.name not in ('completion-archive.json','completion-manifest.json'):files[str(p.relative_to(s.ROOT))]=p
for p in (s.BACKUP/'selected-originals').rglob('*'):
 if p.is_file():files['selected-originals/'+str(p.relative_to(s.BACKUP/'selected-originals'))]=p
plan=json.loads((s.RUN/'batches/batch-001.json').read_bytes())
for x in plan['entries']:
 if x['image']:
  p=s.ROOT/'apps/web/public'/x['image']['path'].lstrip('/');files[str(p.relative_to(s.ROOT))]=p
names=['research-armenian-georgian-session.py','research-armenian-georgian-artworks.py','research-caucasus-priorities.py','select-armenian-georgian-artworks.py','prepare-armenian-georgian-images.py','refine-armenian-georgian-records.py','verify-caucasus-preparation.py','apply-armenian-georgian-artworks.py','apply-caucasus-artist-evidence.py','reconcile-caucasus-batch-links.py','attach-caucasus-primary-citations.py','verify-armenian-georgian-session.py','apply-women-evidence.py','archive-caucasus-session.py','research-wikimedia-catalogues.py','prepare-wikimedia-catalogue-images.py','apply-russian-deep-images.py','research-russian-deep-images.py','resolve-danish-russian-images.py','import-michelangelo-frescoes.py','enrich-artwork-images.py']
for name in names:files['ops/'+name]=s.ROOT/'ops'/name
paths=['apps/server/db/migrations/0019_artist_gender_evidence.sql','apps/server/internal/catalog/timeline.go','apps/server/internal/catalog/types.go','apps/server/internal/catalog/repository.go','apps/server/internal/catalog/painter_options.go','apps/server/internal/catalog/timeline_readonly_test.go','apps/server/internal/catalog/women_readonly_test.go','apps/server/internal/httpapi/filters.go','apps/server/internal/httpapi/router.go','apps/server/internal/httpapi/painter_options.go','apps/server/internal/httpapi/women_filter_test.go','apps/web/components/TimelineExplorer.tsx','apps/web/components/use-painter-choices.ts','apps/web/lib/url-state.ts','apps/web/lib/types.ts','apps/web/lib/__tests__/url-state.test.ts','apps/web/e2e/women-artists.spec.ts','apps/web/app/globals.css','docs/LOCAL_DATA_LOCATIONS.md']
for name in paths:files[name]=s.ROOT/name
entries=[{'path':name,'bytes':p.stat().st_size,'sha256':s.core.sha(p.read_bytes())} for name,p in sorted(files.items())];manifest=s.RUN/'completion-manifest.json';s.save(manifest,{'at':s.core.now(),'files':entries,'note':'Pre-mutation database dump remains separate at the path and checksum recorded in backups.json. Manifest excludes its own recursive checksum and the completion archive receipt.'});files[str(manifest.relative_to(s.ROOT))]=manifest;expected={x['path']:x['sha256'] for x in entries};expected[str(manifest.relative_to(s.ROOT))]=s.core.sha(manifest.read_bytes())
archive=s.BACKUP/'completed-armenian-georgian-women.tar.gz';assert not archive.exists()
with tarfile.open(archive,'w:gz',compresslevel=6) as tar:
 for name,p in sorted(files.items()):tar.add(p,arcname=name,recursive=False)
verified=0
with tarfile.open(archive,'r:gz') as tar:
 for member in tar:
  assert member.isfile() and member.name in expected
  digest=hashlib.sha256(tar.extractfile(member).read()).hexdigest();assert digest==expected[member.name];verified+=1
assert verified==len(files)
s.save(s.RUN/'completion-archive.json',{'at':s.core.now(),'path':str(archive),'bytes':archive.stat().st_size,'sha256':s.core.sha(archive.read_bytes()),'verified_members':verified,'includes':'Research evidence, original selected reproductions, all 38 served image assets, source scripts and feature code snapshots. Separate local dump and Cloud SQL backup are referenced by backups.json.'});print('Completion archive verified',verified,'files',archive.stat().st_size,'bytes',flush=True)
