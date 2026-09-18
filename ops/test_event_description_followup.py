import gzip
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('followup', Path(__file__).with_name('research-event-description-followup.py'))
research = importlib.util.module_from_spec(spec)
spec.loader.exec_module(research)


class FollowupTest(unittest.TestCase):
    def test_redirects_must_preserve_identity_and_have_an_introduction(self):
        with tempfile.TemporaryDirectory(prefix='artline-event-source-test-') as directory:
            out = Path(directory)
            (out / 'sources').mkdir()
            titles = ['lower', 'Broader', 'Ambiguous', 'Empty']
            queue = [{'id': f'event-q{i}', 'sourceId': f'Q{i}', 'title': title, 'language': 'fr', 'basic': True} for i, title in enumerate(titles, 1)]
            (out / 'article-queue.json').write_text(json.dumps(queue))
            pages = []
            for title, qid, extract, extra in [('Exact', 'Q1', 'Introduction.', {}), ('Broader', 'Q99', 'Different subject.', {}), ('Ambiguous', 'Q3', 'Disambiguation.', {'disambiguation': ''}), ('Empty', 'Q4', '', {})]:
                pages.append({'title': title, 'pageprops': {'wikibase_item': qid, **extra}, 'extract': extract, 'fullurl': 'https://fr.wikipedia.org/wiki/' + title, 'lastrevid': 123})
            evidence = {'host': 'fr.wikipedia.org', 'params': {'titles': '|'.join(titles)}, 'retrievedAt': '2026-09-18T00:00:00Z', 'response': {'query': {'normalized': [{'from': 'lower', 'to': 'Lower'}], 'redirects': [{'from': 'Lower', 'to': 'Exact'}], 'pages': pages}}}
            (out / 'sources/source.json.gz').write_bytes(gzip.compress(json.dumps(evidence).encode()))
            with patch.object(research, 'OUT', out):
                research.match()
            matches = json.loads((out / 'matched-introductions.json').read_text())
            self.assertEqual([r['id'] for r in matches], ['event-q1'])
            self.assertEqual(matches[0]['url'], 'https://fr.wikipedia.org/wiki/Exact')
            self.assertEqual(matches[0]['evidenceFile'], 'sources/source.json.gz')
            self.assertEqual(len(json.loads((out / 'article-issues.json').read_text())), 3)


if __name__ == '__main__':
    unittest.main()
