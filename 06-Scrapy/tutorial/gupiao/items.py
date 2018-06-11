# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class GuPiaoItem(scrapy.Item):
    final_price=scrapy.Field()#收盘价
    increment = scrapy.Field()#净利润同比增长
    PB = scrapy.Field()# 市净率
    PE = scrapy.Field() # 市盈率
    BVPS = scrapy.Field() # 每股净资产
