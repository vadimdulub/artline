"""Query observed categories separately: combined filters require all selected types."""
import collections
import importlib.util
import json
import re
from pathlib import Path
from urllib.parse import urlencode

spec=importlib.util.spec_from_file_location('v',Path(__file__).with_name('museum-expansion-athens-city-source-20261010.py'))
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
c,q,m,RUN=v.c,v.q,v.m,v.RUN

def main():
    assert not(RUN/'bounded-index-001.json.gz').exists()
    selection=m.load(RUN/'category-selection-001.json');known={x['external_id'] for x in m.load(RUN/'production-initial-scope-001.json.gz')['snapshot']['identifiers'] if x['scheme']=='searchculture-edm'}
    assert (RUN/'category-query-correction-001.json').exists()
    pages=[];by_id={};totals={}
    for num,typ in enumerate(selection['selected'],1):
        prefix='facets[ekt_proxy_dc_type_hierarchy_uri]'
        params={prefix+'.field':'ekt_proxy_dc_type_hierarchy_uri',prefix+'.values[0].checked':'true',prefix+'.values[0].value':typ['value'],'resultsMode':'GRID','sortResults':'TITLE','language':'en'}
        count=0;expected=int(re.search(r'\((\d+)\)',typ['text'])[1]);assert expected<=60
        for page in range(1,3):
            url=v.BASE+selection['source_form']['action']+'?'+urlencode(dict(params,**{'page.page':page}))
            doc,rc=q.q.capture('category-'+str(num).zfill(2)+'-page-'+str(page).zfill(2),url)
            match=re.search(r"var itemsNum = '(\d+)'",str(doc))
            if match is None:match=re.search(r"\bfrom ([0-9,]+) items?",q.clean(doc.get_text(" ",strip=True)))
            assert match is not None,(typ["label"],q.clean(doc.get_text(" ",strip=True))[-500:])
            total=int(match[1].replace(",",""));assert total==expected,(typ['label'],total,expected)
            rows=v.index(doc);assert 0<len(rows)<=30
            for row in rows:
                row['historical_source_match']=row['source_id'] in known
                sid=row['source_id']
                if sid in by_id:assert {k:w for k,w in by_id[sid].items() if k!='selected_categories'}==row;by_id[sid]['selected_categories'].append(typ['label'])
                else:by_id[sid]=dict(row,selected_categories=[typ['label']])
            count+=len(rows);pages.append(dict(category=typ['label'],page=page,receipt=rc,cards=rows));print(json.dumps(dict(category=typ['label'],page=page,total=total,cards=len(rows),unique=len(by_id))),flush=True)
            if count>=total:break
        assert count==expected;totals[typ['label']]=count
    cards=sorted(by_id.values(),key=lambda x:(x['title'],x['source_id']))
    m.save(RUN/'bounded-index-001.json.gz',dict(at=m.now(),pages=pages,cards=len(cards),unique_cards=cards,observed_category_totals=totals,selected_type_labels=v.TYPES,historical_matches=sum(x['historical_source_match'] for x in cards),category_selection_reference=c.ref(RUN/'category-selection-001.json'),query_correction_reference=c.ref(RUN/'category-query-correction-001.json'),script_reference=c.ref(Path(__file__).resolve()),policy='Eight distinct art-category queries, each at most two pages of30. Duplicate sourceIDs count once. No images or object detail downloads. Dates and categories are leads pending editorial review.'))
    print(json.dumps(dict(unique_cards=len(cards),category_counts=totals,historical=sum(x['historical_source_match'] for x in cards))),flush=True)

if __name__=='__main__':main()
