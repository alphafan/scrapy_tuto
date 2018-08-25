# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class SinaItem(scrapy.Item):

    # Url of news page
    _id = scrapy.Field()

    title = scrapy.Field()
    content = scrapy.Field()
    pub_date = scrapy.Field()
    source = scrapy.Field()
    keywords = scrapy.Field()
