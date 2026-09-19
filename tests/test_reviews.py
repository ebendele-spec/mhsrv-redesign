import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import review_templates as reviews


class ReviewRestorationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stories = reviews.load_stories()
        cls.raw = json.loads((ROOT / 'mhsrv-reviews-all.json').read_text())

    def test_corpus_urls_text_photos_and_stock_are_preserved(self):
        self.assertEqual(len(self.stories), 4571)
        for story, source in zip(self.stories, self.raw):
            self.assertEqual(story['slug'], source[0])
            self.assertEqual(story['title'], source[1])
            self.assertEqual(story['stock'], source[2])
            self.assertEqual(story['text'], source[3].strip())
            self.assertEqual(story['image'], source[4])
            self.assertNotIn('rating', story)
        self.assertEqual(sum(bool(s['image']) for s in self.stories), 3019)

    def test_metadata_comes_from_identified_customer_story(self):
        story = next(s for s in self.stories if s['stock'] == '14931')
        self.assertEqual(story['brand'], 'Entegra Coach')
        self.assertEqual(story['model'], 'Anthem')
        self.assertEqual(story['year'], 2017)
        self.assertEqual(story['type'], 'Diesel Pusher')
        self.assertEqual(story['buyer'], 'McFarland’s')
        self.assertEqual(story['location'], 'Allen, Texas')

    def test_source_brand_names_and_typographical_aliases_remain_filterable(self):
        for title, brand in [('2009 American Tradition', 'American Coach'),
                             ('2016 K-Z Spree', 'KZ'),
                             ('2018 Forestravel Realm', 'Foretravel'),
                             ('2017 Coahmen Pursuit', 'Coachmen'),
                             ('2000 Prevost', 'Prevost')]:
            story = next(s for s in self.stories if s['title'].startswith(title))
            self.assertEqual(story['brand'], brand)

    def test_blank_dates_are_not_presented_as_publication_dates(self):
        undated = next(s for s in self.stories if not s['date'])
        body = reviews.review_detail(undated, None, None, {})
        self.assertNotIn('Published', body)
        self.assertNotIn('★★★★★', body)

    def test_detail_restores_context_and_adjacent_story_links(self):
        story = self.stories[1]
        body = reviews.review_detail(story, self.stories[0], self.stories[2], {})
        self.assertIn('rel="prev"', body)
        self.assertIn('rel="next"', body)
        self.assertIn(self.stories[0]['slug'] + '.html', body)
        self.assertIn(self.stories[2]['slug'] + '.html', body)
        self.assertIn('Stock #' + story['stock'], body)
        self.assertIn('../reviews.html?brand=', body)
        self.assertIn('../index.html?brand=', body)
        self.assertNotIn('ratingValue', body)

    def test_hub_has_static_36_stories_and_filters(self):
        body = reviews.review_hub(self.stories, {})
        self.assertEqual(body.count('<article class="review-card">'), 36)
        self.assertIn('id="reviewBrand"', body)
        self.assertIn('id="reviewType"', body)
        self.assertIn('data-reviews-v2', body)
        self.assertIn('4,535 remaining', body)
        self.assertIn('review-pages/1.html', body)

    def test_untrusted_source_text_is_escaped(self):
        story = dict(self.stories[0], title='<script>alert(1)</script>', text='<img src=x onerror=alert(1)>')
        body = reviews.review_detail(story, None, None, {})
        self.assertIn('&lt;script&gt;', body)
        self.assertNotIn('<img src=x', body)


if __name__ == '__main__':
    unittest.main()
