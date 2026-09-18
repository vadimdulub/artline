#!/usr/bin/env python3
"""Reconcile four independently checked painter names, retaining biographies."""
import importlib.util,json,re
from pathlib import Path
import psycopg
from psycopg.rows import dict_row
ROOT=Path(__file__).resolve().parents[1];RUN=ROOT/'docs/research/overnight-images-20260915/mia-creator-followup'
s=importlib.util.spec_from_file_location('mia',ROOT/'ops/overnight-mia-images.py');mia=importlib.util.module_from_spec(s);s.loader.exec_module(mia);core=mia.core
CHANGES=[('Q200798','ando-hiroshige-nga-4350','Andō Hiroshige',1797,1858,[('Utagawa Hiroshige','en')]),('Q165367','hendrik-goltzius-q165367','Hendrik Goltzius',1558,1617,[('Hendrick Goltzius','nl')]),('Q2871286','auguste-lepere-nga-2622','Auguste Lepère',1849,1918,[('Auguste Louis Lepère','en'),('Auguste-Louis Lepère','en')]),('Q5586','katsushika-hokusai','Katsushika Hokusai',1760,1849,[('Hokusai','en')])]

def main():
 data=json.loads((RUN/'authorities.json').read_text());evidence_hash=core.sha((RUN/'authorities.json').read_bytes());receipts=[json.loads(p.read_text()) for p in (RUN/'metadata').glob('*.receipt.json')];assert len(receipts)==1;receipt=receipts[0]
 for q,slug,name,birth,death,aliases in CHANGES:
  entity=data['entities'][q];assert entity['id']==q
  def values(prop):return [v['mainsnak'].get('datavalue',{}).get('value') for v in entity.get('claims',{}).get(prop,[]) if v.get('rank')!='deprecated']
  assert any(isinstance(v,dict) and v.get('id')=='Q5' for v in values('P31'))
  source_names={v['value'] for v in entity.get('labels',{}).values()}|{v['value'] for seq in entity.get('aliases',{}).values() for v in seq}
  assert name in source_names and all(alias in source_names for alias,lang in aliases)
  assert birth in {int(v['time'][1:5]) for v in values('P569') if v and v.get('precision',0)>=9}
  assert death in {int(v['time'][1:5]) for v in values('P570') if v and v.get('precision',0)>=9}
 results=[];backup=Path.home()/'Library/Application Support/Artline/backups/overnight-images-20260915/mia-creator-followup'
 for target,dsn in [('local','postgres://localhost/artline'),('cloud',core.cloud_dsn())]:
  with psycopg.connect(dsn,autocommit=True,row_factory=dict_row) as db:
   with db.transaction():
    db.execute('SELECT pg_advisory_xact_lock(559220260915)')
    db.execute("INSERT INTO sources(slug,name,source_type,base_url,terms_url) VALUES('overnight-mia-creator-authorities-20260915','Wikidata: checked painter identities and name variants','authority_data','https://www.wikidata.org/',%s) ON CONFLICT(slug) DO NOTHING",(mia.CC0,));sid=db.execute("SELECT id FROM sources WHERE slug='overnight-mia-creator-authorities-20260915'").fetchone()['id']
    for q,slug,name,birth,death,aliases in CHANGES:
     rows=db.execute('SELECT id::text,slug,display_name,birth_year,death_year,status,to_jsonb(a) before FROM artists a WHERE slug=%s FOR UPDATE',(slug,)).fetchall();assert len(rows)==1;c=rows[0];assert c['display_name']==name and (c['birth_year'],c['death_year'])==(birth,death) and c['status']=='review'
     authorities=db.execute("SELECT entity_id::text,external_id FROM external_identifiers WHERE entity_type='artist' AND scheme='wikidata' AND (entity_id=%s OR external_id=%s)",(c['id'],q)).fetchall()
     assert not authorities or (len(authorities)==1 and authorities[0]['entity_id']==c['id'] and authorities[0]['external_id']==q),'Existing canonical identity conflicts'
     old_aliases=db.execute('SELECT to_jsonb(a) FROM artist_aliases a WHERE artist_id=%s',(c['id'],)).fetchall();path=backup/(target+'-'+q+'-before.json')
     if not path.exists():core.save_new(path,{'artist':c['before'],'authorities':authorities,'aliases':old_aliases})
     if not authorities:
      assert q=='Q5586','Only the reviewed Hokusai missing authority may be created'
      db.execute("INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at) VALUES('artist',%s,'wikidata',%s,%s,%s,%s)",(c['id'],q,'https://www.wikidata.org/entity/'+q,sid,receipt['retrieved_at']))
     for alias,lang in aliases:
      other=db.execute("SELECT a.id::text FROM artists a WHERE a.id<>%s AND a.status<>'archived' AND (lower(a.display_name)=lower(%s) OR EXISTS(SELECT 1 FROM artist_aliases al WHERE al.artist_id=a.id AND lower(al.alias)=lower(%s)))",(c['id'],alias,alias)).fetchall();assert not other,'Name belongs to another active artist'
      db.execute("INSERT INTO artist_aliases(artist_id,alias,normalized_alias,language_code,alias_type) VALUES(%s,%s,%s,%s,'alternate') ON CONFLICT DO NOTHING",(c['id'],alias,mia.norm(alias),lang))
     note={'canonical_id':q,'source_label':data['entities'][q]['labels'].get('en'),'aliases_added':aliases,'source_revision':data['entities'][q].get('lastrevid'),'source_capture':receipt,'evidence_checksum':evidence_hash,'identity_check':'Existing name and recorded birth/death years agree. Existing canonical IDs were preserved. No artist merged, no biography or country field overwritten. Lepere source lists conflicting death assertions; the existing 1918 date is retained, not newly inferred.'}
     if not db.execute("SELECT 1 FROM citations WHERE entity_type='artist' AND entity_id=%s AND source_id=%s AND field_name='canonical_identity_and_aliases'",(c['id'],sid)).fetchone():db.execute("INSERT INTO citations(entity_type,entity_id,source_id,field_name,source_record_id,source_url,evidence_note,retrieved_at,created_by) VALUES('artist',%s,%s,'canonical_identity_and_aliases',%s,%s,%s,%s,%s)",(c['id'],sid,q,'https://www.wikidata.org/wiki/'+q,json.dumps(note,ensure_ascii=False),receipt['retrieved_at'],core.ACTOR))
     results.append({'target':target,'artist_id':c['id'],'qid':q,'alias_count':len(aliases),'canonical_authority_added':not bool(authorities)})
   print(target,'four painter authority/name records verified',flush=True)
 path=RUN/'applied.json'
 if not path.exists():core.save_new(path,{'at':core.now(),'records':results})
if __name__=='__main__':main()
