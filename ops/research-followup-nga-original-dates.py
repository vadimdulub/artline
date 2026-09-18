#!/usr/bin/env python3
"""Recover explicit artwork dates when NGA's numeric fields repeat an artist lifespan.

The museum's original artwork date, not the lifespan, supplies the normalized
value. Unknown, open-ended or complex wording remains held. No source is edited.
"""
import argparse,collections,importlib.util,json,re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('core',ROOT/'ops/enrich-artwork-images.py');core=importlib.util.module_from_spec(s);s.loader.exec_module(core)

def explicit_date(obj,person):
    text=obj.get('displaydate','').strip()
    match=re.fullmatch(r'(?P<approx>(?:c\.|ca\.|circa|about|probably(?: c\.)?)\s*)?(?P<lo>\d{4})(?:\s*[-–—/]\s*(?P<hi>\d{4}|\d{2}))?',text,re.I)
    if not match:raise ValueError('No simple explicit original artwork date')
    lo=int(match['lo']);end=match['hi'] or match['lo'];hi=int(str(lo)[:2]+end) if len(end)==2 else int(end)
    if not all(re.fullmatch(r'\d{4}',person.get(k,'')) for k in ('beginyear','endyear')):raise ValueError('Creator lifespan unresolved')
    born,died=int(person['beginyear']),int(person['endyear'])
    if not 1000<=lo<=hi<=1970 or not born<lo<=hi<=died:raise ValueError('Original artwork date outside scope or source creator lifetime')
    if (obj.get('beginyear'),obj.get('endyear'))!=(person['beginyear'],person['endyear']):raise ValueError('This recovery batch only covers demonstrable lifespan defaults')
    if not 1000<=born<died<=1970:raise ValueError('Numeric source bounds cross the cutoff; editorial review needed')
    precision=('circa' if lo==hi else 'circa_range') if match['approx'] else ('exact' if lo==hi else 'range')
    return lo,hi,precision

def main():
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--leads',type=Path,required=True);a=p.parse_args();a.run.mkdir(parents=True,exist_ok=True)
    if (a.run/'source-candidates.json').exists():return
    rows=json.loads(a.leads.read_text());accepted=[];held=collections.Counter()
    for r in rows:
        o=r['object'];person=r['creator'];rel=r['creator_relation'];artist=r['artist']
        try:
            lo,hi,precision=explicit_date(o,person)
            if rel['role'] not in ('artist','painter','engraver','etcher') or rel['prefix'] or rel['suffix']:raise ValueError('Qualified creator relation')
            if person['constituenttype']!='individual' or person['forwarddisplayname']!=o['attribution']:raise ValueError('Creator attribution differs')
            if any(artist[field]!=int(person[key]) for field,key in [('birth_year','beginyear'),('death_year','endyear')]):raise ValueError('Existing creator lifespan differs')
            accepted.append(dict(r,commons_file=None,creation_year_start=lo,creation_year_end=hi,date_precision=precision))
        except ValueError as e:held[str(e)]+=1
    accepted.sort(key=lambda r:(not r['artist']['popular'],r['object']['classification']!='Painting',r['artist']['display_name'],r['object']['objectid']))
    core.save_new(a.run/'source-candidates.json',accepted)
    core.save_new(a.run/'source-selection-report.json',{'at':core.now(),'selected':len(accepted),'popular':sum(r['artist']['popular'] for r in accepted),'types':dict(collections.Counter(r['object']['classification'] for r in accepted)),'held':held,'date_basis':'Explicit original museum artwork date takes precedence over numeric fields that duplicate the source creator lifespan. Circa and probably qualifiers retained; unknown dates not inferred.'})
    print((a.run/'source-selection-report.json').read_text(),flush=True)

if __name__=='__main__':main()
