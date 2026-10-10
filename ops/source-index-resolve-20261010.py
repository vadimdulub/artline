#!/usr/bin/env python3
"""Reconcile native museum objects with production using scoped, read-only queries."""
import importlib.util,json,re,uuid,unicodedata,argparse
from pathlib import Path
from collections import defaultdict,Counter
from urllib.parse import urlsplit,urlunsplit
s=importlib.util.spec_from_file_location('native',Path(__file__).with_name('source-index-native-20261010.py'));n=importlib.util.module_from_spec(s);s.loader.exec_module(n)
m=n.m;RUN=n.RUN;OP=m.OP
INVENTORY='reconciliation-inventory-v2.json.gz';RESOLUTION='native-resolution-v2.json.gz'

def uid(text):return str(uuid.uuid5(uuid.NAMESPACE_URL,OP+'/'+text))
def norm(text):return re.sub(r'[^\w]+',' ',unicodedata.normalize('NFKD',str(text or '')).casefold()).strip()
def canon(url):
    p=urlsplit(url or '');return p.netloc.removeprefix('www.')+p.path.rstrip('/')+('?' + p.query if p.query else '')
def serial(x):return json.loads(json.dumps(x,default=str))
def batches(xs,size=500):
    for i in range(0,len(xs),size):yield xs[i:i+size]
def files():return sorted((RUN/'native').glob('*/*.json.gz'))
def effective_facts(r):
    f=dict(r['facts']);o=r['raw']
    if r['provider']=='smk' and not f.get('image') and o.get('has_image') and o.get('image_native'):
        u=o['image_native'];p=urlsplit(u)
        if p.scheme=='https' and p.netloc=='api.smk.dk' and re.fullmatch(r'/api/v1/thumbnail/[\w-]+\.(?:jpg|png)',p.path) and min(o.get('image_width',0),o.get('image_height',0))>=100:
            f['image']=u;f['image_view_note']='Native museum image endpoint attached to this exact object; complete source frame.'
    if r['provider']=='walters':
        # The broad mixed classification does not distinguish paintings from drawings.
        med=(f.get('medium') or '').casefold()
        if f.get('classification')=='Painting & Drawing':
            f['work_type']='painting' if re.search(r'\boil\b|\btempera\b',med) else 'watercolor' if 'watercolor' in med else 'drawing' if re.search(r'\b(ink|pencil|chalk|charcoal|graphite)\b',med) else 'unknown'
    return f
def read_native():
    out=[];refs,_=n.refs()
    for p in files():
        r=dict(m.load(p),native_file=str(p.relative_to(m.ROOT)))
        if r['key'] not in refs.get(r['provider'],{}):continue
        rr=refs[r['provider']][r['key']];r['index_bindings']=[b for item in rr for b in item['artline_bindings']];r['source_index_ids']=[x['id'] for x in rr]
        r['facts']=effective_facts(r);out.append(r)
    return out

def inventory():
    dest=RUN/INVENTORY;assert not dest.exists()
    rows=read_native();old=m.load(RUN/'inventory.json.gz');ids=set();ext=[];artists=[];ai=[];citations=[];resources={x['id']:x for x in m.resources()}
    pages=set();native_ids=set();accessions=set();schemes=set()
    for r in rows:
        f=r['facts'];pages.add(f['page']);native_ids.add(str(f['native_id']));accessions.add(str(f.get('accession') or ''))
        pages.update(resources[x]['url'] for x in r['source_index_ids'])
        schemes.add(f['scheme'])
        if r['provider'] in ('smk','cleveland'):schemes.add('european-'+r['provider']+'-'+{'smk':'statens-museum-for-kunst','cleveland':'cleveland-museum-of-art'}[r['provider']]+'-object')
        for b in r['index_bindings']:
            if b['entity_type']=='artwork':ids.add(b['entity_id'])
    for page in list(pages):
        p=urlsplit(page);host=p.netloc.removeprefix('www.')
        for h in [host,'www.'+host]:
            for path in [p.path.rstrip('/'),p.path.rstrip('/')+'/']:pages.add(urlunsplit(('https',h,path,p.query,'')))
    institutions=sorted({r['facts']['institution_id'] for r in rows if r['facts'].get('institution_id')})
    with m.m.connect() as db:
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        for ss in batches(sorted(native_ids)):
            ext.extend(db.execute("SELECT * FROM external_identifiers WHERE entity_type='artwork' AND scheme=ANY(%s) AND external_id=ANY(%s)",(sorted(schemes),ss)).fetchall())
        for urls in batches(sorted(pages)):
            ext.extend(db.execute("SELECT * FROM external_identifiers WHERE entity_type='artwork' AND canonical_url=ANY(%s)",(urls,)).fetchall())
            cc=db.execute("SELECT * FROM citations WHERE entity_type='artwork' AND source_url=ANY(%s)",(urls,)).fetchall();citations.extend(cc);ids.update(str(c['entity_id']) for c in cc)
        for acc in batches(sorted(accessions-{''})):
            ids.update(str(x['id']) for x in db.execute('SELECT id FROM artworks WHERE current_institution_id=ANY(%s::uuid[]) AND accession_number=ANY(%s)',(institutions,acc)).fetchall())
        ids.update(str(e['entity_id']) for e in ext)
        works=[];creators=[];media=[]
        for batch in batches(sorted(ids)):
            works.extend(db.execute('SELECT * FROM artworks WHERE id=ANY(%s::uuid[])',(batch,)).fetchall())
            ext.extend(db.execute("SELECT * FROM external_identifiers WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(batch,)).fetchall())
            creators.extend(db.execute('SELECT aa.*,a.display_name,a.normalized_name FROM artwork_artists aa JOIN artists a ON a.id=aa.artist_id WHERE aa.artwork_id=ANY(%s::uuid[])',(batch,)).fetchall())
            media.extend(db.execute('SELECT * FROM artwork_media WHERE artwork_id=ANY(%s::uuid[])',(batch,)).fetchall())
        for scheme in sorted({a['scheme'] for r in rows for a in r['facts'].get('creator_authorities',[])}):
            keys=sorted({str(a['external_id']) for r in rows for a in r['facts'].get('creator_authorities',[]) if a['scheme']==scheme})
            for batch in batches(keys):ai.extend(db.execute("SELECT e.*,a.display_name,a.normalized_name,a.status artist_status FROM external_identifiers e JOIN artists a ON a.id=e.entity_id WHERE e.entity_type='artist' AND e.scheme=%s AND e.external_id=ANY(%s)",(scheme,batch)).fetchall())
        names=sorted({str(a) for r in rows for a in r['facts'].get('creator_labels',[]) if a})
        for batch in batches(names):artists.extend(db.execute("SELECT id,display_name,normalized_name,status FROM artists WHERE display_name=ANY(%s) OR normalized_name=ANY(%s)",(batch,[norm(x) for x in batch])).fetchall())
        query_plans=[]
        for query,args in [("SELECT * FROM external_identifiers WHERE entity_type='artwork' AND canonical_url=ANY(%s)",(list(pages)[:100],)),('SELECT id FROM artworks WHERE current_institution_id=%s AND accession_number=ANY(%s)',(institutions[0],list(accessions)[:100]))]:
            query_plans.append(db.execute('EXPLAIN (FORMAT JSON) '+query,args).fetchone())
    out=dict(at=m.now(),native_files=len(rows),artworks=works,identifiers=list({str(e['id']):e for e in ext}.values()),citations=list({str(c['id']):c for c in citations}.values()),creators=creators,attachments=media,artist_identifiers=ai,artists=list({str(a['id']):a for a in artists}.values()),query_plans=query_plans)
    m.save(dest,serial(out));print('Scoped reconciliation inventory',len(works),'objects',len(ai),'artist identifiers',flush=True)

def resolve():
    inv=m.load(RUN/INVENTORY);works={w['id']:w for w in inv['artworks']};by_native=defaultdict(set);by_url=defaultdict(set);by_acc=defaultdict(set);by_citation=defaultdict(list);resources={x['id']:x for x in m.resources()}
    for c in inv['citations']:by_citation[canon(c['source_url'])].append(c)
    for e in inv['identifiers']:
        by_native[e['scheme'],e['external_id']].add(e['entity_id'])
        if e['canonical_url']:by_url[canon(e['canonical_url'])].add(e['entity_id'])
    for w in inv['artworks']:
        if w['accession_number']:by_acc[w['current_institution_id'],norm(w['accession_number'])].add(w['id'])
    ai=defaultdict(set);names=defaultdict(set)
    for a in inv['artist_identifiers']:
        if a['artist_status']!='archived':ai[a['scheme'],a['external_id']].add(a['entity_id'])
    for a in inv['artists']:
        if a['status']!='archived':names[norm(a['display_name'])].add(a['id'])
    out=[]
    for r in read_native():
        f=r['facts'];provider=r['provider'];matches=set();basis=[]
        schemes=[f['scheme']]
        if provider in ('smk','cleveland'):schemes.append('european-'+provider+'-'+{'smk':'statens-museum-for-kunst','cleveland':'cleveland-museum-of-art'}[provider]+'-object')
        for scheme in schemes:
            hit=by_native[scheme,str(f['native_id'])]
            if hit:matches.update(hit);basis.append('native identifier '+scheme)
        hit=by_url[canon(f['page'])]
        if hit:matches.update(hit);basis.append('canonical object page')
        hit=by_acc[f.get('institution_id'),norm(f.get('accession'))] if f.get('accession') else set()
        if hit:matches.update(hit);basis.append('holding institution and exact accession')
        for page in {f['page'],*[resources[x]['url'] for x in r['source_index_ids']]}:
            for citation in by_citation[canon(page)]:
                candidate=works[citation['entity_id']]
                title_match=norm(candidate['title']) in {norm(t) for t in f['titles'] if t}
                accession_match=not candidate['accession_number'] or norm(candidate['accession_number'])==norm(f.get('accession'))
                if title_match and accession_match and candidate['current_institution_id']==f.get('institution_id'):
                    matches.add(candidate['id']);basis.append('exact object-page citation plus matching native title and institution, with no accession conflict')
        # Source-index bindings are research hints, never sufficient object identity by themselves.
        target=works[next(iter(matches))] if len(matches)==1 and next(iter(matches)) in works else None
        titles=[t.strip() for t in f['titles'] if isinstance(t,str) and t.strip()];date=f['dates'];new=not matches
        state='existing' if target else 'new' if new else 'duplicate_conflict'
        if target and target['status']=='archived':state='archived'
        if not titles:state='missing_title'
        if new and (date.get('start') or 0)>1970:state='out_of_date_scope'
        if new and (not f.get('institution_id') or f.get('holding_qualified')):state='unresolved_holding'
        # Preserve qualified creator text without silently assigning primary authorship.
        creators=[];unlinked=[]
        for authority in f.get('creator_authorities',[]):
            hit=ai[authority['scheme'],str(authority['external_id'])]
            if len(hit)==1 and not f.get('qualified_creators'):creators.append(dict(artist_id=next(iter(hit)),attribution_role='primary',attribution_note='Native creator authority '+authority['scheme']+':'+str(authority['external_id'])))
        if not creators and not f.get('qualified_creators'):
            for label in f.get('creator_labels',[]):
                if label and len(names[norm(label)])==1:creators.append(dict(artist_id=next(iter(names[norm(label)])),attribution_role='primary',attribution_note='Unique exact creator name in the existing catalogue, supported by the native museum object record.'))
        if not creators:unlinked=[x for x in f.get('creator_labels',[]) if x]
        aid=target['id'] if target else uid('artwork/'+provider+'/'+str(f['native_id']))
        image=state in ('new','existing') and (not target or not target['primary_media_id']) and bool(f.get('image') and f.get('image_open'))
        fields={}
        if target:
            for key,sourcekey in [('medium_text','medium'),('dimensions_text','dimensions'),('accession_number','accession')]:
                if not str(target.get(key) or '').strip() and str(f.get(sourcekey) or '').strip():fields[key]=f[sourcekey]
        out.append(dict(provider=provider,key=r['key'],native_file=r['native_file'],artwork_id=aid,state=state,title=titles[0] if titles else None,matched_ids=sorted(matches),identity_basis=basis,creator_links=list({c['artist_id']:c for c in creators}.values()),unlinked_creator_label='; '.join(unlinked) or None,image_candidate=image,field_updates=fields,source_index_ids=r['source_index_ids']))
    # Different native records must not converge to one writable target unnoticed.
    grouped=defaultdict(list)
    for r in out:
        if r['state'] in ('new','existing'):grouped[r['artwork_id']].append(r)
    for aid,rr in grouped.items():
        if len(rr)>1:
            for r in rr:r.update(state='native_target_collision',image_candidate=False,field_updates={})
    m.save(RUN/RESOLUTION,dict(at=m.now(),rows=out,counts=dict(Counter(r['state'] for r in out)),image_candidates=sum(r['image_candidate'] for r in out)))
    print('Identity resolution',dict(Counter(r['state'] for r in out)),'images',sum(r['image_candidate'] for r in out),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['inventory','resolve']);a=p.parse_args();globals()[a.command]()
