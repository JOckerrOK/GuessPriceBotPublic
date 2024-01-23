import sqlite3
import time
from config import Config
from typing import List
from Data_models.goods_db import Good, GoodKeeper


class Choice:
    """
    Класс для формирования сток истории выбора для импорта в базу
    """
    def __init__(self, chose_id=-1, user_id=-1, good_id=-1, subcategory_id=-1, mark=-1, correct_mark=-1, option=0, timestamp=time.time(),
                 **kwargs):
        self.chose_id = chose_id
        self.user_id = user_id
        self.good_id = good_id
        self.mark = mark
        self.correct_mark = correct_mark
        self.subcategory_id = subcategory_id
        self.option = option
        self.timestamp = timestamp

    def __repr__(self):
        return str({"user_id": self.user_id,
                    "good_id": self.good_id,
                    "mark": self.mark,
                    "correct_mark": self.correct_mark,
                    "option": self.option,
                    "timestamp": self.timestamp})


class HistoryOfChoices:
    """
    Класс для управления добавлением/чтением истории выборов цен пользователями
    """
    def __init__(self):
        pass

    @classmethod
    def create_table(cls) -> None:
        """
        Создание таблицы
        :return: None
        """
        with sqlite3.connect(Config.db_pass) as connection:
            connection.row_factory = sqlite3.Row  # Позволяет обращаться по названию столбца к значению
            cursor = connection.cursor()
            cursor.execute(f"""CREATE TABLE IF NOT EXISTS {Config.history_table_name} (
            chose_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            good_id INTEGER,
            mark INTEGER,
            correct_mark INTEGER DEFAULT 0,
            sub_category_id INTEGER,
            option INTEGER DEFAULT 0,
            timestamp INTEGER
            )""")

    @classmethod
    def add_user_choice(cls, user_id: int, good_id: int, mark: int, correct_mark: int, sub_category_id: int, option=0) -> None:
        """
        Добавление строки с пользовательским выбором цен
        :param user_id: ID пользователя
        :param good_id: ID товара
        :param mark: оценка пользователем
        :param correct_mark: верная оценка для товара
        :param sub_category_id: ID подкатегории
        :param option: option параметр
        :return: None
        """
        with sqlite3.connect(Config.db_pass) as connection:
            connection.row_factory = sqlite3.Row
            cursor = connection.cursor()
            timestamp = time.time()
            cursor.execute("""INSERT INTO {history_table_name}
            (user_id,
            good_id,
            mark,
            correct_mark,
            sub_category_id,
            option,
            timestamp)
            VALUES (?,?,?,?,?,?,?)""".format(history_table_name=Config.history_table_name),
                           (user_id, good_id, mark, correct_mark, sub_category_id, option, timestamp))

    @classmethod
    def get_marks_for_good(cls, good_id: int, total_marks_length) -> List[int]:
        """
        Ищет все выборы оценок пользователей для данного товара и возвращает массив с количеством выборов для каждой оценки
        :param good_id: ID товара
        :param total_marks_length: Сколько оценок нужно вернуть (такая будет длинна масива)
        :return: Массив с количеством выборов пользователей для каждой цены
        """
        if good_id < 0:
            raise ValueError(f"good_id is less then zero. good_id: {good_id}")
        with sqlite3.connect(Config.db_pass) as connection:
            connection.row_factory = sqlite3.Row
            cursor = connection.cursor()
            cursor.execute(
                f"""SELECT mark, count(mark) FROM {Config.history_table_name} WHERE good_id=? GROUP BY mark""",
                (good_id,))
            items = cursor.fetchall()
        current_mark = 0
        result = []
        for item in items:
            mark = item["mark"]
            value = item["count(mark)"]
            if mark > current_mark:
                for i in range(current_mark, mark):
                    result.append(0)
                    current_mark += 1
            if mark == current_mark:
                result.append(value)
                current_mark += 1
        if len(result) < total_marks_length:
            for i in range(len(result), total_marks_length):
                result.append(0)
        return result

    @classmethod
    def get_history_by_user_id(cls, user_id: int) -> List[Choice]:
        """
        Поиск истории по user_id
        :param user_id: ID пользователя
        :return: массив объектов Choice
        """
        if user_id < 0:
            raise ValueError(f"User_id is less then zero. user_id: {user_id}")
        with sqlite3.connect(Config.db_pass) as connection:
            connection.row_factory = sqlite3.Row
            cursor = connection.cursor()
            cursor.execute(f"""SELECT * FROM {Config.history_table_name} WHERE user_id=?""", (user_id,))
            results = [Choice(*item) for item in cursor]
            if not results:
                raise ValueError(f"No history for user with id:{user_id}")
            return results


if __name__ == "__main__":
    HistoryOfChoices.create_table()
    print(HistoryOfChoices.get_history_by_user_id(3))
    print(HistoryOfChoices.get_marks_for_good(1, 6))
