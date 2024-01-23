import logging
import sqlite3
import time

from typing import List
from Data_models.categories_db import CategoriesPool, Category
from config import Config


class Good:
    """
    Основной класс товара, используется для взаимодействия между модулями
    """
    def __init__(self, good_id=-1, description="", final_price=0, link="", last_update_timestamp=0,
                 prices_str="", standard_price=0, brand="", image_links_str="", category_id=-1,
                 sub_category_id=-1, shop_id=-1, active=1, option=0):
        self.good_id = good_id  # id товара в базе
        self.brand = brand  # Производитель
        self.description = description  # модель или описание
        self.standard_price = standard_price  # Цена без скидок
        self.final_price = final_price  # Цена со скидками (финальная цена - обязательный параметр)
        self.image_links_str = image_links_str  # строка с массивом ссылок на картинки разделенных через Config.mass_splitter
        self.category_id = category_id  # ID главной категории товара
        self.sub_category_id = sub_category_id  # ID подкатегории товара
        self.link = link  # Ссылка на товар (обязательна)
        self.last_update_timestamp = last_update_timestamp  # Время последнего обновления товара. Обновляется при запрсое товара с сайта
        self.prices_str = prices_str  # массив цен в строке. Разделитель в файле Config.mass_splitter
        self.shop_id = shop_id  # ID онлайн магазина, в котором находится товар
        self.active = active  # active = 0, если у товара нет цены (закончился). Не участвует. Можно запросить повторно через недельку или удалить
        self.option = option  # опциональная переменная, к примеру для одежды будет указывать на пол: Мужская=1, Женская=2,

        self.logger = logging.getLogger(__name__)

    @property
    def marks_statistic(self) -> List[int]:
        """
        Запрашивает актуальную статистику по отметкам других пользователей для данного товара
        :return: Массив строк с количеством выборов каждой отметки в виде:
        ['','1','',3','4']
        """
        self.check_good_id()
        from Data_models.history_of_choices_db import HistoryOfChoices
        return HistoryOfChoices.get_marks_for_good(self.good_id, len(self.prices_list) + 1)

    @property
    def prices_list(self) -> List[str]:
        """
        Возвращает массив строк с ценами подкатегории. Если цен нет - запрашивает в базе в таблице sub_categories
        :return: Массив строк с ценами подкатегории
        """
        if self.sub_category_id == -1:
            raise InvalidGood("No sub_category_id", self)
        if not self.prices_str:
            self.prices_str = CategoriesPool.get_sub_category_by_id(sub_category_id=self.sub_category_id, option=self.option).price_values
        return self.prices_str.split(Config.mass_splitter)

    @property
    def image_links(self) -> List[str]:
        """
        Делит self.image_links_str на раздельные строки со ссылками на изображения
        :return: массив с изображениями товара
        """
        if self.image_links_str == "":
            raise InvalidGood("No images", self)
        return self.image_links_str.split(Config.mass_splitter)

    def set_image_links(self, image_links_list: List) -> None:
        """
        Склеивает массив ссылок на изображения в одну строку для импорта в базу. Записывает в self.image_links_str
        САМ ИМПОРТ ТУТ НЕ ПРОИСХОДИТ
        :param image_links_list: массив ссылок на изображения
        :return: None
        """
        self.image_links_str = Config.mass_splitter.join(image_links_list)

    def set_prices(self, prices_list: List) -> None:
        """
        Склеивает массив цен в одну строку для импорта в базу. Записывает в self.prices_str
        САМ ИМПОРТ ТУТ НЕ ПРОИСХОДИТ
        :param prices_list: массив цен можно в строчном, можно в целочисленном виде
        :return: None
        """
        self.prices_str = Config.mass_splitter.join([str(x) for x in prices_list])

    def check_good_timeout(self) -> None:
        """
        Проверяет время self.last_update_timestamp на актуальность. Если меньше чем time.time() - timeout
        идет на сайт и обновляет данные. После апдейтит в базу
        """
        self.check_good_id()
        if self.last_update_timestamp < time.time()-Config.timeout_for_goods:
            self.refresh_good_from_site()

    def refresh_good_from_site(self) -> None:
        """
        Актуализирует товар, запрашивая повторно его страницу
        :return: None
        """
        from scripts import Parsers
        self.check_good_id()
        Parsers.ParserController.update_good(self)
        self.logger.info(f"Refreshed {self.good_id} from site. Link: {self.link}")

    @property
    def correct_mark_index(self) -> int:
        """
        Вычисляет позицию правильного выбора оценки товара относительно массива цен
        :return:  позиция правильного выбора оценки товара
        """
        self.check_good_id()
        good_price = self.standard_price or self.final_price
        prices = self.prices_list
        for index in range(len(prices)):
            if good_price < int(self.prices_list[index]):
                return index
        return len(prices)

    def check_good_id(self) -> None:
        """
        Проверяет наличие у товара ID.
        Вызывает ошибку InvalidGood если будет использоваться товар с ID = -1
        :return: None
        """
        if self.good_id == -1:
            raise InvalidGood("Empty object used", self)

    def check_good_prices(self) -> None:
        """
        Проверяет наличие у товара обеих цен (стандартная или со скидкой должны быть).
        Вызывает ошибку InvalidGood если будет использоваться товар без цен
        :return: None
        """
        if not self.standard_price and not self.final_price:
            raise InvalidGood(f"No actual price on good", self)

    def insert_or_update_good(self) -> None:
        """
        Добавление либо обновление товара в базе. Используется для исключения дублей.
        :return: None
        """
        try:
            founded_good = GoodKeeper.get_goods_from_db_by_link(self.link)
            if founded_good:
                self.update_in_db()
        except ValueError:
            self.insert_in_db()

    def insert_in_db(self) -> int:
        """
        Добавляет в базу запись с новым товаром
        :return: good_id нового товара.
        """
        with sqlite3.connect(Config.db_pass) as connection:
            connection.row_factory = sqlite3.Row
            cursor = connection.cursor()
            cursor.execute("""INSERT INTO goods (
            description,
            brand,
            standard_price,
            final_price,
            image_links_str,
            link,
            category_id,
            sub_category_id,
            shop_id,
            last_update_timestamp,
            option
             ) VALUES(?,?,?,?,?,?,?,?,?,?,?) RETURNING *""", (
                self.description,
                self.brand,
                self.standard_price,
                self.final_price,
                self.image_links_str,
                self.link,
                self.category_id,
                self.sub_category_id,
                self.shop_id,
                time.time(),
                self.option
            ))
            self.good_id = cursor.fetchone()['good_id']
        return self.good_id

    def update_in_db(self) -> None:
        """
        Делает апдейт товара в базе по текущим значениям полей
        :return: Ничего
        """
        self.check_good_id()
        update_time = time.time()
        with sqlite3.connect(Config.db_pass) as connection:
            connection.row_factory = sqlite3.Row
            cursor = connection.cursor()
            cursor.execute("""UPDATE goods SET 
            description=?,
            brand=?,
            standard_price=?,
            final_price=?,
            image_links_str=?,
            link=?,
            category_id=?,
            sub_category_id=?,
            shop_id=?,
            last_update_timestamp=?,
            option=?
            WHERE good_id=?
            """, (
                self.description,
                self.brand,
                self.standard_price,
                self.final_price,
                self.image_links_str,
                self.link,
                self.category_id,
                self.sub_category_id,
                self.shop_id,
                update_time,
                self.option,
                # WHERE
                self.good_id
            ))
            self.last_update_timestamp = update_time

    def deactivate(self) -> None:
        """
        Устанавливает флаг self.active в 0 и апдейтит товар в базе.
        Используется если у товара не найдены никакие цены (снят с продажи/закончился)
        :return: None
        """
        self.active = 0
        self.check_good_id()
        with sqlite3.connect(Config.db_pass) as connection:
            connection.row_factory = sqlite3.Row
            cursor = connection.cursor()
            cursor.execute("""UPDATE goods SET 
            active=0 WHERE good_id=?
            """, (self.good_id,))

    def __repr__(self):
        return f"id: {self.good_id}, Brand: {self.brand}, model: {self.description}, start_price:{self.standard_price}, final_price:{self.final_price}, prices {self.prices}"

    # def __eq__(self, other):
    #     if self.good_id == other


class GoodKeeper:
    """
    Класс для управлением товарами. Запрос следующего, новых товаров и т.д.
    """
    TIMEOUT_FOR_TIMESTAMP = 60 * 60 * 24  # (сутки) время, которое актуальна цена
    POINTER_BUFFER = 3  # если в массиве остается менее 3х значений - догружаем

    def __init__(self):
        self.goods = [Good]  # массив объектов Good
        self.pointer = 0
        self.category = ""

    @classmethod
    def create_table(cls) -> None:
        """
        Создает таблицу goods в базе
        :return: None
        """
        with sqlite3.connect(Config.db_pass) as connection:
            connection.row_factory = sqlite3.Row
            cursor = connection.cursor()
            cursor.execute("""CREATE TABLE IF NOT EXISTS goods (
                   good_id INTEGER PRIMARY KEY AUTOINCREMENT,
                   description TEXT,
                   brand TEXT,
                   standard_price INTEGER,
                   final_price INTEGER,
                   image_links_str TEXT,
                   link TEXT UNIQ,
                   category_id INTEGER,
                   sub_category_id INTEGER,
                   option INTEGER DEFAULT 0,
                   shop_id INTEGER,
                   last_update_timestamp INTEGER,
                   active INTEGER DEFAULT 1,
                   
                   FOREIGN KEY (category_id) REFERENCES categories (category_id),
                   FOREIGN KEY (sub_category_id) REFERENCES sub_categories (sub_category_id),
                   FOREIGN KEY (shop_id) REFERENCES shops (shop_id)
                   )""")

    @classmethod
    def get_goods_from_db_by_link(cls, link: str) -> List[Good]:
        """
        Поиск товаров по ссылке. Для исключения дублей
        :param link: Ссылка на товар
        :return: массив найденных товаров
        """
        with sqlite3.connect(Config.db_pass) as connection:
            connection.row_factory = sqlite3.Row
            cursor = connection.cursor()
            cursor.execute("""SELECT * FROM goods WHERE link=?""", (link,))
            items = cursor.fetchall()
            if not items:
                raise ValueError(f"No good find in DB with link {link}")
            else:
                return [Good(**item) for item in items]

    @classmethod
    def combine_duplicates(cls, link: str) -> Good:
        """
        Объединение дубликатов. Будет оставлен только самый старший (с минимальным ID).
        Так же правит ID в связанных таблицах history_of_marks и users на минимальный
        :param link:
        :return:
        """
        goods = cls.get_goods_from_db_by_link(link)
        if len(goods) == 1:
            return goods[0]
        target_good = goods[0]
        ids_str = str(goods[1].good_id)
        if len(goods) > 2:
            for good in goods[2:]:
                ids_str += f",{good.good_id}"
        with sqlite3.connect(Config.db_pass) as connection:
            connection.row_factory = sqlite3.Row
            cursor = connection.cursor()
            history_request = """UPDATE history_of_marks SET good_id={id} WHERE good_id IN ({result_str})""".format(id=target_good.good_id, result_str=ids_str)
            cursor.execute(history_request)
            users_request = """UPDATE users SET current_good_id={id} WHERE current_good_id IN ({result_str})""".format(id=target_good.good_id, result_str=ids_str)
            cursor.execute(users_request)
            goods_request = """DELETE FROM goods WHERE good_id IN ({result_str})""".format(result_str=ids_str)
            cursor.execute(goods_request)
        return target_good

    @classmethod
    def get_good_by_id(cls, good_id) -> Good:
        """
        Запрашивает товар в базе по ID
        :param good_id: ID товара
        :return: Объект класса Good с заполненными данными
        """
        if good_id < 0:
            raise ValueError(f"ID товара меньше 0 ({good_id}). Запрос в базу не отправлен")
        with sqlite3.connect(Config.db_pass) as connection:
            connection.row_factory = sqlite3.Row
            cursor = connection.cursor()
            cursor.execute(
                """SELECT goods.*, sub_categories.price_values AS prices_str 
                FROM goods JOIN sub_categories 
                ON sub_categories.sub_category_id = goods.sub_category_id 
                WHERE goods.good_id=?""",
                (good_id,))
            item = cursor.fetchone()
            if not item:
                raise ValueError(f"Товар с ID: {good_id} в базе не найден")
            return Good(**item)

    @classmethod
    def get_next_good_by_sub_category_id(cls, sub_category_id, offset, option=0, inner=0) -> Good:
        """
        Получить следующий товар для пользователя по подкатегории, смещению и option
        :param sub_category_id: ID подкатеории
        :param offset: смещение, относительно всех товаров подкатегории
        :param option: опциональный параметр
        :param inner: внутренний параметр для исключения бесконечного цикла. Всего запросов может быть 3
        :return: Заполненный экземпляр класса Good - товар
        """
        if sub_category_id < 0 or offset < 0:
            raise ValueError(f"Не корректные данные sub_category_id: {sub_category_id}, offset: {offset}")
        if inner > 2:
            raise ValueError(f"Не удалось достать новый товар для подкатегории: {sub_category_id}, смещение:{offset}, option: {option}")
        item = None
        with sqlite3.connect(Config.db_pass) as connection:
            connection.row_factory = sqlite3.Row
            cursor = connection.cursor()
            if option:  # Поиск с указанием option переменной
                cursor.execute("""SELECT goods.*, sub_categories.price_values AS prices_str 
                    FROM goods JOIN sub_categories 
                    ON sub_categories.sub_category_id = goods.sub_category_id
                    WHERE goods.sub_category_id=?
                     and goods.active=1 
                     and goods.option=? 
                     LIMIT 1 OFFSET ?""",
                               (sub_category_id, option, offset))
            else:  # поиск без указания option переменной
                cursor.execute("""SELECT goods.*, sub_categories.price_values AS prices_str 
                                    FROM goods JOIN sub_categories 
                                    ON sub_categories.sub_category_id = goods.sub_category_id
                                    WHERE goods.sub_category_id=?
                                     and goods.active=1 
                                     LIMIT 1 OFFSET ?""",
                               (sub_category_id, offset))

            item = cursor.fetchone()
            good = None
        if not item:
            from scripts.Parsers import ParserController
            good = ParserController.add_new_goods(sub_category_id, option)
        else:
            good = Good(**item)
        if good.image_links_str == "":
            try:
                good.refresh_good_from_site()
            except InvalidGood as error:
                good.deactivate()
                inner += 1
                good = cls.get_next_good_by_sub_category_id(sub_category_id, offset, option, inner)
        return good


class InvalidGood(ValueError):
    """
    Класс ошибки для определения недействительности товара по тем или иным причинам
    """
    def __init__(self, message, good: Good, *args):
        super().__init__(message, *args)
        logger = logging.getLogger(__name__)
        if not good.standard_price and not good.final_price:
            logger.exception(message + f"Good info: {good.good_id}, \
            link: {good.link}, \
            standard_price: {good.standard_price}, \
            final_price: {good.final_price}")


if __name__ == "__main__":
    GoodKeeper.create_table()
    first_good = Good(brand="Grizman",
                      description="Парка",
                      standard_price=20790,
                      final_price=13990,
                      image_links_str="https://a.lmcdn.ru/product/M/P/MP002XM1UE5Z_21304085_1_v1_2x.jpg",
                      category_id=2,
                      sub_category_id=1,
                      link="https://www.lamoda.ru/p/mp002xm1ue5z/clothes-grizman-parka/",
                      shop_id=1,
                      last_update_timestamp=1704898687)
    first_good.insert_or_update_good()
    print(GoodKeeper.get_good_by_id(1))
