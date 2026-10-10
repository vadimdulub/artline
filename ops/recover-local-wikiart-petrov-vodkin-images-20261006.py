#!/usr/bin/env python3
"""Nine existing Petrov-Vodkin gaps with explicit date/version alternatives."""
import argparse
import importlib.util
from pathlib import Path

s=importlib.util.spec_from_file_location('followup',Path(__file__).with_name('recover-local-wikiart-russian-followup-images-20261006.py'))
f=importlib.util.module_from_spec(s);s.loader.exec_module(f)
r,wiki,base,core=f.r,f.wiki,f.base,f.core
RUN=core.ROOT/'docs/research/local-wikiart-petrov-vodkin-images-20261006'
f.RUN=r.RUN=wiki.RUN=base.RUN=wiki.chicago.RUN=RUN
core.VERSION='local-wikiart-petrov-vodkin-physical-versions-v1'
f.IDS=['05826144-a9c0-4723-8567-16e9c34fc432','28bcba94-66a0-4740-9c58-45d4765713b1','7c586e7c-4902-4103-9e5d-1c10cb59bc81','808fe8e3-4eda-4da3-8996-6eb4bb165f74','9285f5e6-bf7e-4d10-a5f1-32757ebe1dfc','19a070d5-2f2a-483e-98c2-87f3a2bcecb7','87fac0c1-8a09-4118-9f6e-219f1224ae5f','86234326-3f7c-4451-98a3-25feceddcf90','9132051e-646d-4184-bc8a-1b7cfa5b374d']
f.MAX_SOURCE_OPTIONS=6
f.DATE_VARIANT_IDS=set(f.IDS)
f.SELECTION='Nine specific existing eligible Russian Museum gaps by Petrov-Vodkin. Explicitly compare all bounded same-title metadata leads, at most six per record, including source dates differing from the catalogue. Dates do not establish physical identity; each source/version requires current native evidence and direct visual review. No catalogue metadata changes or publication.'
r.ARTISTS['86814786-f2e1-4ad8-b893-f03b046439b6']=dict(qid='Q364226',native='petrov_vodkin_ks',label='Петров-Водкин К. С.',life='1878, Хвалынск Саратовской губ. – 1939, Ленинград',birth=1878,death=1939)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['snapshot','sources','research','prepare','apply','verify']);a=p.parse_args()
 if a.phase=='apply':base.apply()
 else:getattr(f,a.phase)()
