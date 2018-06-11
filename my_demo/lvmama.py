#encoding:utf-8
from bs4 import BeautifulSoup
import pymongo

from my_demo import utils
import re
import logging
import time


# 初始化数据库
client = pymongo.MongoClient('localhost', 27017)
lvmama = client['lvmama']
indexData = lvmama['indexData']
detailData = lvmama['detailData']

def get_links(driver):
    datas = []
    soup = BeautifulSoup(driver.page_source, 'lxml')
    links = soup.select('.recommend_list_content h5')
    for link in links:


steps = {'name': '驴妈妈首页',
                 'steps_detail': [{'description': '打开驴妈妈',
                                   'action': ('get', {'url': 'http://ticket.lvmama.com/'}),
                                   'success_flag': '.main_tit',
                                   'if_failed_action': ('quit_and_again', {})},
                                  {'description': '点击推荐景点城市',
                                   'action': ('click', {'selector': '.city_js'}),
                                   'success_flag': '.recommend_list_content h5',
                                   'if_failed_action': ('quit_and_again', {})},
                                  {'description': '获取link',
                                   'ready': '[href="/?category=0"]',
                                   'if_not_ready_action': (
                                       'refresh',
                                       {'url': 'https://weibo.com/?category=0', 'ready_selector': '[href="/?category=0"]'}),
                                   'action': ('scribe', {'method': method,})},
                                  ]}