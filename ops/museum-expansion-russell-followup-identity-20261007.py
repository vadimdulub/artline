#!/usr/bin/env python3
"""Bounded creator, inventory and title comparisons; no database writes."""
import difflib
import argparse
import importlib.util
import re
from pathlib import Path
s=importlib.util.spec_from_file_location('n',Path(__file__).with_name('museum-expansion-russell-followup-research-20261007.py'))
n=importlib.util.module_from_spec(s);s.loader.exec_module(n);w=n.w;m=n.m;RUN=n.RUN
VARIANTS={
"Prosper, d'Epinay":["Prosper d'Épinay","Prosper d'Epinay","Charles Adrien Prosper Caïez d'Épinay"],
'William Ewart Lockhard':['William Ewart Lockhart'],
'Sir Samuel Luke Fildes RA':['Samuel Luke Fildes','Luke Fildes'],
'Robert Poetzelberger':['Robert Pötzelberger'],
'Christopher Nevinson':['Christopher Richard Wynne Nevinson','C. R. W. Nevinson','CRW Nevinson'],
'Jose Benlliure y Gil':['José Benlliure','José Benlliure y Gil'],
'Edward Grenet':['Edouard Grenet','Édouard Grenet'],
'Frederick Goodall RA':['Frederick Goodall'],
'Ferdinand Junck':['Ferdynand Junck'],
'Probably the work of John G. Mossman':['John Mossman','John G. Mossman'],
'Albert Joseph Moore (after)':['Albert Joseph Moore','Albert Moore'],
'Luis Riccardo Falero':['Luis Ricardo Falero'],

'David James':['Joseph Donahue'], 'Francis Derwent Wood':['Derwent Wood'],
'Augusta Freeman':['Horatia Augusta Latilla','Augusta Latilla Freeman'],
'Girolamo Oldofredi':['Gerolamo Oldofredi Tadini'],
'Dominik Skutezky':['Dominik Skutecký','Döme Skutezky'],
'Evelyn de Moran':['Evelyn De Morgan'], 'Edwin Long':['Edwin Longsden Long'],
'George Frederick Watts':['George Frederic Watts'], 'Soloman Hart':['Solomon Alexander Hart','Solomon Hart'],
'Henry Selous':['Henry Courtney Selous','Henry Slous'],'Eugene von Blaas':['Eugene de Blaas','Eugen von Blaas','Eugène de Blaas'],
'Edward Hale':['Edward Matthew Hale'], 'Jan ver der Linde':['Jan van der Linde'],
'Lauritz Holst':['Laurits Bernhard Holst','Lauritz Bernhard Holst'], 'Andreoni Orazio':['Orazio Andreoni'],
'Princess Louise, Duchess of Argyle':['Princess Louise, Duchess of Argyll','Princess Louise'],
'Ernesto Gazzer':['Ernesto Gazzeri','Ernest Gazzeri'],
'Attributed to Jean-Baptiste-Camile Corot':['Jean-Baptiste-Camille Corot','Camille Corot'],
'Pieter Dommershuijzen':['Pieter Cornelis Dommersen','Pieter Cornelis Dommershuijzen'],
'After Jean-Antoine Houdon':['Jean-Antoine Houdon'], 'After Antonio Canova':['Antonio Canova'],
'Minton. After Jean-Jacques Feuchère':['Minton','Jean-Jacques Feuchère'],
}


def names_for(label):
    names={label,*VARIANTS.get(label,[])}
    for x in list(names):
        names.add(re.sub(r'^(?:Sir |After |Attributed to )','',x,flags=re.I))
    return sorted(names)


def tokens(v):return set(re.findall(r'[^\W\d_]+',m.norm(v)))-{'the','de','der','van','von','di','da','la','le','del','after','attributed','to','sir','of'}


def main(suffix):
    assert not (RUN/f'native-identity-{suffix}.json.gz').exists()
    rows=[r for r in m.load(RUN/'native-candidates-003.json.gz')['rows'] if r['state']=='candidate'];names={r['source_id']:names_for(r['facts']['creator_label']) for r in rows};allnames=sorted({a for ns in names.values() for a in ns});keys=sorted({m.norm(x) for x in allnames});patterns=sorted({'%'+last+'%' for x in allnames for last in [m.norm(x).split()[-1],x.split()[-1]] if len(last)>=4 and not re.search('unknown|company',x,re.I)})
    titlekeys=sorted({m.norm(r['facts']['title']) for r in rows}|{m.norm(r['facts']['native_title_caption'].rsplit(',',1)[0]) for r in rows})
    urls=sorted({r['facts']['source_url'] for r in rows});inventories=sorted({x for r in rows for x in [r['facts']['inventory'],w.compact(r['facts']['inventory']).upper(),r['facts']['inventory'].lstrip(':'),re.sub(r'\s+BORGM$','',r['facts']['inventory']),re.sub(r'\s+BORGM$','',r['facts']['inventory']).lstrip(':')]} )
    with m.connect() as db:
        artists=db.execute('SELECT id::text,display_name,normalized_name,slug,birth_year,death_year FROM artists WHERE normalized_name=ANY(%s) OR lower(display_name)=ANY(%s) ORDER BY id',(keys,[x.lower() for x in allnames])).fetchall()
        aliases=db.execute('SELECT aa.artist_id::text,aa.alias,a.display_name FROM artist_aliases aa JOIN artists a ON a.id=aa.artist_id WHERE aa.normalized_alias=ANY(%s) OR lower(aa.alias)=ANY(%s) ORDER BY aa.artist_id,aa.alias',(keys,[x.lower() for x in allnames])).fetchall()
        artistids=sorted({r['id'] for r in artists}|{r['artist_id'] for r in aliases})
        linked=db.execute('''SELECT a.id::text,a.title,a.normalized_title,a.alternate_title,a.date_display,a.creation_year_start,a.creation_year_end,a.date_precision,a.accession_number,a.current_institution_id::text,a.medium_text,a.dimensions_text,a.work_type,a.unlinked_creator_label,
 ARRAY(SELECT aa.artist_id::text FROM artwork_artists aa WHERE aa.artwork_id=a.id ORDER BY aa.artist_id) artist_ids,
 ARRAY(SELECT ar.display_name FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=a.id ORDER BY ar.display_name) creators,
 ARRAY(SELECT c.source_url FROM citations c WHERE c.entity_type='artwork' AND c.entity_id=a.id ORDER BY c.source_url) source_urls
 FROM (SELECT DISTINCT artwork_id FROM artwork_artists WHERE artist_id=ANY(%s::uuid[])) scoped JOIN artworks a ON a.id=scoped.artwork_id ORDER BY a.id''',(artistids,)).fetchall()
        unlinked=db.execute('SELECT id::text,title,normalized_title,alternate_title,date_display,creation_year_start,creation_year_end,date_precision,accession_number,current_institution_id::text,medium_text,dimensions_text,work_type,unlinked_creator_label FROM artworks WHERE unlinked_creator_label ILIKE ANY(%s) ORDER BY id',(patterns,)).fetchall()
        inv=db.execute('SELECT id::text,title,unlinked_creator_label,accession_number,current_institution_id::text FROM artworks WHERE accession_number=ANY(%s::text[]) ORDER BY id',(inventories,)).fetchall()
        exact=db.execute('SELECT id::text,title,normalized_title,unlinked_creator_label,accession_number,current_institution_id::text FROM artworks WHERE normalized_title=ANY(%s::text[]) ORDER BY id',(titlekeys,)).fetchall()
        cites=db.execute("SELECT entity_id::text,source_url FROM citations WHERE entity_type='artwork' AND source_url=ANY(%s) ORDER BY entity_id,source_url",(urls,)).fetchall()
        external=db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND canonical_url=ANY(%s) ORDER BY entity_id,external_id",(urls,)).fetchall()
        # Inventory namespace variants: BORGM and SC numbers are not stripped to bare digits.
        museum_inventory=db.execute("SELECT id::text,title,normalized_title,unlinked_creator_label,accession_number,current_institution_id::text FROM artworks WHERE accession_number LIKE 'BORGM%%' OR accession_number LIKE ':BORGM%%' OR accession_number LIKE 'SC%%' OR accession_number LIKE 'Sc%%' OR accession_number LIKE 'RC%%' OR accession_number LIKE ':T%%' OR accession_number LIKE 'T%%' ORDER BY id").fetchall()
    result=dict(at=m.now(),names_by_source=names,all_names=allnames,name_keys=keys,unlinked_patterns=patterns,title_keys=titlekeys,source_urls=urls,inventories=inventories,artist_ids=artistids,artists=artists,aliases=aliases,linked=linked,unlinked=unlinked,inventory_lookup=inv,exact_title_lookup=exact,source_url_lookup=cites,source_external_lookup=external,museum_inventory= museum_inventory,policy='Read-only identity scope. Creator-name variants are search leads, not metadata edits or new artist links. Native inventories remain literal and museum-scoped. Exact accented display names and raw surname spellings supplement legacy normalized fields.')
    m.save(RUN/f'native-identity-{suffix}.json.gz',result)
    comps=[]
    for r in rows:
        f=r['facts'];ns=set(names[r['source_id']]);sourcekeys={m.norm(x) for x in ns};aids={x['id'] for x in artists if m.norm(x['display_name']) in sourcekeys}|{x['artist_id'] for x in aliases if m.norm(x['alias']) in sourcekeys}
        ns.update(x['display_name'] for x in artists if x['id'] in aids)
        pool=[x for x in linked if set(x['artist_ids'])&aids]
        pool += [x for x in unlinked if any(tokens(name) and tokens(name)<=tokens(x['unlinked_creator_label']) for name in ns) and x['id'] not in {y['id'] for y in pool}]
        def score(x):return max(difflib.SequenceMatcher(None,m.norm(f['title']),m.norm(x[k])).ratio() for k in ['title','alternate_title'] if x.get(k))
        c=dict(source_id=r['source_id'],facts=f,search_names=sorted(ns),artist_ids=sorted(aids),creator_pool_ids=[x['id'] for x in pool],leads=sorted(pool,key=score,reverse=True)[:6],exact_title_hits=[x for x in exact if m.norm(x['title']) in {m.norm(f['title']),m.norm(f['native_title_caption'].rsplit(',',1)[0])}],inventory_hits=[x for x in museum_inventory+inv if n.inventory_key(x['accession_number'])==n.inventory_key(f['inventory'])],source_hits=[x for x in cites if x['source_url']==f['source_url']]+[x for x in external if x['canonical_url']==f['source_url']])
        comps.append(c)
    m.save(RUN/f'native-comparisons-{suffix}.json.gz',dict(at=m.now(),records=comps,policy='Heuristic title ranks guide individual review; all creator-scoped rows remain in the full scope. No new-artwork approval.'))
    print({k:len(result[k]) for k in ['artists','aliases','linked','unlinked','inventory_lookup','exact_title_lookup','source_url_lookup','museum_inventory']})
    for c in comps:
        leads=[dict(id=x['id'],title=x['title'],date=x['date_display'],inventory=x['accession_number'],creator=x.get('creators') or x.get('unlinked_creator_label')) for x in c['leads'] if score(x)>=0] # printed candidates are still manual leads
        print(c['source_id'],'INV',c['inventory_hits'],'SOURCE',c['source_hits'],'LEADS',leads[:3])


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--suffix',default='003');a=p.parse_args();assert re.fullmatch(r'\d{3}',a.suffix);main(a.suffix)
