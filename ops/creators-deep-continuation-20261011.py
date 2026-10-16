#!/usr/bin/env python3
"""Continue the approved creator workflow without rewriting the completed pass."""
import argparse, importlib.util
from pathlib import Path
sp=importlib.util.spec_from_file_location('previous_campaign',Path(__file__).with_name('creators-deep-4h-20261010.py'))
driver=importlib.util.module_from_spec(sp);sp.loader.exec_module(driver)
driver.CAMPAIGN='creators-deep-continuation-20261011'
driver.BASE=driver.ROOT/'docs/research'/driver.CAMPAIGN
driver.RECOVERY=Path.home()/'Library/Application Support/Artline/backups'/driver.CAMPAIGN
driver.ORIGINALS=Path.home()/'Library/Application Support/Artline/source-images'/driver.CAMPAIGN
driver.START='2026-10-11T06:07:06Z';driver.DEADLINE=None;driver.RUN=driver.BASE
def __getattr__(name):return getattr(driver,name)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command');p.add_argument('--creator');a=p.parse_args()
 if a.creator:driver.configure(a.creator)
 assert a.command in ['research','prepare_images','upload_images','attach_images','verify_images','verify_catalogue','attach_research','checkpoint','preflight','apply','backup']
 if a.command in ['preflight','apply','backup']:getattr(driver.c,a.command)()
 else:getattr(driver,a.command)()
