#!/usr/bin/env python3
"""Read-only creator-scoped duplicate research for selected Serbian records."""
import argparse
import difflib
import functools
import importlib.util
import re
from pathlib import Path

spec=importlib.util.spec_from_file_location('s',Path(__file__).with_name('museum-expansion-serbia-20261007.py'))
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
m=s.m
CYR='абвгдђежзијклљмнњопрстћуфхцчџш'
LAT=['a','b','v','g','d','đ','e','ž','z','i','j','k','l','lj','m','n','nj','o','p','r','s','t','ć','u','f','h','c','č','dž','š']
TRANS=dict(zip(CYR,LAT))
def latin(value):return ''.join(TRANS.get(c,c) for c in (value or '').lower())

# Search aids only: source creator labels and catalogue titles remain literal.
NAMES={
 1:['Đorđe Krstić','Djordje Krstic'],2:['Vlaho Bukovac'],3:['Uroš Predić'],5:['Paja Jovanović','Pavle Paja Jovanović'],6:['Pavle Simić'],7:['Pavel Đurković','Pavel Djurkovic'],8:['Konstantin Danil'],9:['Đura Jakšić','Djura Jaksic'],10:['Katarina Ivanović'],12:['Uroš Knežević'],13:['Petar Lubarda'],14:['Nadežda Petrović'],15:['Marko Murat'],16:['Sava Šumanović'],17:['Milan Milovanović'],18:['Peđa Milosavljević','Predrag Milosavljević'],19:['Boža Ilić'],20:['Milan Konjović'],21:['Marko Čelebonović'],22:['Milena Pavlović-Barili','Milena Pavlovic Barilli'],23:['Živorad Nastasijević'],24:['Radomir Damnjanović','Radomir Damjanović Damnjan'],
 35:['Vincent van Gogh'],36:['Pierre-Auguste Renoir'],37:['Pablo Picasso'],38:['Francesco Guardi'],39:['Jan Brueghel the Elder','Jan Brueghel I'],40:['Nicolas Régnier','Niccolò Renieri'],41:['Henri de Toulouse-Lautrec'],42:['Piet Mondrian'],43:['Mary Cassatt'],44:['Claude Monet'],45:['Camille Pissarro'],46:['Hubert Robert'],47:['Tintoretto','Jacopo Tintoretto','Jacopo Robusti'],48:['Josip Seissel','Josip Sajsel','Jo Klek'],49:['Anastas Jovanović'],51:['Uroš Predić'],52:['Sava Šumanović'],53:['Mihailo Petrov'],54:['Adam Stefanović'],55:['August Černigoj'],56:['Vinko Foretić'],57:['Dimitrije Avramović'],58:['Albrecht Dürer'],60:['Vincent van Gogh'],61:['Jacques Callot'],62:['Hannes Meyer'],63:['Paul Gauguin'],64:['Pierre-Auguste Renoir'],65:['Edgar Degas'],66:['Louis Lozowick'],67:['Wassily Kandinsky','Vasily Kandinsky'],68:['Đorđe Jovanović','Djordje Jovanovic'],69:['Ivan Rendić'],70:['Simeon Roksandić'],71:['Petar Ubavkić'],72:['Frano Kršinić'],73:['Risto Stijović'],74:['Đorđe Jovanović','Djordje Jovanovic'],75:['Petar Palavičini','Petar Pallavicini'],77:['Ivan Meštrović'],78:['Sreten Stojanović']}
TITLES={
 1:['Under the Apple Tree'],2:['Portrait of Queen Natalie Obrenovic','Queen Natalija'],3:['Herzegovinian Refugees'],5:['The Proclamation of Dusan’s Law Codex','Coronation of Emperor Dusan'],6:['Portrait of Vasilije Nikolajevic'],7:['Prince Milos with a Turban'],8:['Portrait of the Artist’s Wife','Sofia Dely'],9:['Rest after the Battle','Guardhouse'],10:['Self Portrait'],11:['Portrait of Count Georgije Brankovic'],12:['Karadjordje'],13:['Stony Sea'],14:['Self Portrait'],15:['Entry of Emperor Dusan into Dubrovnik'],16:['Red Carpet'],17:['Blue Door'],18:['White Windows'],19:['Surveying the Terrain in New Belgrade'],20:['Wheat'],21:['Family Group'],22:['Composition'],24:['Blue Circle'],
 35:['Peasant Woman'],36:['Bather'],37:['Head of a Woman','Woman’s Head'],38:['St Mark’s Square in Venice','Piazza San Marco'],39:['Flowers','Vase of Flowers'],40:['David with the Head of Goliath'],41:['Portrait of a Young Woman'],42:['Composition II'],43:['Woman and Child I','Mother and Child'],44:['Rouen Cathedral'],45:['Place du Theatre Francais'],46:['The Staircase of the Park of the Villa Farnese at Caprarola','Stairs in the Park of the Villa Farnese'],47:['Madonna and Child with a Senator'],48:['Advertisements','Reklame'],49:['Portrait of Petar II Petrovic Njegos'],51:['The Gusle Player','Guslar'],52:['Bathers'],53:['Rhythm'],54:['Battle of Kosovo'],55:['Comme attraverso la strada'],56:['Man with a Cigarette','Portrait of a Slovene'],57:['Expulsion of Adam and Eve'],58:['Peasant Couple with a Dove'],60:['Man Writing at a Desk','Writer at a Table'],61:['Beggar with a Wooden Leg'],62:['Co-op III'],63:['Joys of Brittany','Joies de Bretagne'],64:['Coco Writing','Boy with a Pen'],65:['Three Dancers'],66:['Russian Church'],67:['Orange'],68:['Scent of Roses'],69:['Embarrassed Bather'],70:['Boy Removing a Thorn'],71:['Vuk Karadzic'],72:['Awakening'],73:['Head of a Woman','Byzantine Woman'],74:['Abandoned'],75:['Girl with a Bowl'],77:['Remembrance'],78:['Head of Giacometti'],
 25:['Virgin and Child','Mother of God and Child'],26:['Virgin','Mother of God'],27:['Pectoral Cross'],28:['Nativity'],29:['Jerusalem Pilgrimage Icon'],30:['Belt Buckle','Paftes'],33:['Cup'],34:['Cup'],82:['Earring'],83:['Ring'],84:['Earrings'],85:['Ring'],86:['Archer Ring','Thumb Ring'],87:['Ring of Duke Vladislav'],88:['Bowl with Evangelists'],90:['Earring'],91:['Head of Christ','Christ Head'],92:['Bracelet'],93:['Bowl']}


@functools.lru_cache(maxsize=30000)
def tokens(value):return frozenset(re.findall(r'[^\W\d_]+',m.norm(latin(value)),re.U))-{'de','van','the','le','la','da','di','of'}
def label_matches(label,names):
    t=tokens(label)
    return any(tokens(name) and tokens(name)<=t for name in names)


def main(suffix):
    dest=s.RUN/f'creator-identity-review-{suffix}.json.gz';assert not dest.exists()
    records=m.load(s.RUN/'serbia-caption-001-research.json.gz')['records']+m.load(s.RUN/'serbia-vr-001-research.json.gz')['records']+m.load(s.RUN/'serbia-report-001-research.json.gz')['records']
    search={}
    for r in records:
        f=r['facts'];num=r['raw_source_record'].get('queue_number');names=set(NAMES.get(num,[]))
        if f['creator_label'] and f['creator_label']!='Непознати аутор':names.update([f['creator_label'],latin(f['creator_label'])])
        if f['creator_label']=='Јован Исајловић млађи':names.update(['Jovan Isailović the Younger','Jovan Isajlović the Younger'])
        if f['creator_label']=='Јефтимије Поповић':names.update(['Jeftimije Popović','Jeftimij Popović'])
        if r['source_record_id'].startswith('vr-') and 'jovanovic' in m.norm(f['creator_label']):names.update(NAMES[5])
        names.update(m.norm(name) for name in list(names))
        names.update(name.replace('đ','dj') for name in list(names))
        titlelist={f['title'],latin(f['title'])}|set(TITLES.get(num,[]))
        search[r['source_record_id']]=dict(names=sorted(names),titles=sorted(titlelist))
    names=sorted({v for x in search.values() for v in x['names']});keys=[m.norm(v) for v in names]
    with m.connect() as db:
        artists=db.execute('SELECT id::text,display_name,normalized_name,sort_name,slug FROM artists WHERE normalized_name=ANY(%s) OR lower(display_name)=ANY(%s) ORDER BY id',(keys,[v.lower() for v in names])).fetchall()
        aliases=db.execute('SELECT aa.artist_id::text,aa.alias,aa.normalized_alias,a.display_name FROM artist_aliases aa JOIN artists a ON a.id=aa.artist_id WHERE aa.normalized_alias=ANY(%s) ORDER BY aa.artist_id,aa.alias',(keys,)).fetchall()
        ids=sorted({v['id'] for v in artists}|{v['artist_id'] for v in aliases})
        cols='''a.id::text,a.title,a.alternate_title,a.creation_year_start,a.creation_year_end,a.date_display,a.accession_number,a.unlinked_creator_label,a.current_institution_id::text,a.work_type,a.medium_text,a.dimensions_text,
          ARRAY(SELECT ar.display_name FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=a.id ORDER BY ar.display_name) creators,
          ARRAY(SELECT c.source_url FROM citations c WHERE c.entity_type='artwork' AND c.entity_id=a.id ORDER BY c.source_url) source_urls'''
        linked=db.execute('SELECT '+cols+' FROM (SELECT DISTINCT artwork_id FROM artwork_artists WHERE artist_id=ANY(%s::uuid[])) scoped JOIN artworks a ON a.id=scoped.artwork_id ORDER BY a.id',(ids,)).fetchall()
        patterns=sorted({'%'+t+'%' for name in names for t in re.findall(r'[^\W\d_]+',name,re.U) if len(t)>3})
        raw=db.execute('SELECT '+cols+' FROM artworks a WHERE unlinked_creator_label ILIKE ANY(%s) ORDER BY a.id',(patterns,)).fetchall()
        unlinked=[r for r in raw if label_matches(r['unlinked_creator_label'],names)]
        titlekeys=sorted({m.norm(v) for x in search.values() for v in x['titles']})
        collisions=db.execute('SELECT '+cols+' FROM artworks a WHERE normalized_title=ANY(%s) OR lower(title)=ANY(%s) OR lower(alternate_title)=ANY(%s) ORDER BY a.id',(titlekeys,titlekeys,titlekeys)).fetchall()
    allrows={r['id']:r for r in linked+unlinked};comparisons=[]
    aliasmap={}
    for v in aliases:aliasmap.setdefault(m.norm(v['alias']),set()).add(v['display_name'])
    for r in records:
        x=search[r['source_record_id']];expanded=set(x['names'])
        for name in list(expanded):expanded.update(aliasmap.get(m.norm(name),[]))
        pool=[v for v in allrows.values() if any(label_matches(c,expanded) for c in v['creators']) or label_matches(v['unlinked_creator_label'],expanded)]
        keys={m.norm(latin(v)) for v in x['titles']}
        def score(v):return max(difflib.SequenceMatcher(None,k,m.norm(latin(v[t]))).ratio() for k in keys for t in ['title','alternate_title'] if v.get(t))
        exact=[v for v in collisions if keys&{m.norm(latin(v[t])) for t in ['title','alternate_title'] if v.get(t)}]
        comparisons.append(dict(source_record_id=r['source_record_id'],queue_number=r['raw_source_record'].get('queue_number'),facts=r['facts'],search_names=sorted(expanded),search_titles=x['titles'],pool_size=len(pool),pool_ids=[v['id'] for v in pool],leads=sorted(pool,key=score,reverse=True)[:10],exact_title_leads=exact))
    m.save(dest,dict(at=m.now(),artists=artists,aliases=aliases,linked=linked,unlinked=unlinked,collisions=collisions,search=search,policy='Search-only name and translated title variants. No artist links or metadata changes. Full creator-scoped rows retained; rank is not approval.'))
    m.save(s.RUN/f'creator-title-comparison-leads-{suffix}.json.gz',dict(at=m.now(),records=comparisons))
    print('Serbia identity:',len(artists),'artists;',len(aliases),'aliases;',len(linked),'linked;',len(unlinked),'unlinked;',len(collisions),'title leads',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--suffix',default='002');args=p.parse_args();assert re.fullmatch(r'\d{3}',args.suffix);main(args.suffix)
