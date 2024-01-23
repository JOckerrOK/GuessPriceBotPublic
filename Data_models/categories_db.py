import sqlite3
from typing import List
from config import Config
"""
2	Одежда
3	Обувь
4	Аксессуары
"""


class Category:
    """
    Класс главных категорий
    """
    def __init__(self, category_id, text_value):
        self.id = category_id
        self.text_value = text_value

    def __repr__(self):
        return f"id: {self.id}, text: {self.text_value}"


class Option(Category):
    def __init__(self, option_id, text_value):
        super().__init__(option_id, text_value)


class SubCategory(Category):
    """
    Класс подкатегорий. Наследован от главных
    """
    def __init__(self, sub_category_id, text_value, main_category_id, price_values, option=0):
        super().__init__(sub_category_id, text_value)
        self.main_category_id = main_category_id
        self.price_values = price_values
        self.option = option

    @property
    def prices(self) -> List[str]:
        """
        Возвращает массив с возможными ценами для подкатегории
        :return: Массив строк
        """
        if not self.price_values:
            raise ValueError(f"No price values in sub_category:{self.id}")
        return self.price_values.split(Config.mass_splitter)

    def set_prices(self, prices_list: List[str]) -> None:
        """
        Формирует конечную строку с ценами для импорта в базу
        :param prices_list: Массив возможных цен
        :return: None
        """
        if not prices_list:
            raise ValueError("No prices in price list")
        self.price_values = Config.mass_splitter.join(prices_list)

    def __repr__(self):
        return f"id: {self.id}, text: {self.text_value}, main_category_id: {self.main_category_id}, option: {self.option}, price_values:\n{self.price_values}"


class CategoriesPool:
    """
    Класс управления категориями - получение из БД, добавления и т.д.
    """
    def __init__(self):
        self.create_tables()

    @classmethod
    def create_tables(cls):
        """
        Создание таблиц categories и sub_categories в базе
        :return:
        """
        with sqlite3.connect(Config.db_pass) as connection:
            connection.row_factory = sqlite3.Row  # Позволяет обращаться по названию столбца к значению
            cursor = connection.cursor()
            cursor.execute("""CREATE TABLE IF NOT EXISTS categories (
                        category_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        text_value TEXT
                        )""")
            cursor.execute("""CREATE TABLE IF NOT EXISTS sub_categories (
                        sub_category_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        text_value TEXT,
                        main_category_id INTEGER,
                        option TEXT DEFAULT 0,
                        price_values TEXT,
                        FOREIGN KEY (main_category_id) REFERENCES categories (category_id),
                        FOREIGN KEY (option) REFERENCES options (option_id)
                        )""")
            cursor.execute("""CREATE TABLE IF NOT EXISTS options (
                        option_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        text_value TEXT)
                        """)

    @classmethod
    def get_main_categories(cls) -> List[Category]:
        """
        Проверяет наличие записей в таблице sub_categories и возвращает используемые главные категории
        :return: Список главных категорий
        """
        with sqlite3.connect(Config.db_pass) as connection:
            connection.row_factory = sqlite3.Row  # Позволяет обращаться по названию столбца к значению
            cursor = connection.cursor()
            cursor.execute("""SELECT DISTINCT sub_categories.main_category_id as category_id, categories.text_value as text_value 
            FROM sub_categories 
            JOIN categories  
            ON sub_categories.main_category_id=categories.category_id""")
            return [Category(**item) for item in cursor]

    @classmethod
    def find_category(cls, category_id=-1, text_value="") -> Category:
        """
        Поиск главной категории по category_id ИЛИ text_value
        :param category_id: заполнить для поиска по category_id
        :param text_value: заполнить для поиска по text_value
        :return: возвращает объект класса Category/None если не найдена
        """
        if category_id == -1 and text_value == "":
            raise ValueError("No category_id or text_value was requested to find")
        with sqlite3.connect(Config.db_pass) as connection:
            connection.row_factory = sqlite3.Row
            cursor = connection.cursor()
            cursor.execute("""SELECT * FROM categories WHERE category_id=? OR text_value=?""", (category_id, text_value))
            item = cursor.fetchone()
            if item:
                return Category(category_id=item['category_id'], text_value=item['text_value'])
            else:
                raise ValueError(f"No category was found for category_id: {category_id} or text_value: {text_value}")

    @classmethod
    def get_options_list(cls, main_category_id) -> List[Option]:
        """
        Получение списка опций для подкатегорий по ID главной категории. Проверяется таблица sub_categories
        :param main_category_id: main_category_id - главная категория. Обязательна для поиска
        :return:
        """
        if main_category_id < 0:
            raise ValueError("main_category_id less then zero")
        with sqlite3.connect(Config.db_pass) as connection:
            connection.row_factory = sqlite3.Row  # Позволяет обращаться по названию столбца к значению
            cursor = connection.cursor()
            cursor.execute("""SELECT DISTINCT sub_categories.option as option_id, options.text_value 
            FROM sub_categories 
            JOIN options 
            ON sub_categories.option=options.option_id 
            WHERE main_category_id=?""",
                           (main_category_id,))
            result = [Option(**item) for item in cursor]
            if not result:
                raise ValueError(f"No options was found with main_category_id:{main_category_id}")
            return result

    @classmethod
    def get_option(cls, option_id=-1, text_value=""):
        """
        Поиск поля option по ID или тексту
        :param option_id:
        :param text_value:
        :return: ОбЪект класса Option.
        """
        if option_id == -1 and text_value == "":
            raise ValueError("Try to found empty option")
        with sqlite3.connect(Config.db_pass) as connection:
            connection.row_factory = sqlite3.Row  # Позволяет обращаться по названию столбца к значению
            cursor = connection.cursor()
            cursor.execute("""SELECT * FROM options WHERE option_id=? OR text_value=?""", (option_id, text_value))
            result = cursor.fetchone()
            if not result:
                raise ValueError(f"Option id:{option_id} or text: {text_value} not found")
            return Option(**result)

    @classmethod
    def get_sub_categories(cls, main_category_id, option=0) -> list[SubCategory]:
        """
        Получение списка подкатегорий по ID главной категории. Проверяется таблица sub_categories
        :param option: option параметр (к примеру для одежды - пол)
        :param main_category_id: main_category_id - главная категория. Обязательна для поиска
        :return:
        """
        if main_category_id < 0:
            raise ValueError("main_category_id less then zero")
        with sqlite3.connect(Config.db_pass) as connection:
            connection.row_factory = sqlite3.Row  # Позволяет обращаться по названию столбца к значению
            cursor = connection.cursor()
            cursor.execute("""SELECT * FROM sub_categories WHERE main_category_id=? AND option=?""", (main_category_id, option))
            result = [SubCategory(**item) for item in cursor]
            if not result:
                raise ValueError(f"No sub_categories was found with main_category_id:{main_category_id}")
            return result

    @classmethod
    def get_sub_category_by_id(cls, sub_category_id, option=0) -> SubCategory:
        """
        Возвращает подкатегорию по ее ID
        :param option: option параметр
        :param sub_category_id: ID подкатегории
        :return: Экземпляр класса подкатегорий или None, если категория не найдена по ID
        """
        if sub_category_id < 0:
            raise ValueError(f"Sub_category_id less then zero. sub_category_id={sub_category_id}")
        with sqlite3.connect(Config.db_pass) as connection:
            connection.row_factory = sqlite3.Row  # Позволяет обращаться по названию столбца к значению
            cursor = connection.cursor()
            cursor.execute("""SELECT * FROM sub_categories WHERE sub_category_id=? AND option=?""", (sub_category_id, option))
            item = cursor.fetchone()
            if not item:
                raise ValueError(f"No sub_category was found with id:{sub_category_id}")
            else:
                return SubCategory(**item)

    @classmethod
    def add_sub_category(cls, main_category: int, text_value: str, prices_str_list: List[str]):
        """
        Добавялет в базу новую суб категорию товаров
        :param main_category: главная категория
        :param text_value: Текст поиска и название суб категории
        :param prices_str_list: массив строк с ценами на товар ИМЕННО СТРОК
        :return: True - все ОК
        """
        with sqlite3.connect(Config.db_pass) as connection:
            connection.row_factory = sqlite3.Row  # Позволяет обращаться по названию столбца к значению
            cursor = connection.cursor()
            prices_str = Config.mass_splitter.join(prices_str_list)
            cursor.execute("""INSERT INTO sub_categories (text_value, main_category_id, price_values) 
            VALUES (?,?,?) RETURNING *""", (text_value, main_category, prices_str))
            return cursor.fetchone()


if __name__ == "__main__":
    #Config.db_pass = "..\\DB\\main_db.db"
    CategoriesPool()
