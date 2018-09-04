#encoding:utf-8
import traceback

import requests
import sys

from Utils import  log_utils
from model.fangqiang import  user as user_model,ip as ip_model
from Server.Service import  fanqiang_ip_service
import logging

logger = log_utils.Log('Server/log/server',level=logging.DEBUG,name=__name__).logger

user_collection = user_model.User()
ip_collection = ip_model.Fanqiang()

def get_delaytime(account,password)->int:
    user = vertify_user(account,password)[2]
    level=1
    delay = 60
    if user:
        level=user['level']
    if level==1:
        delay = 60
    if level == 2:
        delay = 40
    if level == 3:
        delay = 30
    if level == 4:
        delay = 20
    if level == 5:
        delay = 10
    return delay


def vertify_user(account,password)->(bool,str,dict):
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
        if user['is_frozen']:
            return False, '账号目前处于冻结状态',user
        if not user['password']==password:
            return False,'密码不正确',user
    except StopIteration as e:
        return False,'不存在此账号',{}
    except Exception as e:
        logger.info(traceback.format_exc())
        return False,str(e),{}
    return True,'ok',user


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

    def test_and_update_single_ip_port(ip_port_col_name)->str:
        '''
        就单个user里面的ip_port而言进行更新
        :param ip_port_col_name: user中使用的ip_port字段名，比如’ip_with_port_1','ip_with_port_2'
        :return: 可用的ip_port
        '''
        ip_port = ''
        cursor = ip_collection.query({'ip_with_port': user[ip_port_col_name]})
        if cursor.count():
            ip_with_port_dict = cursor.next()
            # 测试能否使用
            try:
                use_time = fanqiang_ip_service.test_proxy(ip_with_port_dict)
                ip_with_port_dict['time']=use_time
                ip_port = ip_with_port_dict['ip_with_port']
            except (requests.exceptions.ConnectionError, requests.ReadTimeout, requests.exceptions.SSLError) as e:
                logger.debug('代理 %s 已失效' % ip_with_port_dict['ip_with_port'])
                # 不能使用就增加disable统计次数，如果满10次就删除并更新
                temp_ip_port = fanqiang_ip_service.disable_and_update_if_needed(ip_with_port_dict)
                if temp_ip_port == ip_with_port_dict['ip_with_port']:  # 如果没更新，只是disable_times+1就重新获取并更新该user的ip_port_dict
                    ip_port = fanqiang_ip_service.get_random_useful_ip_port_dict()['ip_with_port']
                    user_collection.update({ip_port_col_name: ip_port}, {'_id': user['_id']})
                else:  # 如果有更新就直接使用该ip_port_dict
                    ip_port = temp_ip_port
        else:
            logger.warning('出现ip_port被删而没有更新数据库的情况')
            while not ip_port:
                new_ip_port_dict = fanqiang_ip_service.get_random_useful_ip_port_dict()
                user_collection.update({ip_port_col_name: new_ip_port_dict['ip_with_port']}, {'_id': user['_id']})
                ip_port = new_ip_port_dict['ip_with_port']
        return ip_port

    if user['ip_with_port_1']:
        ip_port_1 = test_and_update_single_ip_port('ip_with_port_1')
    if user['ip_with_port_2'] and user['level']>=5:
        ip_port_2 = test_and_update_single_ip_port('ip_with_port_2')

    #重新获取并返回
    return ip_port_1,ip_port_2


if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == 'doctest':
            import doctest
            doctest.testmod()
    else:
        update_and_get_using_ip_port('ccw')