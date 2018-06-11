# coding:utf-8
'''
爬去高匿代理ip
http://www.xicidaili.com/nn/
'''
import logging

import requests
from selenium.common import  exceptions
from bs4 import BeautifulSoup
import random
import time, datetime
import re
import math
import queue
# from fake_useragent import UserAgent
# ua = UserAgent()
import threading
from multiprocessing import Pool, cpu_count
import traceback
import pymongo

from utils import utils
from utils.utils import get_ip_list,get_useful_ip,headers,logger,system,HashableDict
# from my_demo.modify_file_and_commit import update_pac_and_push



# system = 'windows'

# # 日志
# logger = logging.getLogger(__name__)
# logger.setLevel(level=logging.INFO)
# # 定义一个RotatingFileHandler，最多备份3个日志文件，每个日志文件最大1K
# # rHandler = RotatingFileHandler("log/weibo", maxBytes=1 * 1024, backupCount=3,encoding='utf-8')
# rHandler = logging.FileHandler("../log/weibo" if system == 'linux' else "F:/scribe/log/weibo", encoding='utf-8')
# rHandler.setLevel(logging.WARNING)
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# rHandler.setFormatter(formatter)
# logger.addHandler(rHandler)
#
# console = logging.StreamHandler()
# console.setLevel(logging.DEBUG)
# console.setFormatter(formatter)
# logger.addHandler(console)


def get_random_ip_proxy(ip_list):
    '''
    获取随机的ip代理
    :param ip_list:
    :return:
    '''
    proxy_ip = random.choice(ip_list)
    proxies = {'http': proxy_ip['proxy_type'] +('h' if  proxy_ip['proxy_type']=='socks5' else '') + '://' + proxy_ip['ip_with_port'],
               'https': proxy_ip['proxy_type']+('h' if  proxy_ip['proxy_type']=='socks5' else '') + '://' + proxy_ip['ip_with_port']}
    return proxies




queueLock = threading.Lock()

exitFlag = False




def queue_threads_worker(q,func):
    while not exitFlag:
        try:
            data = q.get(timeout=2)#获取任务（其实就是需要处理的数据/传递给func的参数）
            func(*data[0],**data[1])
        except queue.Empty:#如果过了2秒还没有获得新任务，回去看一下是否已经all_done
            continue
        q.task_done()#任务完成，告诉q一声






def scribe_ip_with_soup(soup, selector, filter=None, ip_list=[], fanqiang_ip_list=[],type_get='request'):
    has_socks4 = False
    trs = soup.select(selector['trs'])
    if filter:
        trs = [tr for tr in trs if filter(tr)]
    threads = []
    for tr in trs:
        try:
            if 'proxy_type' in selector:
                if selector['proxy_type'] in ['http', 'Http', 'https', 'Https', 'socks4', 'Socks4', 'socks5',
                                              'Socks5']:
                    proxy_type = selector['proxy_type'].lower()
                else:
                    if len(tr.select(selector['proxy_type'])) == 0:
                        logger.debug('没有找到proxy_type')
                        continue
                    logger.debug('找到的proxy_type: '+tr.select(selector['proxy_type'])[0].text.strip().lower())
                    proxy_type = re.search(r'(http|https|socks4|socks5|sock4|sock5)', tr.select(selector['proxy_type'])[0].text.strip().lower()).group()
                    if proxy_type == 'sock5':
                        proxy_type = 'socks5'
                    if proxy_type == 'sock4':
                        proxy_type = 'socks4'
            else:
                logger.warning('无法根据selector找到proxy_type：' + str(selector))
            if proxy_type == 'socks4':
                logger.debug('socks4跳过')
                has_socks4 = True
                continue

            if 'ip' in selector and 'port' in selector:
                if len(tr.select(selector['ip'])) == 0 or  len(tr.select(selector['port']))==0:
                    logger.debug('没有找到ip或port')
                    continue
                logger.debug('找到的ip： '+ tr.select(selector['ip'])[0].text.strip())
                logger.debug('找到的port： '+ tr.select(selector['port'])[0].text.strip())
                ip = re.search(r'((?:\d+?\.){3}\d{1,3})', tr.select(selector['ip'])[0].text.strip()).group()
                port = re.search(r'((?!\.)\d+(?!\.))',tr.select(selector['port'])[0].text.strip()).group()
                ip_with_port = ip + ':' + port
            elif 'ip_with_port' in selector:
                if len(tr.select(selector['ip_with_port'])) == 0:
                    logger.debug('没有找到ip_with_port')
                    continue
                ip_with_port_str = tr.select(selector['ip_with_port'])[0].text.strip()
                ip = re.search(r'((?:\d+?\.){3}\d{1,3})', ip_with_port_str).group()
                port = re.search(r'((?!\.)\d{4,5}(?!\.))', ip_with_port_str).group()
                ip_with_port = ip + ':' + port
                logger.debug('找到的ip_with_port：'+ip_with_port)
            else:
                logger.warning('无法根据selector找到ip和port：' + str(selector))
        except AttributeError as e:
            logger.debug(e)
            continue
        except Exception as e:
            logger.warning(traceback.format_exc())
            continue

        if not type_get == 'request':  # yong　webdriver来验证，不能多线程，开太多浏览器容易死机
            get_useful_ip(ip_with_port, proxy_type,ip_list, fanqiang_ip_list,type_get=type_get)
            threads=True
            continue
        # 开启一个线程收集有效的链接
        thread = threading.Thread(target=get_useful_ip,
                                  args=(ip_with_port,proxy_type, ip_list, fanqiang_ip_list),
                                  kwargs={'type_get': type_get})
        thread.start()
        threads.append(thread)
    if not threads and not has_socks4:
        logger.warning('没有找到任何ip_port'+str(selector))
    # 不join也行不知道为什么
    if threads:
        for thread in threads:
            thread.join()
    logger.info('ip_list:' + str(ip_list))
    logger.info('fanqiang_ip_list:' + str(fanqiang_ip_list))
    return ip_list, fanqiang_ip_list

    # trs = soup.select(selector)
    # if filter:
    #     trs = [tr for tr in trs if filter(tr)]
    # threads = []
    #
    # for tr in trs:
    #     ip = re.search(r'(?:>)(\d+\.){3}\d{1,3}(?:<)', str(tr), re.M)
    #     port = re.search(r'(?:>)\d{3,5}(?:<)', str(tr), re.M)
    #     if ip and port:
    #         ip = re.search(r'(\d+\.){3}\d{1,3}', ip.group())
    #         port = re.search(r'\d+', port.group())
    #         ip_with_port = ip.group() + ':' + port.group()
    #         if not type_get == 'request':#yong　webdriver来验证，不能多线程，开太多浏览器容易死机
    #             get_useful_ip(ip_with_port, ip_list, fanqiang_ip_list,type_get = type_get)
    #             continue
    #         # 开启一个线程收集有效的链接
    #         thread = threading.Thread(target=get_useful_ip,
    #                                   args=(ip_with_port, ip_list, fanqiang_ip_list),
    #                                   kwargs={'type_get':type_get})
    #         thread.start()
    #         threads.append(thread)
    # # 不join也行不知道为什么
    # # if threads:
    # #     for thread in threads:
    # #         thread.join()
    # logger.info('ip_list:' + str(ip_list))
    # logger.info('fanqiang_ip_list:' + str(fanqiang_ip_list))
    # return ip_list, fanqiang_ip_list


def scribe_ip(url, selector, proxies_ip_list, filter=None, ):
    '''
    获取代理ip,多线程验证
    :param url:
    :return:
    '''
    ip_list = []
    fanqiang_ip_list = []
    try:
        proxies = get_random_ip_proxy(proxies_ip_list)
        logger.debug(url+'         '+str(proxies))
        resp = requests.get(url, headers=headers, proxies=proxies, timeout=10)
        if resp.status_code != 200:
            # 链接失败也重新来
            logger.debug(resp.status_code)
            return scribe_ip(url, selector, proxies_ip_list, filter, )
    except Exception as e:
        logger.debug(e)
        # 如果ip被封了，马上重试另一个
        return scribe_ip(url, selector, proxies_ip_list, filter, )

    soup = BeautifulSoup(resp.text, 'lxml')
    return scribe_ip_with_soup(soup, selector, filter=filter, ip_list=ip_list,
                               fanqiang_ip_list=fanqiang_ip_list)


def scribe_ip_in_webdriver(url, selector, proxies_ip_list, ok_tag,next_pagination=None, filter=None, page_size=10):
    while True:
        proxy = random.choice(proxies_ip_list)
        logger.debug(url+'         '+ str(proxy))
        driver = utils.ready(proxy)
        try:
            driver.get(url)
            break
        except Exception as e:
            driver.quit()
            logger.debug(e)

    times = 0
    ip_list, fanqiang_ip_list = [], []
    firsr_server = ''
    while times <= page_size:
        tags = utils.wait_and_get_elements_until_ok(driver, ok_tag)
        if not tags:
            logger.warning('没有找到'+ok_tag)
            driver.quit()
            return scribe_ip_in_webdriver(url,selector,proxies_ip_list,ok_tag,next_pagination,filter,page_size)
        soup = BeautifulSoup(driver.page_source, 'lxml')
        temp_first_server = soup.select(selector['trs'])[0]
        if temp_first_server.text == firsr_server:  # 如果翻页了，第一个server还是没变，证明已经翻到最后页，退出循环
            break
        else:
            firsr_server = temp_first_server
        new_ip_list, new_fanqiang_ip_list = scribe_ip_with_soup(soup, selector, filter=filter)
        ip_list.extend(new_ip_list)
        fanqiang_ip_list.extend(new_fanqiang_ip_list)
        if next_pagination:
            try:
                driver.find_element_by_css_selector(next_pagination).click()
                times = times + 1
            except exceptions.NoSuchElementException as e:
                logger.debug('NoSuchElementException:'+ str(e))
                break
        else:
            break
    driver.quit()
    return ip_list, fanqiang_ip_list


def kuaidaili_filter(tag):  # filter要定义在module层才能被multipleprocess pickle
    new_tags = tag.select('td:nth-of-type(3)')
    if new_tags:
        return new_tags[0].text == '高匿名'
    return False


def socks_proxy5_filter(tag):
    new_tags = tag.select('td:nth-of-type(5)')
    if new_tags:
        return new_tags[0].text == 'Socks5'
    return False


def socks_proxy4_filter(tag):
    new_tags = tag.select('td:nth-of-type(5)')
    if new_tags:
        return new_tags[0].text == 'Socks4'
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
        # requests

        {'main': 'http://www.gatherproxy.com/zh/sockslist', 'url': ['http://www.gatherproxy.com/zh/sockslist'],
         'selector': {'trs': 'tr', 'ip': 'td:nth-of-type(2)', 'port': 'td:nth-of-type(3)',
                      'proxy_type': 'socks5'},
         'GFW':True},

        # {'main': 'http://www.66ip.cn/areaindex_35/{}.html',
        #  'url': ['http://www.66ip.cn/areaindex_35/{}.html'.format(i) for i in range(1, 10)],
        #  'selector': {'trs': 'tr', 'ip': 'td:nth-of-type(1)','port':'td:nth-of-type(2)',
        #                'proxy_type': 'http'} ,
        #  'GFW': False},


        # webdriver

        # {'main': 'https://www.socks-proxy.net/', 'url': ['https://www.socks-proxy.net/'],
        #  'selector': {'trs': 'tbody > tr', 'ip': 'td:nth-of-type(1)', 'port': 'td:nth-of-type(2)',
        #               'proxy_type': 'td:nth-of-type(5)'},
        #  'GFW': False,
        #  'ok_tag':'.section-heading',
        #  'next_pagination':'#proxylisttable_next a',
        #  'page_size':4},
        #
        # {'main': 'http://spys.one/socks/', 'url': ['http://spys.one/socks/'],
        #  'selector': {'trs': 'tbody > tr', 'ip_with_port':'td:nth-of-type(1) font:nth-of-type(2)',
        #               'proxy_type': 'td:nth-of-type(2)'},
        #  'GFW': True,
        #  'ok_tag': 'tr.spy1xx'},


    ]

    for web in webs:
        # p = Pool(cpu_count()-1)#预留一个cpu爬虫效率更高，可能是因为主进程本来就占用一个cpu的原因
        p = Pool()  # 预留一个cpu爬虫效率更高，可能是因为主进程本来就占用一个cpu的原因
        if 'ok_tag' in web:
            for url in web['url']:
                logger.info(url)
                asy_list.append(p.apply_async(scribe_ip_in_webdriver,
                                              args=(url, web['selector'], get_ip_list(web['GFW']), web['ok_tag']),
                                              kwds={'filter': web['filter'] if 'filter' in web else None,
                                                    'next_pagination': web[
                                                        'next_pagination'] if 'next_pagination' in web else None,
                                                    'page_size': web['page_size'] if 'page_size' in web else 10,
                                                    }))
        else:
            for url in web['url']:
                logger.info(url)
                asy_list.append(p.apply_async(scribe_ip, args=(url, web['selector'], get_ip_list(web['GFW']),),
                                              kwds={'filter': web['filter'] if 'filter' in web else None}))
    logger.info('Waiting for all subprocesses done...')
    p.close()
    p.join()
    logger.info('All subprocesses done.')
    for asy in asy_list:  # 收集爬到的ip
        ip_list = [*ip_list, *asy.get()[0]]
        ip_fanqiang_list = [*ip_fanqiang_list, *asy.get()[1]]

    # 不使用多进程
    # ip_list = [*ip_list, *scribe_ip(url,web[2],proxies_ip_list)]
    # time.sleep(random.choice(range(1, 2)))

    # 初始化数据库
    client = pymongo.MongoClient('localhost', 27017)
    ips = client['ips']
    ipsData = ips['ipsData']
    ipsFanqiangData = ips['ipsFanqiangData']

    #刷新ip_list
    if ip_list:
        # ip_list = list(set([HashableDict(ip) for ip in ip_list]))  # 去重
        # ipsData.insert_one({'date': time.strftime('%Y-%m-%d'),
        #                     'ip_list': ip_list,
        #                     'isFanqiang': False})
        # 获取旧数据
        try:
            old_data = list(ipsData.find())[-1]
            old_ip_list = old_data['ip_list']
        except:
            old_data = {'_id':'1'}
            old_ip_list = []
        old_ip_list.extend(ip_list)
        ip_list = list(set([HashableDict(ip) for ip in old_ip_list]))  # 去重
        #如果数据过多（超过500），去掉没用的
        useful_ip_list = []
        if len(ip_list) > 1000:
            q = queue.Queue()

            for i in range(20):
                t = threading.Thread(target=queue_threads_worker,
                                     args=(q, get_useful_ip))
                t.start()

            for ip in ip_list:
                q.put(((ip['ip_with_port'], ip['proxy_type'], useful_ip_list, None), {}))

            q.join()
            exitFlag = True


        ipsData.update_one({'_id': old_data['_id']}, {'$set': {
            'updated_at': time.strftime('%Y-%m-%d'),
            'ip_list': useful_ip_list if useful_ip_list else ip_list,
            'isFanqiang': False
        }}, upsert=True)

    # 刷新翻墙list
    # ip_fanqiang_list = list(set([HashableDict(ip) for ip in ip_fanqiang_list]))  # 去重
    # ipsFanqiangData.insert_one({'date': time.strftime('%Y-%m-%d'),
    #                             'ip_fanqiang_list': ip_fanqiang_list,
    #                             'isFanqiang': True})
    try:
        old_data = list(ipsFanqiangData.find())[-1]
        old_ip_fanqiang_list = old_data['ip_fanqiang_list']
    except:
        old_data = {'_id':'1'}
        old_ip_fanqiang_list = []
    old_ip_fanqiang_list.extend(ip_fanqiang_list)
    ip_fanqiang_list = list(set([HashableDict(ip) for ip in old_ip_fanqiang_list]))  # 去重

    # 如果数量过多（多于50）把不能翻墙的去掉
    useful_fanqiang_list = []
    if len(ip_fanqiang_list)>100:
        threads = []
        for ip_with_port_dict in ip_fanqiang_list:
            # get_useful_ip(ip_with_port_dict['ip_with_port'], None, useful_fanqiang_list,ip_with_port_dict['proxy_type'],type_get='driver')
            thread = threading.Thread(target=get_useful_ip,
                                      args=(ip_with_port_dict['ip_with_port'],ip_with_port_dict['proxy_type'], None, useful_fanqiang_list))
            thread.start()
            threads.append(thread)
        for thread in threads:
            thread.join()

    ipsFanqiangData.update_one({'_id': old_data['_id']}, {'$set': {
        'updated_at': time.strftime('%Y-%m-%d'),
        'ip_fanqiang_list': useful_fanqiang_list if useful_fanqiang_list else ip_fanqiang_list,
        'isFanqiang': True
    }}, upsert=True)

    client.close()




if __name__ == '__main__':
    start = datetime.datetime.now()
    write_ip_list()
    logger.info('总共花费时间：' + str((datetime.datetime.now() - start).seconds) + '秒')
    #修改pac文件并commit到github
    # update_pac_and_push()



    # client = pymongo.MongoClient('localhost', 27017)
    # ips = client['ips']
    # ipsData = ips['ipsData']
    # ipsFanqiangData = ips['ipsFanqiangData']

    # # 获取旧数据
    # try:
    #     old_data = list(ipsData.find())[-1]
    #     old_ip_list = old_data['ip_list']
    # except:
    #     old_data = {'_id': '1'}
    #     old_ip_list = []
    # ip_list = list(set([HashableDict(ip) for ip in old_ip_list]))  # 去重
    # # 如果数据过多（超过500），去掉没用的
    # useful_ip_list = []
    # if len(ip_list) > 500:
    #     q = queue.Queue()
    #
    #     for i in range(20):
    #         t = threading.Thread(target=queue_threads_worker,
    #                              args=(q, get_useful_ip))
    #         t.start()
    #
    #     for ip in ip_list:
    #         q.put(((ip['ip_with_port'],ip['proxy_type'],useful_ip_list,None),{}))
    #
    #     q.join()
    #     exitFlag=True

    # try:
    #     old_data = list(ipsFanqiangData.find())[-1]
    #     old_ip_fanqiang_list = old_data['ip_fanqiang_list']
    # except:
    #     old_data = {'_id': '1'}
    #     old_ip_fanqiang_list = []
    # # old_ip_fanqiang_list.extend(ip_fanqiang_list)
    # ip_fanqiang_list = list(set([HashableDict(ip) for ip in old_ip_fanqiang_list]))  # 去重
    #
    # # 如果数量过多（多于50）把不能翻墙的去掉
    # useful_fanqiang_list = []
    # if len(ip_fanqiang_list) > 50:
    #     threads = []
    #     for ip_with_port_dict in ip_fanqiang_list:
    #         # get_useful_ip(ip_with_port_dict['ip_with_port'], None, useful_fanqiang_list,ip_with_port_dict['proxy_type'],type_get='driver')
    #         thread = threading.Thread(target=get_useful_ip,
    #                                   args=(ip_with_port_dict['ip_with_port'], ip_with_port_dict['proxy_type'], None,
    #                                         useful_fanqiang_list))
    #         thread.start()
    #         threads.append(thread)
    #     for thread in threads:
    #         thread.join()
    #
    # ipsFanqiangData.update_one({'_id': old_data['_id']}, {'$set': {
    #     'updated_at': time.strftime('%Y-%m-%d'),
    #     'ip_fanqiang_list': useful_fanqiang_list if useful_fanqiang_list else ip_fanqiang_list,
    #     'isFanqiang': True
    # }}, upsert=True)

    # a =1