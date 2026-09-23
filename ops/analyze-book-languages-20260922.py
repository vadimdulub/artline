#!/usr/bin/env python3
"""Reproducible parsing of the captured work-language sources; no DB writes."""
import collections,importlib.util,json
from pathlib import Path
from book_language_review import aliases_for,wikipedia_language,claim_language_ids

ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'docs/research/book-languages-20260922'
def read(p):return json.loads(p.read_bytes())
def analyze():
    base=read(Path(read(RUN/'baseline-local-reference.json')['path']))
    terms={p.stem:read(p)['entity'] for p in (RUN/'language-entities').glob('*.json')}
    aliases=aliases_for(terms);rows=[]
    for i,row in enumerate(base['books']):
        book=row['book'];q=book['source_id'];entity=read(RUN/'entities'/(q+'.json'))['entity']
        page=RUN/'wikipedia'/(q+'.json')
        wp=wikipedia_language(read(page),q,aliases) if page.exists() else {'state':'no_enwiki_sitelink','languages':[],'fields':[]}
        old=sorted(row['discovery']['languages']);fresh=claim_language_ids(entity)
        item={'bookId':book['id'],'qid':q,'title':book['title'],'author':book['author_label'],'old':old,'fresh':fresh,'wikipedia':wp}
        rows.append(item)
        if i%1000==999:print('Parsed',i+1,flush=True)
    (RUN/'parsed-review.json').write_text(json.dumps(rows,ensure_ascii=False,separators=(',',':')))
    print('States',dict(collections.Counter(r['wikipedia']['state'] for r in rows)))
    print('Clean fields',sum(r['wikipedia']['state']=='explicit_language_field' for r in rows),'different',sum(r['wikipedia']['state']=='explicit_language_field' and r['old']!=r['wikipedia']['languages'] for r in rows))
    print('Unmapped',collections.Counter(v for r in rows for f in r['wikipedia']['fields'] for v in f['unresolved']).most_common(100))
if __name__=='__main__':analyze()
