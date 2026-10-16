"""Curated exact creator reconciliation; qualified source labels remain untouched."""
import json,requests
from psycopg.types.json import Jsonb
import historical_exhibitions_fitzwilliam_oldmaster_drawing_catalogue_20261012 as q
c=q.c;n=q.n;OP='historical-exhibitions-fitzwilliam-drawing-creators-20261012'
MAPPING={
'Tiepolo, Giovanni Battista':'Giovanni Battista Tiepolo','Tiepolo, Giovanni Domenico':'Giovanni Domenico Tiepolo','Leonardo da Vinci':'Leonardo da Vinci','Botticelli (Alessandro di Mariano Filipepi)':'Sandro Botticelli','Parmigianino (Francesco Mazzola)':'Parmigianino','Giulio Romano (Giulio Pippi)':'Giulio Romano','Bartolomeo, Fra':'Fra Bartolomeo','Lorenzo di Credi':'Lorenzo di Credi','Farinati, Paolo':'Paolo Farinati','Gozzoli, Benozzo':'Benozzo Gozzoli','Bassano, Jacopo (Jacopo da Ponte)':'Jacopo Bassano','Bassano, Leandro (Leandro da Ponte)':'Leandro Bassano','Campagnola, Domenico':'Domenico Campagnola','Piazzetta, Giovanni Battista':'Giovanni Battista Piazzetta','Correggio (Antonio Allegri)':'Antonio da Correggio','Ricci, Marco':'Marco Ricci','Ricci, Giovanni Battista':'Giovanni Battista Ricci','Barocci, Federico':'Federico Barocci','Carpaccio, Vittore':'Vittore Carpaccio','Pisanello (Antonio Pisano)':'Pisanello','Michelangelo Buonarroti':'Michelangelo','Goltzius, Hendrik':'Hendrik Goltzius','Modigliani, Amedeo':'Amedeo Modigliani','Guardi, Francesco':'Francesco Guardi','Vecellio, Tiziano':'Titian','Tintoretto, Jacopo (Jacopo Robusti)':'Tintoretto','Tintoretto, Domenico (Domenico Robusti)':'Domenico Tintoretto','Montagna, Bartolomeo':'Bartolomeo Montagna','Passarotti, Bartolommeo':'Bartolomeo Passarotti'}
p=c.load(q.OUT/'plan.json.gz');selected=[r for r in p['records']if r['creator']in MAPPING];held=[dict(nativeID=r['nativeID'],label=r['creator'])for r in p['records']if r['creator']not in MAPPING]
for r in selected:
 q.h.validate_receipt(r['source']['receipt']);makers=r['source']['data']['lifecycle']['creation'][0]['maker'];assert len(makers)==1 and not makers[0].get('@link',{}).get('qualifier')
with c.connect()as db:
 artists=n.normal(db.execute('SELECT * FROM artists WHERE display_name=ANY(%s)',(list(MAPPING.values()),)).fetchall());assert len(artists)==len(set(MAPPING.values()))
 byname={a['display_name']:a for a in artists};assert set(byname)==set(MAPPING.values())
 before=n.normal(db.execute('SELECT * FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id',([r['id']for r in selected],)).fetchall());assert len(before)==len(selected)
 assert not db.execute('SELECT 1 FROM artwork_artists WHERE artwork_id=ANY(%s::uuid[])',([r['id']for r in selected],)).fetchone()
 for r in selected:
  a=next(a for a in before if a['id']==r['id']);assert a['unlinked_creator_label']==r['creator']and a['accession_number']==r['accession']
evidence=dict(at=c.now(),operation=OP,mapping=MAPPING,artists=artists,artworksBefore=before,selectedNativeIDs=[r['nativeID']for r in selected],held=held,basis='Curated creator name order and explicit conventional-name equivalences. Only a single unqualified maker is linked. Original labels retained. Raphael/Sanzio duplicate artist identities remain unresolved.')
c.save(q.BACKUP/'creator-links-preimage.json.gz',evidence)
with c.connect(write=True)as db:
 db.execute("SELECT set_config('artline.actor_user_id','local-european-research',true)");db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))");db.execute('SELECT pg_advisory_xact_lock(2026101201)')
 assert n.normal(db.execute('SELECT * FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',([r['id']for r in selected],)).fetchall())==before
 assert not db.execute('SELECT 1 FROM artwork_artists WHERE artwork_id=ANY(%s::uuid[])',([r['id']for r in selected],)).fetchone()
 current=n.normal(db.execute('SELECT * FROM artists WHERE id=ANY(%s::uuid[])',([a['id']for a in artists],)).fetchall());assert sorted(current,key=lambda x:x['id'])==sorted(artists,key=lambda x:x['id'])
 with db.pipeline():
  for r in selected:
   aid=byname[MAPPING[r['creator']]]['id'];rc=r['source']['receipt'];note=json.dumps(dict(operation=OP,sourceCreator=r['creator'],catalogueCreator=MAPPING[r['creator']],nativeID=r['nativeID'],sourceHash=rc['sha256'],basis=evidence['basis']))
   db.execute("INSERT INTO artwork_artists(artwork_id,artist_id,attribution_role) VALUES(%s,%s,'primary')",(r['id'],aid))
   db.execute("INSERT INTO citations(entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by) VALUES('artwork',%s,'creator_identity',%s,%s,%s,%s,%s,%s)",(r['id'],q.SID,r['nativeID'],rc['url'],note,rc['retrieved_at'],q.ACTOR))
with c.connect()as db:
 links=n.normal(db.execute('SELECT * FROM artwork_artists WHERE artwork_id=ANY(%s::uuid[])',([r['id']for r in selected],)).fetchall());assert len(links)==len(selected)
 assert n.normal(db.execute('SELECT * FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id',([r['id']for r in selected],)).fetchall())==before
 for r in selected:assert any(a['artwork_id']==r['id']and a['artist_id']==byname[MAPPING[r['creator']]]['id']and a['attribution_role']=='primary'for a in links)
result=dict(at=c.now(),newArtworkArtistLinks=len(links),distinctArtists=len(artists),heldObjects=len(held),newArtworks=0,newImages=0,artworkMetadataPreserved=True,realLocalWrites=False,verifiedDatabase=True,held=held)
c.save(c.ROOT/'docs/research/historical-exhibitions-20261012/fitzwilliam-drawing-creators-delivery.json',result);print(json.dumps({k:v for k,v in result.items()if k!='held'}))
