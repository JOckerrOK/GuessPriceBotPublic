import sqlite3
from config import Config


class Shop:
    """
    Класс для контроля над используемыми магазинами. Для возможности масштабирования
    """
    def __init__(self, shop_id=-1, name="", shop_address=""):
        self.shop_id = shop_id
        self.name = name
        self.search_address = shop_address

    @classmethod
    def create_table(cls):
        """
        Создание таблицы магазинов
        :return:
        """
        with sqlite3.connect(Config.db_pass) as connection:
            connection.row_factory = sqlite3.Row  # Позволяет обращаться по названию столбца к значению
            cursor = connection.cursor()
            cursor.execute("""CREATE TABLE IF NOT EXISTS shops (
            shop_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            search_address TEXT
            )""")

    @classmethod
    def get_search_address(cls, shop_id=-1, name="") -> str:
        """
        Получение ссылки поиска для магазина по ID или имени магазина
        (должно быть в формате https://www.lamoda.ru/catalogsearch/result/?page=1&q=
        т.е. добавление к строке поискового запроса должно показывать результирующую страницу.)
        :param shop_id: ID магазина (опционально)
        :param name: имя магазина (опционально - одно из двух)
        :return: строка - ссылка
        """
        with sqlite3.connect(Config.db_pass) as connection:
            connection.row_factory = sqlite3.Row  # Позволяет обращаться по названию столбца к значению
            cursor = connection.cursor()
            cursor.execute("""SELECT * FROM shops WHERE shop_id=? OR name=?""",
                           (shop_id, name))
            item = cursor.fetchone()
            try:
                return item['search_address']
            except IndexError:
                return None


if __name__ == "__main__":
    Shop.create_table()
