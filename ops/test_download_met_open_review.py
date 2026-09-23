import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('download', Path(__file__).with_name('download-met-open-review.py'))
download = importlib.util.module_from_spec(spec)
spec.loader.exec_module(download)


class DownloadGateTests(unittest.TestCase):
    def record(self, **changes):
        return dict(objectID=123, isPublicDomain=True, rightsAndReproduction='',
                    objectBeginDate=1800, objectEndDate=1800, objectDate='1800',
                    primaryImage='https://images.metmuseum.org/CRDImages/ep/original/example.jpg',
                    **changes)

    def test_accepts_explicit_open_access(self):
        obj = self.record()
        self.assertEqual(download.validate(obj, '123'), obj['primaryImage'])

    def test_rejects_unverified_cases(self):
        cases = [dict(isPublicDomain=False), dict(rightsAndReproduction='Copyright'),
                 dict(objectEndDate=1956), dict(objectEndDate=0), dict(objectDate=''),
                 dict(objectID=124), dict(primaryImage='https://example.org/image.jpg'),
                 dict(objectBeginDate=True), dict(objectBeginDate=1801)]
        for changes in cases:
            with self.subTest(changes=changes):
                obj = self.record()
                obj.update(changes)
                with self.assertRaises(ValueError):
                    download.validate(obj, '123')


if __name__ == '__main__':
    unittest.main()
