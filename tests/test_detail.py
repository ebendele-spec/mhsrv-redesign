"""Customer-facing detail regressions, using synthetic inventory and no network."""
from html.parser import HTMLParser
import json
from pathlib import Path
import sys
import unittest
from urllib.parse import parse_qs, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
# Match the builder's entry point; site_templates wires its detail renderer.
import site_templates
import detail_templates as detail


class Element:
    def __init__(self, tag, attrs, parents):
        self.tag, self.attrs, self.parents, self.text = tag, dict(attrs), list(parents), ''


class Document(HTMLParser):
    voids = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}

    def __init__(self, markup):
        super().__init__()
        self.elements, self.stack = [], []
        self.feed(markup)

    def handle_starttag(self, tag, attrs):
        node = Element(tag, attrs, self.stack)
        self.elements.append(node)
        if tag not in self.voids:
            self.stack.append(node)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                break

    def handle_data(self, data):
        for node in self.stack:
            node.text += data

    def select(self, tag=None, within=None, **attrs):
        return [node for node in self.elements
                if (tag is None or node.tag == tag)
                and (within is None or within in node.parents)
                and all(key in node.attrs and (value is None or node.attrs[key] == value) for key, value in attrs.items())]

    def one(self, tag=None, **attrs):
        found = self.select(tag, **attrs)
        if len(found) != 1:
            raise AssertionError(f'Expected one {tag} {attrs}, found {len(found)}')
        return found[0]

    def product(self):
        schema = json.loads(self.one('script', type='application/ld+json').text)
        return next(item for item in schema if item.get('@type') == 'Product')


def rv(**changes):
    photos = [f'https://images.example.invalid/rv/photo-{i}.jpg;width=1200;quality=75' for i in range(45)]
    unit = dict(stock='TEST001', year=2026, brand='Example Coach', model='Trail Series', floorplan='34B',
                type='classc', condition='new', status='listed', state='TX', city='Alvarado',
                phone='8003356054', price=120000, msrp=150000, regularPrice=130000,
                updated='2026-09-17', length=34, sleeps=6, slides=0, fuel='Gas',
                image=photos[0], photos=photos, photoCount=len(photos), features=['Bunk beds'],
                specs={'Length (ft)': '34', 'Sleeps': '6', 'Slideouts': '0', 'Exterior': 'Blue & silver'},
                description='Listed vehicle description.',
                descriptionSections=[{'kind': 'heading', 'text': 'Installed features'},
                                     {'kind': 'item', 'text': 'Bunk beds & storage'},
                                     {'kind': 'paragraph', 'text': 'Confirm installed equipment.'}],
                floorplanImage='https://images.example.invalid/floorplan.png',
                dealerListingUrl='https://dealer.example.invalid/rv-123',
                brochure={'label': '2025 Trail Series factory brochure', 'sameYear': False, 'year': 2025,
                          'url': 'https://documents.example.invalid/2025-trail.pdf'},
                video='TESTVIDEO01', tour='https://tours.example.invalid/trail', newArrival=True)
    unit.update(changes)
    return unit


class DetailTemplatesTest(unittest.TestCase):
    config = {'mode': 'production', 'origin': 'https://mhsrv.example.invalid',
              'leadEmail': 'elisha@mhsrv.com', 'inventoryDate': '2026-09-17'}

    def render(self, unit=None, config=None):
        unit = unit or rv()
        return Document(detail.detail(unit, [unit], config or self.config))

    def test_all_listing_photos_and_thumbnails_are_available_without_a_preview_cap(self):
        unit = rv()
        page = self.render(unit)
        track = page.one(id='inlinePhotoTrack')
        photos = page.select('img', within=track)
        self.assertEqual([photo.attrs['src'] for photo in photos], unit['photos'])
        self.assertEqual([button.attrs['data-photo'] for button in page.select('button', within=track)], [str(i) for i in range(45)])
        self.assertEqual([button.attrs['data-inline-photo'] for button in page.select('button', **{'data-inline-photo': None})], [str(i) for i in range(45)])
        self.assertEqual(photos[0].attrs['fetchpriority'], 'high')
        self.assertTrue(all(photo.attrs.get('loading') == 'lazy' for photo in photos[1:]))
        self.assertEqual(page.one(id='inlinePhotoCount').text, '1 / 45')
        self.assertTrue(all(photo.attrs.get('alt') for photo in photos))

    def test_documents_distinguish_reference_year_and_keep_source_and_missing_document_paths(self):
        unit = rv()
        page = self.render(unit)
        brochure = page.one('button', **{'data-brochure': None})
        self.assertIn(unit['brochure']['label'], brochure.text)
        self.assertIn('Reference brochure', brochure.text)
        self.assertNotIn('Matching model year', brochure.text)
        self.assertTrue(page.select('a', href=unit['brochure']['url']))
        self.assertEqual(page.one('img', **{'data-document-image': None}).attrs['src'], unit['floorplanImage'])
        self.assertTrue(page.select('a', href=unit['dealerListingUrl'] + '#section-detail-floorplan-anchor'))
        matching = self.render(rv(brochure=dict(unit['brochure'], sameYear=True, year=2026, label='2026 Trail Series factory brochure')))
        self.assertIn('Matching model year', matching.one('button', **{'data-brochure': None}).text)
        missing = self.render(rv(brochure=None, floorplanImage=None, video=None, tour=None))
        self.assertFalse(missing.select(**{'data-brochure': None}))
        self.assertFalse(missing.select(**{'data-floorplan': None}))
        self.assertTrue(missing.select('button', **{'data-lead': 'Request the factory brochure', 'data-stock': unit['stock']}))
        self.assertTrue(missing.select('button', **{'data-lead': 'Request the exact floorplan', 'data-stock': unit['stock']}))
        self.assertTrue(missing.select('a', href=unit['dealerListingUrl']))

    def test_archives_preserve_source_date_and_never_offer_unavailable_inventory(self):
        page = self.render(rv(status='unavailable', updated='2026-07-18', unavailableSince='2026-09-17'))
        availability = page.one(**{'class': 'availability'}).text
        self.assertIn('No longer in the feed as of 2026-09-17', availability)
        self.assertIn('Last listing details: 2026-07-18', availability)
        self.assertEqual(page.one('p', **{'class': 'price-label'}).text, 'Last listed price')
        self.assertNotIn('offers', page.product())
        self.assertFalse(page.select(**{'class': 'arrival-detail'}))
        self.assertTrue(page.select('button', **{'data-lead': 'Find a similar available RV'}))
        fallback = self.render(rv(status='unavailable', updated='2026-07-18'))
        self.assertIn('No longer in the feed as of 2026-09-17', fallback.one(**{'class': 'availability'}).text)

    def test_offers_follow_status_and_public_price_without_inventing_missing_prices(self):
        for status, availability in [('listed', 'InStock'), ('onorder', 'PreOrder'), ('coming', 'PreOrder')]:
            with self.subTest(status=status):
                offer = self.render(rv(status=status)).product()['offers']
                self.assertEqual(offer['price'], 120000)
                self.assertEqual(offer['availability'], 'https://schema.org/' + availability)
        for unit, config in [(rv(status='pending'), self.config), (rv(price=None), self.config),
                             (rv(), dict(self.config, mode='preview'))]:
            self.assertNotIn('offers', self.render(unit, config).product())
        missing = self.render(rv(price=None, msrp=None, regularPrice=None, photos=[], image=None, photoCount=0))
        self.assertEqual(missing.one(**{'class': 'listed-price'}).text, 'Request price')
        self.assertFalse(missing.select(id='calcDown'))
        self.assertFalse(missing.select(id='inlinePhotoTrack'))
        self.assertTrue(missing.select(**{'class': 'photo-placeholder detail-empty-photo'}))

    def test_similar_units_limit_and_prioritize_condition_model_and_available_inventory(self):
        base = rv()
        pool = [base, rv(stock='ARCHIVED', status='unavailable'), rv(stock='PENDING', status='pending'),
                rv(stock='OTHER-TYPE', type='diesel'), rv(stock='USED-MATCH', condition='used'),
                rv(stock='OTHER-MODEL', model='Different'),
                rv(stock='EXACT-FAR', price=180000, length=40),
                rv(stock='EXACT-NEAR', price=121000, length=34)]
        pool += [rv(stock=f'OTHER-{i}', model=f'Other {i}', price=130000 + i * 1000) for i in range(7)]
        selected = detail.similar_units(base, list(reversed(pool)))
        self.assertEqual(len(selected), 6)
        self.assertEqual([unit['stock'] for unit in selected[:2]], ['EXACT-NEAR', 'EXACT-FAR'])
        self.assertTrue(all(unit['condition'] == 'new' for unit in selected))
        self.assertTrue(all(unit['status'] == 'listed' and unit['type'] == base['type'] and unit['stock'] != base['stock'] for unit in selected))

    def test_source_prices_and_location_specific_fee_information_remain_distinct(self):
        page = self.render()
        self.assertEqual(page.one(**{'class': 'listed-price'}).text, '$120,000')
        self.assertIn('$150,000', page.one(**{'class': 'msrp'}).text)
        self.assertIn('$30,000 below MSRP', page.one(**{'class': 'save-amount'}).text)
        self.assertIn('$130,000', page.one(**{'class': 'regular-price'}).text)
        fees = page.one('details', **{'class': 'fee-panel'})
        breakdown = dict(zip([node.text for node in page.select('dt', within=fees)], [node.text for node in page.select('dd', within=fees)]))
        self.assertEqual(breakdown['Listed price'], '$120,000')
        self.assertEqual(breakdown['Freight'], '$0')
        self.assertEqual(breakdown['Vehicle preparation'], '$0')
        self.assertEqual(breakdown['Documentation'], '$225')
        self.assertEqual(breakdown['Taxes, title & registration'], 'Based on registration')
        non_texas = self.render(rv(state='CA', city='Palm Desert'))
        self.assertIn('Confirm with location', non_texas.one('details', **{'class': 'fee-panel'}).text)
        self.assertNotIn('$225', non_texas.one('details', **{'class': 'fee-panel'}).text)
        no_discount = self.render(rv(msrp=110000, regularPrice=115000))
        self.assertFalse(no_discount.select(**{'class': 'save-amount'}))
        self.assertFalse(no_discount.select(**{'class': 'regular-price'}))

    def test_stock_context_survives_lead_buttons_sms_documents_and_finance_links(self):
        unit = rv(stock='TEST & 123', floorplan='34 B & C')
        page = self.render(unit)
        main = page.one(id='main')
        mobile = page.one(**{'class': 'detail-mobile-cta'})
        lead_buttons = page.select('button', within=main, **{'data-lead': None}) + page.select('button', within=mobile, **{'data-lead': None})
        self.assertGreater(len(lead_buttons), 5)
        self.assertTrue(all(button.attrs.get('data-stock') == unit['stock'] for button in lead_buttons))
        sms = [node for node in page.select('a', within=main) + page.select('a', within=mobile) if node.attrs.get('href', '').startswith('sms:')]
        self.assertGreaterEqual(len(sms), 3)
        for link in sms:
            body = parse_qs(urlsplit(link.attrs['href']).query)['body'][0]
            self.assertIn('#' + unit['stock'], body)
            self.assertIn(unit['floorplan'], body)
        document_sms = next(node for node in sms if 'documents' in node.text)
        self.assertIn('brochure and installed options', parse_qs(urlsplit(document_sms.attrs['href']).query)['body'][0])
        self.assertEqual(parse_qs(urlsplit(page.one(id='detailFinanceLink').attrs['href']).query)['stock'], [unit['stock']])
        self.assertTrue(page.select('a', within=main, href='tel:' + unit['phone']))

    def test_rich_description_is_collapsible_and_escaped_and_video_is_clearly_labeled(self):
        page = self.render(rv(descriptionSections=[{'kind': 'heading', 'text': 'Features & details'},
                                                   {'kind': 'item', 'text': '<script>untrusted()</script>'}]))
        description = page.one(**{'class': 'description-text rich-description'})
        self.assertTrue(any(parent.tag == 'details' and 'open' in parent.attrs for parent in description.parents))
        self.assertTrue(page.select('h3', within=description))
        self.assertEqual(page.one('li', within=description).text, '<script>untrusted()</script>')
        self.assertFalse(page.select('script', within=description))
        self.assertTrue(page.select('button', **{'data-inline-video': 'TESTVIDEO01'}))
        self.assertIn('Model year, floorplan and installed equipment may differ', page.one(id='video').text)
        self.assertTrue(page.select('button', **{'data-tour': None}))


if __name__ == '__main__':
    unittest.main()
