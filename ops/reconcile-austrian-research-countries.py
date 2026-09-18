#!/usr/bin/env python3
"""Map explicit source country affiliations, never museum geography or empires."""
import argparse,collections,importlib.util,json,re
from pathlib import Path
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('import-austrian-catalogue.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
WORDS={'Austrian':'AT','German':'DE','French':'FR','Italian':'IT','Dutch':'NL','Czech':'CZ','Hungarian':'HU','Polish':'PL','Swiss':'CH','British':'GB','English':'GB','American':'US','New Zealand':'NZ','Danish':'DK','Norwegian':'NO','Swedish':'SE','Russian':'RU','Greek':'GR','Belgian':'BE','Spanish':'ES'}
COUNTRIES={'Austria':'AT','Germany':'DE','France':'FR','Italy':'IT','the Netherlands':'NL','New Zealand':'NZ'}

def affiliations(text):
    text=re.sub(r'\bAustro[- ]Hungarian\b|\bAustria[- ]Hungary\b','historical Habsburg realm',text,flags=re.I)
    out=set()
    for word,code in WORDS.items():
        if re.search(r'\b'+re.escape(word)+r'(?![- ]born)\b(?:[- /][A-Za-z]+)?(?: [\w-]+){0,5} (?:painter|artist|illustrator|composer|sculptor|printmaker|engraver|draughtsperson)\b',text,re.I):out.add(code)
    for country,code in COUNTRIES.items():
        if re.search(r'\b(?:painter|artist) from '+re.escape(country)+r'\b',text,re.I):out.add(code)
    return sorted(out)

def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['plan','apply']);p.add_argument('--run',type=Path,required=True);p.add_argument('--target',choices=['local','cloud']);args=p.parse_args();run=args.run;path=run/'country-affiliation-plan.json'
    if args.command=='plan':
        if path.exists():return
        mp=a.load(run/'metadata-plan.json');out=[];held=[]
        for q,artist in mp['targets']['local']['artists'].items():
            capture=a.load(run/'wikimedia/entities'/(q+'.json'));text=capture['entity'].get('descriptions',{}).get('en',{}).get('value','');codes=affiliations(text)
            if codes:out.append({'qid':q,'artist':artist['name'],'target_ids':{t:v['artists'][q]['id'] for t,v in mp['targets'].items()},'country_codes':codes,'description':text,'source_url':capture['source_url'],'retrieved_at':capture['retrieved_at'],'source_sha256':capture['evidence_sha256'],'relationship_type':'cultural_affiliation'})
            else:held.append({'qid':q,'artist':artist['name'],'description':text,'reason':'No unambiguous modern country affiliation in the source wording; historical traditions preserved without a modern nationality inference.'})
        a.core.save_new(path,{'at':a.core.now(),'records':out,'held':held});print('Explicit affiliations',len(out),'without mapping',len(held));return
    plan=a.load(path);backup=Path.home()/'Library/Application Support/Artline/backups'/run.name;sid=a.uid('source/'+a.SOURCE);counts=collections.Counter()
    with a.connect(args.target) as db:
        nz=a.load(run/'country-code-nz.json')
        assert nz['code']=='NZ' and nz['name']=='New Zealand' and nz['region_code']=='australia-and-new-zealand' and nz['source_url']=='https://unstats.un.org/unsd/methodology/m49/overview'
        db.execute("INSERT INTO countries(code,name,region_code,historical_note) VALUES('NZ','New Zealand','australia-and-new-zealand',%s) ON CONFLICT(code) DO NOTHING",('UN M49 country 554, ISO alpha-2 NZ, subregion 053. Verified '+nz['retrieved_at']+' at '+nz['source_url'],))
        ids=[x['target_ids'][args.target] for x in plan['records']];before=db.execute('SELECT to_jsonb(c) row FROM artist_countries c WHERE artist_id=ANY(%s::uuid[])',(ids,)).fetchall();file=backup/(args.target+'-country-affiliation-preimages.json')
        if not file.exists():a.core.save_new(file,before)
        for x in plan['records']:
            assert affiliations(x['description'])==x['country_codes'];aid=x['target_ids'][args.target]
            with db.transaction(),db.pipeline():
                assert db.execute("SELECT 1 FROM external_identifiers WHERE entity_type='artist' AND entity_id=%s AND scheme='wikidata' AND external_id=%s",(aid,x['qid'])).fetchone(),'Creator metadata import must precede its country evidence'
                for code in x['country_codes']:
                    assert db.execute('SELECT 1 FROM countries WHERE code=%s',(code,)).fetchone(),'Unsupported country code'
                    inserted=db.execute("INSERT INTO artist_countries(artist_id,country_code,relationship_type,is_primary,note) VALUES(%s,%s,'cultural_affiliation',false,%s) ON CONFLICT DO NOTHING RETURNING artist_id",(aid,code,'Explicit source authority wording: '+x['description']+'. Cultural affiliation; not an inferred birthplace or modern citizenship.')).fetchone();counts['new_affiliations']+=bool(inserted)
                a.citation(db,'artist',aid,'source_cultural_country_affiliation',sid,x['qid'],x['source_url'],{'source_wording':x['description'],'country_codes':x['country_codes'],'relationship_type':'cultural_affiliation','metadata_license':a.CC0,'source_sha256':x['source_sha256'],'policy':'No museum-location inference, no historical empire conversion, no existing country overwritten.'},x['retrieved_at'])
                counts['artists_verified']+=1
    a.core.save_new(run/(args.target+'-country-affiliations.json'),{'at':a.core.now(),'counts':dict(counts)});print(args.target,dict(counts))
if __name__=='__main__':main()
