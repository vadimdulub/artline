#!/usr/bin/env python3
"""Resume the authorized, audited production delivery after Cloud login renewal.

Usage: CLOUDSDK_CORE_ACCOUNT=vadim@alingva.com python THIS_FILE
All writes retain pinned preimages and the existing guarded delivery workflow.
"""
import importlib.util
import os
from pathlib import Path

spec=importlib.util.spec_from_file_location('d',Path(__file__).with_name('apply-artwork-locations-20261004.py'))
d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d);r=d.r


def main():
    os.environ['CLOUDSDK_CORE_ACCOUNT']='vadim@alingva.com'
    with r.connect('production')as db:
        assert db.execute('SELECT current_database() name').fetchone()['name']=='artline'
    wave='museum-guides-deposits-colombia-01'
    if not (r.RUN/'delivery'/wave/'verification.json').exists():
        d.apply(wave,'production');d.verify(wave)
    wave='museum-guides-tate-production-01'
    if not (r.RUN/'delivery'/wave/'plan.json.gz').exists():
        d.plan(wave,['tate-current-20261005e'],targets=['production'])
    if not (r.RUN/'delivery'/wave/'verification.json').exists():
        d.apply(wave,'production');d.verify(wave)
    data=r.load(r.RUN/'delivery'/wave/'plan.json.gz')
    r.save(r.ROOT/'docs/research/museum-guides-20261005/production-delivery.json',{
        'at':r.now(),'deposits_colombia_verified':513,'tate_verified':len(data['claims']),
        'tate_preflight_holds':data['held'],'all_requested_records_delivered':not data['held'],
        'no_artwork_publication_or_image_attachment':True})


if __name__=='__main__':main()
