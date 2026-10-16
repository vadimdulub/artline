"""Reconcile research against the pinned local read-only reference, never production IDs."""
import runpy,re,collections
from urllib.parse import urlparse
m=runpy.run_path('ops/germany-deep-facts-20261011.py')['m'];final=(m.RUN/'selection-final.json').exists();x=m.h.load(m.RUN/('selection-final.json'if final else'selection-reviewed.json'));base=m.h.load(m.RUN/'local-reference-audit.json.gz')
aliases={'de-staedel':'staedel-museum','de-alte-pinakothek':'alte-pinakothek','de-neue-pinakothek':'neue-pinakothek','de-pinakothek-der-moderne':'wikimedia-museum-q250195','de-gemaeldegalerie-berlin':'gemaldegalerie-berlin','de-germanisches-nationalmuseum':'germanisches-nationalmuseum','de-kunsthalle-karlsruhe':'staatliche-kunsthalle-karlsruhe','de-albertinum':'wikimedia-museum-q472706','de-hamburger-kunsthalle':'hamburger-kunsthalle','de-museum-folkwang':'wikimedia-museum-q125634','de-staatliches-museum-schwerin':'wikimedia-museum-q2324618','de-wallraf-richartz':'spain-research-museum-q700959'}
by_slug={i['slug']:i for i in base['museums']};work={a['id']:a for a in base['artworks']};by_url=collections.defaultdict(set);by_native=collections.defaultdict(set)
for c in base['citations']:
    if c.get('source_url'):
        by_url[c['source_url'].rstrip('/')].add(c['entity_id'])
        if c.get('source_record_id'):by_native[(urlparse(c['source_url']).netloc,c['source_record_id'].strip())].add(c['entity_id'])
def norm(x):return re.sub(r'[^\w]','',m.h.norm(x or''))
rows=[]
for f in x['records']:
    mu=by_slug.get(aliases.get(f['museum_slug']));ids=set(by_url.get(f['source_url'].rstrip('/'),[]));evidence=[]
    # A catalogue chapter or PDF describes multiple works: URL alone cannot link them.
    same_source=sum(z['source_url']==f['source_url']for z in x['records'])
    if ids and same_source==1:evidence.append('Exact primary object citation URL')
    else:ids=set()
    native=by_native.get((urlparse(f['source_url']).netloc,f['source_record_id'].strip()),set())
    if native:ids|=native;evidence.append('Same provider and native source record ID')
    scoped=[]
    if mu:
        for a in base['artworks']:
            if a['current_institution_id']==mu['id']or any(h['artwork_id']==a['id']and h['institution_id']==mu['id']for h in base['holding_assertions']):scoped.append(a)
    if f.get('accession'):
        iv={a['id']for a in scoped if a.get('accession_number')and norm(a['accession_number'])==norm(f['accession'])}
        if iv:ids|=iv;evidence.append('Same mapped holding institution and inventory number')
    title=[a['id']for a in scoped if norm(a['title'])==norm(f['title'])or(f.get('alternate_title')and norm(a['title'])==norm(f['alternate_title']))]
    state='One local identity candidate'if len(ids)==1 else'Multiple local identity candidates – resolve before import'if ids else'Title-only local leads – identity not established'if title else'No match in this local reference; production check required'
    rows.append(dict(key=f['key'],museum_slug=f['museum_slug'],title=f['title'],state=state,local_candidates=sorted(ids),title_only_leads=title if not ids else[],basis=evidence,candidates=[dict(local_artwork_id=i,title=work[i]['title'],date_display=work[i]['date_display'],accession=work[i]['accession_number'],has_image=bool(work[i]['primary_media_id']))for i in sorted(ids)],production_action='Not determined; authenticated live production check mandatory'))
directory=m.h.load(m.RUN/'association-directory.json');unique={};dupes=[]
for r in directory['records']:
    k=(r['name'],r['city'],r['website_url'])
    if k in unique:dupes.append(dict(name=r['name'],city=r['city'],reason='Exact duplicate association entry'))
    else:unique[k]=r
m.h.save(m.RUN/('local-identity-review-final.json'if final else'local-identity-review.json'),dict(at=m.h.now(),reference_snapshot=base['snapshot'],records=rows,counts=dict(collections.Counter(r['state']for r in rows)),limitations='Local read-only reference only. Local IDs must not be used as production insertion targets. No source URL alone links a multi-object chapter/PDF. Different versions, media, loans and casts still require live review.'))
m.h.save(m.RUN/'association-directory-reviewed.json',dict(records=list(unique.values()),raw_entries=len(directory['records']),distinct_entries=len(unique),duplicates=dupes,source=directory['source'],limitations='A German Museums Association membership directory, including foreign members, branches and non-art institutions. Not a census of German museums. Directory research does not imply artwork or image coverage.'))
print('LOCAL IDENTITY',collections.Counter(r['state']for r in rows));print('DIRECTORY',len(unique),'distinct;',len(dupes),'exact duplicate removed')
