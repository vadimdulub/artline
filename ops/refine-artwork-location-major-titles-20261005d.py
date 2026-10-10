#!/usr/bin/env python3
"""Explicit title comparisons after inventory, creator and date reconciliation."""
import collections
import copy
import importlib.util
from pathlib import Path

s = importlib.util.spec_from_file_location('m', Path(__file__).with_name('research-artwork-location-major-museums-20261005d.py'))
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)
r, p = m.r, m.p

# These are individual comparisons, never rules to match other objects. Each
# selected source already has an exact native ID/inventory, creator and date.
DECISIONS = {
 'f410f207-8f8a-561d-9c11-c9f24ce664fb': 'English/Spanish translation: Juan of Austria presented to Charles V at Yuste.',
 'eda0d478-4ee3-5b54-82d7-e7d29d410700': 'Same named sitter Maria de Figueroa dressed as a menina; child qualifier omitted.',
 '833d4941-a6d1-5200-8039-21c66501b842': 'Same Juana and Catalina at Tordesillas; honorific dona omitted.',
 'aa8350f6-3bd5-5e99-88d2-06995e892e2f': 'English/Spanish translation: an autopsy.',
 '6f12eb18-ca11-50c1-811d-360e7a78926e': 'English/Spanish translation: portrait of a girl.',
 '9f147e1d-7278-56f7-9983-b1b8dd3f5fe5': 'El aquelarre translates as Witches Sabbath; source appends an alternative title. Exact P000761 distinguishes other versions.',
 'a55bc527-9efd-5165-9d5c-db7ca0f648c2': 'English/Spanish translation: Virgin, Child and infant Saint John.',
 '560347b3-b6d0-5116-a033-7db2244d4dba': 'English/Spanish translation: mystical marriage of Saint Catherine.',
 '17b39ad5-32ce-50a3-9551-cd4ea2129c5b': 'English/Spanish translation: Immaculate Conception.',
 'ba59af30-3f5c-5dde-a7e2-7dc81802e209': 'English/Spanish translation: Ferdinand taking the oath as Prince of Asturias.',
 'c94507cf-c0fb-5939-a526-649dd1ae7b66': 'Same named sitter Pedro Lopez de Lerena, first Count of Lerena; honorific differs.',
 '0b98b157-03ca-551c-8b60-f72ed8c62d53': 'Same Pedro de Alcantara de Toledo y Salm-Salm, thirteenth Duke of Infantado; surname expanded locally.',
 '7648a61d-6456-575c-8c60-08435ae69657': 'Same named sitter Jaime Girona; maternal surname omitted from catalogue title.',
 '0673d383-38cf-595a-8a13-345e4af10db7': 'After the bath corresponds to woman leaving the bath; exact inventory identifies the object.',
 'f7d9f718-9489-5de8-9e01-c4a3d8f68224': 'English/Spanish translation: episode of the Battle of Tetuan; catalogue adds event year 1860.',
 '15c8da22-6b0c-5032-ad0f-fd63d225f0ca': 'English/Spanish translation: death of Lucretia.',
 '14d8b0ac-1d28-5a49-b733-64239284d804': 'English/Spanish translation: final moments of King Jaime giving his sword to his son Pedro.',
 'cf781be9-e2a6-57dc-bc78-2c29611a66bf': 'Same boat on the Cabanal beach in Valencia; local place spelling is abbreviated. Exact inventory retained.',
 '19602888-fe38-51d8-ac21-511996885a54': 'English/Spanish translation of the same Prince Juan baptismal procession in Seville.',
 '26ff66e8-71f4-575e-bf7e-fd9f9af9e083': 'English/Spanish translation: Juana the Mad.',
 '39e2d62c-faa2-5296-b867-91e804ac0f90': 'English/Spanish translation: Virgin of the Rosary; exact inventory identifies this composition.',
 '826f1cb3-86cd-523f-bd7d-8392036de73d': 'English/Spanish translation: Hercules fighting the Lernaean hydra.',
 '4e50bcc5-c608-532a-8a5b-82945a0aebc3': 'Same complete sitter name Cesareo Maria Saenz y de la Barrera; portrait prefix omitted.',
 '51ad237d-ffa9-5771-b37c-957e7e167130': 'Same Saint Catherine; catalogue expands identification to Catherine of Alexandria.',
 '5bf7ce9d-7532-5d0a-9c16-7bd9d26cf5de': 'Identical Escorial prior cell title except leading article.',
 '07d10af7-b606-5f65-9f25-49db78cbdfb4': 'Identical first miracle of Teresa and resurrection of Gonzalo Ovalle; honorifics and punctuation differ.',
 '36265c61-b1a1-57f3-90fc-894585456e00': 'Same named Garcia Aznar, Count of Aragon; honorific omitted.',
 '001d3fb8-6e9b-5330-9fe2-0dc2eab3616a': 'English/Spanish translation: Rebecca and Eliezer.',
 '97a21b18-f26c-5508-9c20-3b345c3b5cce': 'English/Spanish translation: And they still say fish is expensive.',
 'b164aa59-a451-5233-a091-2e4e79e6cc38': 'English/Spanish translation: martyrdom of Saint Philip.',
 'a89bb229-bcae-535d-b009-ae42536164eb': 'English/Spanish translation: recovery of Bahia de Todos los Santos.',
 '200972a1-738e-4117-8b91-09fb5b90f9f5': 'Same Battle of Ocana and same event date, 18 November 1809; punctuation and article differ.',
 '0836c9a7-2d44-4afd-a9f9-92549c41605f': 'Same Pope Pius VII with identical life dates; election detail replaced by portrait prefix.',
 'aa8a7f28-c75b-4b51-97fb-31e1a9c802ff': 'Artist self-portrait; current title adds seated beside an easel. Exact RF1608 identifies this version.',
 'c72ae1c5-f167-4dab-9ca6-01991f8b0f34': 'Identical taking/entry of crusaders into Constantinople; current title adds the event date.',
 '423be4f3-df3d-4840-95b0-c334e328e150': 'Identical Liberty Leading the People and 28 July 1830; event date order changed.',
 'd5c6f279-ce21-49ee-a216-73180c1c35d1': 'Identical Triumph of Earth or Cybele; current title adds ceiling designation.',
 'fdfe74d9-a09c-4c63-a5e0-243e986984f9': 'Same Charles V received by Francis I at Saint-Denis in 1540; punctuation differs.',
 '3bb77ac6-7a3e-43bb-8e16-fdb1ce7a1f07': 'Same two alternative titles Apotheosis of Homer and Homer Deified in reversed order.',
 '1e228c9f-b0a6-490e-9f6b-375830502e20': 'Same Charles X with identical life dates; royal clothes/full-length descriptions identify exact INV4435.',
 'd856ab36-c6e5-42a0-84e6-3e98d28c747c': 'Same Lara; parenthetical literary reference removed.',
 'a97a873d-7e9a-40ca-987b-def7c7384343': 'Same Jean-Baptiste Oudry and life dates; painter descriptor added.',
 'cd179aee-7dbf-46a0-b215-f7680dd0182d': 'Same Lambert-Sigisbert Adam the elder and life dates; sculptor descriptor added.',
 '00b73cb0-c67a-4995-bb9c-5d8c035cd1fe': 'Same Children in the Snow; older alternative title omitted.',
 'a546da8a-63f3-4e5f-90c4-9138580712cc': 'Same Hermit or Brother Luce; current title adds La Fontaine literary reference.',
 'e673076e-3544-4246-80ad-e42d48dcb0f4': 'Same Portrait of a Young Woman; older alternative title omitted.',
 '780c68ac-de57-43cd-869f-4a264993ec4f': 'Same Pilgrimage to the Island of Cythera; alternative embarkation title omitted. Inventory distinguishes versions.',
 '7e7aff95-72a3-4ff6-9170-2cb1b76d3384': 'Same couple and former Ferdinand Bol/Lisbeth Dell identification; current title expands the pose.',
 '7dbb3ab7-3508-4289-91d4-f799bf91db12': 'Same concert with female singer and theorbo-lute player; duo wording expanded.',
 'f1774fa6-ce36-4b98-a3bd-94eed4d66d49': 'Identical Adoration of the Shepherds except leading article.',
 '4ff51144-23d0-4b40-b695-48aa11dbbc22': 'Same Maurice of Bavaria with identical dates; former Charles Louis attribution of sitter omitted.',
 'da6def6e-559c-468c-9760-d3978c005de1': 'Same ancient Rome ruins with relief; current title describes the relief subject. Exact INV1086.',
 'aeb9d179-17f6-4655-9e80-acc27154454b': 'Same two alternative titles Evening and Lost Illusions in reversed order.',
 '0cb84e4b-2bc1-414f-be4d-23a113a808d0': 'Same Etienne Jeaurat and life dates; current title adds portrait/painter descriptors.',
 'b421248a-6fcd-4b5d-8255-9a31137c5146': 'Same portrait of a man; current title describes black clothes and gloves. Exact INV2105.',
 'e46ed391-b8eb-406d-bb31-82e5a7649a71': 'Same interior of Monsieur Sauvageot collection; earlier title expands address and pre-transfer setting. Exact MI861.',
}


def main():
    claims = []
    seen = set()
    for provider, flag in [('prado-dataset-20261005d', 'spanish_catalogue_title_requires_review'), ('louvre-authorities-20261005d', 'current_title_requires_review')]:
        for old in r.load(r.RUN / 'primary-plans' / (provider + '.json.gz'))['claims']:
            aid = old['artwork_id']
            if aid not in DECISIONS: continue
            assert old['object_evidence']['qualifications'] == [flag]
            c = copy.deepcopy(old)
            c['review_state'] = 'accepted'
            c['object_evidence']['qualifications'] = []
            c['object_evidence']['individual_title_reconciliation'] = {'local_title': old['title'], 'decision': DECISIONS[aid], 'prior_review_flag': flag, 'source_object_identifier': c['external_id'], 'original_catalogue_titles_preserved': True}
            c['identity_basis'] += '; individually compared title translation/expansion with exact inventory and native object identity'
            if c['scheme'] == 'prado-object':
                number = c['object_evidence']['catalogue_facts_from_2026_dataset']['Número de catálogo']
                c['duplicate_native_ids'] = [number, m.inventory(number)]
            claims.append(c)
            seen.add(aid)
    assert seen == DECISIONS.keys()
    p.output('major-title-reconciliations-20261005d', claims, [])
    print(collections.Counter(c['scheme'] for c in claims), flush=True)


if __name__ == '__main__': main()
