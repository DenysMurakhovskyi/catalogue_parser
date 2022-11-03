from unittest import TestCase

from application.selenium_connector.page_getter import PageGetter


class SeveralPagesParsing(TestCase):

    def test_several_pages_parsing(self):
        res = PageGetter.get_pages(1, 4)
        self.assertEqual(3, len(res))
