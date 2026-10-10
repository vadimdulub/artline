#!/usr/bin/env python3
"""Identify deposit recipients independently from the object's legal owner."""
import collections
import copy
import importlib.util
import re
from pathlib import Path

spec=importlib.util.spec_from_file_location('f',Path(__file__).with_name('refine-artwork-location-french-museum-names-20261005d.py'))
f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f);r,p=f.r,f.p


def decision(obj,authority,registry):
    if obj.get('Code_Museofile')!=authority['Identifiant']:return None
    name,city=f.words(authority['Nom_officiel']),f.words(authority['Ville'])
    if (f.words(obj.get('Nom_officiel_musee')),f.words(obj.get('Ville')))!=(name,city):return None
    loc=[f.words(v)for v in (obj.get('Localisation')or'').split(';')if v.strip()]
    depo=[f.words(v)for v in (obj.get('Lieu_de_depot')or'').split(';')if v.strip()]
    if loc!=[city,name]:return None
    mode=None
    if len(depo)>=3 and depo[-3:] in [['depot',city,name],['depot reglementaire',city,name]]:
        mode='exact_registered_deposit_recipient_and_conservation_place'
    elif obj.get('Code_Museofile')=='M5025' and depo==['depot',name]:
        # This specific notice abbreviates DEPO by omitting the city. The
        # complete LOCA and Museofile code still independently name Paris.
        same_name=[a for a in registry if f.words(a['Nom_officiel'])==name]
        if len(same_name)==1:mode='unique_armee_recipient_name_with_explicit_paris_conservation_place'
    if not mode:return None
    if obj.get('MANQUANT')or obj.get('MANQUANT_COM'):return None
    if re.search(r'\b(attribue|copie|atelier|ecole|suiveur|entourage|apres|anonyme)\b|\?',r.norm(obj.get('Auteur'))):return None
    legal=r.norm(obj.get('Statut_juridique'))
    if not legal or re.search(r'recuperation|restitution|restitue|usufruit|\bearm\b|\bmnr\b|\?',legal):return None
    if re.search(r'\?|\b(pret|prets|pretee?|restitu\w*|recuperation|manquant|disparu|vole|termine|retour\w*)\b',r.norm(obj.get('Lieu_de_depot'))):return None
    if obj.get('Code_Museofile')=='M5031':return None
    return {'basis':mode,'registered_museum':authority,'original_conservation_place':obj['Localisation'],
        'original_deposit_destination':obj['Lieu_de_depot'],'original_legal_status':obj['Statut_juridique'],
        'ownership_is_not_inferred':True,
        'interpretation':'DEPO names the receiving institution; LOCA names the conservation place. Both agree with the unique current museum authority. A private owner or incomplete acquisition wording does not change this documented recipient. The legal owner is preserved without a new ownership claim.'}


def main():
    ids={v['id']for v in r.load(r.RUN/'museum-guides-baseline-20261005e.json.gz')['missing']}
    registry=r.load(r.RUN/'museofile-current-20261005b.json.gz');bycode={a['Identifiant']:a for a in registry['rows']}
    originals={c['artwork_id']:c for provider in ['joconde-deposit-review-20261005','joconde-alias-20261005b']
        for c in r.load(r.RUN/'primary-plans'/(provider+'.json.gz'))['claims']if c['artwork_id']in ids and c.get('review_state')=='review'}
    claims=[]
    for old in originals.values():
        obj=old['object_evidence'];authority=bycode.get(obj.get('Code_Museofile'))
        proof=decision(obj,authority,registry['rows']) if authority else None
        if not proof:continue
        c=copy.deepcopy(old);c.update(review_state='accepted',source_class='primary_catalogue_documented_deposit_recipient',
            identity_basis=old['identity_basis']+'; '+proof['basis'],
            object_evidence={'current_object_record':obj,'prior_review_candidate':old,'recipient_reconciliation':proof,
                'registry_receipt':registry['receipt'],'field_specification':r.load(r.RUN/'joconde-deposit-specification-20261005d.json')},
            limitation='Documented museum holding as the receiving institution of a deposit. The source legal owner may be private or different and is not reassigned. No fresh physical observation, on-view status, publication, creation date or creator change.')
        claims.append(c)
    p.output('deposit-recipients-20261005e',claims,[])
    print(collections.Counter(c['institution']['name']for c in claims),flush=True)


if __name__=='__main__':main()
