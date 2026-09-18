#!/usr/bin/env python3
"""Two reviewed, source-backed refinements: Ukrainian affiliation and co-creator."""
import importlib.util,json,subprocess
from pathlib import Path
s=importlib.util.spec_from_file_location('p',Path(__file__).with_name('research-country-primary.py'));p=importlib.util.module_from_spec(s);s.loader.exec_module(p)
m=p.m;RUN=m.x.BASE/'primary-refinements'
def main():
 pdf=m.x.BASE/'gritchenko-country/mesher-gritchenko.pdf';receipt=json.loads(pdf.with_suffix('.receipt.json').read_text());assert m.m.core.sha(pdf.read_bytes())==receipt['sha256'];text=subprocess.check_output(['pdftotext',str(pdf),'-']).decode();assert 'The Ukrainian artist Alexis Gritchenko' in text and '1883' in text and '1977' in text
 q='Q17330441';rec=json.loads((m.x.BASE/'NL/round-02/delivery/ready'/(q+'.json')).read_text())['record'];data,_=m.x.r.fetch('https://data.rijksmuseum.nl/search/collection?'+p.urlencode({'objectNumber':rec['accession']}));obj,oreceipt=m.x.r.fetch(data['orderedItems'][0]['id']+'?_profile=la-framed');prod=obj['produced_by'];assert any('Dirck Wijntrack, anonymous'==v for v in p.values(prod,'content'));assert any('c. 1652'==v for v in p.values(prod,'content'))
 m.m.core.save_new(RUN/'reviewed-evidence.json',{'country':{'artist_slug':'alexis-gritchenko-research-83eca0e9af0b','country':'UA','source_receipt':receipt,'page':2,'explicit_source_wording':'The Ukrainian artist Alexis Gritchenko','life_dates':[1883,1977],'context':'Museum curator biography distinguishes Ukrainian affiliation from artistic activity in Moscow and later residence in France.'},'artwork':{'qid':q,'source_receipt':oreceipt,'source_production':prod,'anonymous_collaborator':True,'date':'c. 1652'}})
 snapshots={}
 for target in ['local','production']:
  dest=m.BACKUPS/('primary-refinements-'+target+'-preimages.json')
  if dest.exists():snapshots[target]=json.loads(dest.read_text());continue
  with m.m.r.base.connect(target=='production') as db,db.transaction():
   db.execute('SET TRANSACTION READ ONLY')
   artist=db.execute("SELECT to_jsonb(a) row FROM artists a WHERE slug='alexis-gritchenko-research-83eca0e9af0b'").fetchone()['row'];assert artist['status']=='review' and artist['birth_year']==1883 and artist['death_year']==1977
   countries=db.execute('SELECT to_jsonb(c) row FROM artist_countries c WHERE artist_id=%s',(artist['id'],)).fetchall();assert not countries
   authority=db.execute("SELECT 1 FROM external_identifiers WHERE entity_type='artist' AND entity_id=%s AND scheme='smk-person' AND external_id='2859_person'",(artist['id'],)).fetchone();assert authority
   work=db.execute('SELECT to_jsonb(a) row FROM artworks a WHERE slug=%s',('wikimedia-artwork-'+q.lower(),)).fetchone()['row'];assert work['status']=='review' and work['date_precision']=='range' and work['creation_year_start']==1635 and work['creation_year_end']==1678
   links=db.execute('SELECT to_jsonb(aa) row FROM artwork_artists aa WHERE artwork_id=%s',(work['id'],)).fetchall();assert len(links)==1 and links[0]['row']['attribution_role']=='primary'
  snapshots[target]={'artist':artist,'countries':countries,'work':work,'links':links};m.m.core.save_new(dest,snapshots[target])
 for target in ['local','production']:
  dest=RUN/(target+'-verification.json')
  if dest.exists():continue
  old=snapshots[target]
  with m.m.r.base.connect(target=='production') as db,db.transaction():
   db.execute('SELECT pg_advisory_xact_lock(559220260914)')
   artist=db.execute('SELECT to_jsonb(a) row FROM artists a WHERE id=%s FOR UPDATE',(old['artist']['id'],)).fetchone()['row'];assert artist==old['artist']
   work=db.execute('SELECT to_jsonb(a) row FROM artworks a WHERE id=%s FOR UPDATE',(old['work']['id'],)).fetchone()['row'];assert work==old['work']
   sid=m.m.source(db,'overnight-mesher-creator-country-20260913','Meşher curator biography — Alexis Gritchenko','article','https://www.mesher.org/')
   db.execute("INSERT INTO artist_countries(artist_id,country_code,relationship_type,is_primary,note) VALUES(%s,'UA','cultural_affiliation',false,%s)",(artist['id'],'Meşher curator biography explicitly identifies a Ukrainian artist; artistic activity in Moscow and residence in France are distinct facts.'))
   db.execute("UPDATE artists SET geography_review_state='classified',revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s",(m.m.ACTOR,artist['id']))
   m.m.r.base.insert(db,'citations',dict(entity_type='artist',entity_id=artist['id'],source_id=sid,field_name='geography',source_record_id='alexis-gritchenko-20200515-p2',source_url=receipt['url'],retrieved_at=receipt['retrieved_at'],created_by=m.m.ACTOR,evidence_note=json.dumps({'country':'UA','source_wording':'The Ukrainian artist Alexis Gritchenko','life_dates':[1883,1977],'source_receipt':receipt,'source_page':2,'superseded_proposal':'SMK Russisk label held, never added; no Russian nationality inferred from Moscow activity.'},ensure_ascii=False)))
   sid=m.m.source(db,'overnight-rijksmuseum-primary-20260913','Rijksmuseum official object and creator authority cross-checks','museum_api','https://data.rijksmuseum.nl/')
   note='Rijksmuseum names Dirck Wijntrack and an anonymous collaborator. The anonymous contributor is represented on the object, not as an invented artist profile.'
   db.execute("UPDATE artworks SET date_display='c. 1652',creation_year_start=1652,creation_year_end=1652,date_precision='circa',unlinked_creator_label='Anonymous collaborator',description_md=%s,revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s",(work['title']+'. '+note+' Museum dating: c. 1652. Metadata remains in review.',m.m.ACTOR,work['id']))
   db.execute('UPDATE artwork_artists SET attribution_note=%s WHERE artwork_id=%s',(note,work['id']))
   m.m.r.base.insert(db,'citations',dict(entity_type='artwork',entity_id=work['id'],source_id=sid,field_name='official_date_and_collaborator_review',source_record_id=obj['id'].rsplit('/',1)[-1],source_url=obj['id'],retrieved_at=oreceipt['retrieved_at'],created_by=m.m.ACTOR,evidence_note=json.dumps({'source_receipt':oreceipt,'production':prod,'date_classification':'circa','anonymous_creator_support':'Object-level label; no anonymous person profile invented.'},ensure_ascii=False)))
  with m.m.r.base.connect(target=='production') as db,db.transaction():
   db.execute('SET TRANSACTION READ ONLY');a=db.execute('SELECT to_jsonb(a) row FROM artists a WHERE id=%s',(old['artist']['id'],)).fetchone()['row'];w=db.execute('SELECT to_jsonb(w) row FROM artworks w WHERE id=%s',(old['work']['id'],)).fetchone()['row']
   ignored={'geography_review_state','revision','updated_at','updated_by'};assert {k:v for k,v in a.items() if k not in ignored}=={k:v for k,v in old['artist'].items() if k not in ignored};assert a['status']=='review' and a['geography_review_state']=='classified'
   codes=db.execute('SELECT country_code FROM artist_countries WHERE artist_id=%s',(a['id'],)).fetchall();assert codes==[{'country_code':'UA'}]
   ignored={'date_display','creation_year_start','creation_year_end','date_precision','unlinked_creator_label','description_md','revision','updated_at','updated_by'};assert {k:v for k,v in w.items() if k not in ignored}=={k:v for k,v in old['work'].items() if k not in ignored};assert w['date_precision']=='circa' and w['creation_year_start']==w['creation_year_end']==1652 and w['unlinked_creator_label']=='Anonymous collaborator'
  m.m.core.save_new(dest,{'at':m.m.core.now(),'artist_slug':a['slug'],'country':'UA','artwork_id':w['id'],'artwork_qid':q,'date':'c. 1652','anonymous_contributor_preserved':True,'review_and_other_metadata_preserved':True});print(target,'primary refinements verified',flush=True)
if __name__=='__main__':main()
