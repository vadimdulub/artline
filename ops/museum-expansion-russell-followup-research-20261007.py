#!/usr/bin/env python3
"""Read-only follow-up research for 88 selected Russell-Cotes pages."""
import collections,importlib.util,re
from pathlib import Path
s=importlib.util.spec_from_file_location('prior',Path(__file__).with_name('museum-expansion-russell-native-apply-20261007.py'));prior=importlib.util.module_from_spec(s);s.loader.exec_module(prior)
w=prior.w;m=prior.m;RUN=prior.RUN;n=prior.n
INV=re.compile(r':?(?:BORGM[ :]?\d+(?:\.\d+)*[a-zA-Z]?#?|[Ss][Cc]\s*\d+[a-zA-Z]?(?: BORGM)?|RC\d+(?:\.\d+)*|T\d+(?:\.\d+)+(?: BORGM)?|\d+[a-z]?(?:\.\d+)+[a-z]?)')
BAD={
'8398-2':'Caption circa1878 conflicts with narrative that this pair was exhibited in1872; retain for date/version review.',
'nelusko':'Caption circa1878 conflicts with narrative1872 exhibition of this pair; source Pagini/Pagani and birth-year variants remain unresolved.',
'great-argus':'Taxidermy specimen; not selected as an artwork.',
'skull':'Human remains used as a theatrical prop; not an artwork addition.',
'panefer':'Source explicitly questions whether this is an export reproduction. Ancient subject/prototype date cannot date the physical object.',
'collection-of-taiaha':'Compound group and weapon function require separate physical scope review.',
'double-handled-chocolate-cups':'Compound cups, covers and stands; individual inventory/date relationships need review.',
'amida-butsu':'Compound inventory a-b requires physical/component reconciliation before selection.',
}
DEFER={'clock','japanese-jar','chinese-jar','incense-burner','tsuri-daiko','wakahuia','feathered-edge-dessert-plate','pedestal-table','lund-blockley-clock','densho','qabqab','nalin','shatweh','kashkul','borough-theatre-and-opera-house-stratford-poster','theatre-poster-from-theatre-royal-bradford','merchant-of-venice-poster'}

def inventory_key(value):
    value=re.sub(r'\s+BORGM$','',value or '',flags=re.I)
    return w.compact(value)

def source_facts(page):
    p=page['parsed'];lines=p['caption_lines'];assert len(lines)>=3
    header,creator=lines[:2]
    assert m.norm(header)!=m.norm(p['title']),'caption provides no separate artwork creation statement'
    match=re.search(r'(?:,\s*|\()((?:(?:c\.|about|around)\s*)?\d{4}(?:\s*[-–]\s*\d{4})?|\d{3}0s|(?:late )?19th [Cc]entury|(?:mid 1800s-)?late 1800s)\)?$',header)
    assert match,'no separable eligible creation statement';date=match[1];first,last,precision=n.creation(date)
    inventories=[l for l in lines[2:] if INV.fullmatch(l)]
    assert len(inventories)==1,'no single literal inventory';inventory=inventories[0]
    assert not INV.fullmatch(creator) and not re.match(r'Glass|Print|Theatre Poster|Watercolour|Oil\b',creator),'no explicit creator label'
    label=n.creator_label(creator);assert label
    media=[l for l in lines[2:] if l!=inventory and '©' not in l and not re.match(r'(?:Image|Photo)',l)]
    assert len(media)<=1,'ambiguous medium lines';medium=media[0] if media else None
    body=p['narrative'] or ''
    if medium and re.match(r'Oil\b',medium,re.I):typ='painting'
    elif medium and re.search(r'Watercolou?r|Pastel',medium,re.I):typ='drawing'
    elif medium and re.search(r'print|[Ll]ithograph',medium):typ='print'
    elif re.search(r'\b(etching|woodblock print|chromolithograph print)\b',body,re.I):typ='print'
    elif re.search(r'\bink drawing\b',body,re.I):typ='drawing'
    elif re.search(r'\b(sculpture|statue|bust|statuette|sculpted|murti)\b',body,re.I) and (medium is None or re.search(r'Marble|Bronze|Plaster|Stone|Iron',medium,re.I)):typ='sculpture'
    else:typ='unknown'
    return dict(source_id=page['url'].rstrip('/').split('/')[-1],source_url=page['url'],title=p['title'],native_title_caption=header,native_creator=creator,creator_label=label,date_display=date,first=first,last=last,date_precision=precision,inventory=inventory,medium=medium,work_type=typ,dimensions=None)

def main():
    refs=[];allinvs=collections.defaultdict(list)
    for suffix in ['001','002','003']:
        queue=m.load(RUN/f'native-object-queue-{suffix}.json')
        for obj in queue['objects']:
            source=obj['url'].rstrip('/').split('/')[-1];ref=w.reference(RUN/f'native-objects-{suffix}'/(source+'.json.gz'));page=w.checked_native_page(ref)
            for line in page['parsed']['caption_lines'][1:]:
                if INV.fullmatch(line):allinvs[inventory_key(line)].append(source)
            if suffix!='001':refs.append((source,ref,page))
    assert len(refs)==88
    pp,pd=prior.validate_plan()
    with m.connect() as db:
        verified=prior.verify(db,pp,pd);assert verified['current_counts']==dict(linked=179,eligible=179)
        ids=sorted(set(pp['scoped_ids'])|{r['artwork_id'] for r in pp['records']});before=w.snapshot(db,ids)
    assert len(before['artworks'])==234
    backup=m.BACKUP/'russell-cotes-native-003-existing-records.json.gz';m.save(backup,dict(at=m.now(),**before))
    rows=[];disposal=m.load(RUN/'disposal-review-001.json')
    for source,ref,page in refs:
        row=dict(source_id=source,source_reference=ref,parsed=page['parsed'])
        try:
            f=source_facts(page);row['facts']=f
            hits=[a['id'] for a in before['artworks'] if a['accession_number'] and inventory_key(a['accession_number'])==inventory_key(f['inventory'])]
            row.update(state='existing_inventory' if hits else 'candidate',existing_ids=hits,reason='Existing scoped inventory' if hits else None)
            if len(set(allinvs[inventory_key(f['inventory'])]))>1:row.update(state='hold_source',reason='Inventory shared by different native object pages',shared_inventory_sources=sorted(set(allinvs[inventory_key(f['inventory'])])))
            if inventory_key(f['inventory']) in w.compact(disposal['full_extracted_text']):row.update(state='hold_source',reason='Proposed disposal match requires review')
        except AssertionError as err:row.update(state='hold_source',reason=str(err))
        if source in BAD:row.update(state='hold_source',reason=BAD[source])
        if source in DEFER:row.update(state='deferred_scope',reason='Retained museum object evidence; decorative/functional/artifact scope requires separate review, not selected in this artwork batch.')
        rows.append(row)
    m.save(RUN/'native-candidates-003.json.gz',dict(at=m.now(),rows=rows,counts=dict(collections.Counter(r['state'] for r in rows)),scoped_ids=ids,backup_path=str(backup),previous_plan_sha256=pd,policy='Research only. Dates use explicit artwork statements, never artist/sitter lifespans. All228 native inventories checked for aliases/collisions; no automated import approval.'))
    print(collections.Counter(r['state'] for r in rows))
    for r in rows:print(r['source_id'],r['state'],r.get('facts',{}).get('date_display'),r.get('facts',{}).get('inventory'),r['reason'])
if __name__=='__main__':main()
