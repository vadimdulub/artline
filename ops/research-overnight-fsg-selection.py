#!/usr/bin/env python3
"""Read official FSG metadata and select exact named-creator CC0 image leads."""
import argparse,collections,importlib.util,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('fsg',ROOT/'ops/overnight-fsg-images.py');fsg=importlib.util.module_from_spec(s);s.loader.exec_module(fsg);core=fsg.core

def main():
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);a=p.parse_args();r=a.run
    if (r/'source-leads.json').exists():raise SystemExit('Pinned selection already exists')
    with fsg.ro('postgres://localhost/artline') as db:
        people=db.execute("""SELECT a.id::text,a.slug,a.display_name,a.birth_year,a.death_year,
          (SELECT e.external_id FROM external_identifiers e WHERE e.entity_type='artist' AND e.entity_id=a.id AND e.scheme='wikidata') qid,
          ARRAY(SELECT al.alias FROM artist_aliases al WHERE al.artist_id=a.id) aliases,
          EXISTS(SELECT 1 FROM artist_discovery_selection d WHERE d.artist_id=a.id AND d.is_popular) popular
          FROM artists a WHERE a.status<>'archived'""").fetchall()
        existing={x['external_id'] for x in db.execute("SELECT external_id FROM external_identifiers WHERE entity_type='artwork' AND scheme='fsg-object'").fetchall()}
    index=collections.defaultdict(dict)
    for artist in people:
        for name in [artist['display_name']]+artist['aliases']:index[fsg.norm(name)][artist['id']]=artist
    rows=[];held=[];scanned=0
    urls=(r/'index.txt').read_text().splitlines();assert len(urls)==256
    for url in urls:
        path=r/'metadata'/url.rsplit('/',1)[-1];raw=path.read_bytes();receipt=json.loads(path.with_suffix('.receipt.json').read_text());assert core.sha(raw)==receipt['sha256'] and receipt['url']==url
        for line in raw.splitlines():
            o=json.loads(line);scanned+=1;dn=o['content']['descriptiveNonRepeating'];ft=o['content'].get('freetext',{});record=dn.get('record_ID','');oid=record.removeprefix('fsg_')
            mapping={('Painting',):'painting',('Drawing',):'drawing',('Print',):'print'};typ=mapping.get(tuple(fsg.fields(ft,'objectType','Type')))
            if not typ or oid in existing:continue
            try:
                names=fsg.fields(ft,'name','Artist')
                if len(names)!=1:raise ValueError('Unidentified or multiple artists: preserve for separate creator review')
                hits={}
                for variant in fsg.creator_variants(names[0]):hits.update(index[fsg.norm(variant)])
                if len(hits)!=1:raise ValueError('Creator not uniquely matched to existing painter')
                artist=next(iter(hits.values()))
                if not artist['qid']:raise ValueError('Existing painter authority missing')
                life=re.search(r'\((\d{4})[-–—](\d{4})\)',names[0])
                if life and any(a is not None and a!=int(b) for a,b in zip((artist['birth_year'],artist['death_year']),(life[1],life[2]))):raise ValueError('Museum creator biography conflicts with existing identity')
                dates=fsg.fields(ft,'date','Date')
                if len(dates)!=1:raise ValueError('No unique creation date')
                lo,hi,precision=fsg.date_parts(dates[0])
                if (artist['birth_year'],artist['death_year'])==(lo,hi) and lo!=hi:raise ValueError('Creation interval equals painter lifespan')
                origin='; '.join(fsg.fields(ft,'place','Origin'))
                c={'external_id':oid,'title':dn['title']['content'],'work_type':typ,'accession_number':oid,'date_display':dates[0],'creation_year_start':lo,'creation_year_end':hi,'date_precision':precision,'artist':artist['display_name'],'aliases':artist['aliases'],'roles':['primary'],'creation_place_display':origin}
                fsg.source_match(c,o)
                rows.append({'source_object_id':oid,**{k:c[k] for k in ('title','work_type','accession_number','date_display','creation_year_start','creation_year_end','date_precision','creation_place_display')},'artist':artist,'object':o,'metadata_capture':receipt})
            except ValueError as exc:held.append({'source_object_id':oid,'reason':str(exc)})
    rows.sort(key=lambda c:(not c['artist']['popular'],c['work_type']!='painting',c['artist']['display_name'],c['source_object_id']))
    core.save_new(r/'source-leads.json',rows);core.save_new(r/'selection-held.json',held)
    report={'at':core.now(),'scanned_source_objects':scanned,'selected_image_leads':len(rows),'popular':sum(c['artist']['popular'] for c in rows),'by_type':dict(collections.Counter(c['work_type'] for c in rows)),'held':dict(collections.Counter(c['reason'] for c in held)),'note':'Metadata selection precedes images. Qualified and unidentified creators are retained as review leads. Origin is artwork provenance, never inferred painter nationality.'}
    core.save_new(r/'source-lead-report.json',report);print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)
if __name__=='__main__':main()
