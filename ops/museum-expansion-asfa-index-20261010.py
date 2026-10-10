"""Bounded nine-page date-ascending index review; no object/image ingestion."""
import importlib.util,json,re
from pathlib import Path
from urllib.parse import urlencode
spec=importlib.util.spec_from_file_location('src',Path(__file__).with_name('museum-expansion-asfa-source-20261010.py'))
src=importlib.util.module_from_spec(spec);spec.loader.exec_module(src)
c,m,RUN,q=src.c,src.m,src.RUN,src.q

def main():
    assert not (RUN/'bounded-index-001.json.gz').exists()
    first=m.load(RUN/'source-selection-discovery-001.json');pages=[];cards=[]
    for page in range(1,10):
        if page==1:rc=first['first_date_page']['receipt'];rows=first['first_date_page']['cards']
        else:
            doc,rc=q.q.capture('date-index-'+str(page).zfill(3),'https://www.searchculture.gr'+first['form']['action']+'?'+urlencode({'resultsMode':'GRID','sortResults':'YEAR_ASC','language':'en','page.page':page}));rows=src.index(doc)
        assert len(rows)==30 and not {x['source_id'] for x in cards}&{x['source_id'] for x in rows}
        pages.append(dict(page=page,receipt=rc,cards=rows));cards+=rows
        print(json.dumps(dict(page=page,cards=len(cards),first_date=rows[0]['index_date'],last_date=rows[-1]['index_date'])),flush=True)
    selected=[];excluded=[]
    for card in cards:
        dates=[int(x) for x in re.findall(r'(?<!\d)(?:18|19|20)\d{2}(?!\d)',card['index_date'] or '')]
        reason='non_art_document' if card['index_type'] in ['Document','Book','Text'] else 'date_review_required' if not dates or max(dates)>1970 else None
        (excluded if reason else selected).append(dict(card,selection_reason=reason or 'source_dated_artwork_metadata_review'))
    old=m.load(RUN/'production-initial-scope-001.json.gz')['snapshot'];oldids={x['external_id']:x for x in old['identifiers'] if x['scheme']=='searchculture-edm'}
    m.save(RUN/'bounded-index-001.json.gz',dict(at=m.now(),pages=pages,selected=selected,excluded=excluded,existing_source_ids=sorted(oldids),source_total=4012,indexed_total=len(cards),unindexed_total=4012-len(cards),script_reference=c.ref(Path(__file__).resolve()),policy='Only first270date-ascending index cards reviewed; documents excluded before detail capture. Index dates are provisional, not physical-version validation. Existing records preserved; collection total is not eligible count. No images or writes.'))
    print(json.dumps(dict(indexed=len(cards),selected=len(selected),excluded=len(excluded),existing_selected=sum(x['source_id'] in oldids for x in selected))),flush=True)

if __name__=='__main__':main()
