#!/usr/bin/env python3
"""Bounded Wikidata identity research for unresolved closed museum/CSV biographies."""
import collections, importlib.util, json
from pathlib import Path
from urllib.parse import urlencode
spec=importlib.util.spec_from_file_location('lifespans',Path(__file__).with_name('reconcile-creator-lifespans.py'))
l=importlib.util.module_from_spec(spec);spec.loader.exec_module(l);m=l.m;r=m.r
RUN=m.ROOT/'docs/research/creator-authorities-20260913'
r.RUN=RUN

def groups():
    accepted={e['before']['id'] for e in m.read('plan.json')}
    works={w['id']:w for w in m.read('unlinked-artworks.json') if w['id'] not in accepted}
    facts={f['id']:f for f in m.read('museum-creator-facts.json')}
    grouped={}
    for wid,w in works.items():
        fact=facts.get(wid);p=fact['painter'] if fact else l.parse(w['unlinked_creator_label'])
        if not p or any(p.get(k) is None for k in ('birth','death')):continue
        if not 0<=p['death']-p['birth']<=125 or m.old.QUALIFIED.search(w['unlinked_creator_label']) or m.old.QUALIFIED.search(p['name']):continue
        check={'painter':p,'context':(fact or {}).get('context'),'state':(fact or {}).get('state','needs_review'),'review':(fact or {}).get('review_evidence') or {},'note':(fact or {}).get('note') or '', 'precision':w['date_precision'],'first':w['creation_year_start'],'last':w['creation_year_end'],'type':w['work_type']}
        if m.old.blocked(check):continue
        key=(m.names.namekey(p['name']),p['birth'],p['death'])
        group=grouped.setdefault(key,{'painter':p,'works':[],'kind':'official-museum-biography' if fact else 'explicit-supplied-biography'})
        group['works'].append(wid)
    return sorted(grouped.values(),key=lambda g:(-len(g['works']),g['painter']['name']))

def main():
    selected=[g for g in groups() if len(g['works'])>=5][:100]
    r.core.save_new(RUN/'selected-groups.json',selected)
    matcher=m.Matcher(m.read('artists.json'))
    for i,g in enumerate(selected):
        dest=RUN/'decisions-v2'/f'{i+1:03d}.json'
        if dest.exists():continue
        p=g['painter'];name=p['name'];data,search_receipt=r.fetch('https://www.wikidata.org/w/api.php?'+urlencode({'action':'wbsearchentities','search':name,'language':'en','uselang':'en','limit':5,'type':'item','format':'json','maxlag':5}))
        searches=[search_receipt]
        ids=[x['id'] for x in data.get('search',[])]
        # Museum labels commonly put the surname first; Wikidata's entity
        # search is phrase-sensitive. This changes discovery only: acceptance
        # still requires a documented complete name and both lifespan years.
        if not ids and len(name.split())>1:
            tokens=name.split();rotated=' '.join(tokens[1:]+tokens[:1])
            data,receipt=r.fetch('https://www.wikidata.org/w/api.php?'+urlencode({'action':'wbsearchentities','search':rotated,'language':'fr','uselang':'en','limit':5,'type':'item','format':'json','maxlag':5}))
            searches.append(receipt);ids=[x['id'] for x in data.get('search',[])]
        es,receipts=r.entities(ids) if ids else ({},{})
        candidates=[]
        for q,e in es.items():
            labs=r.labels(e);human=any(x.get('id')=='Q5' for x in r.values(e,'P31') if isinstance(x,dict))
            if not human or m.names.namekey(name) not in {m.names.namekey(x) for x in labs}:continue
            if r.year(e,'P569')!=p['birth'] or r.year(e,'P570')!=p['death']:continue
            # Museum/CSV name + both boundaries must agree with independently
            # documented authority. Name-only and one-boundary candidates held.
            researched={**p,'wikidata':q}
            match,reason=matcher.match(researched,'wikidata',labs)
            collisions=set().union(*(matcher.names.get(m.names.namekey(x),set()) for x in labs))
            candidates.append({'qid':q,'label':r.label(e),'birth':r.year(e,'P569'),'death':r.year(e,'P570'),'entity_receipt':receipts[q],'existing_match':match,'existing_match_reason':reason,'all_alias_collisions':[matcher.artists[x] for x in sorted(collisions)]})
        r.core.save_new(dest,{'group':g,'search_receipts':searches,'candidates':candidates,'decision':'unique_authority' if len(candidates)==1 else 'held_ambiguous_or_unconfirmed'})
        print(i+1,len(g['works']),name,'confirmed',len(candidates),flush=True)
    print('Research complete',len(selected),'groups',sum(len(g['works']) for g in selected),'artworks',flush=True)

if __name__=='__main__':main()
