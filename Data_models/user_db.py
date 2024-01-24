import sqlite3
import time

from Data_models.user_states_db import UserStates
from Data_models.categories_db import Category, CategoriesPool
from config import Config
from Data_models.goods_db import Good


class User:
    """
    Класс пользователей
    """
    def __init__(self,
                 user_id=-1,
                 telegram_id=-1,
                 state=UserStates.CHOOSE_CAT,
                 category_id=-1,
                 sub_category_id=-1,
                 current_good_id=-1,
                 option=0,
                 current_good=None,
                 first_visit_timestamp=0,
                 last_updated_timestamp=0,
                 last_message_id_with_buttons=0,
                 name="",
                 last_name="",
                 telegram_login="",
                 ):
        self.user_id = user_id  # ID пользователя - назначается автоматически в БД
        self.telegram_id = telegram_id  # telegramm ID - заполняется при первом посещении бота
        self.state = state  # текущее состояние пользователя - требуется для конечного автомата решений
        self.category_id = category_id  # ID выбранной категории
        self.sub_category_id = sub_category_id  # ID выбранной подгатегории
        self.option = option  # Выбранная опция - для одежды пол: мужской(1)/женский(2)
        self.current_good_id = current_good_id  # ID текущего товара, который отображается пользователю
        self.current_good = current_good  # объект текущего товара
        self.first_visit_timestamp = first_visit_timestamp  # временная отметка первого визита пользователя (время регистрации)
        self.last_updated_timestamp = last_updated_timestamp  # время последнего обновления состояния пользователя
        self.last_message_id_with_buttons = last_message_id_with_buttons  # ID последнего сообщения, отображенного пользователю. Пока не используется
        self.name = name
        self.last_name = last_name
        self.telegram_login = telegram_login
        if telegram_id > 0 or user_id > 0:
            self.sync_db_user(telegram_id=telegram_id, user_id=user_id)

    @classmethod
    def create_table(cls) -> None:
        """
        Создание таблицы
        :return: None
        """
        with sqlite3.connect(Config.db_pass) as connection:
            connection.row_factory = sqlite3.Row  # Позволяет обращаться по названию столбца к значению
            cursor = connection.cursor()
            cursor.execute(f"""CREATE TABLE IF NOT EXISTS {Config.user_table_name} (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER,
            state INTEGER,
            category_id INTEGER,
            sub_category_id INTEGER,
            option INTEGER,
            first_visit_timestamp INTEGER,
            last_updated_timestamp INTEGER,
            current_good_id INTEGER,
            last_message_id_with_buttons INTEGER,
            name TEXT,
            last_name TEXT,
            telegram_login TEXT
            
            FOREIGN KEY (category_id) REFERENCES categories (category_id),
            FOREIGN KEY (sub_category_id) REFERENCES sub_categories (sub_category_id),
            FOREIGN KEY (option) REFERENCES options (option_id)
            )""")

    def fill_user(
            self,
            user_id=-1,
            telegram_id=-1,
            state=UserStates.CHOOSE_CAT,
            category_id=-1,
            sub_category_id=-1,
            option=0,
            current_good_id=-1,
            current_good=None,
            first_visit_timestamp=0,
            last_updated_timestamp=0,
            last_message_id_with_buttons=0,
            name="",
            last_name="",
            telegram_login="",
    ) -> None:
        """
        Функция заполнения переменных в объекте

        :param user_id: ID пользователя
        :param telegram_id: ID телеграмм аккаунта
        :param state: текущее состояние
        :param category_id: ID выбранной категории
        :param sub_category_id:  ID  выбранной подкатегории
        :param option: Опциональный параметр - для одежды - пол
        :param current_good_id: ID текущего товара
        :param current_good: Объект текущего товара
        :param first_visit_timestamp: временная отметка первого визита пользователя (время регистрации)
        :param last_updated_timestamp: время последнего обновления состояния пользователя
        :param last_message_id_with_buttons: ID последнего сообщения, отображенного пользователю. Пока не используется
        :param telegram_login: логин в телеграме
        :param last_name: Фамилия в телеграме
        :param name: имя в телеграме
        :return: None
        """
        self.user_id = user_id
        self.telegram_id = telegram_id
        self.state = state
        self.category_id = category_id
        self.sub_category_id = sub_category_id
        self.option = option
        self.current_good_id = current_good_id
        self.current_good = current_good
        self.first_visit_timestamp = first_visit_timestamp
        self.last_updated_timestamp = last_updated_timestamp
        self.last_message_id_with_buttons = last_message_id_with_buttons
        self.name = name
        self.last_name = last_name
        self.telegram_login = telegram_login

    def create_user_in_db(self, cursor: sqlite3.Cursor) -> None:
        """
        Добавление пользователя в базу
        :param cursor:
        :return: None
        """
        if self.first_visit_timestamp == 0:
            self.first_visit_timestamp = time.time()
        self.last_updated_timestamp = time.time()
        cursor.execute(f"""INSERT INTO {Config.user_table_name} 
                            (telegram_id,
                             state, 
                             category_id, 
                             sub_category_id,
                             option, 
                             current_good_id,
                             first_visit_timestamp, 
                             last_updated_timestamp,
                             last_message_id_with_buttons,
                             name,
                             last_name,
                             telegram_login
                             ) 
                            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                             RETURNING *""", (
            self.telegram_id,
            self.state,
            self.category_id,
            self.sub_category_id,
            self.option,
            self.current_good_id,
            self.first_visit_timestamp,
            self.last_updated_timestamp,
            self.last_message_id_with_buttons,
            self.name,
            self.last_name,
            self.telegram_login
        ))
        self.user_id = cursor.fetchone()['user_id']  # заполняем ID пользователя из новосозданной строки

    def update_user_in_db(self) -> None:
        """
        Обновление пользователя в БД
        :return: None
        """
        with sqlite3.connect(Config.db_pass) as connection:
            connection.row_factory = sqlite3.Row
            cursor = connection.cursor()
            self._update_user_in_db(cursor)

    def _update_user_in_db(self, cursor: sqlite3.Cursor):
        """
        Обновление пользователя в БД
        :return: None
        """
        self.last_updated_timestamp = time.time()
        cursor.execute(f"""UPDATE {Config.user_table_name} SET    
                            state=?, 
                            category_id=?, 
                            sub_category_id=?,
                            option=?, 
                            current_good_id=?, 
                            last_updated_timestamp=?,
                            last_message_id_with_buttons=? WHERE user_id=?""", (
            self.state,
            self.category_id,
            self.sub_category_id,
            self.option,
            self.current_good_id,
            self.last_updated_timestamp,
            self.last_message_id_with_buttons,

            self.user_id
        ))

    def sync_db_user(self, telegram_id=-1, user_id=-1) -> None:
        """
        Метод для синхронизации данных о пользователе. Если время его обновления last_updated_timestamp в базе
        старше, чем актуальное (изменилось какое либо поле пользователя) - обновляем данные в БД, в противном случае
        - подтягиваем данные из БД.
        :param telegram_id: ID пользователя в телеграмм (заполнить один параметр на выбор)
        :param user_id: ID пользователя в базе (заполнить один параметр на выбор)
        :return: None
        """
        if telegram_id or user_id:
            with sqlite3.connect(Config.db_pass) as connection:
                connection.row_factory = sqlite3.Row
                cursor = connection.cursor()
                cursor.execute(
                    f"""SELECT * FROM {Config.user_table_name} 
                    WHERE telegram_id=? OR user_id=?""",
                    (telegram_id, user_id))
                user_data = cursor.fetchone()
                if user_data:
                    if user_data["last_updated_timestamp"] > self.last_updated_timestamp:
                        self.fill_user(**user_data)
                        self.last_updated_timestamp = time.time()
                    else:
                        self._update_user_in_db(cursor)
                else:
                    if telegram_id > 0:
                        self.telegram_id = telegram_id
                    self.create_user_in_db(cursor)

    def set_last_message_id_with_buttons(self, message_id):
        """
        Установка значения последнего сообщения с пользователем (обычный сеттер)
        :param message_id: ID сообщения
        :return:  None
        """
        self.last_message_id_with_buttons = message_id

    def set_state(self, value) -> None:
        """
        Установка значения состояния пользователя в объекте (обычный сеттер)
        :param value: значение
        :return:  None
        """
        self.state = value

    def set_category(self, value=0) -> None:
        """
        Установка значения ID выбранной категории в объекте (обычный сеттер) +
        установка состояния - выбор опций
        :param value: значение
        :return:  None
        """
        self.category_id = value
        self.sub_category_id = -1
        self.option = 0
        self.set_state(UserStates.CHOOSE_OPTION)

    def set_option(self, value):
        """
        Установка значения опционального параметра в объекте (обычный сеттер) +
        установка состояния - выбор подкатегории
        :param value: значение
        :return:  None
        """
        self.option = value
        self.sub_category_id = -1
        self.set_state(UserStates.CHOOSE_SUBCAT)

    def set_subcategory(self, value=0):
        """
        Установка значения подкатегории в объекте (обычный сеттер) +
        установка состояния - ожидание выбора предполагаемой цены
        :param value: значение
        :return:  None
        """
        self.sub_category_id = value
        self.set_state(UserStates.WAIT_PRICE_CHOICE)

    def get_offset_of_actual_sub_category(self) -> int:
        """
        Получение текущего смещения для актуальной категории и опции, для данного пользователя - ищем в базе количество выборов,
        совершенных данным пользователем для данной подкатегории и опции. Далее будет использоваться для получения следующего товара.
        :return: смещение
        """
        with sqlite3.connect(Config.db_pass) as connection:
            cursor = connection.cursor()
            cursor.execute(f"""SELECT count(*)  FROM {Config.history_table_name} WHERE user_id=? AND sub_category_id=? AND option=?""",  (self.user_id, self.sub_category_id, self.option))
            item = cursor.fetchone()
            if item:
                return int(item[0])
            else:
                return 0


if __name__ == "__main__":
    user = User()

