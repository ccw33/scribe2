# encoding:utf-8
import math
import re
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
        # self.ip_port = Conf.ip_port
        self.proxy_type = Conf.proxy_type
        self.headers = Conf.headers

    def test_ok(self):
        '''
        测试是否能翻墙
        :return:
        '''
        try:
            with open(Conf.proxy_filt_path,'r') as fr:
                text = fr.read()
                find_res = re.findall(r'forward-socks5 \/ (\d+\.\d+\.\d+\.\d+\:\d+)',text)
                if not find_res:
                    raise Exception('请配置代理')
                self.ip_port = find_res[0]
            resp = requests.get('https://www.baidu.com/', headers=self.headers,
                                proxies={'http': self.proxy_type + (
                                    'h' if self.proxy_type == 'socks5' else '') + '://' + self.ip_port,
                                         'https': self.proxy_type + (
                                             'h' if self.proxy_type == 'socks5' else '') + '://' + self.ip_port},
                                timeout=10)
            use_time = resp.elapsed.microseconds / math.pow(10, 6)
            return True
        except requests.exceptions.ConnectionError or requests.exceptions.ReadTimeout or requests.exceptions.SSLError as e:  # request 访问错误
            return False
        except Exception as e:
            logger.warning(traceback.format_exc())
            return False

    def update(self):
        payload = {'uuid': uuid.uuid1()}
        resp = requests.get(Conf.server + 'get_new_ip_port', params=payload)
        ip_port = resp.content.decode('utf-8')
        # 更新本地的配置文件
        new_text = ''
        with open(Conf.proxy_filt_path,'r') as fr:
            text = fr.read()
            find_res = re.findall(r'forward-socks5 \/ (\d+\.\d+\.\d+\.\d+\:\d+)', text)
            new_text = text.replace(find_res[0],ip_port)
        with open(Conf.proxy_filt_path,'w') as fw:
            fw.write(new_text)
        a = 1


if __name__ == "__main__":
    auto_updater = AutoUpdater()
    while True:
        if not auto_updater.test_ok():
            auto_updater.update()
        time.sleep(3600)

    # payload = {'uuid': uuid.uuid1()}
    # resp = requests.get(Conf.server + 'get_new_ip_port', params=payload)
    # content = resp.content.decode('utf-8')
    # a = 1

