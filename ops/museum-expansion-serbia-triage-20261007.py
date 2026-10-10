#!/usr/bin/env python3
"""Preserve Serbian object-review decisions before a separately pinned import."""
import collections
import hashlib
import importlib.util
from pathlib import Path

spec=importlib.util.spec_from_file_location('v',Path(__file__).with_name('museum-expansion-serbia-vr-20261007.py'))
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
s=v.s;m=s.m;RUN=s.RUN
HOLDS={
 2:('duplicate_in_selected_sources','The 1882, 214 × 131 cm full Queen Natalie portrait is also VR object LvFtYJitunPAhuk4T. Count once using that richer record; the 82 × 66 cm preparatory bust study is separate.'),
 14:('existing_object_identity','Existing Nadezda Petrovic Self Portrait (1907), 9f3b6d5b-b6ea-51ea-a5c1-68d4f3c3b801, requires reconciliation as the same-work lead, not a new row. Its missing physical details remain unknown.'),
 25:('medium_classification_review','Keep the wood/дрворез wording. Confirm carved relief versus woodcut before retaining the preliminary sculpture classification; an unknown type is permissible in a revised reviewed plan.'),
 36:('version_review','Several same-creator bather records exist, including a London work with no physical details. Compare the 1915, 65.5 × 54 cm canvas before adding.'),
 37:('version_review','The Picasso pool includes many heads of women. Compare the 1909, 59 × 50 cm oil canvas with the native versions; do not decide solely from translated title or date.'),
 38:('version_review','Multiple Piazza San Marco paintings and records lacking physical details require comparison with this 75 × 98 cm canvas.'),
 39:('creator_and_version_review','An existing Jan Brueghel Vase of flowers has no physical details. The spelling probe also found a Bruegel Jan artist profile outside the initial exact-name pool; reconcile that scope before addition.'),
 41:('version_review','The generic 1883 young-woman caption needs comparison with other female portraits, including the 80.7 × 59.5 cm Jeanne Wenz canvas. The date discrepancy alone does not prove a different work.'),
 43:('version_review','The Cassatt pool includes Mother and Child and Mother and Little Girl records with missing physical details. Identify the 69 × 52 cm pastel independently.'),
 44:('version_review','Several Rouen Cathedral canvases have nearly identical formats. Match the particular facade/light version; no automatic addition based on the 1892 label.'),
 45:('version_review','This caption gives no medium or dimensions. Compare the 1898 Place du Theatre Francais variants before adding.'),
 46:('version_review','Existing ESCALIER TOURNANT DU PALAIS FARNESE A CAPRAROLA lacks dimensions. Compare against the 217 × 148 cm oil canvas, preserving both literal titles.'),
 47:('version_review','Existing Madonna with Child and Donor Tintoretto has an anomalous 1524 date and lacks physical metadata. Reconcile before assuming that the museum’s 1564–1567 tondo is a new object.'),
 58:('print_identity_review','Resolve the specific Durer engraved composition and impression. Other Peasant Couple titles exist and catalogue numbers are not supplied in the gallery caption.'),
 61:('print_identity_review','Callot Beggar with Wooden Leg impressions share plate and close sheet formats. The caption alone does not resolve this physical impression against retained NGA/Cleveland leads.'),
 63:('print_identity_review','Compare the hand-coloured Gauguin zincograph with the existing Joies de Bretagne record, retaining image, sheet and mount dimensions separately.'),
 65:('version_review','Existing Three Dancers in an Exercise Hall lacks physical metadata. Compare with the 29.8 × 42.8 cm charcoal/pastel before addition.'),
 67:('print_identity_review','The existing Chicago Orange has the same 1923 design and nearly identical sheet dimensions. Resolve the specific impression before adding another physical-object row.'),
}
NOTES={
 35:'The 42 × 27.5 cm oil-on-panel support differs from the existing peasant portraits on canvas and postcard/drawing scenes. Retain the source support and do not silently substitute a head-only title.',
 40:'The museum caption describes a 98 × 123 cm landscape-format canvas. The existing Nantes David composition is 132 × 104 cm portrait format; keep the separate version and literal century dating.',
 42:'The native Composition II is a 45 × 45 cm square. Existing explicitly numbered No. II canvases have distinct non-square formats, including the 1929 MoMA work (40.3 × 32.1 cm). The generic composition leads remain retained in the creator evidence.',
 60:'No writer-at-a-desk subject appeared in the complete captured Van Gogh creator pool. Preserve the 1882–1883 date range and 32 × 22.5 cm ink/pencil sheet.',
 64:'The retained Renoir creator pool produced no Coco-writing subject. Keep the approximately 1905 charcoal drawing and its 45 × 56.4 cm paper format.',
 66:'The retained Lozowick pool produced no Russian Church subject. This is an ink drawing, not a lithograph inferred from the artist’s other work.',
 77:'The complete ten-row Mestrovic pool contains other named sculptural subjects and crayon sheets, with no Remembrance lead. The museum sculpture department supports the object type; unspecified material remains unknown.',
 83:'Other generic Ring matches are later gold/gem objects, distinct from the source silver/enamel medieval ring. Preserve the literal early-fourteenth-century qualifier and unknown origin.',
 85:'Other generic Ring matches are later gem/enamel objects; this is the fifteenth-century gold-niello ring with Dubrovnik origin stated in the caption.',
 91:'The caption belongs to the authentic medieval collection, not the modern fresco-copy department. Retain the fourteenth-century fresco fragment and Pec Patriarchate origin.',
 92:'The generic Bracelet lead is later gold/gem work; the museum entry is silver from Markov Grad, Prilep, dated to the first half of the fourteenth century.',
 93:'Other generic Bowl matches differ in stated ceramic process or material and chronology. Retain the Pec glazed sgraffito bowl and source fourteenth-century interval.',
}


def ref(path):return dict(path=str(path.relative_to(m.ROOT)),sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def main():
    dest=RUN/'editorial-triage-001.json';assert not dest.exists()
    sources=[RUN/(x+'-research.json.gz') for x in ['serbia-caption-001','serbia-vr-001','serbia-report-001']]
    research=[m.load(p) for p in sources];records=[r for d in research for r in d['records']]
    comparison=RUN/'creator-title-comparison-leads-003.json.gz';comps={r['source_record_id']:r for r in m.load(comparison)['records']}
    decisions=[]
    for r in records:
        oid=r['source_record_id'];number=r['raw_source_record'].get('queue_number');c=comps[oid]
        if number in HOLDS:decision,note=HOLDS[number]
        elif oid=='vr-YQwXSuHgbYFiy6aiF':
            decision='source_medium_followup';note='Selected native object says tempera on board. A differently worded search lead needs capture before deciding whether it describes the same object; retain this source wording and do not replace it with acrylic.'
        else:
            decision='reviewed_candidate_pending_import_plan'
            note=NOTES.get(number,'Museum-supplied creator/title/date and object identity reviewed against the retained creator/name/title leads. No same-object lead established. Keep missing fields and source-qualified creator labels; this decision does not itself write to the catalogue.')
            if oid.startswith('report-'):
                note='Individually inventoried object in the museum’s 2015 outgoing-loan list, with explicit creation date and source collection. No existing creator/title match found in the retained scope. Keep source inventory, unknown individual type/medium, attribution qualifiers and historical evidence date; the loan venue is not the holding museum.'
            elif oid.startswith('vr-'):
                note='Native virtual-object and exhibition records agree on identity and physical format; official museum link and retained collection evidence support the holding. The existing creator pool contains other named subjects/formats. Preserve native narrative, creation qualifiers, version details and missing accession.'
        decisions.append(dict(source_record_id=oid,queue_number=number,decision=decision,note=note,facts=r['facts'],creator_pool_size=c['pool_size'],creator_pool_ids=c['pool_ids'],exact_title_lead_ids=[v['id'] for v in c['exact_title_leads']]))
    counts=collections.Counter(d['decision'] for d in decisions)
    assert len(records)==134 and counts['reviewed_candidate_pending_import_plan']==115
    m.save(dest,dict(at=m.now(),decisions=decisions,counts=counts,evidence=[ref(p) for p in sources+[comparison,RUN/'creator-identity-review-003.json.gz',RUN/'creator-spelling-probe-001.json']],
        source_level_holds=sum(len(d['held']) for d in research),policy='Editorial triage only, not an import plan or apply authorization. 115 candidates can proceed to pinned-plan validation and fresh database identity checks; 19 require reconciliation. All supplied evidence retained. No catalogue writes.'))
    print(dict(counts),flush=True)


if __name__=='__main__':main()
