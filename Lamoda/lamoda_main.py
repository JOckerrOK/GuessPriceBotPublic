from Data_models.goods_db import Good, GoodKeeper
from Lamoda.Pages.lamoda_search_page import LamodaSearchPage
from Lamoda.Pages.lamoda_good_page import LamodaGoodPage
from Data_models.shops_db import Shop
from Data_models.current_search_pages import NextSearchPages
from Data_models.categories_db import CategoriesPool, Category


class LamodaMain:
    LAMODA_SHOP_ID = 1

    @classmethod
    def add_new_goods(cls, sub_category_id, option) -> Good:
        """
        Поиск новых товаров на сайте и добавление в базу
        :param option: опциональный параметр
        :param sub_category_id: ID подкатегории
        :return: объект первого добавленного товара.
        """
        new_search = 0
        try:
            sub_category = CategoriesPool.get_sub_category_by_id(sub_category_id=sub_category_id, option=option)
        except ValueError as error:
            raise ValueError(error)
        try:
            next_page = NextSearchPages.get_next_search_page(sub_category_id=sub_category_id, option=option, shop_id=cls.LAMODA_SHOP_ID)
        except ValueError:
            search_string = Shop.get_search_address(cls.LAMODA_SHOP_ID)
            ends = ""
            if option > 0:
                option_item = CategoriesPool.get_option(option)
                ends = f"+{option_item.text_value}"
            next_page = search_string+sub_category.text_value.replace(" ", "+") + ends
            new_search = 1
        try:
            search_page = LamodaSearchPage(next_page)
        except ValueError as error:  # не найдены новые товары
            raise ValueError(error)
        goods = search_page.goods_on_page(category_id=sub_category.main_category_id, sub_category_id=sub_category_id, shop_id=cls.LAMODA_SHOP_ID, option=option)
        for good in goods:
            try:
                good.insert_or_update_good()
            except Exception as err:
                print('Query Failed: %s\nError: %s' + (str(err)))
        if new_search:
            NextSearchPages.insert_next_search_page(sub_category_id=sub_category_id, shop_id=cls.LAMODA_SHOP_ID, address=search_page.next_page)
        else:
            NextSearchPages.update_next_search_page(sub_category_id=sub_category_id, shop_id=cls.LAMODA_SHOP_ID, address=search_page.next_page)
        if len(goods) > 0:
            return goods[0]
        else:
            raise ValueError(f"No goods was found by category:{sub_category_id}")

    @classmethod
    def update_good(cls, good: Good):
        """
        Запрашивает по ссылке good.link актуальное состояние товара
        :param good:
        :return: возвращает экземпляр обновленного товара
        """
        lamoda_good = LamodaGoodPage(good.link.replace(" ", "+")).get_good_on_page()
        good.brand = lamoda_good.brand
        good.final_price = lamoda_good.final_price
        good.standard_price = lamoda_good.default_price
        good.set_image_links(lamoda_good.images)
        good.update_in_db()
        return good

    # @classmethod
    # def get_good_by_link(cls, link, good_id=-1) -> Good:
    #     """
    #     Запрашивает товар по ссылке. Нужна для актуализации информации о товаре
    #     :param link:
    #     :param good_id:
    #     :return: объект типа Good, найденный на странице.
    #     """
    #     lamoda_good = LamodaGoodPage(link).get_good_on_page()
    #     return Good(
    #         good_id=good_id,
    #         description=lamoda_good.model,
    #         brand=lamoda_good.brand,
    #         final_price=lamoda_good.final_price,
    #         standard_price=lamoda_good.default_price,
    #         link=link,
    #         )


if __name__ == "__main__":
    LamodaMain.add_new_goods(1)