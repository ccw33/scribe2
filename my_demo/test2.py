# encoding:utf-8
import re
import threading

import pymongo
import time
import requests
from bs4 import BeautifulSoup
from my_demo import utils
from selenium.webdriver.common.keys import Keys

# 初始化数据库
client = pymongo.MongoClient('localhost', 27017)
ips = client['ips']
ipsData = ips['ipsData']
ipsFanqiangData = ips['ipsFanqiangData']

old_data = list(ipsFanqiangData.find())[-1]
ip_fanqiang_list = old_data['ip_fanqiang_list']
ip_fanqiang_list = sorted(ip_fanqiang_list, key=lambda ip: ip['time'])

# 把需要验证的去掉
proxy_type = 'socks5'
ok_list = []
for ip_dict in ip_fanqiang_list:
    try:
        ip_with_port = ip_dict['ip_with_port']
        resp = requests.get('http://www.google.com/', headers=utils.headers,
                            proxies={'http': proxy_type + (
                                'h' if proxy_type == 'socks5' else '') + '://' + ip_with_port,
                                     'https': proxy_type + (
                                         'h' if proxy_type == 'socks5' else '') + '://' + ip_with_port},
                            timeout=30)
        soup = BeautifulSoup(resp.text, 'lxml')
        driver = utils.ready(ip_dict)
        driver.set_page_load_timeout(60)
        driver.get('http://www.google.com/')
        tags = utils.wait_and_get_elements_until_ok(driver, '#lst-ib')
        tags[0].send_keys('kkk')
        tags[0].send_keys(Keys.ENTER)
        if re.findall(r'91\.206\.30\.205', driver.page_source):  # 证明需要验证
            continue
        else:  # 不需要验证，可以使用
            # 替换ip和port
            new_text
            with open('E:/git-repository/blog/ccw33.github.io/file/OmegaProfile_auto_switch.pac',
                      'r', encoding='utf-8') as fr:
                old_text = fr.read()
                new_text = old_text.replace(re.findall(r'(?:SOCKS |SOCKS5 )\d+\.\d+\.\d+\.\d+:\d+', old_text)[0],
                                            ip_with_port)
            with open('E:/git-repository/blog/ccw33.github.io/file/OmegaProfile_auto_switch.pac',
                      'w', encoding='utf-8') as fw:
                fw.write(new_text)
            # commit
            repo.index.add([file_path.replace(git_repo_path + '/', '')])
            repo.index.commit('auto update ' + file_path)
            # 获取远程库origin
            remote = repo.remote()
            # 提交到远程库
            remote.push()

    except Exception as e:
        continue
    a = 1

client.close()
a = 2
