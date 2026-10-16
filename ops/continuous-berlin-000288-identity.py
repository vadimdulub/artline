import importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('h','ops/india-300-delivery-20261011.py');h=importlib.util.module_from_spec(s);s.loader.exec_module(h)
E=h.ROOT/'docs/research/continuous-production-20261011/batches/000288';mid='cf0f806e-05a5-5380-9a8d-c05f8b02b348'
rows=[]
with h.connect() as db:
 for fp in sorted((E/'objects').glob('*.json')):
  o=h.load(fp);oid=o['id'].split('-')[1];urls=[o['permalink'],'https://search.smb.museum/en/object/obj-'+oid,'https://search.smb.museum/object/obj-'+oid,'https://recherche.smb.museum/detail/'+oid]
  exact=[dict(x) for x in db.execute("SELECT id::text,title,accession_number,current_institution_id::text,dimensions_text FROM artworks WHERE accession_number=%s OR normalized_title=%s",(o['ident'],h.norm(o['title'])))];native=[dict(x) for x in db.execute("SELECT entity_id::text,scheme,external_id FROM external_identifiers WHERE entity_type='artwork' AND (canonical_url=ANY(%s) OR (external_id=%s AND scheme ILIKE '%%smb%%'))",(urls,oid))];cites=[dict(x) for x in db.execute("SELECT entity_id::text FROM citations WHERE entity_type='artwork' AND source_url=ANY(%s)",(urls,))]
  rows.append(dict(source_id=oid,inventory=o['ident'],title=o['title'],exact=exact,native=native,citations=cites));print(oid,o['ident'],len(exact),len(native),len(cites))
h.save(E/'page3-global-identity-initial.json',dict(at=h.now(),records=rows))
