# encoding:utf-8
import datetime

from model import base
from model import fangqiang as baseinfo
import pymongo


class Fanqiang(base.Base):
    db_name = baseinfo.name
    collection_name = 'ip'
    template = {
        'ip_with_port': str,
        'proxy_type': str,
        'time': float,
        'disable_times': (int, 0),
        'location': {
            'region': str,
            'country': str,
            'province': str,
            'city': str,
            'rect': str,
            'timezone': str,
            'postcode': str,
        },
        'Elite': ({
            'ip': str,
            'location': {
                'region': str,
                'country': str,
                'province': str,
                'city': str,
                'rect': str,
                'timezone': str,
                'postcode': str,
            }
        },{}),  # 如果数据有这个字段，则证明是高匿的，代理后还经过其他ip跳转，十分安全
    }

    def __init__(self):
        super(Fanqiang, self).__init__()
        # 另外加一个主键
        self.collection.create_index('ip_with_port', unique=True)


if __name__ == "__main__":
    f = Fanqiang()
    a = list(f.query().sort([('time', pymongo.ASCENDING)]))
    # f.save({
    #     "proxy_type": "socks5",
    #     "ip_with_port": "50.62.35.225:1111",
    #     "time": 0.406683,
    #     "location": {
    #         "region": "地区：Norteamérica(北美洲)",
    #         "country": "国家：United States(美国) ，简称:US",
    #         "province": "洲／省：Arizona",
    #         "city": "城市：Scottsdale",
    #         "rect": "经度：-111.8906，纬度33.6119",
    #         "timezone": "时区：America/Phoenix",
    #         "postcode": "邮编:85260"
    #     },
    #     'Elite': {
    #         'ip': '',
    #         'location': {
    #             'region': '',
    #             'country': '',
    #             'province': '',
    #             'city': '',
    #             'rect': '',
    #             'timezone': '',
    #             'postcode': '',
    #         }
    #     },
    #     "updated_at": datetime.datetime.now(),
    #     "created_at": datetime.datetime.now()
    # })

    # f.collection.update_many({}, {'$unset': {'x': 3}})
    # f.collection.update_many({}, {'$set': {'disable_times': 0}})

    # test_data = a[0]
    # test_data['disable_times']=0
    # test_data['Elite']={}
    # f.update(test_data,{'_id':test_data['_id']})

    b = 1
