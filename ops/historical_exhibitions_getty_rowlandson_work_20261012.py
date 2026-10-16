#!/usr/bin/env python3
"""One selected Getty Rowlandson drawing; audited original, not an etched version."""
import sys
import exhibitions_common as c
import historical_exhibitions_getty_thirtyone_20261012 as core
import historical_exhibitions_nga_histories_20261012 as n
R=c.DATA/'getty-rowlandson';OP='historical-exhibitions-getty-rowlandson-work-20261012';core.OP=OP;core.OUT=R/'work-release';core.BACKUP=n.BACKUP.parent/'getty-rowlandson-work';core.SID=c.uid(OP+'/source')
def plan():
 src=c.load(R/'object.json');d=src['data'];im=c.load(R/'images/reviewed.json');audit=c.load(R/'production-audit.json');artist=next(a for a in audit['artists']if a['display_name']=='Thomas Rowlandson');key=d['id'].rsplit('/',1)[-1];assert im['visualReview'].startswith('Passed');assert d['produced_by']['timespan']['identified_by'][0]['content']=='1785'
 medium=next(x['content']for x in d['referred_to_by']if x.get('_label')=='Materials Description');dims='; '.join(x['content']for x in d['referred_to_by']if x.get('_label')=='Dimensions Statement')
 r=dict(id=c.uid('artwork/getty/84.GG.645'),mid=c.uid(OP+'/media/'+key),slug='getty-box-lobby-loungers-84-gg-645',objectID=d['id'],key=key,accession='84.GG.645',title='Box-Lobby Loungers',url='https://www.getty.edu/art/collection/object/103QXP',date='1785',first=1785,last=1785,precision='exact',medium=medium,dimensions=dims,creator='Thomas Rowlandson',artistID=artist['id'],workType='drawing',source=src,image=im,imagePath='/assets/artworks/imported/'+OP+'/'+im['sha256'][:16]+'.jpg')
 with c.connect()as db:
  assert not core.conflicts(db,[r]);assert n.normal(db.execute('SELECT id,display_name,birth_year,death_year,revision FROM artists WHERE id=%s',(artist['id'],)).fetchone())==artist;inst=n.normal(db.execute('SELECT id,name,status FROM institutions WHERE id=%s',(core.IID,)).fetchone());before=n.normal(db.execute('SELECT * FROM artworks WHERE id=ANY(%s::uuid[])',([x['id']for x in audit['works']],)).fetchall())
 p=dict(at=c.now(),records=[r],artists=[artist],institution=inst,candidatesBefore=before,counts=dict(newArtworks=1,newImages=1,newPrimaryArtistLinks=1,newHoldings=1),review='Exact Getty accession and native original drawing, with four reciprocal historical venue references and reviewed CC0 primary image. Scoped catalogue title/accession candidates are different print subjects. Preserve existing artist birth1756 despite Getty1757 source variation; no artist lifetime update. Historical Wigstead attribution lead is not a confirmed modern creator assignment. No current-display claim.')
 c.save(core.OUT/'plan.json.gz',p);c.save(core.BACKUP/'preimage.json.gz',p);print(p['counts'])
if __name__=='__main__':
 assert sys.argv[1]in ['plan','upload','apply','verify']
 if sys.argv[1]=='plan':plan()
 else:getattr(core,sys.argv[1])()
