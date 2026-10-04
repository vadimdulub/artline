#!/usr/bin/env python3
"""Overlay the authorised release on the deployed 9b24873 source baseline."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT=Path(__file__).resolve().parents[1]
DEST=Path('/tmp/artline-womens-release-20260927')
RUN=ROOT/'docs/research/womens-rights-publication-20260927'
BASE='9b24873'
FILES=[
 'app/about/page.tsx','app/artists/page.tsx','app/layout.tsx','app/museums/page.tsx','app/museums/[slug]/page.tsx',
 'components/AllArtworkDrawer.tsx','components/ArtistChronologyRecord.tsx','components/ArtistRecord.tsx',
 'components/BookDrawer.tsx','components/CatalogueClient.tsx','components/EditorAccess.tsx','components/EventDrawer.tsx',
 'components/EventsIndex.tsx','components/EvidenceNote.tsx','components/MuseumDetail.tsx','components/MuseumDrawer.tsx',
 'components/MuseumsIndex.tsx','components/SiteHeader.tsx',
]

def replace(path,old,new):
    p=DEST/path;s=p.read_text();assert old in s,(path,old);p.write_text(s.replace(old,new))

def main():
    DEST.mkdir(parents=True,exist_ok=True)
    tar=subprocess.check_output(['git','archive',BASE,'apps/server','apps/web','ops'],cwd=ROOT)
    subprocess.run(['tar','-x','-C',str(DEST)],input=tar,check=True)
    for name in FILES:shutil.copy2(ROOT/'apps/web'/name,DEST/'apps/web'/name)
    preset=json.loads((ROOT/'docs/research/womens-rights-20260926/preset.json').read_text())
    remaps=json.loads((RUN/'audit-reconciled.json').read_text())['artwork_id_map']
    for section in ['related','context']:
        preset['focus'][section]['artwork']=[remaps.get(i,i) for i in preset['focus'][section]['artwork']]
    p=DEST/'apps/server/internal/atlas/presets.json';ps=json.loads(p.read_text());assert len(ps)==30
    ps.insert(next(i for i,v in enumerate(ps) if v['id']=='french-revolution'),preset)
    p.write_text(json.dumps(ps,ensure_ascii=False,indent=2)+'\n')
    replace('apps/server/internal/atlas/presets.go','type Preset struct {','type Preset struct {\n StartingHighlights *bool `json:"startingHighlights,omitempty"`')
    replace('apps/server/internal/atlas/presets.go','type PresetFocus struct {','type PresetFocus struct {\n SelectedBooks bool `json:"selectedBooks,omitempty"`')
    replace('apps/server/internal/atlas/preset_focus.go','kind == "event" && focus.SelectedEvents','(kind == "event" && focus.SelectedEvents || kind == "book" && focus.SelectedBooks)')
    replace('apps/server/internal/httpapi/atlas.go','highlights := q.Get("highlights")','highlights := q.Get("highlights")\n if highlights == "" {\n  if preset, ok := atlas.FindPreset(id); ok && preset.StartingHighlights != nil && !*preset.StartingHighlights { highlights = "false" }\n }')
    replace('apps/server/internal/atlas/atlas_test.go','30 historical lenses','31 historical lenses')
    replace('apps/server/internal/atlas/atlas_test.go','len(presets) != 30','len(presets) != 31')
    replace('apps/server/internal/atlas/preset_review_test.go','len(f.Countries)+len(f.Regions) == 0','len(f.Countries)+len(f.Regions)+len(f.Related["artwork"])+len(f.Context["artwork"]) == 0')
    replace('apps/server/internal/atlas/preset_review_test.go','missing regional scope','missing regional or explicitly selected artwork scope')
    replace('apps/web/lib/atlas.ts','startingCountries?: string[];','startingCountries?: string[]; startingHighlights?: boolean;')
    replace('apps/web/components/AllAtlas.tsx','highlights=params.get("highlights")!=="false"','highlights=params.has("highlights")?params.get("highlights")!=="false":(preset?.startingHighlights??true)')
    replace('apps/web/components/AllAtlas.tsx','...startingGeography(next,preset,params,starting),preset:', '...startingGeography(next,preset,params,starting),highlights:String(next?.startingHighlights??true),preset:')
    subprocess.run(['gofmt','-w',str(DEST/'apps/server/internal/atlas/presets.go'),str(DEST/'apps/server/internal/atlas/preset_focus.go'),str(DEST/'apps/server/internal/httpapi/atlas.go')],check=True)
    files={}
    for p in DEST.rglob('*'):
        if p.is_file() and not any(part in ('node_modules','.next') for part in p.parts) and p.name != 'tsconfig.tsbuildinfo':files[str(p.relative_to(DEST))]=hashlib.sha256(p.read_bytes()).hexdigest()
    RUN.mkdir(parents=True,exist_ok=True)
    (RUN/'release-source.json').write_text(json.dumps({'baseline':BASE,'directory':str(DEST),'web_overlays':FILES,'files':files},indent=2)+'\n')
    print('Pinned release source:',len(files),'files. Other 30 historical presets retained from deployed baseline.')

if __name__=='__main__':main()
