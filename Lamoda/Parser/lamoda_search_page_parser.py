from bs4 import BeautifulSoup
from Lamoda.Locators.lamoda_search_page_locators import LamodaPageLocators


class LamodaSearchPageParser:
    def __init__(self, page):
        self.page = page
        self.page_soup = BeautifulSoup(page, "html.parser")

    @property
    def goods_soup(self):
        """
        Запрос массива супов для каждого товара на странице
        :return: массив супов для дальнейшего парсинга
        """
        locator = LamodaPageLocators.ITEMS

        return self.page_soup.select(locator)