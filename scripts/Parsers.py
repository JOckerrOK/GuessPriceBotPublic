from Data_models.goods_db import Good
from Lamoda.lamoda_main import LamodaMain


class ParserController:

    @classmethod
    def update_good(cls, good: Good) -> Good:
        """
        Запрашивает по ссылке good.link актуальное состояние товара
        :param good:
        :return: возвращает экземпляр обновленного товара
        """
        if good.shop_id == 1:  #1 - ламода
            return LamodaMain.update_good(good)

    @classmethod
    def add_new_goods(cls, sub_category_id, option=0) -> Good:
        """
        Добавление новых товаров в базу по указанным подкатегории и опции
        :param sub_category_id: ID подкатегории
        :param option: опциональный параметр
        :return: обьект класса Good
        """
        return LamodaMain.add_new_goods(sub_category_id, option)
