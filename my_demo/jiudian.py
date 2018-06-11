#encoding:utf-8
from bs4 import BeautifulSoup
import pymongo

from my_demo import utils
import re
import logging
import time


# 初始化数据库
client = pymongo.MongoClient('localhost', 27017)
jiudian = client['jiudian']
indexData = jiudian['indexData']
detailData = jiudian['detailData']


def xiecheng_link(driver):
    scribed_data = []
    soup = BeautifulSoup(driver.page_source, 'lxml')
    links = soup.select('.J_trace_hotHotel')
    for link in links:
        scribed_data.append(link.attrs['href'])
    return scribed_data

steps = {'name': '携程首页',
                 'steps_detail': [{'description': '打开携程酒店',
                                   'action': ('get', {'url': 'http://hotels.ctrip.com/'}),
                                   'success_flag': '#hotsold_city_list a',
                                   'if_failed_action': ('quit_and_again', {})},
                                  {'description': '点击推荐城市（循环）',
                                   'action': ('loop_click', {'selector': '#hotsold_city_list a'}),
                                   'success_flag': '.J_trace_hotHotel',
                                   'if_failed_action': ('quit_and_again', {})},
                                  {'description': '获取link',
                                   'ready': '.J_trace_hotHotel',
                                   'if_not_ready_action': (
                                       'refresh',
                                       {'url': 'http://hotels.ctrip.com/', 'ready_selector': '#hotsold_city_list a'}),
                                   'action': ('scribe', {'method': xiecheng_link,})},
                                  ]}

if __name__=='__main__':
    xiecheng_indexes = utils.run_steps(steps)
    a=1