import time
from unittest import TestCase
from unittest.mock import patch, MagicMock

import scripts.Parsers
from goods_db import Good, GoodKeeper, InvalidGood
from config import Config


class TestGood(TestCase):
    def setUp(self):
        """
        Выполняется перед КАЖДЫМ тестом
        :return:
        """
        Config.db_pass = '..\\DB\\main_db.db'
        self.empty_good = Good()
        self.test_good = Good(good_id=0,
                              brand="PlayToday",
                              description="Перчатки",
                              standard_price=1899,
                              final_price=1025,
                              image_links_str="https://a.lmcdn.ru/product/M/P/MP002XB01OAZ_18096864_1_v2.jpg, https://a.lmcdn.ru/product/M/P/MP002XB01OAZ_18096865_2_v2.jpg",
                              link="https://www.lamoda.ru/p/mp002xb01oaz/accs-playtoday-perchatki/",
                              category_id=4,
                              sub_category_id=10,
                              shop_id=1,
                              last_update_timestamp=1704898687,
                              active=1,
                              option=0)

    def test_marks_statistic_empty_good(self):
        with self.assertRaises(InvalidGood):
            result = self.empty_good.marks_statistic

    def test_marks_statistic_valid_good(self):
        valid_marks_list_len = 4  #len of marks list
        result = self.test_good.marks_statistic
        self.assertEqual(len(result), valid_marks_list_len)

    def test_prices_list_empty_good(self):
        with self.assertRaises(InvalidGood):
            result = self.empty_good.prices_list

    def test_prices_list_valid_good_only_parse(self):
        self.test_good.prices_str = "1000, 2000, 3000"
        excepted = ['1000', '2000', '3000']  #len of marks list
        result = self.test_good.prices_list
        self.assertEqual(excepted, result)

    def test_prices_list_valid_good_no_call_update(self):
        self.test_good.prices_str = "1000, 2000, 3000"
        with patch('Data_models.categories_db.CategoriesPool.get_sub_category_by_id') as mock:
            pool = mock.return_value
            pool.price_values = "1000, 2000, 3000"
            result = self.test_good.prices_list
            mock.assert_not_called()

    def test_prices_list_empty_str(self):
        self.test_good.prices_str = ""
        with patch('Data_models.categories_db.CategoriesPool.get_sub_category_by_id') as mock:
            pool = mock.return_value
            pool.price_values = "1000, 2000, 3000"
            result = self.test_good.prices_list
            mock.assert_called()

    def test_image_links_empty_good(self):
        with self.assertRaises(InvalidGood):
            result = self.empty_good.image_links

    def test_image_links_valid_good(self):
        valid_images_list_len = 2  #len of marks list
        result = self.test_good.image_links
        self.assertEqual(len(result), valid_images_list_len)

    def test_check_good_timeout_timouted(self):
        self.test_good.refresh_good_from_site = MagicMock(name='refresh_good_from_site')
        self.test_good.check_good_timeout()
        self.test_good.refresh_good_from_site.assert_called()

    def test_check_good_timeout_no_need(self):
        self.test_good.last_update_timestamp = time.time()-60
        self.test_good.refresh_good_from_site = MagicMock(name='refresh_good_from_site')
        self.test_good.check_good_timeout()
        self.test_good.refresh_good_from_site.assert_not_called()

    def test_refresh_good_from_site_correct(self):
        self.test_good.refresh_good_from_site()
        self.assertAlmostEqual(self.test_good.last_update_timestamp, time.time(), delta=60)

    def test_correct_mark_index_correct(self):
        expected = 1
        result = self.test_good.correct_mark_index
        self.assertEqual(expected, result)

    def test_correct_mark_index_empty_sub_category(self):
        with self.assertRaises(InvalidGood):
            result = self.empty_good.prices_list

    def test_insert_in_db_duplicate_update(self):
        self.test_good.insert_in_db()

    def test_insert_or_update_func_update(self):
        self.test_good.update_in_db = MagicMock(name='update_good__in_db')
        self.test_good.insert_or_update_good()
        self.test_good.update_in_db.assert_called()

    def test_insert_or_update_func_insert(self):
        self.test_good.link += "123"
        self.test_good.insert_in_db = MagicMock(name='update_good__in_db')
        self.test_good.insert_or_update_good()
        self.test_good.insert_in_db.assert_called()

    @classmethod
    def tearDownClass(cls):
        """
        Выполняется после всех тестов
        :return:
        """
        GoodKeeper.combine_duplicates("https://www.lamoda.ru/p/mp002xb01oaz/accs-playtoday-perchatki/")


class TestGoodKeeper(TestCase):
    def setUp(self):
        """
        Выполняется перед КАЖДЫМ тестом
        :return:
        """
        Config.db_pass = '..\\DB\\main_db.db'
        self.empty_good = Good()
        self.test_good = Good(good_id=0,
                              brand="PlayToday",
                              description="Перчатки",
                              standard_price=1899,
                              final_price=1025,
                              image_links_str="https://a.lmcdn.ru/product/M/P/MP002XB01OAZ_18096864_1_v2.jpg, https://a.lmcdn.ru/product/M/P/MP002XB01OAZ_18096865_2_v2.jpg",
                              link="https://www.lamoda.ru/p/mp002xb01oaz/accs-playtoday-perchatki/",
                              category_id=4,
                              sub_category_id=10,
                              shop_id=1,
                              last_update_timestamp=1704898687,
                              active=1,
                              option=0)

    def test_get_goods_from_db_by_link_valid(self):
        expected = 0
        good = GoodKeeper.get_goods_from_db_by_link(self.test_good.link)[0]
        result = good.good_id
        self.assertEqual(expected, result)

    def test_get_goods_from_db_by_link_error(self):
        with self.assertRaises(ValueError):
            GoodKeeper.get_goods_from_db_by_link('')

    def test_combine_duplicates(self):
        GoodKeeper.combine_duplicates(self.test_good.link)

    def test_get_good_by_id_valid(self):
        good = GoodKeeper.get_good_by_id(self.test_good.good_id)
        self.assertEqual(self.test_good.good_id,good.good_id)

    def test_get_good_by_id_less_zero_id(self):
        with self.assertRaises(ValueError):
            good = GoodKeeper.get_good_by_id(-1)

    def test_get_good_by_id_not_found(self):
        with self.assertRaises(ValueError):
            good = GoodKeeper.get_good_by_id(568489461)

    def test_get_next_good_by_sub_category_id_less_zero_id(self):
        with self.assertRaises(ValueError):
            good = GoodKeeper.get_next_good_by_sub_category_id(sub_category_id=-1, offset=0)

    def test_get_next_good_by_sub_category_id_valid_in_db(self):
        good = GoodKeeper.get_next_good_by_sub_category_id(sub_category_id=self.test_good.sub_category_id, offset=0)
        self.assertEqual(self.test_good.good_id, good.good_id)

    def test_get_next_good_by_sub_category_id_site_request(self):
        scripts.Parsers.ParserController.add_new_goods = MagicMock(name="parsers_mock")
        good = GoodKeeper.get_next_good_by_sub_category_id(sub_category_id=self.test_good.sub_category_id, offset=56687)
        scripts.Parsers.ParserController.add_new_goods.assert_called()
