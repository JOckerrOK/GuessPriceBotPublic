import re

from bs4 import BeautifulSoup
from typing import List
from Lamoda.Locators.lamoda_good_page_locators import LamodaGoodPageLocators


class LamodaGoodPageParser:
    """
    Класс для поиска на странице значений товара
    """
    def __init__(self, page):
        self.page_soup = BeautifulSoup(page, 'html.parser')
        self._prices = []

    def get_prices(self) -> List[float]:
        """
        Поиск цен на странице. Заполняется self._prices
        :return: Список цен. [стандартная цена, финальная] или [стандартная цена]
        """
        if not self._prices:
            locator = LamodaGoodPageLocators.PRICE
            price_line = self.page_soup.select(locator)
            self._prices = [float(x.attrs['content'].strip()) for x in price_line]
        return self._prices

    @property
    def default_price(self) -> float:
        """
        Возвращает стандартную цену товара
        :return: стандартная цена товара
        """
        try:
            return self.get_prices()[0]
        except IndexError:
            return 0.0

    @property
    def final_price(self) -> float:
        """
        Финальная цена товара (если есть)
        :return: финальная цена
        """
        try:
            return self.get_prices()[1]
        except IndexError:
            return 0.0

    @property
    def discount(self):
        #еще не реализовано
        return ""
        # locator = LamodaGoodPageLocators.DISCOUNT
        # return self.page_soup.select_one(locator).attrs['best_price_info']

    @property
    def brand(self) -> str:
        """
        Поиск на странице значения бренда
        :return:  Бренд
        """
        locator = LamodaGoodPageLocators.BRAND
        return self.page_soup.select_one(locator).string.rstrip()

    @property
    def model(self) -> str:
        """
        Поиск на странице значение модели
        :return: Модель
        """
        locator = LamodaGoodPageLocators.MODEL
        return self.page_soup.select_one(locator).string

    @property
    def images(self) -> List[str]:
        """
        Поиск на странице ссылок на изображения
        :return: Массив ссылок на изображения
        """
        locator = LamodaGoodPageLocators.IMAGES
        return ["https:" + re.sub("/img\d{3,4}x\d{3,4}/", "/product/", x.attrs['src']) for x in self.page_soup.select(locator)]

    def __repr__(self):
        return f'Brand {self.brand}, model: {self.model}, old price = {self.default_price}, final price = {self.final_price}, images = {self.images}\n'