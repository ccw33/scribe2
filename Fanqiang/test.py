#encoding:utf-8
import math

import requests

from Utils import scribe_utils


proxy_type='socks5'
ip_with_port='216.144.230.233:15993' # 连接不是隐私连接
# ip_with_port='192.169.217.40:35968' # 成功
# ip_with_port='103.216.82.148:6667' # 超时


def test():
    resp = requests.get('https://www.baidu.com/', headers=scribe_utils.headers,
                        proxies={'http': proxy_type + (
                            'h' if proxy_type == 'socks5' else '') + '://' + ip_with_port,
                                 'https': proxy_type + (
                                     'h' if proxy_type == 'socks5' else '') + '://' + ip_with_port},
                        timeout=10)
    use_time = resp.elapsed.microseconds / math.pow(10, 6)
    location = scribe_utils.get_location(ip_with_port.split(':')[0])

    a = 1

if __name__ == "__main__":
    test()