"""Regression checks for the restored public inventory and rich descriptions."""
import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import import_inventory as importer
import site_templates  # Load the shared template module before its extensions.
from detail_templates import description_html


class RestoredInventoryTests(unittest.TestCase):
    def import_row(self, changes=None, maps=None):
        row = {'Stock Number': 'QA123', 'Year': '2026', 'Brand': 'Example',
               'Model': 'Voyager', 'Floorplan': '32A', 'Type': 'Class A',
               'Images': '', 'Price': '100000', 'Condition': 'New',
               'Dealer ID': '2321', 'Item ID': '999',
               'Description': '<p>An RV for your next trip.</p>'}
        row.update(changes or {})
        resources = {'fpmap.json': {}, 'vidmap.json': {}, 'bcmap.json': {},
                     'tools/brochures.json': {'stocks': {}, 'catalog': {}}}
        resources.update(maps or {})
        with tempfile.TemporaryDirectory() as directory:
            feed = Path(directory) / 'private.csv'
            with feed.open('w', newline='') as stream:
                writer = csv.DictWriter(stream, fieldnames=list(row))
                writer.writeheader()
                writer.writerow(row)
            with patch.object(importer, 'read_map', side_effect=resources.__getitem__):
                catalog, details = importer.import_feed(feed, '2026-09-19')
        return catalog['items'][0], details['QA123']

    def test_arrival_and_special_flags_require_explicit_evidence(self):
        unit, _ = self.import_row({'Attributes': ' New Arrival | On Special '})
        self.assertTrue(unit['newArrival'])
        self.assertTrue(unit['deal'])
        unit, _ = self.import_row({'Description': 'Ask about new arrivals and deals.'})
        self.assertFalse(unit['newArrival'])
        self.assertFalse(unit['deal'])

    def test_deal_discount_boundary_and_missing_msrp(self):
        for price, expected in [('58000', True), ('58001', False)]:
            with self.subTest(price=price):
                unit, _ = self.import_row({'Price': price, 'MSRP': '100000'})
                self.assertEqual(unit['deal'], expected)
        unit, _ = self.import_row({'Price': '50000', 'MSRP': ''})
        self.assertFalse(unit['deal'])

    def test_regular_price_is_only_shown_above_actual_sale_price(self):
        unit, detail = self.import_row({'Price': '150000', 'Sale Price': '125000'})
        self.assertEqual(unit['price'], 125000)
        self.assertEqual(unit['regularPrice'], 150000)
        self.assertEqual(detail['regularPrice'], 150000)
        for sale in ['', '150000', '160000']:
            with self.subTest(sale=sale):
                unit, _ = self.import_row({'Price': '150000', 'Sale Price': sale})
                self.assertIsNone(unit['regularPrice'])

    def test_horsepower_needs_explicit_field_or_labeled_engine_power(self):
        for changes, expected in [({'Horsepower': '450', 'Engine Model': 'L9 380 HP'}, 450),
                                  ({'Engine Model': 'Cummins L9 380 HP'}, 380),
                                  ({'Engine Model': 'Cummins 450 horsepower'}, 450),
                                  ({'Engine Model': 'Cummins ISB 6.7L'}, None),
                                  ({'Engine Model': 'Ford V8 7.3L'}, None)]:
            with self.subTest(changes=changes):
                unit, detail = self.import_row(changes)
                self.assertEqual(unit['horsepower'], expected)
                self.assertEqual(detail['horsepower'], expected)

    def test_card_images_are_bounded_but_detail_retains_every_photo(self):
        images = ['https://example.com/2321/i/999/o/1_2321_999_%s.jpg' % i
                  for i in range(1, 10)]
        unit, detail = self.import_row({'Images': '|'.join(images)},
                                       {'fpmap.json': {'QA123': 9}})
        self.assertEqual(unit['photoCount'], 8)
        self.assertEqual(len(detail['photos']), 8)
        self.assertEqual(len(unit['images']), 6)
        self.assertIn('_9.jpg', detail['floorplanImage'])
        self.assertTrue(all('_9.jpg' not in image for image in detail['photos']))
        self.assertTrue(all(image.startswith('https://d17qgzvii7d4wm.cloudfront.net/')
                            for image in unit['images'] + detail['photos']))
        self.assertTrue(all('width=640;quality=70' in image for image in unit['images']))

    def test_new_fields_do_not_expand_private_column_export(self):
        private = {name: 'PRIVATE_SENTINEL_' + str(index) for index, name in enumerate(
            ['Cost', 'Dealer Cost', 'Invoice', 'Profit', 'Margin', 'Internal Notes',
             'Customer Name', 'Customer Email', 'Social Security Number', 'API Key'])}
        unit, detail = self.import_row(private)
        serialized = json.dumps([unit, detail])
        self.assertNotIn('PRIVATE_SENTINEL_', serialized)
        for name in private:
            self.assertNotIn(name, unit)
            self.assertNotIn(name, detail)
        expected_public = {'stock', 'year', 'brand', 'model', 'floorplan', 'type',
            'condition', 'price', 'msrp', 'length', 'sleeps', 'slides', 'city', 'state',
            'phone', 'status', 'image', 'photoCount', 'fuel', 'mileage', 'features',
            'searchText', 'hasFloorplan', 'hasVideo', 'hasBrochure', 'gvwr',
            'dryWeight', 'updated', 'images', 'newArrival', 'deal', 'regularPrice',
            'horsepower', 'engine', 'chassis', 'exterior', 'interior'}
        self.assertEqual(set(unit), expected_public)
        self.assertEqual(set(detail) - expected_public,
            {'description', 'descriptionSections', 'photos', 'floorplanImage',
             'brochure', 'video', 'tour', 'specs', 'dealerListingUrl', 'youtubeSearchUrl'})

    def test_description_preserves_structure_and_escapes_source_text(self):
        source = ('<h2>Equipment</h2><p>Coach <strong>features</strong> &amp; dimensions.</p>'
                  '<ul><li>Solar prep</li><li>Full bath &lt;with window&gt;</li></ul>'
                  '<script>unsafeScript()</script><style>unsafeStyle{}</style>')
        sections = importer.description_sections(source)
        self.assertEqual([block['kind'] for block in sections],
                         ['heading', 'paragraph', 'item', 'item'])
        output = description_html({'descriptionSections': sections})
        self.assertIn('<h3>Equipment</h3>', output)
        self.assertIn('<ul><li>Solar prep</li><li>Full bath &lt;with window&gt;</li></ul>', output)
        self.assertNotIn('unsafeScript', output)
        self.assertNotIn('unsafeStyle', output)
        self.assertNotIn('<with window>', output)

    def test_paragraph_wrapped_list_items_keep_list_semantics(self):
        source = '<ul><li><p>Solar prep</p></li><li><p>Full bath</p></li></ul>'
        sections = importer.description_sections(source)
        self.assertEqual([block['kind'] for block in sections], ['item', 'item'])
        self.assertEqual(description_html({'descriptionSections': sections}),
                         '<ul><li>Solar prep</li><li>Full bath</li></ul>')


if __name__ == '__main__':
    unittest.main()
