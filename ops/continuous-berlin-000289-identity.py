import importlib.util,gzip,json
from pathlib import Path
s=importlib.util.spec_from_file_location('b','ops/continuous-berlin-batch-000289.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h;E=b.E
checks=[];accids=set();titleids=set();allowed={};urls=[]
with h.connect() as db,db.transaction():
 db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
 for oid in b.SELECTED:
  o,rc=b.native(oid);assert not o['actors']
  us=[o['permalink'],'https://search.smb.museum/en/object/obj-'+oid,'https://search.smb.museum/object/obj-'+oid,'https://recherche.smb.museum/detail/'+oid]
  native=[dict(x) for x in db.execute("SELECT entity_id::text,scheme,external_id FROM external_identifiers WHERE entity_type='artwork' AND (canonical_url=ANY(%s) OR (external_id=%s AND scheme ILIKE '%%smb%%'))",(us,oid))]
  cites=[dict(x) for x in db.execute("SELECT entity_id::text FROM citations WHERE entity_type='artwork' AND source_url=ANY(%s)",(us,))];assert not native and not cites
  acc=[dict(x) for x in db.execute('SELECT id::text,title,accession_number,current_institution_id::text,dimensions_text,medium_text,date_display FROM artworks WHERE accession_number=%s',(o['ident'],))]
  ts=[o['title']]+b.ALIASES[oid]+[x['nameLine'] for x in o.get('additionalTitles',[])]
  titles=[dict(x) for x in db.execute('SELECT id::text,title,accession_number,current_institution_id::text,dimensions_text,medium_text,date_display,unlinked_creator_label FROM artworks WHERE normalized_title=ANY(%s)',([h.norm(t) for t in ts],))]
  allowed[oid]=[x['id'] for x in titles];accids.update(x['id'] for x in acc);titleids.update(allowed[oid])
  checks.append(dict(source_id=oid,inventory=o['ident'],title=o['title'],dimensions=o['dimensions'],accession_collisions=acc,title_collisions=titles,native=native,citations=cites))
 h.save(E/'global-accession-collision-evidence.json',dict(at=h.now(),snapshots=h.snapshot(db,list(accids))))
 h.save(E/'global-title-collision-evidence.json',dict(at=h.now(),snapshots=h.snapshot(db,list(titleids))))
 h.save(E/'global-collision-source-identities.json',dict(at=h.now(),external_identifiers=[dict(x) for x in db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(list(accids|titleids),))],citations=[dict(x) for x in db.execute("SELECT entity_id::text,source_record_id,source_url FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(list(accids|titleids),))]))
h.save(E/'global-identity-initial.json',dict(at=h.now(),records=checks));print(json.dumps(checks,ensure_ascii=False,indent=2))
