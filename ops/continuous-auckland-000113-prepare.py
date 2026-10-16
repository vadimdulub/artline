"""Select exact Wikidata/native crosswalks before fetching any image."""
import importlib.util,json,gzip,re,fcntl
from pathlib import Path
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('b','ops/continuous-auckland-images-000113.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h;i=b.i
native=b.mod('native113prepare','museum-expansion-auckland-20261006.py');data=b.load(b.E/'gap-input.json.gz');discovery=b.load(b.E/'native-discovery.json');selected=[];holds=[]
raw,rc=b.capture(b.POLICY);text=BeautifulSoup(raw,'html.parser').get_text(' ',strip=True);assert 'This material may be copied and otherwise re-used in New Zealand without copyright or other intellectual property right related restriction' in text
b.save('source-policy-verification.json',dict(at=h.now(),receipt=rc,text=text,decision='Only explicit NKCR/Copyright expired museum records, with New Zealand qualification preserved. No independent worldwide licence claim.'))
with b.connect() as db:
 for d in discovery['rows']:
  aid=d['artwork_id'];a=data['before'][aid]['artwork'];reason=d.get('hold');f=d.get('fields',{})
  if not reason and f.get('Copyright','').lower() not in ['no known copyright restrictions','copyright expired']:reason='Native copying restrictions apply; no image downloaded'
  if not reason and not d['image_available']:reason='Native record supplies no image'
  if not reason and a['creation_year_end']>1955:reason='Later native-image date requires separate approval review'
  if reason:holds.append(dict(artwork_id=aid,title=a['title'],reason=reason));continue
  x=b.load(b.E/'native'/(aid+'.json'));attrs=x['parsed']['native_route']['attributes'];oid=d['native_id'];ext=next(e for e in data['identifiers'] if e['entity_id']==aid and e['scheme']=='wikidata')
  cs=[c for c in data['citations'] if c['entity_id']==aid];cite=next((c for c in cs if '/artwork/'+oid+'/' in c['source_url']),None) or next(c for c in cs if oid in c['evidence_note'] and ext['external_id'] in c['source_url'])
  old=json.loads(cite['evidence_note']);entity=old.get('raw_source_record',{}).get('entity') or old.get('source_entity');accessions=[]
  if entity:
   accessions=[z['mainsnak'].get('datavalue',{}).get('value') for z in entity.get('claims',{}).get('P217',[])]
  else:
   for c in cs:
    z=json.loads(c['evidence_note']);e=z.get('raw_source_record',{}).get('entity') or z.get('source_entity')
    if e:accessions += [v['mainsnak'].get('datavalue',{}).get('value') for v in e.get('claims',{}).get('P217',[])]
  creator=a['unlinked_creator_label']
  if not creator:
   creators=[dict(v) for v in db.execute('SELECT ar.display_name FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=%s',(aid,))];creator=' / '.join(v['display_name'] for v in creators)
  dates=native.creation_date(f['Production date'])[:2]
  basis=dict(title_equal=h.norm(f['Title'])==h.norm(a['title']),creator_equal=h.norm(f['Artist'])==h.norm(creator),date_equal=dates==(a['creation_year_start'],a['creation_year_end']),accession_equal=f['Accession No']==a['accession_number'] or f['Accession No'] in accessions,object_id_equal=str(attrs['id'])==oid)
  similar=[dict(v) for v in db.execute("SELECT id::text,title,accession_number,primary_media_id::text FROM artworks WHERE status<>'archived' AND (lower(title)=lower(%s) OR (current_institution_id=%s AND accession_number=%s)) ORDER BY id LIMIT 100",(a['title'],b.MID,f['Accession No']))]
  native_ids=[dict(v) for v in db.execute("SELECT entity_id::text,scheme,external_id FROM external_identifiers WHERE entity_type='artwork' AND ((scheme='auckland-object' AND external_id=%s) OR (scheme='wikidata' AND external_id=%s))",(oid,ext['external_id']))]
  if not all(basis.values()) or {v['id'] for v in similar}!={aid} or {v['entity_id'] for v in native_ids}!={aid}:
   holds.append(dict(artwork_id=aid,title=a['title'],reason='Exact crosswalk or globally unique catalogue identity unresolved; no download',checks=basis,source_creator=f['Artist'],catalogue_creator=creator,similar=similar,identifiers=native_ids));continue
  assert h.snapshot(db,[aid])[aid]==data['before'][aid] and a['primary_media_id'] is None
  dims=[float(v) for v in re.findall(r'[0-9]+(?:\.[0-9]+)?',f['Dimensions'])];assert len(dims) in [2,3] and f['Dimensions'].endswith(' mm')
  identity_basis='Exact saved Wikidata-to-native object URL, museum accession, concordant creator, title and creation date; global same-title/accession/native-ID reconciliation unique. Catalogue unknowns retained; no holding/current-display changes.'
  identity=dict(artwork_id=aid,native_id=oid,wikidata_id=ext['external_id'],source_citation=cite,source_citation_sha256=h.sha(json.dumps(cite,sort_keys=True,ensure_ascii=False).encode()),current_source_sha256=x['receipt']['sha256'],dimensions_mm=dims,checks=basis,source_accession=f['Accession No'],global_identifiers=native_ids,same_title_inventory_rows=similar,confidence=.99,confidence_basis=identity_basis)
  url=attrs['zoom_image'];assert '/images/xlarge/' in url and b.urlsplit(url).hostname==i.CFG['auckland']['host']
  selected.append(dict(artwork_id=aid,native_id=ext['external_id'],current_source_id=oid,title=a['title'],creator_label=f['Artist'],source_url=x['receipt']['url'],accession_number=a['accession_number'],first=a['creation_year_start'],last=a['creation_year_end'],precision=a['date_precision'],work_type=a['work_type'],provider='auckland',expected_museum_id=b.MID,rights_status='restricted',rights_label=f['Copyright'],rights_basis='Museum '+f['Copyright']+'; policy permits reuse in New Zealand. Actual territorial statement retained separately from user authorization; no worldwide public-domain assertion.',source_credit=f['Artist']+'. '+f['Title']+'. '+f['Credit line'],image=dict(native_url=url,image_url=url,source=dict(official_metadata=x,identity_reconciliation=identity),receipt=x['receipt']),plan_sha256=old['plan_sha256'],identity_confidence=.99,identity_basis=identity_basis,manual_visual_required=True))
b.save('global-identity-reconciliation.json',dict(at=h.now(),holds=holds,selected_ids=[r['artwork_id'] for r in selected]))
b.save('authorization.json',dict(at=h.now(),production_image_updates_authorized=True,policy_reference='Original 111-source registry Auckland per-object rule and ARTLINE_IMAGE_USE.md; current museum reuse statement',copyright_holder_licence=False,actual_rights_labels_and_territorial_qualification_preserved=True,local_catalogue_read_only=True))
print('Selected',len(selected),'held',len(holds),flush=True)
if selected:
 b.save('batches/'+b.B+'/selection.json.gz',dict(at=h.now(),provider='auckland',batch=b.B,rows=selected));b.save('batches/'+b.B+'/pin.json',dict(sha256=h.sha((i.folder(b.B)/'selection.json.gz').read_bytes())))
 for r in selected:
  im=i.prepare_one(r,b.B);print(r['title'],im['state'],im.get('path',im.get('reason')),flush=True)
 i.audit(b.B)
