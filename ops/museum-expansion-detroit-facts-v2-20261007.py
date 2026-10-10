#!/usr/bin/env python3
"""Preserve Detroit source facts while flagging creation ranges matching artist lifespans."""
import argparse,importlib.util,re
from pathlib import Path
s=importlib.util.spec_from_file_location('v',Path(__file__).with_name('museum-expansion-detroit-facts-20261007.py'));v=importlib.util.module_from_spec(s);s.loader.exec_module(v);original_parse=v.parse
def parse(path):
 row=original_parse(path);f=row['facts'];life=next(x['value'] for x in f['source_fields'] if x['label']=='Life Dates');years=[int(x) for x in re.findall(r'(?<!\d)\d{3,4}(?!\d)',life)]
 if len(years)==2 and years[1]-years[0]>=10 and (f['first'],f['last'])==tuple(years):
  row['review_flags']=sorted(set(row['review_flags'])|{'creation_range_matches_creator_lifespan'})
 row['parser_extension_reference']=v.ref(Path(__file__).resolve());return row
v.parse=parse
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--suffix',required=True);a=p.parse_args();assert re.fullmatch(r'\d{3}',a.suffix);v.main(a.suffix)
