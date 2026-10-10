"""Inspect literal field vocabulary before collection/date selection rules."""
import collections,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('d',Path(__file__).with_name('museum-expansion-france-fifteenth-discovery-20261008.py'));d=importlib.util.module_from_spec(s);s.loader.exec_module(d)
def main():
    p=d.RUN/'discovery-field-profile-001.json';assert not p.exists();x=d.m.load(d.DISCOVERY);out={}
    fields=['Nom_officiel_musee','Ville','Localisation','Statut_juridique','Denomination','Domaine','Millesime_de_creation','Periode_de_creation','Lieu_de_depot','MANQUANT','MANQUANT_COM']
    for code in d.CODES:
        rows=[v['raw_source_record'] for v in x['rows'] if v['raw_source_record']['Code_Museofile']==code]
        out[code]={key:dict(collections.Counter(v.get(key) or '' for v in rows)) for key in fields}
    d.m.save(p,dict(at=d.m.now(),museums=out,discovery_reference=d.prior.reference(d.DISCOVERY),profiler_reference=d.prior.reference(Path(__file__).resolve()),database_writes=0,policy='Vocabulary discovery only. Source labels, dates and custody still require individual evidence; totals are not eligible artwork counts.'))
    for code,v in out.items():print(code,json.dumps({k:dict(sorted(c.items(),key=lambda v:-v[1])[:12]) for k,c in v.items()},ensure_ascii=False),flush=True)
if __name__=='__main__':main()
