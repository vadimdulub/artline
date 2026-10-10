"""Preserve exact primary evidence for close physical-version comparisons."""
import gzip, importlib.util, json
from pathlib import Path
s = importlib.util.spec_from_file_location('f', Path(__file__).with_name('museum-expansion-france-eighth-facts-20261008.py'))
f = importlib.util.module_from_spec(s); s.loader.exec_module(f)
m = f.m
def main():
    out = f.RUN / 'physical-comparison-context-001.json.gz'; assert not out.exists()
    citation_path = f.RUN / 'identity-citations-003.json.gz'
    citations = m.load(citation_path)['citations']
    dependencies = {Path(__file__).resolve(), citation_path}
    rows = []
    for prefix, number in [('5a434825', 83), ('f7af95a9', 160), ('90dfbf3f', 183), ('12b14556', 192)]:
        found = []
        for citation in citations:
            if not citation['entity_id'].startswith(prefix): continue
            try: note = json.loads(citation['evidence_note'])
            except (ValueError, TypeError): continue
            record = None
            if 'facts' in note:
                record = note['facts']
            elif 'evidence_path' in note:
                path = m.ROOT / note['evidence_path']; dependencies.add(path)
                data = json.load(gzip.open(path, 'rt'))
                if 'data' in data:
                    record = next(v for v in data['data'] if v['Reference'] == citation['source_record_id'])
                elif 'hits' in data:
                    matches = [v['_source'] for v in data['hits']['hits'] if any(i.get('value') == citation['source_record_id'] for i in v['_source']['identifier'])]
                    assert len(matches) == 1; record = matches[0]
            if record is not None:
                found.append(dict(candidate_number=number, existing_artwork_id=citation['entity_id'], source_record_id=citation['source_record_id'], source_url=citation['source_url'], literal_primary_record=record))
        assert len(found) == 1, (prefix, len(found)); rows += found
    m.save(out, dict(at=m.now(), rows=rows, dependencies=[f.ref(p) for p in sorted(dependencies)], policy='Saved primary-source comparison evidence is used only to distinguish physical objects, not to update existing catalogue records. Original source bodies and citation references remain pinned.'))
    print('Four primary physical-object comparison extracts preserved.')
if __name__ == '__main__': main()
