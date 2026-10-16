"""Translate artist-guide prose; preserve object/source identities and record source hashes."""
import concurrent.futures
import importlib.util
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('museum_translation',ROOT/'ops/translate-guide-expansion-20261011.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
m.RUN=ROOT/'docs/research/women-artist-guides-20261011'
m.STAGE=Path('/tmp/artline-women-guides-20261011/editions')
m.CACHE=m.RUN/'translations';m.CACHE.mkdir(exist_ok=True)
def one(pair):
 result=m.one(pair)
 slug,locale=pair;src=m.load(m.STAGE/slug/'en.json');p=m.STAGE/slug/(locale+'.json');g=m.load(p)
 keys=['contextNote','visit','website','officialGuide','updated']
 values=m.translate([src['labels'][key]for key in keys]+[src['artist']['lifeDates']],locale)
 for k,v in zip(keys,values):g['labels'][k]=m.plain(v)
 g['artist']['lifeDates']=m.plain(values[-1])
 # The word "guide" refers to this publication, never a current exhibition.
 if locale=='ja':
  for field in ['introduction','selectionNote','visitNote']:g[field]=g[field].replace('本展','本ガイド')
 m.save(p,g)
 return result
if __name__=='__main__':
 slugs=['artemisia-gentileschi','mary-cassatt','frida-kahlo']
 with concurrent.futures.ThreadPoolExecutor(max_workers=3)as ex:
  for result in ex.map(one,[(s,l)for s in slugs for l in m.LOCALES]):print(json.dumps(result),flush=True)
