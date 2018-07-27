#encoding:utf-8
from model import base
from model import fangqiang as baseinfo
import pymongo

class Fanqiang(base.Base):
    db_name = baseinfo.name
    collection_name = 'ip'
    template = {
        'ip_with_port':str,
        'proxy_type':str,
        'time': float,
        'location':{
            'region':str,
            'country': str,
            'province': str,
            'city': str,
            'rect': str,
            'timezone': str,
            'postcode': str,
        }
    }

    def __init__(self):
        super(Fanqiang,self).__init__()
        #另外加一个主键
        self.collection.create_index('ip_with_port',unique=True)


if __name__=="__main__":
    f = Fanqiang()
    a = f.query()