#!/usr/bin/env python3
"""Twenty French primary-object reviews from exact POP authority crosswalks.

Metadata captures only: museum copyright images are not copied. Museum school
labels are retained as object-catalogue context, not automatic citizenship.
"""
import collections,importlib.util,json,re,time
from pathlib import Path
import requests
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('m',Path(__file__).with_name('apply-country-round.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
CORE=m.m.core;BASE=m.x.SESSION_BASE;RUN=BASE/'france/primary-objects'
def capture(oid):
    dest=RUN/'captures'/(oid+'.json')
    if dest.exists():return json.loads(dest.read_text())
    url='https://pop.culture.gouv.fr/notice/joconde/'+oid;time.sleep(2)
    r=requests.get(url,timeout=(15,60),headers={'User-Agent':'Artline research (https://github.com/vadimdulub/artline)'});r.raise_for_status();soup=BeautifulSoup(r.content,'html.parser');fields={}
    for node in soup.select('div.fr-text--bold'):
        sib=node.find_next_sibling('div')
        if sib:fields[node.get_text(' ',strip=True)]=sib.get_text(' ',strip=True)
    assert fields.get('Référence de la notice')==oid,fields
    receipt=dict(url=url,resolved_url=r.url,status=r.status_code,retrieved_at=CORE.now(),sha256=CORE.sha(r.content),bytes=len(r.content))
    CORE.save_new(RUN/'captures'/(oid+'.html'),r.content);out=dict(receipt=receipt,fields=fields);CORE.save_new(dest,out);return out
def namekey(s):return tuple(sorted(m.f.names.namekey(s).split()))
def research(n):
    folder=RUN/f'round-{n:02d}';dest=folder/'research.json'
    if dest.exists():return
    ready=BASE/f'france/FR/round-{n:02d}/delivery/ready';records=[json.loads(p.read_text())['record'] for p in sorted(ready.glob('Q*.json'))];out=[];counts=collections.Counter();holds=[]
    for rec in records:
        ids=[v for v in m.m.r.values(rec['entity'],'P347') if isinstance(v,str) and re.fullmatch(r'\d{11}',v)]
        if not ids or counts[rec['creator_qid']]>=3:continue
        counts[rec['creator_qid']]+=1
        for oid in ids[:1]:
            try:
                ev=capture(oid);f=ev['fields'];names={namekey(x) for x in m.m.r.labels(rec['creator_entity'])};maker=f.get('Auteur','');acc=f.get("Numéro d'inventaire",'')
                exact_maker=namekey(maker) in names;expected=m.m.accession_key(rec['accession'] or '')
                exact_accession=bool(expected) and any(m.m.accession_key(part.strip())==expected for part in acc.split(';'))
                qualified=bool(re.search(r'attribu|copie|atelier|école de|entourage|d’après|d.apres|anonyme',maker,re.I))
                decision='corroborated_primary_maker_and_accession' if exact_maker and exact_accession and not qualified else 'manual_object_identity_review'
                out.append(dict(qid=rec['qid'],creator_qid=rec['creator_qid'],creator_name=rec['creator_label'],candidate_title=rec['title'],candidate_date=rec['date'],candidate_accession=rec['accession'],pop_id=oid,primary=ev,exact_named_maker=exact_maker,exact_accession=exact_accession,qualified_maker=qualified,decision=decision))
            except Exception as e:holds.append(dict(qid=rec['qid'],pop_id=oid,error=type(e).__name__,reason=str(e)[:300]))
    CORE.save_new(dest,dict(at=CORE.now(),round=n,records=out,source_failures=holds,metadata_inspected=len(out),complete=not holds,policy='At most three exact museum metadata objects per painter in this source round. Original object school, source chronology and media restrictions retained. No source photos downloaded or current display inferred.'))
    print('French POP primary round',n,'objects',len(out),'confirmed',sum(r['decision']=='corroborated_primary_maker_and_accession' for r in out),'failures',len(holds),flush=True)
if __name__=='__main__':
    for n in range(1,21):research(n)
