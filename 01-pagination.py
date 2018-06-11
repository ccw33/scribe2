#coding:utf-8
'''
https://www.jianshu.com/p/d99f6fd8b209
环境搭建
pip install BeautifulSoup4
pip install requests
pip install lxml
pip install pymongo
'''
from bs4 import BeautifulSoup
import requests

s = requests.Session()

def detailOper(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36"
    }
    # headers = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    #            'Accept-Encoding': 'gzip, deflate, br',
    #            'Accept-Language': 'zh-CN,zh;q=0.9',
    #            'Connection': 'keep-alive',
    #            'Cookie':'antipas=f5L6637159021095C236G42W911; uuid=92a417e0-365f-470f-d258-7a1203ebc408; cityDomain=tj; clueSourceCode=%2A%2300; ganji_uuid=8210410187166491920413; sessionid=f116487d-f0bf-456c-cbc0-acad4d00c180; lg=1; cainfo=%7B%22ca_s%22%3A%22self%22%2C%22ca_n%22%3A%22self%22%2C%22ca_i%22%3A%22-%22%2C%22ca_medium%22%3A%22-%22%2C%22ca_term%22%3A%22-%22%2C%22ca_kw%22%3A%22-%22%2C%22keyword%22%3A%22-%22%2C%22ca_keywordid%22%3A%22-%22%2C%22scode%22%3A%22-%22%2C%22version%22%3A1%2C%22platform%22%3A%221%22%2C%22client_ab%22%3A%22-%22%2C%22guid%22%3A%2292a417e0-365f-470f-d258-7a1203ebc408%22%2C%22sessionid%22%3A%22f116487d-f0bf-456c-cbc0-acad4d00c180%22%7D; preTime=%7B%22last%22%3A1521599209%2C%22this%22%3A1521599008%2C%22pre%22%3A1521599008%7D',
    #            'Host': 'www.guazi.com',
    #            'Upgrade - Insecure - Requests': '1',
    #            'User - Agent': 'Mozilla / 5.0(Windows NT 6.1; Win64; x64) AppleWebKit / 537.36(KHTML, like Gecko) Chrome / 64.0 .3282 .186 Safari / 537.36'
    #            }
    resp = s.get(url, headers=headers)
    soup = BeautifulSoup(resp.text, 'lxml')
    titles = soup.select('h2.t')
    prices = soup.select('div.t-price > p')
    print(resp.text)
    for title, price in zip(titles, prices):
        data = {
            'title': title.get_text(),
            'detailHerf': title.get('href'),
            'price': price.get_text().replace(u'万', '').replace(' ', '')
        }
        print(data)


def start():
    urls = ['http://www.guazi.com/tj/buy/o{}/'.format(str(i)) for i in range(1, 30, 1)]
    for url in urls:
        detailOper(url)


start()
