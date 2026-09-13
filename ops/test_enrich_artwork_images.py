"""Offline checks for museum rights gates and the derivative byte limit."""
import importlib.util
import io
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from PIL import Image

spec = importlib.util.spec_from_file_location('enrichment', Path(__file__).with_name('enrich-artwork-images.py'))
enrichment = importlib.util.module_from_spec(spec)
spec.loader.exec_module(enrichment)


class Metadata:
    def __init__(self, value):
        self.value = value

    def metadata(self, url):
        return self.value


class ImageEnrichmentTests(unittest.TestCase):
    def test_upload_consumer_cannot_fall_back_to_source_requests(self):
        with TemporaryDirectory(prefix='artline-upload-cache-', dir='/tmp') as directory:
            with patch.object(enrichment.storage, 'Client'), patch.object(enrichment, 'AttachmentDB') as databases, \
                 patch.object(enrichment, 'nga_index') as index, patch.object(enrichment, 'image_record') as source, \
                 patch.object(enrichment, 'event') as event:
                enrichment.worker('nga', [{'provider':'nga','artwork_id':'missing','external_id':'123'}],
                    SimpleNamespace(run=Path(directory),upload_prepared_only=True), None)
                index.assert_not_called()
                source.assert_not_called()
                databases.return_value.apply.assert_not_called()
                self.assertEqual(event.call_args.args[1]['outcome'], 'failed')
                self.assertIn('source download is disabled', event.call_args.args[1]['error'])

    def test_prepare_only_never_contacts_cloud_storage_or_attaches_to_databases(self):
        with TemporaryDirectory(prefix='artline-image-prep-', dir='/tmp') as directory:
            root = Path(directory)
            run = root / 'run'
            source = io.BytesIO()
            Image.new('RGB', (20, 20), 'white').save(source, 'JPEG')
            data = source.getvalue()
            receipt = {'path':'/assets/example.jpg','sha256':enrichment.sha(data),'bytes':len(data)}
            enrichment.save_new(root / 'apps/web/public/assets/example.jpg', data)
            enrichment.save_new(run / 'images/smk/example.json', receipt)
            candidate = {'provider':'smk','artwork_id':'example','external_id':'KMS-example'}
            with patch.object(enrichment, 'ROOT', root), patch.object(enrichment.storage, 'Client') as storage, \
                 patch.object(enrichment, 'AttachmentDB') as databases, patch.object(enrichment, 'event') as event:
                enrichment.worker('smk', [candidate], SimpleNamespace(run=run,prepare_only=True), None)
                storage.assert_not_called()
                databases.return_value.apply.assert_not_called()
                self.assertEqual(event.call_args.args[1]['outcome'], 'prepared')

    def test_lost_database_connection_retries_same_receipt(self):
        connections = [Mock(closed=False), Mock(closed=False)]
        receipt = {'media_id': 'unchanged-receipt-id'}
        with patch.object(enrichment.psycopg, 'connect', side_effect=connections) as connect, \
             patch.object(enrichment, 'attach', side_effect=[enrichment.psycopg.OperationalError('connection lost'), 'attached']) as attach, \
             patch.object(enrichment.time, 'sleep'):
            target = enrichment.AttachmentDB('test-connection', 'cloud')
            self.assertEqual(target.apply(receipt), 'attached')
            self.assertEqual(connect.call_count, 2)
            self.assertTrue(all(call.args[1] is receipt for call in attach.call_args_list))
            connections[0].close.assert_called_once()
            target.close()

    def test_database_row_lock_timeout_is_not_retried(self):
        with patch.object(enrichment.psycopg, 'connect', return_value=Mock(closed=False)) as connect, \
             patch.object(enrichment, 'attach', side_effect=enrichment.psycopg.errors.LockNotAvailable('row locked')), \
             patch.object(enrichment.time, 'sleep') as sleep:
            target = enrichment.AttachmentDB('test-connection', 'local')
            with self.assertRaises(enrichment.psycopg.errors.LockNotAvailable):
                target.apply({'media_id': 'unchanged-receipt-id'})
            connect.assert_called_once()
            sleep.assert_not_called()
            target.close()

    def candidate(self, provider):
        return {'provider': provider, 'external_id': '123'}

    def test_met_requires_explicit_public_domain_without_conflicting_rights(self):
        raw = {'objectID': 123, 'isPublicDomain': True, 'rightsAndReproduction': '',
               'primaryImageSmall': 'https://images.metmuseum.org/example.jpg'}
        self.assertEqual(enrichment.image_record(self.candidate('met'), Metadata(raw), {}, {})['rights_status'], 'cc0')
        for override in ({'isPublicDomain': False}, {'isPublicDomain': None},
                         {'rightsAndReproduction': 'Artist copyright'}, {'primaryImageSmall': ''}):
            self.assertIsNone(enrichment.image_record(self.candidate('met'), Metadata({**raw, **override}), {}, {}))
        with self.assertRaisesRegex(ValueError, 'identity mismatch'):
            enrichment.image_record(self.candidate('met'), Metadata({**raw, 'objectID': 124}), {}, {})

    def test_cleveland_metadata_license_alone_does_not_authorize_image(self):
        raw = {'id': 123, 'share_license_status': 'CC0', 'copyright': '',
               'images': {'web': {'url': 'https://openaccess-cdn.clevelandart.org/example.jpg'}}}
        self.assertIsNotNone(enrichment.image_record(self.candidate('cleveland'), Metadata({'data': raw}), {}, {}))
        for override in ({'share_license_status': 'Copyright'}, {'copyright': 'Artist copyright'}, {'images': {}}):
            self.assertIsNone(enrichment.image_record(self.candidate('cleveland'), Metadata({'data': {**raw, **override}}), {}, {}))

    def test_chicago_rejects_conflicting_notice(self):
        raw = {'id': 123, 'is_public_domain': True, 'copyright_notice': '', 'image_id': 'example'}
        self.assertIsNotNone(enrichment.image_record(self.candidate('chicago'), None, {}, {'123': raw}))
        self.assertIsNone(enrichment.image_record(self.candidate('chicago'), None, {}, {'123': {**raw, 'copyright_notice': 'Copyright'}}))

    def test_nga_requires_selected_open_primary_image_and_matching_iiif_identity(self):
        self.assertIsNone(enrichment.image_record(self.candidate('nga'), None, {}, {}))
        raw = {'uuid': 'example', 'iiifurl': 'https://api.nga.gov/iiif/example'}
        self.assertEqual(enrichment.image_record(self.candidate('nga'), None, {'123': raw}, {})['rights_status'], 'public_domain')
        with self.assertRaisesRegex(ValueError, 'identity mismatch'):
            enrichment.image_record(self.candidate('nga'), None, {'123': {**raw, 'uuid': 'different'}}, {})

    def test_smk_current_primary_url_and_explicit_public_domain_mark(self):
        raw = {'object_number': '123', 'public_domain': True, 'has_image': True,
               'rights': enrichment.POLICIES['smk'],
               'image_native': 'https://api.smk.dk/api/v1/thumbnail/12345678-1234-1234-1234-123456789abc.jpg'}
        self.assertEqual(enrichment.image_record(self.candidate('smk'), Metadata({'items': [raw]}), {}, {})['source_image_url'], raw['image_native'])
        for override in ({'public_domain': False}, {'rights': ''}, {'image_native': 'https://unrelated.example/image.jpg'}, {'object_number': '124'}):
            self.assertIsNone(enrichment.image_record(self.candidate('smk'), Metadata({'items': [{**raw, **override}]}), {}, {}))

    def test_fetch_rejects_unapproved_hosts_before_network(self):
        fetcher = enrichment.Fetcher(Path('/tmp/unused-artline-offline-test'))
        for url in ('http://api.smk.dk/image', 'https://api.smk.dk.evil.example/image', 'file:///etc/passwd'):
            with self.assertRaisesRegex(ValueError, 'Unapproved source host'):
                fetcher.get(url)

    def test_rijks_image_rights_and_exact_identity_are_separate_from_metadata(self):
        document = '''<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
          xmlns:ore="http://www.openarchives.org/ore/terms/" xmlns:edm="http://www.europeana.eu/schemas/edm/"
          xmlns:dc="http://purl.org/dc/elements/1.1/">
          <ore:Aggregation><edm:aggregatedCHO rdf:resource="https://id.rijksmuseum.nl/123"/>
            <edm:rights rdf:resource="http://creativecommons.org/publicdomain/mark/1.0/"/>
            <edm:isShownBy rdf:resource="https://iiif.micr.io/example/full/max/0/default.jpg"/>
          </ore:Aggregation>
          <edm:ProvidedCHO rdf:about="https://id.rijksmuseum.nl/123"><dc:identifier>SK-A-1</dc:identifier></edm:ProvidedCHO>
          <edm:WebResource rdf:about="https://iiif.micr.io/example/full/max/0/default.jpg"/>
          <rdf:Description rdf:about="https://data.rijksmuseum.nl/123"><dc:rights>CC0 metadata</dc:rights></rdf:Description>
        </rdf:RDF>'''
        self.assertIsNotNone(enrichment.rijks_edm(document, '123', 'SK-A-1'))
        self.assertIsNone(enrichment.rijks_edm(document, '123', 'SK-A-10'))
        self.assertIsNone(enrichment.rijks_edm(document.replace('http://creativecommons.org/publicdomain/mark/1.0/', 'http://rightsstatements.org/vocab/InC/1.0/'), '123'))
        with self.assertRaisesRegex(ValueError, 'identity mismatch'):
            enrichment.rijks_edm(document, '124')

    def test_complex_image_is_bounded_decodable_and_keeps_full_frame(self):
        original = Image.effect_noise((1800, 1200), 80).convert('RGB')
        source = io.BytesIO()
        original.save(source, 'PNG')
        data, width, height, quality = enrichment.compress(source.getvalue())
        self.assertLessEqual(len(data), 100000)
        self.assertGreater(width, 0)
        self.assertAlmostEqual(width / height, 1.5, places=2)
        with Image.open(io.BytesIO(data)) as output:
            self.assertEqual(output.format, 'JPEG')
            self.assertEqual(output.size, (width, height))
            output.verify()


if __name__ == '__main__':
    unittest.main()
