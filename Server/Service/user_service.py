#encoding:utf-8
import traceback

import requests
import sys

from Utils import  log_utils
from model.fangqiang import  user as user_model,ip as ip_model
from Server.Service import  fanqiang_ip_service

logger = log_utils.Log('Server/log/server').logger

user_collection = user_model.User()
ip_collection = ip_model.Fanqiang()

def vertify_user(account,password):
    '''
    验证用户是否合法
    :param account:账号
    :param password:密码
    :return:

    Example:
    >>> vertify_user('ccw','123456')
    (False, '密码不正确')
    >>> vertify_user('yy','123456')
    (False, '不存在此账号')
    >>> vertify_user('ccw','123qwe')
    (True, 'ok')
    '''
    try:
        user = user_collection.query({'account':account}).next()
        if user['is_freeze']:
            return False, '账号目前处于冻结状态'
        if not user['password']==password:
            return False,'密码不正确'
    except StopIteration as e:
        return False,'不存在此账号'
    except Exception as e:
        logger.info(traceback.format_exc())
        return False,str(e)
    return True,'ok'

def update_and_get_using_ip_port(account):
    '''
    更新并获取当前用户正在使用的ip_port(ip_port已失效的情况下才会更新)
    :param account:账号
    :return:

    Example:
    >>> update_and_get_using_ip_port('not_exist')
    Traceback (most recent call last):
        ...
    StopIteration
    >>> update_and_get_using_ip_port('ccw')
    ('123.206.56.247:1080', '')

    '''

    ip_port_1 , ip_port_2 = '',''
    #获取所使用的ip_port
    user = user_collection.query({'account':account}).next()
    if user['ip_with_port_1']:
        ip_with_port_dict_1 = ip_collection.query({'ip_with_port':user['ip_with_port_1']}).next()
        # 测试能否使用
        try:
            fanqiang_ip_service.test_proxy(ip_with_port_dict_1)
            ip_port_1 = ip_with_port_dict_1['ip_with_port']
        except (requests.exceptions.ConnectionError, requests.ReadTimeout, requests.exceptions.SSLError) as e:
            logger.debug('代理 %s 已失效' % ip_with_port_dict_1['ip_with_port'])
            # 不能使用就删除并更新
            ip_port_1 = fanqiang_ip_service.delete_and_update_ip_port(ip_with_port_dict_1['ip_with_port'])

    if user['ip_with_port_2'] and user['level']>=5:
        ip_with_port_dict_2 = ip_collection.query({'ip_with_port':user['ip_with_port_2']})
        # 测试能否使用
        try:
            fanqiang_ip_service.test_proxy(ip_with_port_dict_2)
            ip_port_2 = ip_with_port_dict_2['ip_with_port']
        except (requests.exceptions.ConnectionError, requests.ReadTimeout, requests.exceptions.SSLError) as e:
            logger.debug('代理 %s 已失效' % ip_with_port_dict_2['ip_with_port'])
            #不能使用就删除并更新
            ip_port_2 = fanqiang_ip_service.delete_and_update_ip_port(ip_with_port_dict_2['ip_with_port'])
        

    #重新获取并返回
    return ip_port_1,ip_port_2


if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == 'doctest':
            import doctest
            doctest.testmod()
    else:
        pass