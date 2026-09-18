#!/usr/bin/env python3
"""Four exact museum-object pairs after verified creator reconciliation."""
import argparse,importlib.util
from pathlib import Path
s=importlib.util.spec_from_file_location('c',Path(__file__).with_name('consolidate-overnight-fng-cross-country.py'));c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
c.ROOT=c.m.x.BASE/'duplicates/fng-after-person-objects';c.REVIEWED={'Q20795908','Q20792018','Q20798145','Q20780007'}
original=c.configure
def configure(target):
 original(target);c.p.BACK=c.m.BACKUPS/'fng-after-person-objects'/target;c.p.SOURCE='overnight-fng-after-person-physical-identity-20260913'
c.configure=configure
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['plan','apply','verify']);p.add_argument('--target',choices=['local','production'],required=True);a=p.parse_args();configure(a.target)
 if a.command=='plan':
  assert (c.m.x.BASE/'duplicates/fng-person-consolidation'/a.target/('verification-'+a.target+'.json')).exists();c.plan(a.target)
 else:getattr(c.p,a.command)(targets=(a.target,))
