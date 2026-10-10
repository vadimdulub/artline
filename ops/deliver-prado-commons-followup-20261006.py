#!/usr/bin/env python3
"""Independently licensed Prado original-gap follow-up, using the audited delivery adapter."""
import argparse,importlib.util
from pathlib import Path
s=importlib.util.spec_from_file_location('delivery',Path(__file__).with_name('deliver-prado-expansion-commons-20261006.py'))
d=importlib.util.module_from_spec(s);s.loader.exec_module(d)
d.OP='prado-commons-followup-20261006'
d.m.RUN=d.m.m.RUN/'images/commons-followup'
d.RUN=d.m.RUN/'delivery'
d.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/d.OP
d.ORIGINALS=Path.home()/'Library/Application Support/Artline/source-images'/d.OP
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','sheets','plan','upload','apply']);getattr(d,p.parse_args().command)()
