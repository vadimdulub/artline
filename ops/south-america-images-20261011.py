#!/usr/bin/env python3
"""Deliver only selected, approved, exactly matched South American images."""
import argparse,importlib.util
from pathlib import Path
s=importlib.util.spec_from_file_location('campaign',Path(__file__).with_name('south-america-1000-20261011.py'));c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
i=c.module('sa_image_delivery','images-switzerland-southern-cone-20261011.py');i.m=c.d;i.ARCHIVE=Path.home()/'Library/Application Support/Artline/source-images'/c.OP
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['select','prepare','sheets','upload','attach']);p.add_argument('phase');a=p.parse_args();getattr(i,a.action)(a.phase)
