"""Retain selective visual and object comparisons; no image attachment or DB mutation."""
import gzip,hashlib,importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('s',Path(__file__).with_name('museum-expansion-city-art-additions-common-20261009.py'));s=importlib.util.module_from_spec(z);z.loader.exec_module(s);m=s.m;RUN=s.RUN
OBS={
'00e52a40-2230-585a-bd05-9471a4ba2e13':'1919 Peploe is vertical, tall individual tulips, vivid blue/red cloth, vase central and fruit lower right; different from horizontal dark1905–1906 source with vase right and fruit left.',
'ad501e87-0f8e-5dc0-a5bf-5c2977390991':'Square1912Duncan shows crowned Iseult left and red-robed Tristan right holding broad potion bowl aboard boat. Specific narrative,creator,date and title alias agree with University lender item4. Link existing, preserve allmetadata/image.',
'431a1be7-c02c-53a1-aa1c-798b9857dca8':'1907Fergusson close portrait looks outward with street pedestrians behind; different from1909side-profile woman with two glasses at cafétable in Pallant credit.',
'2c5331fb-e484-5bde-83a1-57e025c25e8e':'1950Fergusson cropped head with paintednumeral hat; different from1909widebluehat sideprofile atcafétable.',
'06888e8b-57e4-51cd-b751-858c9ad8b1af':'CadellReflections seatedwoman with flowerhat, mirrorandteatable; not1914standingwoman besidefireplace.',
'97123f11-e485-594b-90b5-4f1acdab2955':'CadellGirlBlue seatedpaledress nohat andmirrorleft; notBlackHatstandingwoman.',
'9901afc2-2ed3-5bbd-a4ac-ad7856ada2b7':'CadellLadyWhite seatedwhiteblousewithbluebelt,flowers; notBlackHat.',
'e9a0f405-9e18-5e80-9495-2cdad8d1336f':'CadellLadyBlack seatedblackhatanddress,vaseabovehead; differentpose/composition fromBlackHat1914standingbymantel.',
'fed48899-4fa9-5e82-b8c9-2e5d495fcb3c':'PeploeRosesGreyJar vertical,greybulbousvaseleft,grapesfrontwhitecloth; nothorizontalCitywhitebluevaseatright.',
'3da8d695-d3d1-586f-8159-961c353af124':'PeploeTulipsBrownJar vertical,yellowflowersbulbousvasecentre,orangeforegroundandbluebackground; notCitydarkhorizontalcomposition.'}
def main():
 refs={};imgs=[];raws=[]
 for fn in ['physical-comparator-snapshot-001.json.gz','physical-comparator-snapshot-002.json.gz']:
  snap=m.load(RUN/fn)['snapshot'];arts={a['id']:a for a in snap['artworks']}
  for aid,a in arts.items():
   if aid not in OBS:continue
   asset=next(v for v in snap['media_assets'] if v['id']==a['primary_media_id']);p=m.ROOT/'apps/web/public'/asset['storage_path'].lstrip('/');ref=s.ref(p);assert ref['sha256']==asset['checksum_sha256'];refs[ref['path']]=ref;imgs.append(dict(artwork_id=aid,asset_reference=ref,visual_observation=OBS[aid]))
  for c in snap['citations']:
   try:n=json.loads(c['evidence_note'])
   except(ValueError,TypeError):continue
   if not isinstance(n,dict) or 'tate-current-api' not in n.get('evidence_path',''):continue
   p=m.ROOT/n['evidence_path'];raw=gzip.decompress(p.read_bytes());assert hashlib.sha256(raw).hexdigest()==n['source_response_sha256'];ref=s.ref(p);refs[ref['path']]=ref;raws.append(dict(artwork_id=c['entity_id'],reference=ref,data=json.loads(raw)))
 p=m.ROOT/'docs/research/wikiart-artist-followup-20260920/captures/dc1914c891b843adbe98229952b4d6a429d93739c1289241ec026a00559f4614.body';ref=s.ref(p);assert ref['sha256']=='b0b5d23a59fa3bbfe847f1ac2aaade321e0042860b5c874194ef6441a8f54cdc';refs[ref['path']]=ref
 m.save(RUN/'physical-object-review-001.json.gz',dict(at=m.now(),images=imgs,extra_tate_comparators=raws,tristan_reconstructed_body=ref,body_references=list(refs.values()),selected_thumbnail_reference=s.ref(RUN/'selected-image-reference-001.json'),thumbnail_observation='1909BlueHat:sideprofiledarkhairedwoman,widebluehat,rosetteatneck,two glasses on cafétable. Different from both existingFergussonportraits.',policy='Ten existing local catalogue images visually inspected,one300pxpublicthumbnail researchreference. No imageattachment or rightslabelchange. ExistingTateobjects PeploeN04224 and McTaggartN06044,N04701,N04610 have separate titles,physicaldimensions,dates and collection evidence. Sourcepastcapture is not newcurrentverification.'))
 print(json.dumps(dict(existing_images=len(imgs),extra_tate_sources=len(raws),body_refs=len(refs))))
if __name__=='__main__':main()
