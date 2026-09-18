import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('artifact_scan', Path(__file__).with_name('audit-followup-artifacts.py'))
scan = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scan)


class ArtifactScanTests(unittest.TestCase):
    def check(self, content, patterns):
        with tempfile.TemporaryDirectory(prefix='artline-artifact-scan-') as directory:
            root = Path(directory)
            path = root / 'synthetic.txt'
            path.write_bytes(content)
            with patch.object(scan, 'ROOT', root):
                return scan.findings(path, patterns)

    def test_secret_across_stream_boundary(self):
        token = b'ya' + b'29.' + b'A' * 90
        result = self.check(b' ' * (1024 * 1024 - 15) + token, scan.CREDENTIALS)
        self.assertEqual([x['pattern'] for x in result], ['google_access_token'])
        self.assertNotIn(token.decode(), str(result))

    def test_password_url_is_reported_without_value(self):
        value = b'postgres' + b'://synthetic:fixture_password@example.invalid/db'
        result = self.check(value, scan.CREDENTIALS)
        self.assertEqual(result[0]['pattern'], 'database_password_url')
        self.assertNotIn('fixture_password', str(result))

    def test_passwordless_local_connection_is_not_secret(self):
        self.assertEqual(self.check(b'postgres://localhost/artline', scan.CREDENTIALS), [])

    def test_private_archive_path_is_blocked(self):
        value = b'/offline/' + b'art' + b'500k.tar.gz'
        self.assertTrue(self.check(value, scan.PRIVATE_REFERENCE))

    def test_no_use_statement_is_not_dataset_material(self):
        self.assertEqual(self.check(b'{"art500k_used": false}', scan.PRIVATE_REFERENCE), [])


if __name__ == '__main__':
    unittest.main()
