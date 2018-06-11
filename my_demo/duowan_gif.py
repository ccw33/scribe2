import requests
from bs4 import BeautifulSoup
from . import ip_scriber
import re

import pymongo

client = pymongo.MongoClient('localhost', 27017)
gaoxiao_gif = client['gaoxiao_gif']
gaoxiaoGifData = gaoxiao_gif['gaoxiaoGifData']

ip_list = ip_scriber.get_ip_list()

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36"
}


def scribe_index(url):
    resp = ''
    try:
        proxies = ip_scriber.get_random_ip_proxy(ip_list)
        resp = requests.get(url, headers=headers, proxies=proxies)
    except:
        print('link failed ' + str(proxies))
        return scribe_index(url)

    if resp.status_code != 200:
        print(resp.status_code)
        return scribe_index(url)

    # 因为使用了代理，有些代理并没有访问我所输入的地址，所以需要判断一下
    if resp.url != url:
        print('没有访问：' + url + '\n访问的是：' + resp.url)
        scribe_index(url)
        return

    soup = BeautifulSoup(resp.text, 'lxml')
    # 如果代理的ip被封
    if re.search(r'无效用户', soup.text, re.M):
        print('被封ip  ' + str(proxies))
        scribe_index(url)
        return

    lis = soup.select('li.box')[1:]
    hrefs = [re.findall(r'href=".*?\.html"',str(li))[0].split('"')[1] for li in lis]
    for href in hrefs:
        scribe_detail(href+'#p{}')


def scribe_detail(url):
    resp = requests.get(url, headers=headers, proxies=ip_scriber.get_random_ip_proxy(ip_list))
    soup = BeautifulSoup(resp.text, 'lxml')


if __name__ == '__main__':
    url = 'http://tu.duowan.com/m/bxgif'
    urls = ['http://tu.duowan.com/m/bxgif?offset={}&order=created&math=0.8234315953925675'.format(30 * i) for i in
            range(0, 5)]
    scribe_index(url)
