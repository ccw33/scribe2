# coding:utf-8
'''
爬去高匿代理ip
http://www.xicidaili.com/nn/
'''
import pickle

import requests
from bs4 import BeautifulSoup
import random
import time, datetime
import re
# from fake_useragent import UserAgent
# ua = UserAgent()
import threading
from multiprocessing import Pool,cpu_count
import traceback

import pymongo




def get_random_ip_proxy(ip_list):
    '''
    获取随机的ip代理
    :param ip_list:
    :return:
    '''
    proxy_list = []
    for ip in ip_list:
        proxy_list.append('http://' + ip)
    proxy_ip = random.choice(proxy_list)
    proxies = {'http': proxy_ip}
    return proxies


headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36"
}

lock = threading.Lock()
lock2 = threading.Lock()

get = 0
lock_get = threading.Lock()
close = 0
lock_close = threading.Lock()

def get_useful_ip(ip_with_port, ip_list,fanqiang_ip_list, proxy_type='http'):
    try:
        if proxy_type == 'socks5':
            requests.get('https://www.baidu.com/', headers=headers,
                         proxies={'http': 'socks5://' + ip_with_port, 'https': 'socks5://' + ip_with_port}, timeout=5, )

            lock.acquire()
            try:
                ip_list.append(ip_with_port)
            finally:
                lock.release()

            requests.get('https://www.google.com/', headers=headers,
                         proxies={'http': 'socks5://' + ip_with_port, 'https': 'socks5://' + ip_with_port}, timeout=5, )

            lock2.acquire()
            try:
                fanqiang_ip_list.append(ip_with_port)
            finally:
                lock2.release()
        else:
            global get,close
            requests.get('https://www.baidu.com/', headers=headers,
                         proxies={'http': 'http://' + ip_with_port, 'https': 'https://' + ip_with_port}, timeout=5, )

            lock.acquire()
            try:
                ip_list.append(ip_with_port)
            finally:
                lock.release()

            requests.get('https://www.google.com/', headers=headers,
                         proxies={'http': 'http://' + ip_with_port, 'https': 'https://' + ip_with_port}, timeout=5, )

            lock2.acquire()
            try:
                fanqiang_ip_list.append(ip_with_port)
            finally:
                lock2.release()

    except Exception as e:
        pass

def normal_scribe(url,selector):
    ip_list = []
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text,'lxml')
    trs = soup.select(selector)
    for tr in trs:
        ip = re.search(r'(?:>)(\d+\.){3}\d{1,3}(?:<)', str(tr), re.M)
        port = re.search(r'(?:>)\d{3,5}(?:<)', str(tr), re.M)
        if ip and port:
            ip = re.search(r'(\d+\.){3}\d{1,3}', ip.group())
            port = re.search(r'\d+', port.group())
            ip_with_port = ip.group() + ':' + port.group()
            ip_list.append(ip_with_port)

    return ip_list

def scribe_ip(url, selector,proxies_ip_list,fanqiang_ip_list,filter = None):
    '''
    获取代理ip,多线程验证
    :param url:
    :return:
    '''
    ip_list = []
    fanqiang_ip_list = []
    try:
        resp = requests.get(url, headers=headers, proxies=get_random_ip_proxy(proxies_ip_list),timeout=10)
        if resp.status_code != 200:
            # 链接失败也重新来
            print(resp.status_code)
            return scribe_ip(url, selector, proxies_ip_list,filter)
    except Exception as e:
        print(e)
        # 如果ip被封了，马上重试另一个
        return scribe_ip(url, selector, proxies_ip_list,filter)

    soup = BeautifulSoup(resp.text, 'lxml')
    trs = soup.select(selector)
    if filter:
        trs = [tr for tr in trs if filter(tr)]
    threads = []

    for tr in trs:
        ip = re.search(r'(?:>)(\d+\.){3}\d{1,3}(?:<)', str(tr), re.M)
        port = re.search(r'(?:>)\d{3,5}(?:<)', str(tr), re.M)
        if ip and port:
            ip = re.search(r'(\d+\.){3}\d{1,3}', ip.group())
            port = re.search(r'\d+', port.group())
            ip_with_port = ip.group() + ':' + port.group()
            # 开启一个线程收集有效的链接
            thread = threading.Thread(target=get_useful_ip,
                                      args=(ip_with_port, ip_list,fanqiang_ip_list))
            thread.start()
            threads.append(thread)
    # # block当前进程(不知道为什么不用join都能爬取，而且更快)
    # for thread in threads:
    #     thread.join()
    print('ip_list:' + str(ip_list))
    print('fanqiang_ip_list:' + str(fanqiang_ip_list))
    return ip_list, fanqiang_ip_list


def kuaidaili_filter(tag):#filter要定义在module层才能被multipleprocess pickle
    new_tags = tag.select('td:nth-of-type(3)')
    if new_tags:
        return new_tags[0].text == '高匿名'
    return False

def write_ip_list():
    '''
    爬ip并写到数据库，多进程爬取
    :return:
    '''
    ip_list = []
    ip_fanqiang_list = []
    asy_list = []
    webs = [
        # ('http://www.xicidaili.com/nn/{}',['http://www.xicidaili.com/nn/{}'.format(i) for i in range(1, 10)],'#ip_list > tr'),
        # ( 'http://www.data5u.com/free/gngn/index.shtml',[ 'http://www.data5u.com/free/gngn/index.shtml'],'ul.l2'),
        # ('http://www.66ip.cn/areaindex_35/{}.html',['http://www.66ip.cn/areaindex_35/{}.html'.format(i) for i in range(1, 6)], 'tr',),
        ('http://www.66ip.cn/areaindex_35/{}.html',['http://www.66ip.cn/areaindex_35/{}.html'.format(i) for i in range(1,10)],'tr'),
        # ('https://www.kuaidaili.com/ops/proxylist/{}/',['https://www.kuaidaili.com/ops/proxylist/{}/'.format(i) for i in range(1, 20)], 'tr',
        #  kuaidaili_filter),

        # ('https://31f.cn/socks-proxy/',['https://31f.cn/socks-proxy/'],'tr',False),
    ]

    proxies_ip_list = get_ip_list()
    for web in webs:
        # p = Pool(cpu_count()-1)#预留一个cpu爬虫效率更高，可能是因为主进程本来就占用一个cpu的原因
        p = Pool()#预留一个cpu爬虫效率更高，可能是因为主进程本来就占用一个cpu的原因
        for url in web[1]:
            print(url)
            # p.apply_async(scribe_ip, args=(url, web[2], proxies_ip_list))
            # p.apply_async(scribe_ip, args=(url, web[2], proxies_ip_list,ip_list,ip_fanqiang_list,web[3] if len(web) > 3 else None))
            asy_list.append(p.apply_async(scribe_ip, args=(url, web[2], proxies_ip_list,web[3] if len(web)>3 else None)))
        print('Waiting for all subprocesses done...')
        p.close()
        p.join()
        print('All subprocesses done.')
        for asy in asy_list:  # 收集爬到的ip
            ip_list = [*ip_list, *asy.get()[0]]
            ip_fanqiang_list = [*ip_fanqiang_list, *asy.get()[0]]

        # 不使用多进程
        # ip_list = [*ip_list, *scribe_ip(url,web[2],proxies_ip_list)]
        # time.sleep(random.choice(range(1, 2)))

    # 初始化数据库
    client = pymongo.MongoClient('localhost', 27017)
    ips = client['ips']
    ipsData = ips['ipsData']
    ipsFanqiangData = ips['ipsFanqiangData']

    if ip_list:
        ip_list = list(set(ip_list))  # 去重
        ipsData.insert_one({'date': time.strftime('%Y-%m-%d'),
                            'ip_list': ip_list,
                            'isFanqiang': False})
    if ip_fanqiang_list:
        ip_fanqiang_list = list(set(ip_fanqiang_list))  # 去重
        ipsFanqiangData.insert_one({'date': time.strftime('%Y-%m-%d'),
                            'ip_fanqiang_list': ip_fanqiang_list,
                            'isFanqiang': True})
    client.close()


def get_ip_list():
    # # 获取昨天爬取的ip
    # yes_time = (datetime.datetime.now()+datetime.timedelta(days=-1)).strftime('%Y-%m-%d')
    # a = ipsData.find_one({'date': yes_time,})

    # 获取最近爬到的ip
    # 初始化数据库
    client = pymongo.MongoClient('localhost', 27017)
    ips = client['ips']
    ipsData = ips['ipsData']
    ipsFanqiangData = ips['ipsFanqiangData']
    try:
        a = list(ipsData.find())[-1]
        ip_list = a['ip_list']
    except IndexError as e:
    #     没有已经爬到了的ｉｐ
        url = 'http://www.66ip.cn/areaindex_35/1.html'
        selector = 'tr'
        ip_list= normal_scribe(url,selector)
    client.close()
    return ip_list


if __name__ == '__main__':
    start = datetime.datetime.now()
    print(write_ip_list())
    print('总共花费时间：' + str((datetime.datetime.now() - start).seconds) + '秒')
