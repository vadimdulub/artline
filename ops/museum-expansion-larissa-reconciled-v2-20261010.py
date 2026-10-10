"""Bind the reviewed comparison refresh to the schema-correct album writer."""
import argparse
import importlib.util
from pathlib import Path

def module(name,file):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value

b=module('b','museum-expansion-larissa-reconciled-20261010.py')
a=module('a','museum-expansion-larissa-apply-v2-20261010.py')
c,m,RUN=a.c,a.m,a.RUN
a.global_identity_unchanged=b.global_identity_unchanged

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['prepare','apply']);parser.add_argument('--plan-sha');args=parser.parse_args()
    if args.command=='prepare':a.prepare()
    else:assert args.plan_sha;a.apply(args.plan_sha)
