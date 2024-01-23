import requests
import aiohttp
import asyncio
import re

from typing import List
from Lamoda.Parser.lamoda_search_page_parser import LamodaSearchPageParser
from Lamoda.Parser.lamoda_search_goods_parser import LamodaGoodsOnSearchPageParser
from Data_models.goods_db import Good, GoodKeeper


async def fetch_page(url):
    async with aiohttp.ClientSession().get(url) as response:
        # print(f'time for request: {time.time()-page_time}')
        return await response.text()


class LamodaSearchPage:
    def __init__(self, url):
        self.url = url
        self.page_content = ""
        self.page_parser = None
        self._get_page()

    def _get_page(self) -> None:
        """
        Загружает и парсит страницу self.url на момент товаров.
        :return: None
        """
        if not self.page_content:
            self.page_content = requests.get(self.url, timeout=(5.0, 10.0)).content
        if not self.page_parser:
            self.page_parser = LamodaSearchPageParser(self.page_content)

    def goods_on_page(self, category_id, sub_category_id, shop_id, option=0) -> List[Good]:
        """
        Парсит каждый товар и формирует объекты Good
        :param option: option параметр
        :param category_id: ID главной категории
        :param sub_category_id: ID подкатегории
        :param shop_id: ID магазина
        :return: массив объектов Good
        """
        self._get_page()
        result = []
        for good_item in self.page_parser.goods_soup:
            item = LamodaGoodsOnSearchPageParser(good_item)
            try:
                brand = item.brand
                description = item.description
                link = item.link
                image_link = item.image_link
                old_price = item.default_price
                new_price = item.final_price
                if old_price or new_price:
                    good = Good(description=description, final_price=new_price, image_links_str=image_link, link=link,
                                brand=brand, standard_price=old_price, sub_category_id=sub_category_id, shop_id=shop_id,
                                category_id=category_id, option=option)
                    result.append(good)
            except ValueError:
                # При возникновении данной ошибки нет либо описания. либо бренда либо ссылки. Добавление такого товара не требуется - не валиден
                pass
        if not result:
            raise ValueError("No goods was found")
        return result

    @property
    def next_page(self) -> str:
        """
        Вычисляет адрес следующей страницы
        :return: адрес следующей страницы
        """
        this_page = re.search("page=([0-9]{1,2})", self.url).group(1)
        if this_page:
            this_page = int(this_page) + 1
            next_page = re.sub("page=\d{1,2}", "page=" + str(this_page), self.url)
            return next_page
        self._get_page()
        return self.page_parser.next_page


if __name__ == '__main__':
    search = LamodaSearchPage('https://www.lamoda.ru/catalogsearch/result/?q=куртка+мужская&page=2')
    print(search.next_page)
