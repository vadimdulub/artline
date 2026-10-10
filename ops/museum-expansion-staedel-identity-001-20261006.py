#!/usr/bin/env python3
"""Read-only creator and translated-title duplicate leads for Städel."""
import argparse
import difflib
import functools
import importlib.util
import re
from pathlib import Path

spec=importlib.util.spec_from_file_location('s',Path(__file__).with_name('museum-expansion-staedel-20261006.py'))
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
m=s.m
VARIANTS={
 'Alexej von Jawlensky':['Alexey von Jawlensky','Alexej Georgewitsch von Jawlensky'],
 'Rembrandt Harmensz. van Rijn':['Rembrandt','Rembrandt van Rijn'],
 'Auguste Renoir':['Pierre-Auguste Renoir'], 'Claude Monet':['Oscar-Claude Monet'],
 'Jan Brueghel the Elder':['Jan Brueghel the elder','Jan Brueghel I'],
 'Jan Brueghel the Younger':['Jan Brueghel II'], 'Aert van der Neer':['Aert van der Neer'],
 'Francesco Guardi':['Francesco Lazzaro Guardi'], 'Carl Morgenstern':['Karl Morgenstern'],
 'Carl Schuch':['Karl Schuch'], 'Jacob Isaacksz. van Ruisdael':['Jacob van Ruisdael'],
 'Gerrit Adriaensz. Berckheyde':['Gerrit Berckheyde'], 'Giovanni Battista Tiepolo':['Giambattista Tiepolo'],
 'Pompeo Girolamo Batoni':['Pompeo Batoni'], 'Giovanni Antonio Canal called Canaletto':['Canaletto','Giovanni Antonio Canal'],
 'Jacopo Robusti called Tintoretto':['Tintoretto','Jacopo Tintoretto'], 'Jacob Jordaens':['Jakob Jordaens'],
 'François Boucher':['Francois Boucher'], 'Sandro Botticelli':['Botticelli'],
 'Johann Heinrich Wilhelm Tischbein':['Johann Heinrich Tischbein'],
 'Jean-Baptiste Siméon Chardin':['Jean Baptiste Simeon Chardin'],
 'Adolf Schreyer':['Christian Adolf Schreyer'],
 'Henri Evenepoel':['Henri Jacques Edouard Evenepoel'],
 'Pieter Jacobsz. Codde':['Pieter Codde'],
 'Théodule Ribot':['Augustin Théodule Ribot','Théodule-Augustin Ribot'],
 'Bartholomäus Bruyn the Elder':['Bruyn der Ältere Bartholomäus','Barthel Bruyn the Elder'],
 'Günter Fruhtrunk':['Fruhtrunk Günter'],
 'Theobald Michau':['Michau Theobald'],
 'Godfried Schalcken':['Godefridus Schalcken'],
 'Pieter Janssens':['Pieter Janssens Elinga','Pieter Elinga'],
 'Altobello Meloni':['Altobello Melone'],
 'Paul Meyerheim':['Paul Friedrich Meyerheim'],
 'Carl Georg Adolph Hasenpflug':['Carl Hasenpflug'],
 'Karl von Pidoll':['Karl von Pidoll zu Quinten'],
 'Johan Christian Clausen Dahl':['Johan Christian Dahl','Johann Christian Dahl'],
 'Camille Corot':['Jean-Baptiste-Camille Corot'],
}


@functools.lru_cache(maxsize=20000)
def name_tokens(value):
    return frozenset(re.findall(r'[^\W\d_]+',m.norm(value),re.U)) - {'the','de','der','van','von','di','da','la','le','del','called'}


def label_matches(label,names):
    tokens=name_tokens(label)
    return any(name_tokens(name) and name_tokens(name)<=tokens for name in names)


def main(suffix='001'):
    research=m.load(s.RUN/'staedel-001-research.json.gz')
    labels=sorted({r['facts']['creator_label'] for r in research['records']})
    names=set(labels)
    for label in labels:
        for name in label.split(', '):
            bare=re.sub(r'\s*\?$','',name.split(';')[0]).strip()
            names.add(bare);names.update(VARIANTS.get(bare,[]))
    names=sorted(names);keys=[m.norm(x) for x in names]
    with m.connect() as db:
        artists=db.execute('''SELECT id::text,display_name,normalized_name,sort_name,slug FROM artists
          WHERE normalized_name=ANY(%s) OR lower(display_name)=ANY(%s) ORDER BY id''',(keys,[v.lower() for v in names])).fetchall()
        aliases=db.execute('''SELECT aa.artist_id::text,aa.alias,aa.normalized_alias,a.display_name
          FROM artist_aliases aa JOIN artists a ON a.id=aa.artist_id WHERE aa.normalized_alias=ANY(%s) ORDER BY aa.artist_id,aa.alias''',(keys,)).fetchall()
        ids=sorted({v['id'] for v in artists}|{v['artist_id'] for v in aliases})
        rows=db.execute('''SELECT a.id::text,a.title,a.alternate_title,a.creation_year_start,a.creation_year_end,a.date_display,
          a.accession_number,a.unlinked_creator_label,a.current_institution_id::text,a.work_type,a.medium_text,a.dimensions_text,
          ARRAY(SELECT ar.display_name FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=a.id ORDER BY ar.display_name) creators,
          ARRAY(SELECT c.source_url FROM citations c WHERE c.entity_type='artwork' AND c.entity_id=a.id ORDER BY c.source_url) source_urls
          FROM (SELECT DISTINCT artwork_id FROM artwork_artists WHERE artist_id=ANY(%s::uuid[])) scoped
          JOIN artworks a ON a.id=scoped.artwork_id ORDER BY a.id''',(ids,)).fetchall()
        # Catalogue object labels can put surname first and insert role/lifespan
        # text. Search a bounded set of creator-name tokens, then require the
        # complete unordered name before keeping a duplicate-review lead.
        patterns=sorted({'%'+token+'%' for v in names if not any(w in v.lower() for w in ['unknown','anonymous','master']) for token in name_tokens(v) if len(token)>3})
        unlinked=db.execute('''SELECT id::text,title,alternate_title,creation_year_start,creation_year_end,date_display,
          accession_number,unlinked_creator_label,current_institution_id::text,work_type,medium_text,dimensions_text,
          ARRAY(SELECT c.source_url FROM citations c WHERE c.entity_type='artwork' AND c.entity_id=a.id ORDER BY c.source_url) source_urls
          FROM artworks a WHERE unlinked_creator_label ILIKE ANY(%s) ORDER BY id''',(patterns,)).fetchall()
        unlinked=[r for r in unlinked if label_matches(r['unlinked_creator_label'],names)]
        collisions=s.title_collisions(db,research['records'])
    identity=dict(at=m.now(),source_creator_labels=labels,names=names,variants=VARIANTS,artists=artists,aliases=aliases,artworks=rows,unlinked_artworks=unlinked,title_collisions=collisions,
        policy='Exact and qualified name variants are duplicate-search leads, not approved painter identities or links.')
    destination=s.RUN/f'creator-identity-review-{suffix}.json'
    assert not destination.exists(), 'Preserve previous identity evidence'
    m.save(destination,identity)
    aliasmap={}
    for alias in aliases:aliasmap.setdefault(m.norm(alias['alias']),set()).add(alias['display_name'])
    allrows={r['id']:r for r in rows+unlinked};comparisons=[]
    for record in research['records']:
        label=record['facts']['creator_label'];expanded={label}
        for name in label.split(', '):
            bare=re.sub(r'\s*\?$','',name.split(';')[0]).strip();expanded.add(bare);expanded.update(VARIANTS.get(bare,[]))
        for name in list(expanded):expanded.update(aliasmap.get(m.norm(name),[]))
        keys={m.norm(v) for v in expanded}
        pool=[r for r in allrows.values() if keys&{m.norm(v) for v in r.get('creators',[])} or label_matches(r.get('unlinked_creator_label'),expanded)]
        title=m.norm(record['facts']['title'])
        def score(row):return max(difflib.SequenceMatcher(None,title,m.norm(row[k])).ratio() for k in ['title','alternate_title'] if row.get(k))
        comparisons.append(dict(source_record_id=record['source_record_id'],title=record['facts']['title'],creator_label=label,search_names=sorted(expanded),pool_size=len(pool),pool_ids=[r['id'] for r in pool],leads=sorted(pool,key=score,reverse=True)[:8]))
    m.save(s.RUN/f'creator-title-comparison-leads-{suffix}.json',dict(at=m.now(),records=comparisons,policy='Heuristic title ranking only; full creator-scoped rows retained for object-version review.'))
    print('Städel creator review',len(artists),'artists',len(aliases),'aliases',len(rows),'linked rows',len(unlinked),'unlinked labels',len(collisions),'title collisions',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--suffix',default='001')
    args=parser.parse_args();assert re.fullmatch(r'\d{3}',args.suffix);main(args.suffix)
