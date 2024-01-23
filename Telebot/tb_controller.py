import logging

import telebot
import random

from Data_models.user_db import UserStates, User
from Data_models.categories_db import Category, CategoriesPool, Option
from Data_models.goods_db import GoodKeeper, Good, InvalidGood
from Data_models.history_of_choices_db import HistoryOfChoices, Choice
from telebot import types
from typing import List
from config import Config

COMMAND_SPLIT_SYMBOL = " "


def get_keyboard_by_categories_list(categories: List[Category], command: str) -> types.InlineKeyboardMarkup:
    """
    Получение клавиатуры с категориями/подкатегориями/опциями (заполняется текст и команда)
    :param categories: массив категорий
    :param command: команда, которая будет использоваться для формирования результирующей строки в кнопке callback_data
    :return: объект готовой клавиатуры для сообщения
    """
    keyboard = types.InlineKeyboardMarkup()
    for category in categories:
        key = types.InlineKeyboardButton(text=category.text_value,
                                         callback_data=command + COMMAND_SPLIT_SYMBOL + str(category.id))
        keyboard.add(key)  # добавляем кнопку в клавиатуру
    return keyboard


def get_keyboard_for_good_prices(good: Good, selected_index=-1):
    """
    Получение клавиатуры с ценами
    :param good: объект искомого товара
    :param selected_index: выбранная пользователем кнопка (нужна при обновлении клавиатуры после выбора)
    является триггером для понимания это первичноая клавиатура, или обновление после выбора
    :return: объект готовой клавиатуры для сообщения
    """
    marks_statistics = None
    prices = good.prices_list
    total_prices_len = len(prices) + 1
    keyboard = types.InlineKeyboardMarkup()
    selected_text = "➡️ "
    correct_text = "✅ "
    keys = [{"text": f"Менее {prices[0]}"}]
    for i in range(total_prices_len-2):
        keys.append({"text": f"От {prices[i]} до {prices[i + 1]}"})  # добавляем по одному цены, включая предпоследний
    keys.append({"text": f"Более {prices[total_prices_len-2]}"})  # добавляем последний элемент из списка цен
    if selected_index != -1:
        marks_statistics = good.marks_statistic
        keys[selected_index]["text"] = selected_text + keys[selected_index]["text"]
        keys[good.correct_mark_index]["text"] = correct_text + keys[good.correct_mark_index]["text"]
    for i in range(total_prices_len):
        if selected_index != -1:
            keys[i]["callback_data"] = "no_command"
            marks_count = marks_statistics[i]
            if not marks_count:
                marks_count = str(random.randint(0, 10))
            keys[i]["text"] += f" (оценки: {marks_count})"
        else:
            keys[i]["callback_data"] = "price" + COMMAND_SPLIT_SYMBOL + str(i)
        key = types.InlineKeyboardButton(**keys[i])
        keyboard.add(key)
    return keyboard


class TelegramBot:
    """
    общий класс для работы с телеграмм ботом
    """
    def __init__(self):
        self.bot = telebot.TeleBot(Config.tg_token)
        self.logger = logging.getLogger(__name__)

        @self.bot.message_handler(commands=['start'])
        def get_started(message) -> None:
            """
            Сообщение пользователю при ввобде команды /start
            :param message: сообщение
            :return: None
            """
            self.bot.send_message(message.from_user.id, "Привет, угадаешь ценник вещи?")
            this_user = User(telegram_id=message.from_user.id)
            if this_user.state == UserStates.CHOOSE_CAT:
                choose_category(message, this_user)
            elif this_user.state == UserStates.CHOOSE_SUBCAT:
                self.bot.send_message(message.from_user.id, "Ты еще не выбрал подкатегорию, жду!")
            elif this_user.state == UserStates.WAIT_PRICE_CHOICE:
                self.bot.send_message(message.from_user.id, "Ты еще не угадал цену!, жду!")

        def send_idle_message(user_id) -> None:
            """
            Отправляет сообщение с возможностью продолжить или выбора категории
            :param user_id: какому пользователю
            :return: None
            """
            keyboard = types.InlineKeyboardMarkup()
            refresh_key = types.InlineKeyboardButton(text="Выбор категории",
                                                     callback_data="refresh")
            next_key = types.InlineKeyboardButton(text="Дальше",
                                                  callback_data="next")
            keyboard.add(refresh_key, next_key)
            self.bot.send_message(user_id, "Куда дальше?", reply_markup=keyboard)

        @self.bot.message_handler(commands=['category'])
        def choose_category(message, this_user=None) -> None:
            """
            обработка команды выбора категории. Будет предложен выбор основных категорий
            :param message: сообщение
            :param this_user: объект User текущего пользователя телеграмм
            :return: None
            """
            keyboard = get_keyboard_by_categories_list(CategoriesPool.get_main_categories(), "cat")  # через бд
            self.bot.send_message(message.from_user.id, "Выбери категорию", reply_markup=keyboard)
            if not this_user:
                this_user = User(telegram_id=message.from_user.id)
            this_user.set_state(UserStates.CHOOSE_CAT)
            this_user.update_user_in_db()

        @self.bot.callback_query_handler(func=lambda call: True)
        def key_press_manager(call: types.CallbackQuery) -> None:
            """
            Менеджер нажатий клавиш пользователем на клавиатуре (инлайн)
            работает конечный автомат состояний пользователя.
            :param call: значение вызова
            :return: None
            """
            if call.data == "no_command":
                self.bot.answer_callback_query(call.id,
                                               text="Ты уже знаешь правильную цену этого товара) Можешь либо нажать далее, либо выбрать другую категорию!",
                                               show_alert=True)
                return None
            this_user = User(telegram_id=call.from_user.id)
            log_string = f"Data = {call.data}, user_state: {this_user.state} user_id {call.from_user.id}, name:{call.from_user.first_name}, {call.from_user.last_name}, login: {call.from_user.username}"
            self.logger.info("Button_command accepted from Tg " + log_string)
            print(log_string)
            if this_user.state == UserStates.CHOOSE_CAT:
                choose_option(call, this_user=this_user)
            elif this_user.state == UserStates.CHOOSE_OPTION:
                choose_subcategory(call, this_user=this_user)
            elif this_user.state == UserStates.CHOOSE_SUBCAT:
                choose_price(call, this_user=this_user)
            elif this_user.state == UserStates.WAIT_PRICE_CHOICE:
                price_selected(call, this_user=this_user)
            elif this_user.state == UserStates.IDLE:
                idle(call, this_user=this_user)
            else:
                self.logger.error(f"НЕ обработанное состояние у пользователя id: {this_user.user_id}, state: {this_user.state}")
            self.bot.answer_callback_query(call.id)

        def choose_option(call: types.CallbackQuery, this_user=None) -> None:
            """
            Вызывается при выборе пользователем категории. Обновляется клавиатура для выбора опции
            :param call: значение вызова
            :param this_user: объект User текущего пользователя телеграмм
            :return: None
            """
            command = call.data.split(COMMAND_SPLIT_SYMBOL)
            if command[0] == "cat":
                if not this_user:
                    this_user = User(telegram_id=call.from_user.id)
                this_user.set_category(int(command[1]))
                this_user.update_user_in_db()
                options = CategoriesPool.get_options_list(int(command[1]))
                if not options:
                    call.data = "option" + COMMAND_SPLIT_SYMBOL + "0"
                    choose_subcategory(call, this_user)
                keyboard = get_keyboard_by_categories_list(options, "option")
                print(call.message)
                self.bot.edit_message_text("Какие товары показать?", call.message.chat.id, call.message.id)
                self.bot.edit_message_reply_markup(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    reply_markup=keyboard
                )

        def idle(call: types.CallbackQuery, this_user=None) -> None:
            """
            Вызывается после выбора пользователем конечной цены. Предлагает либо продолжить в данной категории, либо выбрать новую.
            :param call: значение вызова
            :param this_user: объект User текущего пользователя телеграмм
            :return: None
            """
            if call.data == "refresh":
                choose_category(call, this_user)
            elif call.data == "next":
                choose_price(call, this_user)

        # @bot.callback_query_handler(func=lambda call: user.get_state() == UserStates.CHOOSE_CAT)
        def choose_subcategory(call: types.CallbackQuery, this_user=None) -> None:
            """
            Вызывается при выборе пользователем опции. Обновляется клавиатура для выбора подкатегории
            :param call: значение вызова
            :param this_user: объект User текущего пользователя телеграмм
            :return: None
            """
            command = call.data.split(COMMAND_SPLIT_SYMBOL)
            if command[0] == "option":
                if not this_user:
                    this_user = User(telegram_id=call.from_user.id)
                this_user.set_option(int(command[1]))
                this_user.update_user_in_db()
                sub_categories = CategoriesPool.get_sub_categories(main_category_id=this_user.category_id, option=this_user.option)
                keyboard = get_keyboard_by_categories_list(sub_categories, "subcat")
                self.bot.edit_message_reply_markup(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    reply_markup=keyboard
                )

        @self.bot.message_handler(commands=['next'])
        def send_next_good(message, this_user=None) -> None:
            """
            Вызывается для отправки следующего товара пользователю. Генерирует отправку фото и клавиатуры с предложенным диапазном цен.
            :param message: сообщение
            :param this_user: объект User текущего пользователя телеграмм
            :return: None
            """
            good = None
            if not this_user:
                this_user = User(telegram_id=message.from_user.id)
            if this_user.category_id == -1:
                choose_category(message, this_user)
                return
            elif this_user.sub_category_id == -1:
                choose_subcategory(message, this_user)
                return
            current_offset = this_user.get_offset_of_actual_sub_category()
            try:
                good = GoodKeeper.get_next_good_by_sub_category_id(this_user.sub_category_id, current_offset, option=this_user.option)
            except ValueError as error:
                self.logger.error(error)
                self.bot.send_message(message.chat.id, "Пока товаров в этой категории больше нет.")
                choose_category(message, this_user)
            this_user.current_good = good
            this_user.current_good_id = good.good_id
            this_user.set_subcategory(this_user.sub_category_id)
            this_user.update_user_in_db()
            self.bot.send_photo(message.chat.id, good.image_links[0])
            #keyboard = set_prices_keyboard(good.get_prices())
            keyboard = get_keyboard_for_good_prices(good)
            self.bot.send_message(message.chat.id, f"""Производитель: {good.brand}
Описание: {good.description}""", reply_markup=keyboard)

        def choose_price(call: types.CallbackQuery, this_user=None) -> None:
            """
            Вызывается при выборе пользователем подкатегории
            :param call: значение вызова
            :param this_user: объект User текущего пользователя телеграмм
            :return: None
            """
            command = call.data.split(COMMAND_SPLIT_SYMBOL)
            if not this_user:
                this_user = User(telegram_id=call.from_user.id)
            if command[0] == "subcat":
                this_user.sub_category_id = int(command[1])
            elif call.data == "next":
                next = 1
            else:  # если был рандомный вызов - заглушка:
                self.bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id)
                # call.message.edit_message_reply_markup()
                self.bot.send_message(call.message.chat.id, "Спасибо за выбор категории, дальше будет больше!")
                self.bot.answer_callback_query(call.id)
                return None
            self.bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id)
            send_next_good(call.message, this_user)
            self.bot.answer_callback_query(call.id)

        def price_selected(call: types.CallbackQuery, this_user=None):
            """
            Вызывается при выборе пользователем цены товара.
            :param call: значение вызова
            :param this_user: объект User текущего пользователя телеграмм
            :return: None
            """
            if not this_user:
                this_user = User(telegram_id=call.from_user.id)
            command = call.data.split(COMMAND_SPLIT_SYMBOL)
            if command[0] == "price":
                index = int(command[1])
                try:
                    good = GoodKeeper.get_good_by_id(this_user.current_good_id)
                except ValueError as error:
                    self.logger.error(error)
                    self.bot.answer_callback_query(call.id, text="Произошла ошибка товара. Попробуйте, пожалуйста, выбрать категорию заново", show_alert=True)
                    return None
                HistoryOfChoices.add_user_choice(user_id=this_user.user_id, good_id=good.good_id, mark=index, correct_mark=good.correct_mark_index, sub_category_id=good.sub_category_id, option=good.option)
                # index = int(call.data)
                win_text = "А ты молодец\! Правильно\!"
                fail_text = 'Ты был\(а\) близко, попробуй еще\!'
                final_text = ""
                call_keyboard = get_keyboard_for_good_prices(good, index)
                self.bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.id,
                                                   reply_markup=call_keyboard)
                if good.correct_mark_index == index:
                    final_text = win_text
                else:
                    final_text = fail_text

                if good.standard_price and good.final_price:
                    final_text += f"""
Цена: *{good.standard_price}*
*С учетом текущей скидки: {good.final_price}*"""
                else:
                    final_text += f"""
Цена: *{good.standard_price or good.final_price}*"""
                keyboard = types.InlineKeyboardMarkup()
                refresh_key = types.InlineKeyboardButton(text="Ссылка на товар",
                                                         url=good.link)
                keyboard.add(refresh_key)
                self.bot.send_message(call.message.chat.id, final_text, parse_mode='MarkdownV2', reply_markup=keyboard)

                # user.set_wait_price_choice(0)
                this_user.set_state(UserStates.IDLE)
                this_user.update_user_in_db()
                self.bot.answer_callback_query(call.id)

                send_idle_message(call.from_user.id)

        @self.bot.message_handler(content_types=['text'])
        def get_text_message(message) -> None:
            """
            Обработка набранного паользователем текста. Нужна для админки и добавления новых подкатегорий
            :param message: сообщение
            :return: None
            """
            if message.from_user.id == 610700554:
                print(message.chat.id)
                print(message.text)
                command = message.text.split(Config.mass_splitter)
                if len(command) > 1:
                    if command[0] == "get":  # добавить интерфейс запроса распечатки чего либо в чат
                        try:
                            if command[1] == "cat":
                                categories = CategoriesPool.get_main_categories()
                                result_str = ""
                                for cat in categories:
                                    result_str += f"\n{cat}"
                                self.bot.send_message(message.chat.id, result_str)
                            elif command[1] == "sub" or command[1] == "subcat":
                                categories = CategoriesPool.get_sub_categories(int(command[2]))
                                result_str = ""
                                for cat in categories:
                                    result_str += f"\n{cat}"
                                self.bot.send_message(message.chat.id, result_str)
                        except Exception:
                            self.bot.send_message(message.chat.id, "Давай другую команду")

                    category_id = 0
                    try:
                        category_id = int(command[0])
                    except Exception as err:
                        print(err)
                        category = command[0]
                        try:
                            category_id = CategoriesPool.find_category(text_value=category)
                        except ValueError:
                            self.bot.send_message(message.chat.id, text=f"Не найдена категория с названием {category}")
                    if category_id:
                        subcategory_text = command[1]
                        prices = command[2:]
                        add_result = CategoriesPool.add_sub_category(category_id, subcategory_text, prices)
                        if add_result:
                            self.bot.send_message(message.chat.id,
                                                  text=f"Категория успешно добавлена {str(dict(add_result))}")
            print(message)
            if message.text:
                self.bot.send_message(message.chat.id,
                                      "Попробуй выбрать категорию, введя /category, или используй меню")

    def run(self):
        """
        Запустить поллинг телеграмма (получать сообщения ботом)
        :return:
        """
        self.bot.polling(none_stop=True, interval=1)

    def stop(self):
        """
        Остановить работу бота
        :return:
        """
        self.bot.stop_bot()


if __name__ == "__main__":
    TelegramBot().bot.send_message(610700554, f"""*{__name__}*, 
    _italic_""", parse_mode="MarkdownV2")
