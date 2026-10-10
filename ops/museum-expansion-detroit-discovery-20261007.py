#!/usr/bin/env python3
"""Bounded official Detroit catalogue discovery and read-only museum scope."""
import argparse,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('d',Path(__file__).with_name('museum-expansion-ago-discovery-20261007.py'));d=importlib.util.module_from_spec(s);s.loader.exec_module(d);m=d.m;n=d.n;ref=d.ref
IID='872a1711-593a-5fe0-9446-8f9265373004';RUN=m.RUN/'native/detroit';BASE='https://dia.org';n.SITES['detroit']=BASE
def scope():d.scope('detroit',IID)
def sources():
 x=d.d.capture_page('detroit',BASE+'/collection',RUN/'collection-context-001.json.gz')
 if not x.get('error'):print(json.dumps([r for r in x['links'] if '/collection' in r['url']][:45]),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['scope','sources']);a=p.parse_args();globals()[a.command]()
