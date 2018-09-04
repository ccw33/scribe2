#encoding:utf-8
import logging
import math
import random
import re

import requests

from Server.server import app
from model.fangqiang import ip,user as user_model
from Utils import scribe_utils, log_utils

logger = log_utils.Log('Server/log/server',logging.DEBUG if app.debug else logging.ERROR,__name__).logger

fanqiang = ip.Fanqiang()
user = user_model.User()

def get_random_useful_ip_port_dict()->dict:
    '''
    获取一个有用的ip_port_dict
    :return:
    '''
    ip_list = list(fanqiang.query())
    if not ip_list:
        raise Exception('没有可用ip')
    ip_port_dict = ip_list[math.floor(random.random() * len(ip_list))]
    try:
        use_time = test_proxy(ip_port_dict)
        ip_port_dict["time"] = use_time
        return ip_port_dict
    except (scribe_utils.RobotException,\
           requests.exceptions.ConnectionError, requests.ReadTimeout, requests.exceptions.SSLError) as e: # request 访问错误
        disable_and_update_if_needed(ip_port_dict)
        logger.debug('随机ip_port %s 无法翻墙，从新获取' % ip_port_dict['ip_with_port'])
        return get_random_useful_ip_port_dict()


def test_proxy(ip_port_dict):
    '''
    测试ip代理
    :param ip_port_dict: 包含ip port等数据的dict对象
    :type ip_port_dict: dict
    :return:use_time 用时，秒为单位。
    '''
    ip_with_port = ip_port_dict['ip_with_port']
    proxy_type = ip_port_dict['proxy_type']
    logger.debug('开始测试%s' % ip_with_port)
    resp = requests.get('https://www.baidu.com/', headers=scribe_utils.headers,
                        proxies={'http': proxy_type + (
                            'h' if proxy_type == 'socks5' else '') + '://' + ip_with_port,
                                 'https': proxy_type + (
                                     'h' if proxy_type == 'socks5' else '') + '://' + ip_with_port},
                        timeout=10)
    use_time = resp.elapsed.microseconds / math.pow(10, 6)
    return use_time

def disable_times_add_one(ip_port_dict):
    '''
    更新disable_times（加1）
    :param ip_port_dict:
    :return:
    '''
    new_disable_times = ip_port_dict['disable_times'] + 1
    fanqiang.update({'disable_times': new_disable_times}, {'_id': ip_port_dict['_id']})
    def is_disable_times_lg_10():
        '''
        判断代理失效次数是否大于10，是返回True
        :param ip_port_dict:
        :return:
        '''
        return ip_port_dict['disable_times'] > 10

    return is_disable_times_lg_10


def delete_and_update_ip_port(ip_with_port)->str:
    '''
    删除ip_port_dict 同时级联更新使用该ip_port的用户的ip_with_port字段
    :param ip_with_port:
    :type ip_with_port:str
    :return:
    '''
    fanqiang.delete({'ip_with_port':ip_with_port})
    new_ip_with_port = get_random_useful_ip_port_dict()['ip_with_port']
    user.update({'ip_with_port_1':new_ip_with_port},{'ip_with_port_1':ip_with_port})
    user.update({'ip_with_port_2':new_ip_with_port},{'ip_with_port_2':ip_with_port})
    return new_ip_with_port


def disable_and_update_if_needed(ip_port_dict)->str:
    '''
    ip_port_dict的disable_times字段加1，同时如果超过10就更新相关的ip_port_dict和user数据并返回更新后的ip_with_port。
    否组返回原来的ip_with_port
    :param ip_port_dict:
    :return:
    '''
    is_disable_totaly = disable_times_add_one(ip_port_dict)
    if is_disable_totaly():
        return delete_and_update_ip_port(ip_port_dict['ip_with_port'])
    return ip_port_dict['ip_with_port']