#!/usr/bin/env python3
"""Read-only source/date and identity research for selected Russell-Cotes objects."""
import collections
import argparse
import importlib.util
import re
from pathlib import Path
s=importlib.util.spec_from_file_location('w',Path(__file__).with_name('museum-expansion-russell-holdings-20261007.py'))
w=importlib.util.module_from_spec(s);s.loader.exec_module(w);m=w.m;RUN=w.RUN


def creator_label(value):
    value=re.sub(r'\s*\([^)]*(?:\d{3,4}|\d{1,2}(?:st|nd|rd|th)\s+[Cc]entury)[^)]*\)','',value).strip()
    return re.sub(r'\s+\d{4}\s*[-–]\s*\d{4}$','',value).strip()


def creation(value):
    value=value.replace('–','-').strip()
    match=re.fullmatch(r'(?:(c\.|about|around)\s*)?(\d{4})(?:\s*-\s*(\d{4}))?',value)
    if match:
        first,last=int(match[2]),int(match[3] or match[2]);circa=bool(match[1])
        assert 100<=first<=last<=1970 and not (circa and last==1970),'ineligible date or circa cutoff'
        return first,last,('circa' if first==last else 'circa_range') if circa else ('exact' if first==last else 'range')
    decade=re.fullmatch(r'(\d{3}0)s',value)
    if decade:
        first=int(decade[1]);assert first+9<=1970
        return first,first+9,'range'
    if value.lower() in ['19th century','late 19th century','late 1800s','mid 1800s-late 1800s']:
        return 1800,1899,'range'
    raise AssertionError('unresolved creation statement')


def source_facts(page):
    p=page['parsed'];lines=p['caption_lines'];assert len(lines)>=3
    header,creator=lines[:2]
    assert m.norm(header)!=m.norm(p['title']), 'caption supplies no date separate from the title or sitter lifespan'
    # A trailing creation statement only; dates inside a sitter title are not dates of making.
    match=re.search(r'(?:,\s*|\()((?:(?:c\.|about|around)\s*)?\d{4}(?:\s*[-–]\s*\d{4})?|\d{3}0s|(?:late )?19th [Cc]entury|(?:mid 1800s-)?late 1800s)\)?$',header)
    assert match,'no separable eligible creation statement'
    date=match[1];first,last,precision=creation(date)
    inventories=[l for l in lines[2:] if re.fullmatch(r':?BORGM[ :]?\d+(?:\.\d+)*[a-zA-Z]?|[Ss][Cc]\s*\d+|RC\d+|T\d+(?:\.\d+)+|\d+(?:\.\d+)+ BORGM',l)]
    assert len(inventories)==1,'no single literal inventory'
    inventory=inventories[0];label=creator_label(creator);assert label
    media=[l for l in lines[2:] if l!=inventory and '©' not in l and not re.match(r'(?:Image|Photo)',l)]
    assert len(media)<=1,'ambiguous medium lines';medium=media[0] if media else None
    if medium and re.search(r'^Oil\b',medium,re.I):typ='painting'
    elif medium and re.search(r'Watercolou?r|Pastel',medium,re.I):typ='drawing'
    elif medium=='Chromolithograph':typ='print'
    elif re.search(r'\b(sculpture|statue|bust|statuette|sculpted)\b',p['narrative'] or '',re.I) and medium in [None,'Marble','Bronze','Plaster','Stone','Iron']:typ='sculpture'
    else:typ='unknown'
    return dict(source_id=page['url'].rstrip('/').split('/')[-1],source_url=page['url'],title=p['title'],native_title_caption=header,native_creator=creator,creator_label=label,date_display=date,first=first,last=last,date_precision=precision,inventory=inventory,medium=medium,work_type=typ,dimensions=None)


def main(suffix):
    destination=RUN/f'native-candidates-{suffix}.json.gz'
    assert not destination.exists()
    refs=m.load(RUN/'native-holding-comparison-001.json.gz')['capture_files'];rows=[];allinventories=collections.defaultdict(list)
    scope=w.baseline()['artworks'];disposal=m.load(RUN/'disposal-review-001.json')
    for ref in refs:
        page=w.checked_native_page(ref);source=page['url'].rstrip('/').split('/')[-1]
        for line in page['parsed']['caption_lines'][2:]:
            if re.fullmatch(r':?BORGM[ :]?\d+(?:\.\d+)*[a-zA-Z]?|[Ss][Cc]\s*\d+|RC\d+|T\d+(?:\.\d+)+|\d+(?:\.\d+)+ BORGM',line):
                allinventories[w.compact(line)].append(source)
        try:f=source_facts(page)
        except AssertionError as error:rows.append(dict(source_id=source,source_reference=ref,state='hold_source',reason=str(error),parsed=page['parsed']));continue
        matches=[a['id'] for a in scope if w.compact(a['accession_number'])==w.compact(f['inventory'])]
        state='existing_inventory' if matches else 'candidate';reason='existing initial-scope inventory' if matches else None
        if w.compact(f['inventory']) in w.compact(disposal['full_extracted_text']):state='hold_source';reason='proposed disposal list needs review'
        if source=='cornish-holiday':state='hold_source';reason='native caption 1940–1946 conflicts with stated 1936 purchase'
        rows.append(dict(source_id=source,source_reference=ref,state=state,reason=reason,existing_ids=matches,facts=f,parsed=page['parsed']))
    for r in rows:
        if r.get('facts') and len(allinventories[w.compact(r['facts']['inventory'])])>1:
            r.update(state='hold_source',reason='native inventory shared by different object pages',shared_inventory_sources=allinventories[w.compact(r['facts']['inventory'])])
    with m.connect() as db:
        pp,pd=w.validate_plan();verified=w.verify(db,pp,pd);before=w.snapshot(db,pp['scoped_ids']);assert w.counts(db)==dict(linked=111,eligible=111)
        backup=m.BACKUP/f'russell-cotes-native-{suffix}-existing-records.json.gz';m.save(backup,dict(at=m.now(),**before))
    m.save(destination,dict(at=m.now(),rows=rows,counts=dict(collections.Counter(r['state'] for r in rows)),previous_plan_sha256=pd,scoped_ids=pp['scoped_ids'],backup_path=str(backup),policy='Source parsing and local initial inventory comparison only. No import approval; source narratives and full catalogue identities still need review. Dates are never derived from artist or sitter lifespans. Earlier candidate snapshots are superseded research evidence, not import approvals.'))
    print(collections.Counter(r['state'] for r in rows))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--suffix',default='002');a=p.parse_args();assert re.fullmatch(r'\d{3}',a.suffix);main(a.suffix)
