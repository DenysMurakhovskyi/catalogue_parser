from unittest import TestCase

import pandas as pd

from application.google_connector import GoogleConnector


class TestGConnector(TestCase):

    def test_get_numeric_code(self):
        sequence = ['SP4309', 'SP_4309', 'SP_4320-100', 'SP-4320-100']
        actual = list(map(GoogleConnector._get_the_numeric_code, sequence))
        self.assertListEqual(['', '4309', '4320-100', ''], actual)
