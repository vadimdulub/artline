#!/usr/bin/env python3
"""Scoped duplicate/creator candidate audit for remaining Getty objects; no writes."""
import re,difflib
import exhibitions_common as c
import historical_exhibitions_nga_histories_20261012 as n
from historical_exhibitions_getty_checklist_expansion_20261012 import DEST
ALIASES={'Correggio (Antonio Allegri)':['Antonio da Correggio'],'Paolo Veronese (Paolo Caliari)':['Paolo Veronese'],'Rembrandt Harmensz. van Rijn':['Rembrandt van Rijn'],"Lorenzo di Credi (Lorenzo d'Andrea d'Oderigo)":['Lorenzo di Credi'],"Pordenone (Giovanni Antonio de'Sacchis)":['Il Pordenone'],'Giulio Romano (Giulio Pippi)':['Giulio Romano'],'Perino del Vaga (Piero Buonaccorsi)':['Perino del Vaga'],'Raphael (Raffaello Sanzio)':['Raphael','Sanzio Raffaello'],'Hans Holbein the Younger':['Hans Holbein the Younger','Holbein Hans Dit Le Jeune'],'Nicolaes Eliasz. Pickenoy':['Nicolaes Eliasz. Pickenoy','Pickenoy Elias Nicolaes'],'Joseph Mallord William Turner':['J. M. W. Turner'],"Nicolò dell'Abate":["Niccolo dell'Abbate","Nicolò dell'Abate","Niccolò dell'Abbate"]}
def main():
 scope=c.load(DEST/'scope-review.json.gz');done={r['accession_number']for r in scope['existingExactAccessionMatches']};objects=[o for o in scope['eligibleObjects']if o['accession']not in done];artists=c.load(DEST/'artist-candidates.json');results=[]
 with c.connect()as db:
  for o in objects:
   d=c.load(DEST/'objects'/(o['id'].rsplit('/',1)[-1]+'.json'))['data'];prod=d['produced_by'];names=o['creator']or[x['content']for part in prod.get('part',[])for x in part.get('referred_to_by',[])if x.get('_label')=='Artist/Maker (Producer) Name'];matched=[a for a in artists if any(c.norm(a['display_name'])in {c.norm(v)for v in ALIASES.get(name,[name])}for name in names)]
   workrows=n.normal(db.execute('SELECT a.id,a.title,a.work_type,a.medium_text,a.accession_number,a.current_institution_id,a.primary_media_id FROM artworks a WHERE a.id IN(SELECT artwork_id FROM artwork_artists WHERE artist_id=ANY(%s::uuid[])) OR a.accession_number=%s',([a['id']for a in matched],o['accession'])).fetchall())
   title=next(x['content']for x in d['identified_by']if x.get('_label')=='Preferred Title');ranked=[]
   for w in workrows:
    score=difflib.SequenceMatcher(None,c.norm(title),c.norm(w['title'])).ratio()
    if score>=.48:ranked.append(w|dict(similarity=round(score,3)))
   ranked.sort(key=lambda x:-x['similarity']);results.append(dict(objectID=o['id'],accession=o['accession'],title=title,creatorLabels=names,creatorCandidates=matched,creatorState='single-name-candidate'if len(matched)==len(names)==1 else'missing-or-ambiguous',artworkCandidates=ranked[:8]))
 result=dict(at=c.now(),objects=results,counts=dict(objects=len(results),singleCreatorCandidates=sum(r['creatorState']=='single-name-candidate'for r in results),highSimilarityObjectLeads=sum(any(w['similarity']>=.8 for w in r['artworkCandidates'])for r in results)),limitations=['Title scores are discovery only, not identity evidence.','Duplicate creator profiles must not be silently merged.','Acquisition numbers are not creation dates.'])
 c.save(DEST/'matching-review.json.gz',result)
 for r in results:print(r['accession'],r['title'],r['creatorState'],[(w['id'],w['title'],w['work_type'],w['accession_number'])for w in r['artworkCandidates']if w['similarity']>=.8])
 print(result['counts'])
if __name__=='__main__':main()
