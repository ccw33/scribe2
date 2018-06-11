# coding:utf-8
import requests
from bs4 import BeautifulSoup
import re
from selenium import webdriver
from selenium.webdriver.common.proxy import Proxy
import time
import sys
from my_demo import ip_scriber
import random

# headers = {'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.89 Safari/537.36'}
headers = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1'}
ip_list = ip_scriber.get_ip_list()


def scribe_index(url):
    resp = ''
    try:
        proxies = ip_scriber.get_random_ip_proxy(ip_list)
        resp = requests.get(url, headers=headers, proxies=proxies, timeout=5)
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
    hrefs = [re.findall(r'href=".*?\.html"', str(li))[0].split('"')[1] for li in lis]
    for href in hrefs:
        scribe_detail(href + '#p{}')


def scribe_detail(url, driver=None, page=1):
    # resp = requests.get(url,headers=headers)
    # soup = BeautifulSoup(resp.text,'lxml')
    # video_href = soup.select('source[type="video/mp4"]')[0]['src']
    page_size = 0
    if not driver:
        fireFoxOptions = webdriver.FirefoxOptions()
        fireFoxOptions.set_headless()
        # fireFoxOptions.add_argument("--proxy-server=http://{}".format(random.choice(ip_list)))
        # driver = webdriver.Firefox( executable_path='temp_file/geckodriver',options=fireFoxOptions)
        ip_port = random.choice(ip_list)
        print(ip_port)
        proxy = Proxy({'httpProxy': ip_port})
        driver = webdriver.Firefox(executable_path='D:/geckodriver/geckodriver.exe', options=fireFoxOptions,
                                   proxy=proxy)
    real_url = url.format(page)
    driver.get(real_url)
    soup = BeautifulSoup(driver.page_source, 'lxml')
    #     获取最高评论
    try_time = 0
    while not soup.select('source[type="video/mp4"]'):
        try_time = try_time + 1
        soup = BeautifulSoup(driver.page_source, 'lxml')
        if try_time > 3:  # 尝试三次加载不出来换链接
            print('source[type="video/mp4"]')
            return scribe_detail(url, page=page)
    video_href = soup.select('source[type="video/mp4"]')[0]['src']
    driver.execute_script('window.scrollTo(0,document.body.scrollHeight)')
    soup = BeautifulSoup(driver.page_source, 'lxml')
    # 如果评论没有加载出来，等一面再从新获取soup
    try_time = 0
    while not soup.select('.comment_text'):
        try_time = try_time + 1
        soup = BeautifulSoup(driver.page_source, 'lxml')
        if try_time > 3:  # 尝试三次加载不出来换链接
            print('.comment_text')
            return scribe_detail(url, page=page)
    common = soup.select('.comment_text')[0].text
    print(video_href + '\n' + common + '\n\n')
    if not page_size:
        page_size = int(re.findall(r'\d+', soup.select('#seq')[0].text)[1])
    # 翻页
    print(page)
    if page < page_size:
        page = page + 1
        scribe_detail(url, driver, page)


if __name__ == '__main__':
    url = 'http://tu.duowan.com/m/bxgif'
    scribe_index(url)
