# encoding:utf-8
import math
import traceback
import uuid
import requests
import time
import logging

from Utils import log_utils
import Conf

logger = log_utils.Log('log/debug.log', logging.DEBUG).logger


class AutoUpdater():

    def __init__(self):
        self.ip_port = Conf.ip_port
        self.proxy_type = Conf.proxy_type
        self.headers = Conf.headers

    def test_ok(self):
        '''
        测试是否能翻墙
        :return:
        '''
        try:
            resp = requests.get('http://www.baidu.com/', headers=self.headers,
                                proxies={'http': self.proxy_type + (
                                    'h' if self.proxy_type == 'socks5' else '') + '://' + self.ip_port,
                                         'https': self.proxy_type + (
                                             'h' if self.proxy_type == 'socks5' else '') + '://' + self.ip_port},
                                timeout=10)
            use_time = resp.elapsed.microseconds / math.pow(10, 6)
            return True
        except requests.ConnectionError or requests.ReadTimeout as e:  # request 访问错误
            return False
        except Exception as e:
            logger.warning(traceback.format_exc())
            return False

    def update(self):
        payload = {'uuid': uuid.uuid1()}
        resp = requests.get(Conf.server + 'get_new_ip_port', params=payload)
        a = 1


if __name__ == "__main__":
    # auto_updater = AutoUpdater()
    # while True:
    #     if not auto_updater.test_ok():
    #         auto_updater.update()
    #     time.sleep(1)

    payload = {'uuid': uuid.uuid1()}
    resp = requests.get(Conf.server + 'get_new_ip_port', params=payload)
    content = resp.content.decode('utf-8')
    a = 1

