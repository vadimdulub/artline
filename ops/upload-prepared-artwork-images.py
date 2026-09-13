#!/usr/bin/env python3
"""Upload immutable prepared receipts while a separate source worker runs.

This consumer cannot request museum metadata or images. It only processes
fully flushed prepared events, and never claims the producer's future IDs.
"""
import argparse
import collections
import importlib.util
import json
import os
from pathlib import Path
import time
from types import SimpleNamespace

spec = importlib.util.spec_from_file_location('enrichment', Path(__file__).with_name('enrich-artwork-images.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--producer-pid', type=int, required=True)
    args = parser.parse_args()
    candidates = {c['artwork_id']:c for c in json.loads((args.run / 'candidates.json').read_bytes())['candidates']}
    dsn = module.cloud_dsn()
    while True:
        latest = {}
        for line in (args.run / 'events.jsonl').read_text().splitlines(keepends=True):
            if not line.endswith('\n'):
                continue
            event = json.loads(line)
            if event.get('artwork_id'):
                latest[event['artwork_id']] = event
        grouped = collections.defaultdict(list)
        for key, event in latest.items():
            if event['outcome'] == 'prepared':
                grouped[candidates[key]['provider']].append(candidates[key])
        for provider, rows in grouped.items():
            print(module.now(), 'Uploading prepared', provider, min(len(rows),200), flush=True)
            failed_before = module.COUNTS[provider + ':failed']
            module.worker(provider, rows[:200], SimpleNamespace(run=args.run,upload_prepared_only=True), dsn)
            if module.COUNTS[provider + ':failed'] > failed_before:
                raise SystemExit('Upload paused after a failed attachment; inspect the saved receipts before resuming')
        try:
            os.kill(args.producer_pid, 0)
            live = True
        except ProcessLookupError:
            live = False
        if not live and not grouped:
            print(module.now(), 'Producer ended; no prepared events remain', dict(module.COUNTS), flush=True)
            return
        print(module.now(), 'producer_live', live, dict(module.COUNTS), flush=True)
        time.sleep(10 if grouped else 30)


if __name__ == '__main__':
    main()
