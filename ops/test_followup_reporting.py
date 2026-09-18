import copy
import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('followup_report', Path(__file__).with_name('report-followup-images.py'))
report = importlib.util.module_from_spec(spec)
spec.loader.exec_module(report)


class PublicDeliveryReportTests(unittest.TestCase):
    def setUp(self):
        self.sample = {'image_canaries_total': 1, 'image_canaries_verified': 1,
                       'api_checks_total': 2, 'api_checks_verified': 2,
                       'checks': [{'provider': 'synthetic', 'artwork_id': 'fixture',
                                   'checks': {'image': {'verified': True},
                                              'artists': {'verified': True},
                                              'museums': {'verified': True}}}]}

    def test_healthy_public_delivery(self):
        self.assertEqual(report.public_delivery_status(self.sample)['status'], 'passed')

    def test_museum_failure_is_explicitly_reported(self):
        self.sample['checks'][0]['checks']['museums'] = {'verified': False, 'http_status': 500}
        self.sample['api_checks_verified'] = 1
        result = report.public_delivery_status(self.sample)
        self.assertEqual(result['status'], 'museum_detail_issue')
        self.assertEqual(result['museum_detail_failures'][0]['http_status'], 500)
        self.assertEqual(result['api_checks_verified'], 1)

    def test_failed_image_blocks_success_report(self):
        self.sample['image_canaries_verified'] = 0
        with self.assertRaises(AssertionError):
            report.public_delivery_status(self.sample)

    def test_failed_artist_route_blocks_success_report(self):
        self.sample['checks'][0]['checks']['artists']['verified'] = False
        with self.assertRaises(AssertionError):
            report.public_delivery_status(self.sample)


if __name__ == '__main__':
    unittest.main()
