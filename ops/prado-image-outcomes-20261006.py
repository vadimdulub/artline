"""Build per-object Markdown outcomes from verified Prado production snapshots."""
import collections

def write(m, current, images, source_records, mapping, baseline, folder):
 r=m.r;root=m.RUN;delivery=root/'museum-image-delivery'
 selected={x['artwork_id']:x for x in r.load(delivery/'selection.json.gz')['ready']}
 for f in sorted(delivery.glob('selection-addendum-*.json.gz')):selected.update({x['artwork_id']:x for x in r.load(f)['ready']})
 holds={}
 for f in sorted(delivery.glob('batch-*-visual.json')):
  value=r.load(f).get('held',[])
  if isinstance(value,dict):holds.update(value)
  else:holds.update({x['artwork_id']:x['reason']for x in value})
 for x in r.load(delivery/'selection.json.gz')['held']:holds.setdefault(x['lead']['artwork_id'],x['reason'])
 for x in r.load(root/'images/commons-reviewed-selection.json.gz')['held']:holds.setdefault(x['lead']['artwork_id'],x['reason'])
 events={}
 if (delivery/'preparation-events.jsonl').exists():
  import json
  for line in (delivery/'preparation-events.jsonl').read_text().splitlines():
   x=json.loads(line);events[x['artwork_id']]=x
 manual={
 'P004254':'The Commons Prado image is P005552, the 1910 Guadarrama view from Plantío de los Infantes, not this 1911 P004254 view.',
 'P002440':'Prado-sourced Carlota portraits identify Troni P002416, not Maella P002440. The exact Maella file has a royaltyguide.nl source; no approved-origin replacement was verified.',
 'P001339':'The returned octagonal panel is Saint Damian P001340, not the pendant Saint Cosmas P001339.',
 'P004574':'Returned seated child with apples is P004571 (1887, 65 × 53 cm), now separately attached; this is P004574 (1892, 42 × 37 cm).',
 'P004564':'Returned seated child with apples is P004571 (1887); this is the distinct 1885 portrait P004564.',
 'P006964':'Returned French Lady portrait is dated 1864; this Dama con abanico is a distinct circa-1878 work. No exact file-to-object correspondence established.',
 'P003140':'Prado-sourced Dream of Saint Joseph is P007735 (1805, 187 × 118 cm), not P003140. The other candidate cites pintura.aut.org and lacks approved-origin evidence.',
 'P000596':'Arellano-florero.jpg has the 60 × 45 cm dimensions and historical inventory 349 of pendant P000597, not this 60 × 46 cm P000596.',
 'P003027':'Exact-title Commons candidates cite Web Gallery of Art or secondary reproduction sources. An approved WikiArt/Prado-origin image or independently documented photograph was not verified.',
 'P000666':'Exact-title Commons candidates cite Web Gallery of Art or secondary reproduction sources. An approved WikiArt/Prado-origin image or independently documented photograph was not verified.',
 'P000992':'Only a cropped detail of the Coello portrait was found; a complete supplied composition remains unverified.',
 'P005641':'Google Art Project / MNAC candidate remains separate from the approved Prado-origin file set. Exact reproduction-origin review is incomplete; no WikiArt or Prado-source replacement was verified.',
 'P002780':'The exact preparatory Floridablanca portrait candidate cites an AllPosters commercial reproduction; Prado reference establishes artwork identity but not photograph origin.',
 'P008061':'Exact 1918 self-portrait candidate has source explicitly unknown. The 1910 Prado-source portrait is P008229 and was attached separately.',
 'P004582':'The Prado-source 1901 Self-portrait with a Hat is P004572, now separately attached. This P004582 is the distinct 1895 portrait.',
 'P004050':'Returned riverbank views include 1908–1910 or 1910 paintings; this is the 1877–1878 work. Exact version and approved image origin remain unverified.',
 'P002581':'The exact Esteve portrait file cites Artdaily.com without documented Prado image origin. No approved-origin replacement was verified.',
 'P002512':'Returned Morales Annunciation files cite pintura.aut.org and include differing dimensions/versions; the independently photographed Virgin and Child is a different subject and collection.',
 'P007592':'Search returned Cecilio Pla’s portrait of Casimiro Sáinz, not Pla’s self-portrait.',
 'P005687':'Returned Meifrén seascapes identify other collections or versions; no exact P005687 image match was verified.',
 'P006018':'Returned Urgell landscapes identify other collections or unspecified versions; no exact P006018 match was verified.',
 }
 outcomes=[]
 for x in source_records:
  aid=mapping.get(x['artwork_id'],x['artwork_id']);a=current[aid];acc=x['accession'];ev=[]
  for name in ['original-gap-source-search','original-gap-refinement','original-gap-creator-search']:
   f=root/name/'objects'/(aid+'.json')
   if f.exists():ev.append(str(f.relative_to(root)))
  if aid in images:code='attached';reason='Verified image added in this expansion; original catalogue fields and review status preserved.'
  elif a['primary_media_id']:code='existing-image-preserved';reason='Existing primary image preserved.'
  elif aid in selected and not(delivery/'prepared'/(aid+'.json')).exists():code='download-pending';reason=events.get(aid,{}).get('error','Selected source file not yet prepared.')
  elif aid in holds:code='object-or-source-review';reason=holds[aid]
  elif acc in manual:code='no-verified-exact-source';reason=manual[acc]
  elif aid in selected:code='visual-review-pending';reason='Prepared selected file has not passed the recorded final attachment decision.'
  elif x['date']['review']:code='date-review';reason='Source date is unknown or insufficient for automatic creation-scope clearance; record retained in review.'
  else:code='no-verified-exact-source';reason='No exact complete image with verified approved-source or independent-photo provenance was established in the bounded source and object searches.'
  outcomes.append({'artwork_id':aid,'accession':acc,'title':x['object']['Título'],'creator':x['creator_label'],'source_date':x['object']['Fecha'],'source_url':x['object']['url'],'outcome':code,'reason':reason,'research_evidence':ev,'image_url':('https://artlines.org'+images[aid]['path'])if aid in images else None,'image_source':images.get(aid,{}).get('source_page_url')or images.get(aid,{}).get('page',{}).get('url'),'original_gap':aid in baseline and not baseline[aid]['primary_media_id']})
 counts=collections.Counter(x['outcome']for x in outcomes);r.save_gz(folder/'detailed-image-outcomes.json.gz',outcomes)
 def cell(value):return str(value or 'Unknown').replace('|','\\|').replace('\n',' ')
 def table(rows):
  text=['| Prado inventory | Artwork / creator | Outcome | Evidence and decision |','|---|---|---|---|']
  for x in rows:
   links=' · '.join('[research '+str(i+1)+']('+p+')'for i,p in enumerate(x['research_evidence']))
   if x['image_url']:links+=' [image]('+x['image_url']+') · [image source]('+x['image_source']+')'
   text.append('| ['+x['accession']+']('+x['source_url']+') | '+cell(x['title'])+' — '+cell(x['creator'])+' | '+x['outcome']+' | '+cell(x['reason'])+' '+links+' |')
  return '\n'.join(text)+'\n'
 (root/'image-outcomes.md').write_text('# Prado painting image outcomes\n\nVerified at '+r.now()+'. One row for each of the 7,129 selected museum-native painting objects. These are bounded research outcomes, not claims that a missing image does not exist. WikiArt and Prado source acceptance is approved; source/version evidence and download completion are reported separately. Existing catalogue records remain in review.\n\n'+ '\n'.join('- '+k+': '+str(v)for k,v in sorted(counts.items()))+'\n\n'+table(outcomes))
 gaps=[x for x in outcomes if x['original_gap']];missing=[x for x in gaps if x['outcome']not in ('attached','existing-image-preserved')]
 (root/'original-gap-outcomes.md').write_text('# Original Prado image gaps\n\nOf the original 295 gaps, '+str(295-len(missing))+' are filled and '+str(len(missing))+' remain at '+r.now()+'. Every remaining record is listed below with its evidence. WikiArt approval is already applied; no row is held merely for a missing WikiArt public-domain label. Search and access limits do not establish image absence.\n\n'+table(missing)+'\n## Filled original gaps\n\n'+table([x for x in gaps if x not in missing]))
 return dict(counts)
