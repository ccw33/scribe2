#encoding:utf-8
import json

import requests

import Conf
from Utils import exception_utils

dynamic_conf = Conf.Dynamic_conf()



class AccountException(Exception):
    def __init__(self,*args,message):
        super(AccountException,self).__init__(*args,message)
        self.message = message

def is_logined():
    '''
    验证是否已经登录
    :return:
    '''
    account = dynamic_conf.account
    password = dynamic_conf.password
    if not account or not password:
        return False
    return True

def get_delaytime()->int:
    import uuid
    uuid = uuid.uuid1()
    account = dynamic_conf.account
    password = dynamic_conf.password
    resp = requests.get(Conf.server+'get_delaytime',params={'account':account,'password':password,'uuid':uuid})
    if resp.status_code!=200:
        raise exception_utils.ServerErrorException(resp.content.decode('utf-8'))
    return int(resp.content)

# todo
def open_login_UI(message=''):
    '''
    打开登录界面
    :param message:打开界面时显示的信息
    :return:
    '''
    pass