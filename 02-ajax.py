#coding:utf-8
'''
https://www.jianshu.com/p/6002ef3434fd
'''
from bs4 import BeautifulSoup
import requests
import json
import pymongo

client = pymongo.MongoClient('localhost', 27017)
guoke = client['guoke']
guokeData = guoke['guokeData']

def dealData(url):
    web_data = requests.get(url)
    datas = web_data.json()
    print(datas.keys())
    for data in datas['result']:
        guokeData.insert_one(data)

def start():
    urls = ['http://www.guokr.com/apis/minisite/article.json?retrieve_type=by_subject&limit=20&offset={}&_=1462252453410'.format(str(i)) for i in range(20, 100, 20)]
    for url in urls:
        dealData(url)

start()

