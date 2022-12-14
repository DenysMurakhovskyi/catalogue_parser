from unittest import TestCase

import pandas as pd

from application.google_connector import GoogleConnector


class TestGConnector(TestCase):

    def setUp(self) -> None:
        self.gc = GoogleConnector()

    def test_get_table_into_df(self):
        actual = self.gc.get_table_into_df()
        self.assertIsNotNone(actual)
