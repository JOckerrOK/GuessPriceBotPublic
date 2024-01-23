import sqlite3
from config import Config


class NextSearchPages:
    """
    Класс для хранения адреса следующей страницы поиска по какой либо под категории
    """
    @classmethod
    def create_table(cls):
        """
        Создание таблицы
        :return:
        """
        with sqlite3.connect(Config.db_pass) as connection:
            connection.row_factory = sqlite3.Row  # Позволяет обращаться по названию столбца к значению
            cursor = connection.cursor()
            cursor.execute("""CREATE TABLE IF NOT EXISTS next_shop_pages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sub_category_id INTEGER,
            shop_id INTEGER,
            next_search_page TEXT,
            option INTEGER DEFAULT 0,
            FOREIGN KEY (sub_category_id) REFERENCES sub_categories (sub_category_id)
            FOREIGN KEY (shop_id) REFERENCES shops (shop_id)
            )""")

    @classmethod
    def get_next_search_page(cls, sub_category_id, shop_id, option=0) -> str:
        """
        Получение адреса следующей страницы поиска.
        Если ссылка не найдена - Value Error
        :param sub_category_id: ID подкатегории
        :param shop_id: ID магазина
        :param option: option параметр
        :return: ссылка на следующую страницу поиска
        """
        with sqlite3.connect(Config.db_pass) as connection:
            connection.row_factory = sqlite3.Row  # Позволяет обращаться по названию столбца к значению
            cursor = connection.cursor()
            cursor.execute("""SELECT * FROM next_shop_pages 
            WHERE sub_category_id=? AND shop_id=? AND option=?""",
                           (sub_category_id, shop_id, option))
            item = cursor.fetchone()
            try:
                return item['next_search_page']
            except TypeError:
                raise ValueError(f"No next page founded for category {sub_category_id}, shop: {shop_id}")

    @classmethod
    def insert_next_search_page(cls, sub_category_id, shop_id, address, option=0) -> None:
        """
        Добавление в базу строки со следующей ссылкой
        :param sub_category_id: ID подкатегории
        :param shop_id: ID магазина
        :param address: ссылка
        :param option: option параметр
        :return: None
        """
        with sqlite3.connect(Config.db_pass) as connection:
            connection.row_factory = sqlite3.Row  # Позволяет обращаться по названию столбца к значению
            cursor = connection.cursor()
            cursor.execute("""INSERT INTO next_shop_pages (sub_category_id, shop_id, next_search_page, option) 
            VALUES (?,?,?,?)""", (sub_category_id, shop_id, address, option))

    @classmethod
    def update_next_search_page(cls, sub_category_id, shop_id, address, option=0) -> None:
        """
        Обновление в базе строки со следующей ссылкой
        :param sub_category_id: ID подкатегории
        :param shop_id: ID магазина
        :param address: ссылка
        :param option: option параметр
        :return: None
        """
        with sqlite3.connect(Config.db_pass) as connection:
            connection.row_factory = sqlite3.Row  # Позволяет обращаться по названию столбца к значению
            cursor = connection.cursor()
            cursor.execute("""UPDATE next_shop_pages SET 
            next_search_page=? 
            WHERE sub_category_id=? AND shop_id=? AND option=?""", (address, sub_category_id, shop_id, option))


if __name__ == "__main__":
    NextSearchPages.create_table()
