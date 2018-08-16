# encoding:utf-8
import datetime

from model import base
from model import fangqiang as baseinfo
import pymongo


class User(base.Base):
    db_name = baseinfo.name
    collection_name = 'user'
    template = {
        'account': str,
        'password': str,
        'email':str,
        'level': int,
        'begin': datetime.datetime,
        'end': datetime.datetime,
        'is_frozen':bool,
        'ip_with_port_1': str,
        'ip_with_port_2': str,
    }

    def __init__(self):
        super(User, self).__init__()
        # 另外加一个主键
        self.collection.create_index('account', unique=True)


if __name__ == "__main__":
    user = User()
    user.save({
        'account': 'ccw',
        'password': '123qwe',
        'email': '952424500@qq.com',
        'level': 1,
        'begin': datetime.datetime.now(),
        'end': datetime.datetime.now() + datetime.timedelta(days=365),
        'is_frozen': False,
        'ip_with_port_1': '123.206.56.247:1080',
        'ip_with_port_2': ''
    })
