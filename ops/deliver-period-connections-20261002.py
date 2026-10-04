#!/usr/bin/env python3
"""Deliver the selected Timbuktu chronicle with exact production preimages."""
import argparse
import importlib.util
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('book_delivery', ROOT / 'ops/deliver-library-books-20261001.py')
workflow = importlib.util.module_from_spec(spec)
spec.loader.exec_module(workflow)
workflow.CAMPAIGNS = ['period-connections-20261002']
workflow.RESEARCH = ROOT / 'docs/research/period-connections-20261002/production'
workflow.RESEARCH.mkdir(parents=True, exist_ok=True)
workflow.PLAN = workflow.RESEARCH / 'books-plan.json'
workflow.BACKUP = Path('/Users/vadimdulub/Library/Application Support/Artline/backups/period-connections-20261002-production')
workflow.BACKUP.mkdir(parents=True, exist_ok=True)
workflow.CLOUD_BACKUP_ID = '1790963667418'
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['prepare', 'apply'])
    parser.add_argument('--sha256')
    args = parser.parse_args()
    if args.stage == 'prepare':
        workflow.prepare()
    else:
        if not args.sha256:
            parser.error('apply requires the reviewed plan SHA-256')
        workflow.apply(args.sha256)
