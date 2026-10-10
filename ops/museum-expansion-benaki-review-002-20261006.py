#!/usr/bin/env python3
"""Individually read creation/attribution excerpts for the second Benaki pass."""
import collections
import hashlib
import importlib.util
import json
import re
from pathlib import Path

spec=importlib.util.spec_from_file_location('benaki',Path(__file__).with_name('museum-expansion-benaki-20261006.py'))
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
m=b.m

# Every date below was read in its object description. Prototype dates,
# depicted events, lifespans, modern false inscriptions and donation dates
# were reviewed separately; this is not a general narrative date extractor.
CLAIMS='''108399|Αρχές 19ου αι.|
108540|Aρχές 19ου αι.|
108699|Τέλη 18ου αι.|
108729|1779|
108393|1727|
108606|19ος αι.|
107679|Δεύτερο μισό 18ου αι.|
108633|18ος αι.|
108621|18ος αι.|
108696|18ος αι.|
108639|18ος αι.|
108642|18ος αι.|
108702|18ος αι.|Εργαστήριο Αγίου Όρους (;)
108705|18ος αι.|Εργαστήριο Αγίου Όρους (;)
108324|18ος αι.|
108684|18ος αι.|
108693|Αρχές 18ου αι.|
108726|Αρχές 18ου αι.|
108681|Αρχές 18ου αι.|
108663|Αρχές 18ου αι.|Ελλαδικό εργαστήριο (;)
108720|Αρχές 18ου αι.|
108678|Αρχές 18ου αι.|Εργαστήριο Αγίου Όρους ή βορειοελλαδικό
108714|Αρχές 18ου αι.|
108723|Αρχές 18ου αιώνα.|
107640|Γύρω στα 1700|Επτανησιακό εργαστήριο
108411|Γύρω στο 1700|
108690|Γύρω στο 1700|
108648|1678|Το έργο φέρει την υπογραφή του Ρεθύμνιου ζωγράφου Ηλία Μόσκου (1649-1687)
107508|Τέλη 17ου-18ος αι.|
107457|Τέλη 17ου αι.|Το έργο συνδέεται με την τέχνη τού ζωγράφου Θεόδωρου Πουλάκη (1620-1692)
107544|Τέλη 17ου αι.|
107634|Τέλη 17ου αι.|
108462|Τέλη 17ου αι.|
108654|Τέλη 17ου αι.|
108669|Τέλη 17ου αι.|
108687|Τέλη 17ου αι.|συνδέει την εικόνα με εργαστήρια που έδρασαν στον ηπειρωτικό ελλαδικό χώρο τον 17ο αι.
107697|Tέλη 17ου αι.|ενυπόγραφο έργο του Γεώργιου Ορέγκου
108267|τέλη 16ου αι.|Κρητικό εργαστήριο
108561|τέλη 17ου αι.|Επτανησιακό εργαστήριο
108294|1658|ενυπόγραφη δημιουργία του Pεθύμνιου ζωγράφου Hλία Mόσκου
108306|Β΄ μισό 17ου αι.|
107427|Β' μισό 17ου αι.|του Βίκτωρος
107439|Β' μισό 17ου αι.|του Κωνσταντίνου Τζάνε
107661|1623|συνδέεται με το κρητικό εργαστήριο των Λαμπάρδων
107655|17ος αι.|
107688|17ος αι.|η υπογραφή του ζωγράφου, Λουκά Μαυρίκη
107763|17ος αι.|εικόνα βορειοελλαδικού εργαστηρίου
107574|17ος αι.|Κρητικό εργαστήριο
107658|17ος αι.|Εικόνα κρητικού εργαστηρίου
107541|Α' μισό 17ου αι.|του Εμμανουήλ Λαμπάρδου
107670|Α' μισό 17ου αι.|του Εμμανουήλ Λαμπάρδου. Στις πηγές αναφέρονται δύο ομώνυμοι αγιογράφοι, θείος και ανιψιός, οι οποίοι πιθανώς δούλευαν σε κοινό εργαστήριο στο Χάνδακα της Κρήτης
107745|α' μισό 17ου αι.|Κρητικό εργαστήριο
107517|Αρχές 17ου αι.|
107673|Αρχές 17ου αι.|Το έργο φέρει την υπογραφή τού Κρητικού ζωγράφου Ιωάννη Λαμπάρδου (1627-1639)
108660|Αρχές 17ου αι.|Κρητικό εργαστήριο
108666|Αρχές 17ου αι.|Κρητικό εργαστήριο
107502|γύρω στο 1600|Κρητικό εργαστήριο
107535|Γύρω στo 1600|Τα τεχνοτροπικά χαρακτηριστικά συσχετίζουν το έργο με αγιορείτικα εργαστήρια που ακολουθούν την κρητική παράδοση
108333|Τέλος 16ου-αρχές 17ου αι.|Κρητικό εργαστήριο
108384|Τέλη 16ου - αρχές 17ου αι.|Κρητικό εργαστήριο
107562|Τέλη 16ου - α' τέταρτο 17ου αι.|του Εμμανουήλ Τζανφουρνάρη
107481|Τέλη 16ου αι.|Κρητικό εργαστήριο
108369|Tέλη 16ου αι.|έργο μακεδονικού εργαστηρίου
107685|Τέλη 16ου αι.|Η εικόνα φέρει πλαστή υπογραφή του Εμμανουήλ Λαμπάρδου, προέρχεται όμως από σύγχρονο κρητικό εργαστήριο
108414|Τέλη 16ου αι.|Κρητικό εργαστήριο
107583|1565-1567|ενυπόγραφη δημιουργία της κρητικής περιόδου του Δομήνικου Θεοτοκόπουλου (1541-1614)
108459|Δεύτερο μισό 16ου αι.|δημιουργία εργαστηρίου της ηπειρωτικής Eλλάδας
108483|Δεύτερο μισό 16ου αι.|δημιουργία εργαστηρίου της ηπειρωτικής Eλλάδας
107910|β' μισό 16ου αι.|Εργαστήριο Αγίου Όρους
107721|Μέσα 16ου αι.|του Πέτρου Λαμπάρδου
107652|μέσα 16ου αι.|Κρητικό εργαστήριο
108276|μέσων του 16ου αι.|έργο της Kρητικής Σχολής
108531|Μέσα 16ου αι.|Κρητικό εργαστήριο
108585|Μέσα 16ου αι.|Εργαστήριο Αγίου Όρους (;)
108672|16ος αι.|Κρητικό εργαστήριο
108309|Πρώτο μισό 16ου αι.|δημιουργία του εγκατεστημένου στη Bενετία Έλληνα ζωγράφου Iωάννη Περμενιάτη
107589|α' μισό 16ου αι.|Κρητικό εργαστήριο
108408|Aρχές 16ου αι.|εικόνα κρητικής τέχνης, ίσως από την Kωνσταντινούπολη
108651|αρχές 16ου αι.|Κρητικό εργαστήριο
107424|Β' μισό 15ου αι.|έργο κρητικού εργαστηρίου
107700|δεύτερο μισό του 15ου αι.|συνδέεται με την παράδοση της καλλιτεχνικής παραγωγής του ζωγράφου Aγγέλου
108279|Δεύτερο μισό 15ου αι.|δημιουργία της ιταλοκρητικής ζωγραφικής
108348|δεύτερο μισό του 15ου αι.|εικόνα κρητικής τέχνης
108372|δεύτερο μισό του 15ου αι.|μας παραπέμπει στο δεύτερο μισό του 15ου αι. και στην καλλιτεχνική παραγωγή του Aνδρέα Pίτζου
108453|Δεύτερο μισό 15ου αι.|
108327|Δεύτερο μισό 15ου αι.|Η πρώιμη αυτή κρητική εικόνα φέρει πλαστή υπογραφή του πολύ μεταγενέστερου ζωγράφου Εμμανουήλ Τζανφουρνάρη
108351|Δεύτερο μισό 15ου αι.|Εικόνα ιταλοκρητικής τεχνοτροπίας
107607|μέσα 15ου αι.|Εργαστήριο του ζωγράφου Aγγέλου (;)
108597|Μέσα 15ου αι.|Κρητικό εργαστήριο
108366|Δεύτερο τέταρτο 15ου αι.|ενυπόγραφη δημιουργία του ζωγράφου Aγγέλου
107595|Αρχές 15ου αι.|'''

HELD={
    '108615':'Painted icon and silver cover have separate dimensions; production-phase scope unresolved.',
    '108441':'Silver cover and its assay monogram need separate component/date review.',
    '108477':'Silver cover rather than a painting; object classification review required.',
    '108567':'Mixed painted and silver-gilt object classification remains unresolved.',
    '108285':'Early medieval lamp on a 1783 disc: distinct physical production phases.',
    '108588':'Silver-gilt object classification remains unresolved.',
    '108645':'Central triptych leaf: component and whole-object identity require further review.',
    '107739':'Existing Stavrakis Deposition record 03df8d95-134a-5f09-b4fc-5b02adb0f670 has the translated subject, author and Benaki holding; no duplicate addition.',
    '108177':'Wooden panagiarion fragment, not assumed to be a painted icon.',
    '108288':'Native object title and description are blank.',
    '107850':'Icon and carved iconostasis have separate donor statements; composite object scope requires review.',
    '107499':'Archangel possibly from an artophorion: component scope and qualified attribution need review.',
    '107553':'Existing Benaki inventory 3027; no duplicate addition.',
    '107859':'Whole triptych with exterior/interior scenes: one-object/face identity needs further review.',
    '107715':'Existing Benaki inventory 3728; no duplicate addition.',
    '107784':'Existing Benaki inventory 11198; no duplicate addition.',
    '107682':'Existing Benaki inventory 3008; no duplicate addition. Also preserve potential legacy translated-title duplicate In You Rejoiceth for later reconciliation.',
    '107547':'Existing Leos Moskos Christ the Vine, 8e89c291-b1c2-5c38-aeb1-6b0fa94f74c7; old inventory remains unknown.',
    '107577':'Existing Elias Moskos Virgin and Child on Bronze, 78281794-c1d7-5c14-ba92-55d07f56c4db; old inventory remains unknown.',
    '107616':'Existing Benaki inventory 3009; no duplicate addition.',
    '107637':'Whole triptych: one-object/face identity needs further review.',
    '107691':'Existing Poulakis Archangel Michael, 9f37c95d-2951-54ec-8a72-60ab9d91a638; old inventory remains unknown.',
    '108381':'Questioned source century and relief/plaster background require separate review.',
    '107442':'Anonymous painting after a Damaskinos model with a modern false Tzanes signature: reconcile with existing Allegory of Holy Communion record fc830118-18b7-5dd0-8027-9bbf04c7f718 before adding.',
    '108435':'1560s wording directly qualifies Arabic inscriptions; verify creation-date scope before adding.',
    '107988':'Potential same work as El Greco St. Luke Painting the Virgin d8a0f607-54e3-529b-bab4-570e7948c0fb, currently without a holding. Source date differs; reconcile identity without creating a duplicate.',
    '107604':'Sixteenth-century statement refers to painter activity, not explicitly the object creation; hold date.',
    '108330':'Existing Benaki inventory 21168; no duplicate addition.',
    '107919':'Triptych leaf: component identity requires further review.',
    '108603':'Later frame and painting need a separate scope review.',
    '107463':'Templon architrave fragment: support/component identity requires further review.',
    '108273':'Triptych leaf, surviving centre and lost right leaf require whole-object reconciliation.',
    '108405':'Whole triptych attributed to Ritzos workshop; compare against existing Ritzos Virgin Enthroned records before adding.',
    '107592':'Relief icon: not assumed to be a painting.',
    '107979':'Blank title; steatite triptych component with questioned date.',
    '108066':'Blank title; steatite icon, not a painting.',
}


def capture_rows():
    rows={}
    for number in range(1,6):
        path=b.RUN/f'byzantine-objects-{number:03d}.json.gz'
        for row in m.load(path)['records']:
            key=row['item']['source_id']
            parsed=b.fields(b.read_capture(row['source']))
            if key in rows:assert parsed==rows[key]['native_fields'],'Native object changed between index pages'
            else:rows[key]=dict(row,native_fields=parsed)
    return rows


def review():
    rows=capture_rows();selected=[];errors=[]
    for line in CLAIMS.splitlines():
        key,date,creator=line.split('|');r=rows[key];p=r['native_fields'];body=p['description']
        inv=re.search(r'\((?:ΓΕ )?\d+\)\.?$',body)
        dimensions=re.findall(r'\d+,\d+\s*[xX]\s*\d+,\s*\d+ μ\.',body)
        dimensions+=re.findall(r'Ύψ\. \d+,\d+ μ\., πλ\. \d+,\d+ μ\.',body)
        if not inv or len(dimensions)>1:errors.append((key,'inventory/dimensions'));continue
        rv=dict(creation_statement=date,creator_statement=creator or None,dimensions_statement=dimensions[0] if dimensions else None,medium_statement=None,accession=inv[0].rstrip('.').strip('()'),work_type='painting',object_form='icon')
        if re.match(r'(?:[ΑA]ρχές|[ΤT]έλη|Τέλος|Μέσα|μέσων του) ',date,re.I):rv['date_interval_basis']='enclosing_source_century_without_invented_subdivision'
        if re.match('γύρω',date,re.I):rv['date_interval_basis']='source_circa_central_year_no_invented_uncertainty_interval'
        if 'από δωδεκάορτο' in body:rv['object_scope_review']=dict(kind='single_templon_panel',note='This individually catalogued painted panel has its own inventory and panel dimensions. It is counted once as this panel, not as an entire altar or cycle; source component wording is preserved.')
        if 'Αμφιπρόσωπη' in body:rv['object_scope_review']=dict(kind='single_double_sided_icon',note='The native record describes one two-sided icon under one inventory. Create one whole-object record, not two face records; retain both-sided scope in the source evidence.')
        if key=='107583':rv['support_scope_review']='painting_on_reused_chest_panel_not_fragment_of_painting'
        if key in ['107661','108453','108327','107607']:rv['production_phase_review']='Selected creation statement dates the underlying painting. Later inscription, angel addition or false signature is separately described in the retained native narrative; its date is not substituted as original creation.'
        try:f=b.facts(p,rv,r['source']['receipt']['url'])
        except AssertionError as e:errors.append((key,str(e),rv));continue
        selected.append(dict(source_record_id=key,review=rv,source=r['source'],native_fields=p,facts=f))
    if errors:
        print(json.dumps(dict(errors=errors),ensure_ascii=False,indent=2));return
    prior={r['source_record_id'] for r in m.load(m.RUN/'benaki-001-current-plan.json.gz')['records']}
    assert not prior&{r['source_record_id'] for r in selected}
    unresolved=set(rows)-prior-{r['source_record_id'] for r in selected}-HELD.keys()
    assert not unresolved,unresolved
    holds=[dict(source_record_id=key,reason=reason,native_fields=rows[key]['native_fields'],source=rows[key]['source']) for key,reason in HELD.items() if key in rows]
    result=dict(at=m.now(),records=selected,held=holds,policy='Individually reviewed source clauses. Qualitative subdivisions retain conservative enclosing-century bounds; explicit circa dates retain the approximate central year and circa precision without fabricated uncertainty endpoints. Catalogue captions distinguish paintings from components, prototypes, attributions, false signatures, artist life dates and depicted events. No additions approved until source and duplicate validation completes.')
    m.save(b.RUN/'byzantine-reviewed-statements-002.json',result)
    print(json.dumps(dict(selected=len(selected),held=len(holds),date_precision=dict(collections.Counter(r['facts']['date_precision'] for r in selected))),ensure_ascii=False))


if __name__=='__main__':review()
