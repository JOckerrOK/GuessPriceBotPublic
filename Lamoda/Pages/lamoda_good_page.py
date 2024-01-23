import logging

import requests
import config
from Lamoda.Parser.lamoda_good_page_parser import LamodaGoodPageParser


class LamodaGoodPage:
    """
    Класс для загрузки страницы товара
    """
    def __init__(self, url):
        self.url = url
        self.logger = logging.getLogger(__name__)
        self.page_content = ""

    def get_good_on_page(self) -> LamodaGoodPageParser:
        """
        Загружает старницу и парсит
        :return: Объект класса LamodaGoodPageParser
        """
        page = requests.get(self.url)
        self.page_content = page.content
        self.logger.info(f"Load:{self.url}, status_code = " + str(page.status_code))
        good_page = LamodaGoodPageParser(self.page_content)
        return good_page


if __name__ == "__main__":
    URL = "https://www.lamoda.ru/p/mp002xm0vhli/shoes-salamander-sapogi/"
    HEADERS = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    #test_page = requests.get(URL).content
    #print(page)
    #test_good_page = LamodaGoodPageParser(test_page)
    lamoda_test = LamodaGoodPage(URL)
    goods = lamoda_test.get_good_on_page()
    print(lamoda_test.page_content)
    print('________________________________')
    print(goods)

