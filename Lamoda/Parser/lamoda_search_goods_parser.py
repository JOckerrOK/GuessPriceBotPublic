import re
import logging

from bs4 import BeautifulSoup
from Lamoda.Locators.lamoda_search_good_locators import LamodaSearchGoodLocators


# class NotFoundElement(ValueError):
#     def __init__(self, locator, soup_with_error):
#         #super().__init__(f'Locator: {locator} not found in soup: {soup_with_error}')
#         print("LOG-------------------")
#         print(f'Locator: {locator} not found in soup: {soup_with_error}')
#         print("LOG-------------------")


class LamodaGoodsOnSearchPageParser:
    """
    класс для парсинга каждого товара на странице поиска Ламоды
    """
    def __init__(self, good_soup=BeautifulSoup):
        self.soup = good_soup
        self.logger = logging.getLogger(__name__)

    @property
    def link(self) -> str:
        """
        Получение ссылки на товар
        :return: строка со ссылкой
        """
        locator = LamodaSearchGoodLocators.LINK
        line = self.soup.select_one(locator)
        try:
            value = line.attrs['href']
            return "https://www.lamoda.ru" + value
        except AttributeError:
            self.logger.debug(f"Link locator {locator} not find in soup: {self.soup}")
            raise ValueError("Link not found")

    @property
    def image_link(self) -> str:
        """
        Поиск изобраения товара на странице (может и не быть)
        :return: ссылка на изображение
        """
        locator = LamodaSearchGoodLocators.IMAGE
        image_line = self.soup.select_one(locator)
        try:
            value = image_line.attrs['src']
            value = re.sub("/img\d{3,4}x\d{3,4}/", "/product/", value)
            return "https:" + value
        except AttributeError:
            self.logger.debug(f"Image links Locator {locator} not find in soup: {self.soup}")
            return ""

    @property
    def default_price(self) -> int:
        """
        Получение стандартной цены (без скидки, если есть скидка вообще). Если цена одна (без скидок) - будет храниться здесь
        :return: значение цены
        """
        locator = LamodaSearchGoodLocators.OLD_PRICE
        price_line = self.soup.select_one(locator)
        try:
            value = str(price_line.contents[0]).replace("₽", "").replace(" ", "")  #'5 200'
            if value:
                return int(value)
            else:
                return 0
        except AttributeError:
            self.logger.debug(f"Default_price Locator {locator} not find in soup: {self.soup}")
            return self._single_price

    @property
    def final_price(self) -> int:
        """
        Поиск финальной цены (со скидкой) - может и не быть
        :return: значение цены
        """
        locator = LamodaSearchGoodLocators.NEW_PRICE
        price_line = self.soup.select_one(locator)
        try:
            value = str(price_line.contents[0]).replace("₽", "").replace(" ", "")
            if value:
                return int(value)
            else:
                return 0
        except AttributeError:
            self.logger.debug(f"Final_price Locator {locator} not find in soup: {self.soup}")
            return 0

    @property
    def _single_price(self) -> int:
        """
        Поиск единичиной цены (если нет скидки вообще)
        :return: значение цены
        """
        locator = LamodaSearchGoodLocators.SINGLE_PRICE
        price_line = self.soup.select_one(locator)
        try:
            value = str(price_line.contents[0]).replace("₽", "").replace(" ", "")
            if value:
                return int(value)
            else:
                return 0
        except AttributeError:
            self.logger.debug(f"Single_price Locator {locator} not find in soup: {self.soup}")
            return 0

    @property
    def brand(self) -> str:
        """
        Поиск бренда товара
        :return: строка с брендом
        """
        locator = LamodaSearchGoodLocators.BRAND
        line = self.soup.select_one(locator)
        try:
            value = line.contents[0]
            return str(value)
        except AttributeError:
            self.logger.debug(f"Brand Locator {locator} not find in soup: {self.soup}")
            raise ValueError('Brand not found')

    @property
    def description(self) -> str:
        """
        Поиск модели товара (описание)
        :return: строка с описанием/моделью
        """
        locator = LamodaSearchGoodLocators.DESCRIPTION
        line = self.soup.select_one(locator)
        try:
            value = line.contents[0]
            return str(value)
        except AttributeError:
            self.logger.info(f"Description Locator {locator} not find in soup: {self.soup}")
            raise ValueError('Description not found')

    def __repr__(self):
        print(self.soup)
        brand = self.brand
        description = self.description
        old_price = self.default_price
        new_price = self.final_price
        link = self.link
        image_link = self.image_link
        return f"{brand} {description} {old_price} {new_price} {link} {image_link}\n"