#!/usr/bin/env python3
"""Exact Met object evidence with independently licensed Commons reproductions."""
import importlib.util
from pathlib import Path
from urllib.parse import urlparse
s=importlib.util.spec_from_file_location('commons',Path(__file__).with_name('overnight-commons-images.py'));common=importlib.util.module_from_spec(s);s.loader.exec_module(common);core=common.core
s=importlib.util.spec_from_file_location('direct',Path(__file__).with_name('overnight-image-campaign.py'));direct=importlib.util.module_from_spec(s);s.loader.exec_module(direct)
core.VERSION='overnight-met-independent-commons-v1';core.PROVIDERS['night-met-commons']='The Metropolitan Museum of Art / Wikimedia Commons'
def verify(im):
 raw=im['raw'];o=raw['met_record'];e=raw['wikidata'];institution=raw['museum_authority']
 if institution.get('id')!=im['institution_qid'] or im['institution_slug']!='the-met':raise ValueError('Exact holding museum identity differs')
 websites=common.values(institution,'P856')
 if not any(urlparse(u).hostname in ('www.metmuseum.org','metmuseum.org') for u in websites if isinstance(u,str)):raise ValueError('Museum authority lacks the official institution website')
 common.entity_match(im,e)
 if str(o.get('objectID'))!=im['external_id'] or o.get('accessionNumber')!=im['accession_number']:raise ValueError('Exact Met native object/accession differs')
 if im['external_id'] not in common.values(e,'P3634'):raise ValueError('Wikidata Met cross-reference differs')
 if {x['qid'] for x in im['creators']}!={o.get('artistWikidata_URL','').rsplit('/',1)[-1]}:raise ValueError('Museum creator authority differs')
 direct.fresh_scope('met',o,im)
 result=common.rights_and_identity(im,e,raw['commons'],raw['structured_data'],im.get('rendered_licence_evidence'))
 if result[3]!=im['policy_url'] or result[5]!=im['source_image_url']:raise ValueError('Exact independently licensed Commons resource differs')
 if im.get('source_record_url')!=o['objectURL']:raise ValueError('Museum source page differs')
 return result
original_attach=common.original_attach
def attach(db,im,target):
 verify(im)
 with db.transaction():
  rows=db.execute("SELECT a.id::text,a.slug,a.title,a.creation_year_start,a.creation_year_end,a.work_type,a.primary_media_id::text FROM artworks a JOIN external_identifiers e ON e.entity_type='artwork' AND e.entity_id=a.id WHERE e.scheme=%s AND e.external_id=%s FOR UPDATE OF a",(im['scheme'],im['external_id'])).fetchall()
  if len(rows)!=1 or rows[0]['id']!=im['target_ids'][target] or any(rows[0][k]!=im[k] for k in ('slug','title','creation_year_start','creation_year_end','work_type')):raise ValueError('Target catalogue object changed or ambiguous')
  if rows[0]['primary_media_id'] and rows[0]['primary_media_id']!=im['media_id']:return 'existing_media_preserved'
  holding=db.execute("SELECT i.slug FROM artworks a JOIN institutions i ON i.id=a.current_institution_id WHERE a.id=%s",(rows[0]['id'],)).fetchone()
  if not holding or holding['slug']!='the-met':raise ValueError('Target holding institution changed')
  actual=db.execute("SELECT e.external_id FROM artwork_artists aa JOIN external_identifiers e ON e.entity_type='artist' AND e.entity_id=aa.artist_id AND e.scheme='wikidata' WHERE aa.artwork_id=%s",(rows[0]['id'],)).fetchall()
  if {r['external_id'] for r in actual}!={r['qid'] for r in im['creators']}:raise ValueError('Target creator authority differs')
  result=original_attach(db,im,target)
  if result=='attached':
   db.execute('UPDATE media_assets SET creator_credit=%s,attribution_text=%s WHERE id=%s',(im['creator_credit'],im['attribution_text'],im['media_id']))
   db.execute('UPDATE media_rights_evidence SET rights_basis=%s WHERE media_id=%s',('Exact current Met object ID, accession, creator authority and creation/type evidence independently verified. Image comes from the exact Wikimedia Commons file with explicit per-file approved licence; this is not a claim that the current Met API supplies a downloadable image.',im['media_id']))
  return result
core.attach=attach
