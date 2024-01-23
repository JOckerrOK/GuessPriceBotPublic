"""
Локаторы для товаров на странице поиска
"""


class LamodaSearchGoodLocators:
    LINK = ' a' #attr['href']
    IMAGE = "*.x-product-card__pic-img" #attr['src']
    OLD_PRICE = "span.x-product-card-description__price-old" #content
    NEW_PRICE = "span.x-product-card-description__price-new" #content
    SINGLE_PRICE = "span.x-product-card-description__price-single"
    BRAND = "div.x-product-card-description__brand-name" #content
    DESCRIPTION = "div.x-product-card-description__product-name" #content utf-8