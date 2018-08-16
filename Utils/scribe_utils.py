# coding:utf-8
import threading

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.proxy import Proxy, ProxyType
from selenium.common import exceptions
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import pymongo

import random
import time
import logging
import re
from multiprocessing import Pool
import traceback
import functools
import pickle
import math

from Conf import system,driver_type,mode
from Utils.log_utils import Log

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36"
}

lock = threading.Lock()
lock2 = threading.Lock()

logger = Log('log/scribe_utils').logger

# 初始化数据库
client = pymongo.MongoClient('localhost', 27017)


class RobotException(Exception):
    '''
    需要机器人验证时抛出这个错
    '''
    def __init__(self, *args,message='需要机器人验证', **kwargs):
        super(RobotException,self).__init__(*args, **kwargs)
        self.message = message

class HashableDict(dict):
    def __eq__(self, other):
        return self['ip_with_port']==other['ip_with_port']

    def __ne__(self, other):
        return not self.__eq__(other)


    def __hash__(self):
        if 'ip_with_port' in self:
            return hash(self['ip_with_port'])
        else:
            raise Exception('dict对象' + self + '缺少key：ip_with_port')

def get_useful_ip(ip_with_port, proxy_type, ip_list=None, fanqiang_ip_list=None, timeout=10, type_get='request'):
    '''
    :param ip_with_port: Required
    :param proxy_type: Required
    :param ip_list: 如果传list，则会验证出普通ip_list,否则不会
    :param fanqiang_ip_list: 如果传list，则会验证出普通ip_list,否则不会
    :param timeout: 验证时的timeout时长，默认10
    :param type_get: 如果是’request'则是用requests来get，否则用selenium，默认request
    :return: ip_list,fanqiang_ip_list
    '''
    logger.debug('get_useful_ip:  ' + proxy_type + '-----' + ip_with_port)
    try:
        if isinstance(ip_list, list):
            if type_get == 'request':
                resp = requests.get('http://www.baidu.com/', headers=headers,
                                    proxies={'http': proxy_type + (
                                    'h' if proxy_type == 'socks5' else '') + '://' + ip_with_port,
                                             'https': proxy_type + (
                                             'h' if proxy_type == 'socks5' else '') + '://' + ip_with_port},
                                    timeout=timeout)
                use_time = resp.elapsed.microseconds/math.pow(10,6)
                if resp.status_code == 200:
                    lock.acquire()
                    try:
                        ip_list.append({'proxy_type': proxy_type, 'ip_with_port': ip_with_port,
                                        'time': use_time,'location':get_location(ip_with_port.split(':')[0])})
                        # ip_list.append({'proxy_type': proxy_type, 'ip_with_port': ip_with_port,
                        #                 'time': use_time})
                    finally:
                        lock.release()
                else:
                    logger.debug('失败：' + proxy_type + ':' + ip_with_port + ' status_code:' + str(resp.status_code))
                    pass
            else:
                driver = utils.ready({'proxy_type': proxy_type, 'ip_with_port': ip_with_port})
                try:
                    driver.get('http://www.baidu.com/')
                except Exception as e:
                    driver.quit()
                    return ip_list, fanqiang_ip_list
                tags = utils.wait_and_get_elements_until_ok(driver, 'input#su')
                if not tags:
                    driver.quit()
                    return ip_list, fanqiang_ip_list
                lock.acquire()
                try:
                    ip_list.append({'proxy_type': proxy_type, 'ip_with_port': ip_with_port})
                finally:
                    lock.release()
                driver.quit()

        # except Exception as e:
        #     # if not proxy_type == 'http':
        #     #     logger.debug('失败：' + proxy_type + ':' + ip_with_port + e)
        #     pass
        #
        # try:
        if isinstance(fanqiang_ip_list, list) and proxy_type == 'socks5':
            if type_get == 'request':
                resp = requests.get('http://www.google.com/', headers=headers,
                                    proxies={'http': proxy_type + (
                                    'h' if proxy_type == 'socks5' else '') + '://' + ip_with_port,
                                             'https': proxy_type + (
                                             'h' if proxy_type == 'socks5' else '') + '://' + ip_with_port},
                                    timeout=timeout)
                use_time = resp.elapsed.microseconds/math.pow(10,6)
                if resp.status_code == 200:
                    lock2.acquire()
                    try:
                        fanqiang_ip_list.append(
                            {'proxy_type': proxy_type, 'ip_with_port': ip_with_port,
                             'time': use_time,'location':get_location(ip_with_port.split(':')[0])})
                        # fanqiang_ip_list.append(
                        #     {'proxy_type': proxy_type, 'ip_with_port': ip_with_port,
                        #      'time': use_time})
                    finally:
                        lock2.release()
                else:
                    logger.debug('失败：' + proxy_type + ':' + ip_with_port + ' status_code:' + str(resp.status_code))
                    pass

            else:
                driver = utils.ready({'proxy_type': proxy_type, 'ip_with_port': ip_with_port})
                try:
                    driver.get('http://www.google.com/')
                except Exception as e:
                    driver.quit()
                    return ip_list, fanqiang_ip_list
                tags = utils.wait_and_get_elements_until_ok(driver, 'input#lst-ib')
                if not tags:
                    driver.quit()
                    return ip_list, fanqiang_ip_list
                lock2.acquire()
                try:
                    fanqiang_ip_list.append({'proxy_type': proxy_type, 'ip_with_port': ip_with_port})
                finally:
                    lock2.release()
                driver.quit()
    except Exception as e:
        logger.debug('失败：' + proxy_type + ':' + ip_with_port + str(e))
        pass
    return ip_list, fanqiang_ip_list


def get_ip_list(GFW=False):
    # # 获取昨天爬取的ip
    # yes_time = (datetime.datetime.now()+datetime.timedelta(days=-1)).strftime('%Y-%m-%d')
    # a = ipsData.find_one({'date': yes_time,})

    # url = 'http://www.66ip.cn/areaindex_35/1.html'
    # selector = 'tr'
    # ip_list = normal_scribe(url, selector)
    # 获取最近爬到的ip
    # 初始化数据库
    client = pymongo.MongoClient('localhost', 27017)
    ips = client['ips']
    ipsData = ips['ipsData']
    ipsFanqiangData = ips['ipsFanqiangData']
    client.close()
    try:
        a = list(ipsData.find() if not GFW else ipsFanqiangData.find())[-1]
        return a['ip_list'] if not GFW else a['ip_fanqiang_list']
    except IndexError as e:
        #     没有已经爬到了的ｉｐ
        url = 'http://www.66ip.cn/areaindex_35/1.html'
        selector = 'tr'
        ip_list, ip_fanqiang_list = normal_scribe(url, selector)
        return ip_list if not GFW else ip_fanqiang_list


def normal_scribe(url, selector):
    ip_list = []
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, 'lxml')
    trs = soup.select(selector)
    new_ip_list = []
    new_fanqiang_list = []
    for tr in trs:
        ip = re.search(r'(?:>)(\d+\.){3}\d{1,3}(?:<)', str(tr), re.M)
        port = re.search(r'(?:>)\d{3,5}(?:<)', str(tr), re.M)
        if ip and port:
            ip = re.search(r'(\d+\.){3}\d{1,3}', ip.group())
            port = re.search(r'\d+', port.group())
            ip_with_port = ip.group() + ':' + port.group()
            get_useful_ip(ip_with_port, 'http', new_ip_list, new_fanqiang_list)
            # ip_list.append({'proxy_type': 'http', 'ip_with_port': ip_with_port})

    return new_ip_list, new_fanqiang_list


ip_list = get_ip_list()


# ip定位：
def get_location(ip):
    '''
    ip定位并返回{'region': '地区：Europa(欧洲)', 'country': '国家：Russia(俄罗斯) ，简称:RU', 'province': '洲／省：Bashkortostan', 'city': '城市：Ufa', 'rect': '经度：56.0456，纬度54.7852', 'timezone': '时区：Asia/Yekaterinburg', 'postcode': '邮编:450068'}
    :param ip:
    :return:
    '''
    import geoip2.database
    reader = geoip2.database.Reader('file/GeoLite2-City_20180501/GeoLite2-City.mmdb')
    ip = ip
    response = reader.city(ip)
    # # 有多种语言，我们这里主要输出英文和中文
    # print("你查询的IP的地理位置是:")
    #
    # print("地区：{}({})".format(response.continent.names["es"],
    #                          response.continent.names["zh-CN"]))
    #
    # print("国家：{}({}) ，简称:{}".format(response.country.name,
    #                                 response.country.names["zh-CN"],
    #                                 response.country.iso_code))
    #
    # print("洲／省：{}({})".format(response.subdivisions.most_specific.name,
    #                           response.subdivisions.most_specific.names["zh-CN"]))
    #
    # print("城市：{}({})".format(response.city.name,
    #                          response.city.names["zh-CN"]))
    #
    # # print("洲／省：{}".format(response.subdivisions.most_specific.name))
    # #
    # # print("城市：{}".format(response.city.name))
    #
    # print("经度：{}，纬度{}".format(response.location.longitude,
    #                           response.location.latitude))
    #
    # print("时区：{}".format(response.location.time_zone))
    #
    # print("邮编:{}".format(response.postal.code))

    data = {
        'region': "地区：{}({})".format(response.continent.names["es"],
                                     response.continent.names["zh-CN"]),
        'country': "国家：{}({}) ，简称:{}".format(response.country.name,
                                             response.country.names["zh-CN"],
                                             response.country.iso_code),
        'province': "洲／省：{}".format(response.subdivisions.most_specific.name),
        'city': "城市：{}".format(response.city.name),
        'rect': "经度：{}，纬度{}".format(response.location.longitude,
                                    response.location.latitude),
        'timezone': "时区：{}".format(response.location.time_zone),
        'postcode': "邮编:{}".format(response.postal.code)
    }
    return data


def print_action_name(prefix='', debug=False):
    '''
    打印此调用此方法所使用的时间
    :param func:
    :return:
    '''

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kw):
            if debug:
                if prefix:
                    print(prefix + ':action--------' + func.__name__)
                else:
                    print('action--------' + func.__name__)
            result = func(*args, **kw)
            return result

        return wrapper

    return decorator


def ready(proxy_ip_port=None):
    '''
    根据 proxy_ip_port（dict）获取driver（设置好代理）
    :param proxy_ip_port: ex:{'proxy_type': 'socks5', 'ip_with_port': '91.206.30.205:3129', 'time': 0.072113, 'location': {'region': '地区：Europa(欧洲)', 'country': '国家：Ukraine(乌克兰) ，简称:UA', 'province': '洲／省：Kyiv City', 'city': '城市：Kiev', 'rect': '经度：30.5167，纬度50.4333', 'timezone': '时区：Europe/Kiev', 'postcode': '邮编:01016'}}
    :return:
    '''
    if system == 'windows':
        executable_path = 'D:/geckodriver/geckodriver.exe' if driver_type == 'firefox' else 'D:/geckodriver/chromedriver.exe'
    elif system == 'linux':
        executable_path = '../temp_file/geckodriver' if driver_type == 'firefox' else '../temp_file/chromedriver'
    else:
        logger.warning('没有这个系统：%s,暂时默认为windows' % system)
        executable_path = 'D:/geckodriver/geckodriver.exe' if driver_type == 'firefox' else 'D:/geckodriver/chromedriver.exe'

    if driver_type == 'firefox':  # 如果用火狐
        fireFoxOptions = webdriver.FirefoxOptions()
        if not mode == 'debug':
            fireFoxOptions.headless=True
        if proxy_ip_port:
            profile = webdriver.FirefoxProfile()
            profile.set_preference("network.proxy.type", 1)
            if proxy_ip_port['proxy_type'] == 'http':
                profile.set_preference("network.proxy.http", proxy_ip_port['ip_with_port'].split(':')[0])
                profile.set_preference("network.proxy.http_port", int(proxy_ip_port['ip_with_port'].split(':')[1]))
            else:
                profile.set_preference('network.proxy.socks', proxy_ip_port['ip_with_port'].split(':')[0])
                profile.set_preference('network.proxy.socks_port', int(proxy_ip_port['ip_with_port'].split(':')[1]))
            profile.update_preferences()
            driver = webdriver.Firefox(executable_path=executable_path, firefox_profile=profile,
                                       options=None if mode == 'debug' else fireFoxOptions)
            # webdriver.Chrome()
        else:
            driver = webdriver.Firefox(executable_path=executable_path,
                                       options=None if mode == 'debug' else fireFoxOptions)

        # if proxy_ip_port:
        #     if proxy_ip_port['proxy_type'] == 'http':
        #         proxy = Proxy({'prox'
        #                        'yType': ProxyType.MANUAL['string'], 'httpProxy': proxy_ip_port['ip_with_port']})
        #     elif proxy_ip_port['proxy_type'] == 'socks5' or proxy_ip_port['proxy_type'] == 'socks4':
        #         proxy = Proxy({'proxyType': ProxyType.MANUAL['string'], 'socksProxy': proxy_ip_port['ip_with_port']})
        #     else:
        #         raise Exception('Has no this kind of proxy:' + proxy_ip_port['proxy_type'])
        # else:
        #     proxy = None
        # if mode == 'product':
        #     driver = webdriver.Firefox(executable_path=executable_path, options=fireFoxOptions,
        #                                proxy=proxy)
        # elif mode == 'debug':
        #     if system == 'windows':
        #         binary_path = 'C:/Program Files (x86)/Mozilla Firefox/firefox.exe'
        #     else:
        #         binary_path = '/usr/bin/firefox'
        #     binary = FirefoxBinary(binary_path)
        #     driver = webdriver.Firefox(firefox_binary=binary,executable_path=executable_path, proxy=proxy)
        # else:
        #     raise Exception('ready方法的参数里面没有这种mode：%s' % mode)

        # PROXY = proxy_ip_port['ip_with_port']
        # webdriver.DesiredCapabilities.FIREFOX['proxy'] = {
        #     # "httpProxy": PROXY,
        #     # "ftpProxy": PROXY,
        #     # "sslProxy": PROXY,
        #     "socksProxy": PROXY,
        #     "noProxy": None,
        #     "proxyType": "MANUAL",
        #     "class": "org.openqa.selenium.Proxy",
        #     "autodetect": False
        # }
        # driver = webdriver.Remote("http://localhost:4444/wd/hub", webdriver.DesiredCapabilities.FIREFOX)
    else:  # 不是火狐就是chrome
        chrome_options = webdriver.ChromeOptions()
        if not mode == 'debug':
            chrome_options.headless=True
        if proxy_ip_port:
            chrome_options.add_argument(
                '--proxy-server=%s://%s' % (proxy_ip_port['proxy_type'], proxy_ip_port['ip_with_port']))
        driver = webdriver.Chrome(executable_path='D:/geckodriver/chromedriver.exe', chrome_options=chrome_options)
    driver.implicitly_wait(10)  # 设置寻找（包括异步加载的）element所等待的时间（如果不设置，则异步加载的element有可能会找不到）
    driver.set_page_load_timeout(10)  # 设置timeout时间
    return driver


def close(driver):
    '''
    关闭网页，并切换到最后一页,如果全部网页关闭了就quit
    :param driver:
    :return:
    '''
    if len(driver.window_handles) > 1:
        driver.close()
        driver.switch_to.window(driver.window_handles[-1])
    else:
        driver.quit()


def wait_and_get_elements_until_ok(driver, selector, by=By.CSS_SELECTOR, timeout=10,
                                   timeout_handler=None, delay_time=2):
    '''

    :param driver:
    :param selector:
    :param by:
    :param timeout: 超时时间
    :param timeout_handler: 如果超时，自定义的处理方法
    :param delay_time: 定位到元素之后延迟返回的时间
    :return:
    '''
    try:
        now = time.time()
        elements = ''
        while not elements:
            if time.time() - now > timeout:
                raise exceptions.TimeoutException
            elements = driver.find_elements_by_css_selector(selector)
            time.sleep(0.5)

        # elements = WebDriverWait(driver, timeout).until(
        #     EC.presence_of_all_elements_located((by, selector)),
        #     message="等待了%s秒也没有加载出%s，地址　%s" % (timeout, selector, driver.current_url)
        # )
        time.sleep(delay_time)
        return elements
    except exceptions.TimeoutException as e:
        if timeout_handler:
            return timeout_handler
        else:
            logger.debug(e)
    except Exception as e:
        logger.debug(e)


def get_and_target_blank(driver, url):
    '''
    打开新网页并切换到该页面
    :param driver:
    :param url:
    :return:
    '''
    driver.switch_to.window(driver.window_handles[-1])
    js = 'window.open("%s");' % url
    driver.execute_script(js)
    driver.switch_to.window(driver.window_handles[-1])


def add_url_prefix(url, prefix='https:'):
    '''
    自动判断是否缺前缀，如果缺了就加上去并返回
    :param url:
    :param prefix:
    :return:
    '''
    return url if re.findall(re.compile(prefix), url) else prefix + url


def scribe_less(data_list):
    '''
    最后爬取遗漏的网页
    :param driver: 有剩余网页没有爬取的driver
    :param scribe_method: 继续爬取所使用的function
    :param data_list:-->存储数据的容器集合，长度必须与driver.window_handles相同
    :return:
    '''
    driver = ready(random.choice(ip_list))
    driver.get('https://www.baidu.com')
    wait_and_get_elements_until_ok(driver, '[id="su"]')
    # for data in data_list:
    #     time.sleep(2)
    #     get_and_target_blank(driver, data['url'])
    # # 关闭空窗口
    # driver.switch_to.window(driver.window_handles[0])
    # close(driver)
    init_less = [data for data in data_list if not data['detail']]
    now_less = []

    for index, data in enumerate(data_list):
        if data['detail']:
            continue
        data_list[index] = \
            run_steps({'name': 'scribe_less', 'steps_detail': [pickle.loads(data['step'])]}, outer_driver=driver)[0]
        if not data_list[index]['detail']:
            now_less.append(data_list[index])

    print('now_less:%d;init_less-now_less:%d' % (len(now_less), len(init_less) - len(now_less)))
    if len(now_less) > 0 and len(init_less) - len(now_less) > 0:  # 递归直到剩余空置data不在减少（即这个捡漏方法不在生效）
        scribe_less(data_list)
    driver.quit()


class Action(object):
    self_check_ations = ['scroll']

    def __init__(self, driver, steps):
        self.driver = driver
        self.steps = steps

    @print_action_name()
    def get(self, url):
        '''
        get方式打开页面
        :param driver:
        :param url:
        :return:
        '''
        try:
            self.driver.get(url)
        except exceptions.TimeoutException as e:
            pass
        except Exception as e:
            logger.warning(e)
            self.driver.quit()
            self.driver = ready(random.choice(ip_list))
            self.get(url)

    @print_action_name()
    def open(self, url):
        '''
        新窗口打开
        :param url:
        :return:
        '''
        get_and_target_blank(self.driver, url)

    @print_action_name()
    def open_multiple(self, urls):
        '''
        DEPRECATE
        :param urls:
        :return:
        '''
        for url in urls:
            get_and_target_blank(self.driver, url)
            time.sleep(3)
        # 关掉空白页
        self.driver.switch_to.window(self.driver.window_handles[0])
        close(self.driver)

    @print_action_name(True)
    def skip(self):
        '''
        相当于pass
        :return:
        '''
        pass

    @print_action_name()
    def refresh(self, url, ready_selector):
        '''
        刷新页面
        :return:如果刷新成功返回True,否则返回False
        '''
        self.driver.get(url)
        return True if wait_and_get_elements_until_ok(self.driver, ready_selector) else False

    @print_action_name()
    def quit_and_again(self):
        '''
        关闭浏览器重新来一次
        :param driver:
        :param steps:
        :return:
        '''
        self.driver.quit()
        return run_steps(self.steps)

    @print_action_name()
    def anagin_previous_step(self):
        '''
        关闭浏览器重新来一次
        :param driver:
        :param steps:
        :return:
        '''
        self.driver.quit()
        return run_steps(self.steps)

    @print_action_name()
    def click(self, selector, index=None):
        '''
        点击
        :param driver:
        :param selector:
        :return:
        '''
        if isinstance(index, int):
            self.driver.find_elements_by_css_selector(selector)[index].click()

        self.driver.find_element_by_css_selector(selector).click()

    @print_action_name()
    def loop_click(self, selector):
        '''
        多次点击，重复后面的steps
        :param driver:
        :param selector:
        :return:
        '''
        raise Exception('loop开得的action是循环步骤，本身并不执行任何方法，只是告诉run_steps循环对应的非loop方法以及后面的step')

    @print_action_name()
    def scroll(self, ok_selector, scroll_times):
        '''
        下拉
        :param ok_selector: 下拉成功的标记
        :param scroll_times: 下拉次数
        :return:
        '''
        for t in range(scroll_times):
            init_len = len(self.driver.find_elements_by_css_selector(ok_selector))
            self.driver.execute_script('window.scrollTo(0,document.body.scrollHeight)')
            try:
                WebDriverWait(self.driver, 10).until(
                    lambda driver: len(driver.find_elements_by_css_selector(ok_selector)) > init_len,
                    message="等待了10秒也没有加载出新的'%s'   %s" % (ok_selector, self.driver.current_url))
            except Exception as e:
                logger.debug(e)
                self.quit_and_again()
                # # 点击热门
                # re_men = wait_and_get_elements_until_ok(driver, '[href="/?category=0"]')[0]
                # re_men.click()
                return

    @print_action_name()
    def scribe(self, method, mongo_path=None, close_after_scribe=True):
        '''
        调用爬取信息的方法，默认容器是
        {
         'url':'',
         'created_at':''
    	'data':{}
        }
        :param method:自己定义的爬虫方法
        :param mongo_path:如果有，则按照这个路劲保存到mongodb，如'weibo.indexData'
        :param close_after_scribe:True or False ,默认True，如果不出错，爬完后关闭
        :return:爬取后获得的数据 dict类型
        '''
        detail = method(self.driver)
        if mongo_path:
            db = client[mongo_path.split('.')[0]]
            table = db[mongo_path.split('.')[1]]
            table.insert_one({
                'url': self.driver.current_url,
                'created_at': time.strftime('%Y-%m-%d'),
                'detail': detail
            })
        if close_after_scribe:
            close(self.driver)
        return detail


def run_steps(steps, outer_driver=None, container=None):
    '''
    按步骤爬取，并返回· list
            [{
                'url': driver.current_url,
                'created_at': time.strftime('%Y-%m-%d'),
                'detail': {}
            },{
                'url': driver.current_url,
                'created_at': time.strftime('%Y-%m-%d'),
                'detail': {}
            },{
                'url': driver.current_url,
                'created_at': time.strftime('%Y-%m-%d'),
                'detail': {}
            }]
    :param steps:
    :return:
    '''
    if not outer_driver:
        driver = ready(random.choice(ip_list))
        print(steps['name'] + '-------Start ... init driver')
    else:
        driver = outer_driver

    ac = Action(driver, steps)
    # 存取爬取完的数据
    datas = []
    for index, step in enumerate(steps['steps_detail']):

        print(steps['name'] + '-------' + step['description'])

        # 如果是scribe action，调用scribe方法并收集数据
        if step['action'][0] == 'scribe':
            # 准备好的标记selector(爬取前才有这两个选项)
            if 'ready' in step and 'if_not_ready_action' in step:
                data = {
                    'url': step['if_not_ready_action'][1]['url'],
                    'created_at': time.strftime('%Y-%m-%d'),
                    'detail': {},
                    'step': pickle.dumps(step)
                }
                if not wait_and_get_elements_until_ok(driver, step['ready']):  # 如果页面没有准备好
                    # 页面没有准备好的后补方法
                    logger.debug('没有找到：' + step['success_flag'])
                    if step['if_not_ready_action'][0] == 'quit_and_again':  # 如果是全部步骤重新开始类方法
                        return getattr(ac, step['if_not_ready_action'][0])(**step['if_not_ready_action'][1])
                    elif step['if_not_ready_action'][0] == 'refresh':  # 如果只是刷新页面
                        ok_flag = getattr(ac, step['if_not_ready_action'][0])(**step['if_not_ready_action'][1])
                        if not ok_flag:  # 刷新页面不成功，跳过
                            print('refresh failed')
                            datas.append(data)
                            continue
                        else:  # 刷新成功
                            try:
                                data['detail'] = ac.scribe(**step['action'][1])
                            except Exception as e:
                                data['detail'] = {'error': traceback.format_exc()}
                            datas.append(data)
                            continue
                    else:  # 如果不是重新开始，也不是刷新页面，执行方法并跳过
                        getattr(ac, step['if_not_ready_action'][0])(**step['if_not_ready_action'][1])
                        datas.append(data)
                        continue
                else:  # 如果页面准备好
                    try:
                        data['detail'] = ac.scribe(**step['action'][1])
                    except Exception as e:
                        data['detail'] = {'error': traceback.format_exc()}
                    datas.append(data)
                    continue
            else:
                raise Exception('''action为scribe的step里，必须声明ready和if_not_ready_action,如：
                                    'ready': '[node-type="comment_list"] [comment_id]',
                                    'if_not_ready_action': (
                                    'refresh', {'url': url, 'ready_selector': '[node-type="comment_list"] [comment_id]'}),
                                    ''')


        else:  # 如果不是scribe action，直接调用
            # 判断是不是循环步骤
            if step['action'][0].startswith('loop'):
                for i, tag in enumerate(
                        driver.find_elements_by_css_selector(step['action'][1]['selector'])):  # 根据selector来确定循环次数
                    getattr(ac, step['action'][0].replace('loop_', ''))(**step['action'][1], index=i)
                    steps['steps_detail'] = steps['steps_detail'][index + 1:]
                    run_steps(steps, driver, {'datas': datas})
                break

            # 如果不是循环步骤则正常执行
            getattr(ac, step['action'][0])(**step['action'][1])

            # 验证是否成功
            if 'success_flag' in step and 'if_failed_action' in step:  # 如果有成功的标记success_flag
                if not wait_and_get_elements_until_ok(driver, step['success_flag']):
                    logger.debug('没有找到：' + step['success_flag'])
                    if step['if_failed_action'][0] == 'quit_and_again':  # 如果是全部步骤重新开始类方法
                        return getattr(ac, step['if_failed_action'][0])(**step['if_failed_action'][1])
                    elif step['if_failed_action'][0] == 'refresh':  # 如果只是刷新页面
                        ok_flag = getattr(ac, step['if_failed_action'][0])(**step['if_failed_action'][1])
                        if not ok_flag:  # 刷新页面不成功
                            print('refresh failed')
                            ac.quit_and_again()
                            continue
                    else:  # 如果不是重新开始，也不是刷新页面
                        getattr(ac, step['if_failed_action'][0])(**step['if_failed_action'][1])
            else:
                if step['action'][0] not in ac.self_check_ations:  # 如果不是自查action
                    raise Exception('''非scribe action的step里，如果不是自查action，必须声明success_flag和if_failed_action,如：
                                                        'success_flag': '[node-type="comment_list"] [comment_id]',
                                                        'if_failed_action': (
                                                        'refresh', {'url': url, 'ready_selector': '[node-type="comment_list"] [comment_id]'})
                                                        ''')
        # if index == 0 and step['action'][0]=='open': #如果是第一步，一般是打开网址，我们要关闭默认的初始空白网页
        #     driver.switch_to.window(driver.window_handles[0])
        #     close(driver)

    if not outer_driver:
        try:
            driver.quit()
        except:
            pass

        # 爬取没能打开的
        if [data for data in datas if not data['detail']]:
            scribe_less(datas)

        print(steps['name'] + '-------Done ... Quti driver')

    if container:
        if 'datas' in container:
            container['datas'].extend(datas)
        else:
            container['datas'] = datas
    return datas


def run_steps_list(*steps_list):
    '''
    多进程爬取，每个steps一个进程
    :param steps_list:
    :return:
    '''
    pool = Pool()
    asy_list = []
    datas_list = []
    for index, steps in enumerate(steps_list):
        datas_list.append({'name': steps['name']})
        # pool.apply_async(run_steps, args=(steps,),kwds={'container':datas_list[index]})
        asy_list.append(pool.apply_async(run_steps, args=(steps,)))
    print('Waiting for all subprocesses done...')
    pool.close()
    pool.join()
    print('All subprocesses done.')
    for index, asy in enumerate(asy_list):
        datas_list.append({'name': steps_list[index]['name'], 'datas': asy.get()})
    return datas_list




if __name__ == '__main__':
    from my_demo import utils

    help(utils)
