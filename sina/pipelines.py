# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

from pymongo import MongoClient


class SinaPipeline(object):

    collection_name = 'NEWS'

    def __init__(self, mongo_host, mongo_port, mongo_database):
        self.mongo_host = mongo_host
        self.mongo_port = mongo_port
        self.mongo_database = mongo_database

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            crawler.settings.get('MONGO_HOST'),
            int(crawler.settings.get('MONGO_PORT')),
            crawler.settings.get('MONGO_DATABASE')
        )

    def open_spider(self, spider):
        self.client = MongoClient(host=self.mongo_host, port=self.mongo_port)
        self.database = self.client[self.mongo_database]
        self.collection = self.database[self.collection_name]

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        self.collection.insert_one(dict(item))
        return item
