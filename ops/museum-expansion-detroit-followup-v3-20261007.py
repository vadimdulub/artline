#!/usr/bin/env python3
"""Detroit follow-up with source-documented former attributions and title aliases."""
import argparse,importlib.util,re
from pathlib import Path
s=importlib.util.spec_from_file_location('previous',Path(__file__).with_name('museum-expansion-detroit-followup-v2-20261007.py'));previous=importlib.util.module_from_spec(s);s.loader.exec_module(previous)
f=previous.f;i=previous.i;m=previous.m;RUN=previous.RUN;IID=previous.IID;ref=previous.ref
previous.ALIASES.update({
 '46117':['Corrado Giaquinto'],
 '47422':['Johannes Cornelisz Verspronck'],
 '48132':['Jan van Goyen'],
 '48657':['Caravaggio','Michelangelo Merisi'],
 '48297':['Gerard Dow','Gerrit Dou','Samuel van Hoogstraten','Govaert Flinck','Salomon de Bray'],
 '48358':['William Beechey'],
 '48363':['Joshua Reynolds'],
})
TITLE_ALIASES={
 '45275':['The Harvester'],
 '48293':['The Winter Queen','Elizabeth of Bohemia'],
 '48294':['A Dutch Interior'],
 '48363':['Young Lady Seated in a Wood','A Young Lady Sitting in a Wood'],
}
i.SUBJECTS.update({
 '44986':['%crucifix%jerome%','%crucifix%magdal%','%croci%girol%'],
 '45030':['%pilat%wash%','%pilat%lav%','%pilat%hand%','%pilat%main%'],
 '45031':['%agony%garden%','%agon%jardin%','%christ%olive%','%christ%oliv%'],
})
prior_parse=previous.parse
def parse(path):
 row=prior_parse(path);facts=row['facts'];aliases=TITLE_ALIASES.get(row['source_id'],[])
 facts['titles']=sorted(set(facts['titles']+aliases));row['title_alias_basis']='Historical titles are duplicate-discovery labels from the retained native bibliography or provenance, not a replacement of the current source title.' if aliases else None
 row['followup_v3_reference']=ref(Path(__file__).resolve());return row
previous.parse=parse
facts=previous.facts;identity=previous.identity;scope=previous.scope
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['scope','facts','identity']);p.add_argument('--suffix',default='002');v=p.parse_args();assert re.fullmatch(r'\d{3}',v.suffix);scope() if v.command=='scope' else globals()[v.command](v.suffix)
