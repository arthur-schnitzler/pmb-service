from django.test import TestCase

from browsing.templatetags.pagination_tags import smart_page_range


class SmartPageRangeTestCase(TestCase):
    def test_single_page(self):
        self.assertEqual(smart_page_range(1, 1), [1])

    def test_small_range_no_ellipsis(self):
        self.assertEqual(smart_page_range(3, 5), [1, 2, 3, 4, 5])

    def test_first_page_large_range(self):
        result = smart_page_range(1, 50)
        self.assertEqual(result[0], 1)
        self.assertIn(None, result)
        self.assertEqual(result[-1], 50)
        self.assertNotIn(None, result[:3])

    def test_last_page_large_range(self):
        result = smart_page_range(50, 50)
        self.assertEqual(result[0], 1)
        self.assertIn(None, result)
        self.assertEqual(result[-1], 50)

    def test_middle_page_both_ellipsis(self):
        result = smart_page_range(10, 50)
        self.assertEqual(result[0], 1)
        self.assertEqual(result[-1], 50)
        self.assertIn(None, result)
        self.assertIn(10, result)
        self.assertIn(8, result)
        self.assertIn(12, result)
        self.assertNotIn(7, result)
        self.assertNotIn(13, result)
        none_indices = [i for i, p in enumerate(result) if p is None]
        self.assertEqual(len(none_indices), 2)

    def test_near_start_single_ellipsis(self):
        result = smart_page_range(3, 50)
        self.assertEqual(result[0], 1)
        self.assertEqual(result[-1], 50)
        none_indices = [i for i, p in enumerate(result) if p is None]
        self.assertEqual(len(none_indices), 1)

    def test_near_end_single_ellipsis(self):
        result = smart_page_range(48, 50)
        self.assertEqual(result[0], 1)
        self.assertEqual(result[-1], 50)
        none_indices = [i for i, p in enumerate(result) if p is None]
        self.assertEqual(len(none_indices), 1)

    def test_no_duplicate_pages(self):
        for current in [1, 2, 3, 4, 5, 25, 46, 47, 48, 49, 50]:
            result = smart_page_range(current, 50)
            pages_only = [p for p in result if p is not None]
            self.assertEqual(len(pages_only), len(set(pages_only)))
