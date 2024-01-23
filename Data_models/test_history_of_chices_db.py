import time

from unittest import TestCase
from unittest.mock import patch, MagicMock

from config import Config
from Data_models.history_of_choices_db import HistoryOfChoices, Choice


class TestHistoryOfChoices(TestCase):
    def setUp(self):
        Config.db_pass = "..\\DB\\main_db.db"
        self.user_id = 18

    def test_get_mark_for_goods_negative_id(self):
        with self.assertRaises(ValueError):
            HistoryOfChoices.get_marks_for_good(-1, 5)

    def test_get_mark_for_goods_valid(self):
        expected_len = 5
        result = HistoryOfChoices.get_marks_for_good(2, expected_len)
        self.assertEqual(expected_len, len(result))
