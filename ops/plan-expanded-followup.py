#!/usr/bin/env python3
"""Reconcile remaining artworks against the painter identities established by prior rounds."""
import argparse,importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
s=importlib.util.spec_from_file_location('activity',ROOT/'ops/plan-expanded-activity.py');activity=importlib.util.module_from_spec(s);s.loader.exec_module(activity)
def main(number):
 out=ROOT/f'docs/research/expanded-round{number}-20260913';matches,paths=activity.merged_matches(number-1);activity.p.previous.save(out/'source-matches.json',matches);activity.p.previous.save(out/'source-audit.json',{'strategy':f'Fresh catalogue authority reconciliation using all pinned official object captures from rounds 2–{number-1}, including established artist IDs with documented activity.','matched_candidate_records_available':len(matches)});activity.p.previous.save(out/'source-paths.json',paths+['ops/plan-expanded-followup.py','ops/plan-expanded-activity.py']);activity.p.main(directory=out,matches_path=out/'source-matches.json',round_slug=f'round{number}')
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--round',type=int,required=True);main(a.parse_args().round)
