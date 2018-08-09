#encoding:utf-8

import math
import random
import re

import requests

from model.fangqiang import ip,user as user_model
from Utils import scribe_utils

fanqiang = ip.Fanqiang()
user = user_model.User()

def get_random_ip_port_dict():
    '''
    获取一个有用的ip_port_dict
    :return:
    '''
    ip_list = list(fanqiang.query())
    if not ip_list:
        raise Exception('没有可用ip')
    ip_port_dict = ip_list[math.floor(random.random() * len(ip_list))]
    try:
        test_proxy(ip_port_dict)
        return ip_port_dict
    except scribe_utils.RobotException or\
           requests.exceptions.ConnectionError or requests.exceptions.ReadTimeout or requests.exceptions.SSLError as e:  # request 访问错误
        fanqiang.delete({'ip_with_port':ip_port_dict['ip_with_port']})
        return get_random_ip_port_dict()


def test_proxy(ip_port_dict):
    '''
    测试ip代理
    :param ip_port_dict: 包含ip port等数据的dict对象
    :type ip_port_dict: dict
    :return:use_time 用时，秒为单位。
    '''
    ip_with_port = ip_port_dict['ip_with_port']
    proxy_type = ip_port_dict['proxy_type']
    resp = requests.get('https://www.baidu.com/', headers=scribe_utils.headers,
                        proxies={'http': proxy_type + (
                            'h' if proxy_type == 'socks5' else '') + '://' + ip_with_port,
                                 'https': proxy_type + (
                                     'h' if proxy_type == 'socks5' else '') + '://' + ip_with_port},
                        timeout=10)
    use_time = resp.elapsed.microseconds / math.pow(10, 6)
    return use_time

def delete_and_update_ip_port(ip_with_port):
    '''
    删除ip_port_dict 同时级联更新使用该ip_port的用户的ip_with_port字段
    :param ip_with_port:
    :type ip_with_port:str
    :return:
    '''
    fanqiang.delete({'ip_with_port':ip_with_port})
    new_ip_with_port = get_random_ip_port_dict()['ip_with_port']
    user.update({'ip_with_port_1':new_ip_with_port},{'ip_with_port_1':ip_with_port})
    user.update({'ip_with_port_2':new_ip_with_port},{'ip_with_port_2':ip_with_port})
    return new_ip_with_port