#!/usr/bin/env python3
"""Extend Detroit identity searches to named schools ending in 'School'."""
import argparse,importlib.util,re
from pathlib import Path
s=importlib.util.spec_from_file_location('v',Path(__file__).with_name('museum-expansion-detroit-identity-20261007.py'));v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
oldterms=v.terms
def terms(facts):
 out=set(oldterms(facts))
 for label in [facts.get('creator_label'),facts.get('detail_creator_label')]+facts.get('identity_creator_labels',[]):
  if label and re.search(r'\bStroganov\b',label,re.I):out.add('stroganov')
 return sorted(out)
v.i.search_terms=terms
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--suffix',required=True);a=p.parse_args();assert re.fullmatch(r'\d{3}',a.suffix)
 v.main(a.suffix)
 path=v.RUN/('native-identity-'+a.suffix+'.json.gz');x=v.m.load(path)
 v.m.save(v.RUN/('identity-extension-'+a.suffix+'.json'),dict(at=v.m.now(),identity_reference=v.ref(path),extension_reference=v.ref(Path(__file__).resolve()),prior_query_reference=v.ref(Path(v.__file__).resolve()),policy='This fresh identity scope additionally searches the named Stroganov school. The original preliminary scope remains unchanged. No database writes.'))
