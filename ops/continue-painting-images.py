#!/usr/bin/env python3
"""Start a disjoint painting batch after each museum finishes its earlier IDs.

One worker per museum across both campaigns. Completion is established from
terminal per-artwork outcomes, never from an expired observation timeout.
"""
import argparse
import collections
import concurrent.futures
import importlib.util
import json
import os
from pathlib import Path
import time
from types import SimpleNamespace

spec = importlib.util.spec_from_file_location('enrichment', Path(__file__).with_name('enrich-artwork-images.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def terminal_ids(run):
    latest = {}
    path = run / 'events.jsonl'
    if not path.exists():
        return set()
    for line in path.read_text().splitlines(keepends=True):
        if not line.endswith('\n'):
            continue  # A writer may still be flushing the final line.
        row = json.loads(line)
        if row.get('artwork_id'):
            latest[row['artwork_id']] = row
    return {key for key, row in latest.items()
            if row['outcome'] in ('complete', 'failed') or
            (row['outcome'] == 'no_explicit_open_image' and row.get('adapter_version') == module.VERSION)}


def pending_candidates(run, provider):
    rows = json.loads((run / 'candidates.json').read_bytes())['candidates']
    latest = {}
    if (run / 'events.jsonl').exists():
        for line in (run / 'events.jsonl').read_text().splitlines():
            event = json.loads(line)
            if event.get('artwork_id'):
                latest[event['artwork_id']] = event
    return [c for c in rows if c['provider'] == provider and not (
        latest.get(c['artwork_id'], {}).get('outcome') == 'complete' or
        (latest.get(c['artwork_id'], {}).get('outcome') == 'no_explicit_open_image' and
         latest[c['artwork_id']].get('adapter_version') == module.VERSION))]


def resume_provider(provider, args, dsn):
    for run in (args.after, args.run):
        pending = pending_candidates(run, provider)
        if pending:
            print('Resuming', provider, run.name, len(pending), 'pending items', flush=True)
            module.worker(provider, pending, SimpleNamespace(run=run), dsn)
        required = {c['artwork_id'] for c in json.loads((run / 'candidates.json').read_bytes())['candidates']
                    if c['provider'] == provider}
        unattempted = required - terminal_ids(run)
        if unattempted:
            module.event(args.run, {'provider':provider,'outcome':'chain_paused',
                'campaign':str(run),'unattempted':len(unattempted)})
            return
        time.sleep(2)


def resume_chain(args):
    previous = json.loads((args.after / 'candidates.json').read_bytes())['candidates']
    selected = json.loads((args.run / 'candidates.json').read_bytes())['candidates']
    if {c['artwork_id'] for c in previous}.intersection(c['artwork_id'] for c in selected):
        raise ValueError('Campaign artwork IDs overlap')
    dsn = module.cloud_dsn()
    providers = sorted({c['provider'] for c in previous + selected})
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        pending = {pool.submit(resume_provider, p, args, dsn):p for p in providers}
        while pending:
            finished, _ = concurrent.futures.wait(pending, timeout=30,
                return_when=concurrent.futures.FIRST_COMPLETED)
            for future in finished:
                provider = pending.pop(future)
                try:
                    future.result()
                except Exception as error:
                    module.event(args.run, {'provider':provider,'outcome':'chain_failed','error':str(error)[:500]})
            print(module.now(), 'active chains', list(pending.values()), dict(module.COUNTS), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--after', type=Path, required=True)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--predecessor-pid', type=int)
    parser.add_argument('--resume-chain', action='store_true', help='Resume both campaigns after all prior import processes have exited')
    args = parser.parse_args()
    if args.resume_chain:
        resume_chain(args)
        return
    if not args.predecessor_pid:
        parser.error('--predecessor-pid is required when waiting on an earlier live importer')
    previous = json.loads((args.after / 'candidates.json').read_bytes())['candidates']
    selected = json.loads((args.run / 'candidates.json').read_bytes())['candidates']
    previous_ids = {c['artwork_id'] for c in previous}
    if previous_ids.intersection(c['artwork_id'] for c in selected):
        raise ValueError('Campaign artwork IDs overlap')
    if any(c['work_type'] != 'painting' for c in selected):
        raise ValueError('Follow-up selection contains non-paintings')
    prerequisites = collections.defaultdict(set)
    for c in previous:
        prerequisites[c['provider']].add(c['artwork_id'])
    grouped = collections.defaultdict(list)
    for c in selected:
        grouped[c['provider']].append(c)
    if (args.run / 'events.jsonl').exists():
        raise ValueError('Follow-up already has events; inspect its live process before using the standard resumable importer')
    dsn = module.cloud_dsn()
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        running = {}
        while grouped or running:
            completed = terminal_ids(args.after)
            for provider in list(grouped):
                if prerequisites[provider].issubset(completed):
                    candidates = grouped.pop(provider)
                    time.sleep(2)  # Keep a source-request gap between the two workers.
                    module.event(args.run, {'provider':provider,'outcome':'followup_started',
                                           'after':str(args.after),'selected':len(candidates)})
                    running[pool.submit(module.worker, provider, candidates, args, dsn)] = provider
                    print('Started', provider, len(candidates), 'additional paintings', flush=True)
            if grouped:
                try:
                    os.kill(args.predecessor_pid, 0)
                except ProcessLookupError:
                    for provider, candidates in grouped.items():
                        module.event(args.run, {'provider':provider,'outcome':'followup_deferred',
                            'reason':'Earlier process ended with unattempted artwork IDs',
                            'unattempted_previous':len(prerequisites[provider] - completed)})
                    grouped.clear()
            if running:
                finished, _ = concurrent.futures.wait(running, timeout=30,
                    return_when=concurrent.futures.FIRST_COMPLETED)
                for future in finished:
                    provider = running.pop(future)
                    try:
                        future.result()
                    except Exception as error:
                        module.event(args.run, {'provider':provider,'outcome':'provider_failed','error':str(error)[:500]})
            elif grouped:
                time.sleep(30)
            print(module.now(), 'waiting for', list(grouped), 'running', list(running.values()),
                  dict(module.COUNTS), flush=True)


if __name__ == '__main__':
    main()
