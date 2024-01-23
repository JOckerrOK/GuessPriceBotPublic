import time

from unittest import TestCase
from unittest.mock import patch, MagicMock

from config import Config
from Data_models.categories_db import CategoriesPool, Category, SubCategory


class TestSubCategory(TestCase):
    def setUp(self):
        Config.db_pass = "..\\DB\\main_db.db"
        self.category_valid = Category(2, 'Одежда')
        self.category_empty = Category(-1, '')
        self.sub_category_valid = SubCategory(1, "Куртки", 2, "5000, 10000, 30000")
        self.sub_category_empty = SubCategory(-1,"", -1, "")

    def test_prices_negative_id(self):
        with self.assertRaises(ValueError):
            prices = self.sub_category_empty.prices

    def test_prices_valid(self):
        expected = ['5000', '10000', '30000']
        result = self.sub_category_valid.prices
        self.assertEqual(expected, result)

    def test_set_prices_negative(self):
        with self.assertRaises(ValueError):
            self.sub_category_empty.set_prices([])

    def test_set_prices_valid(self):
        expected = '2000, 4000, 6000'
        self.sub_category_empty.set_prices(['2000', '4000', '6000'])
        result = self.sub_category_empty.price_values
        self.assertEqual(expected, result)


class TestCategoriesPool(TestCase):
    def setUp(self):
        Config.db_pass = "..\\DB\\main_db.db"
        self.category_valid = Category(2, 'Одежда')
        self.category_empty = Category(-1, '')
        self.sub_category_valid = SubCategory(1, "Куртки", 2, "5000, 10000, 30000")
        self.sub_category_empty = SubCategory(-1, "", -1, "")

    def test_get_main_categories(self):
        categories = CategoriesPool.get_main_categories()
        self.assertTrue(categories[0].id >= 0)
############

    def test_find_category_empty(self):
        with self.assertRaises(ValueError):
            result = CategoriesPool.find_category()

    def test_find_category_not_found_cat(self):
        with self.assertRaises(ValueError):
            result = CategoriesPool.find_category("135")

    def test_find_category_valid(self):
        expected_text = "Одежда"
        result = CategoriesPool.find_category(category_id=2)
        self.assertEqual(expected_text, result.text_value)
###############

    def test_get_sub_categories_empty(self):
        with self.assertRaises(ValueError):
            result = CategoriesPool.get_sub_categories(-1)

    def test_get_sub_categories_not_found(self):
        with self.assertRaises(ValueError):
            result = CategoriesPool.get_sub_categories(568487945)

    def test_get_sub_categories_valid(self):
        expect = 1
        sub_categories = CategoriesPool.get_sub_categories(2)
        result = sub_categories[0].id
        self.assertEqual(expect, result)
##############

    def test_sub_category_by_id_empty(self):
        with self.assertRaises(ValueError):
            result = CategoriesPool.get_sub_category_by_id(-1)

    def test_sub_category_by_id_not_found(self):
        with self.assertRaises(ValueError):
            result = CategoriesPool.get_sub_category_by_id(568487945)

    def test_sub_category_by_id_valid(self):
        expect = "Куртки"
        sub_category = CategoriesPool.get_sub_category_by_id(1)
        result = sub_category.text_value
        self.assertEqual(expect, result)



