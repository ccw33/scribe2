# encoding:utf-8

from model.fangqiang import ip

import traceback
import random
import math
import pymongo
import re
from functools import reduce
import requests
import time
# from queue import Queue,Empty
import queue
import threading
import logging
from Utils import scribe_utils, thread_utils, git_utils, log_utils
from selenium.webdriver.common.keys import Keys
from selenium.common import exceptions
import os

Git = git_utils.Git()
Fanqiang = ip.Fanqiang()
logger = log_utils.Log("log/Pac", logging.DEBUG).logger

io_lock = threading.Lock()
lock = threading.Lock()

google_machine_test = False  # 没卵用，用浏览器内核肯定会认定为机器人，无论是谷歌还是火狐，所以一般设为False

file_path = 'E:/git-repository/blog/ccw33.github.io/file/http_surge.pac'
file_path_chrome = 'E:/git-repository/blog/ccw33.github.io/file/OmegaProfile_auto_switch.pac'
file_path_chrome_socks = 'E:/git-repository/blog/ccw33.github.io/file/OmegaProfile_socks.pac'

is_ok_at_least_one = False


def generate_replace_text(ip_fanqiang_list):
    new_proxy_list = ["%s%s = %s,%s\n" % (
        ip['proxy_type'], str(index), ip['proxy_type'] if ip['proxy_type'] == 'http' else 'socks5',
        ip['ip_with_port'].replace(':', ',')) for index, ip in enumerate(ip_fanqiang_list)]
    new_proxy_group = [s.split('=')[0] for s in new_proxy_list]
    return (reduce(lambda v1, v2: v1 + v2, new_proxy_list), reduce(lambda v1, v2: v1 + ',' + v2, new_proxy_group) + ',')


# 修改pac文件并commit到github
def update_surge_pac():
    '''
    更新surge用的pac
    :return:
    '''
    ip_fanqiang_list = list(Fanqiang.query())
    if len(ip_fanqiang_list) < 7:
        pass
    else:
        start = math.floor(random.random() * len(ip_fanqiang_list))
        ip_fanqiang_list = ip_fanqiang_list[start:start + 5]

    # 读取文件
    old_text = ''
    new_text = ''
    with open(file_path, 'r', encoding='utf-8') as fr:
        try:
            old_text = fr.read()
            proxy_replace_text, group_replace_text = generate_replace_text(ip_fanqiang_list)
            new_text = old_text.replace(re.findall(r'\[Proxy\]\n((?:.+\n)+)Socks1',
                                                   old_text)[0], proxy_replace_text)
            new_text = new_text.replace(
                re.findall(
                    r'\[Proxy Group\]\nProxy = url-test, (.+) url = http://www.google.com/generate_204\nSocks_Proxy',
                    new_text)[0], group_replace_text)
        finally:
            fr.close()

    # 修改文件
    with open(file_path, 'w', encoding='utf-8') as fw:
        try:
            fw.write(new_text)
        finally:
            fw.close()
    Git.git_push(file_path)


def update_chrome_pac():
    '''
    检查mongodb里面的ip——port,调用update_chrome_pac_by_gatherproxy(),更新到数据库,并更新chrome用的pac
    :return:
    '''

    ip_fanqiang_list = list(Fanqiang.query())
    if len(ip_fanqiang_list) < 7:
        pass
    else:
        start = math.floor(random.random() * len(ip_fanqiang_list))
        ip_fanqiang_list = ip_fanqiang_list[start:]

    q = queue.Queue()
    for ip_dict in ip_fanqiang_list:
        q.put(ip_dict)
    for i in range(20) if not google_machine_test else range(5):
        t = threading.Thread(target=get_useful_fanqiang_ip_mongo, args=(q,))
        t.start()
    q.join()


def update_chrome_pac_by_gatherproxy():
    '''
    从proxies.txt里面检测ip_port，最后更新chrome用的pac
    :return:
    '''
    merge_proxy()
    with open('file/proxy_file/proxies.txt', 'r') as fr:
        try:
            ip_port_list = fr.read().split('\n')
        except Exception:
            logger.error(traceback.format_exc())
            return
        finally:
            fr.close()

    q = queue.Queue()
    ip_port_list = list(set(ip_port_list))  # 去重
    for ip_with_port in ip_port_list:
        ip_dict = {
            'ip_with_port': ip_with_port,
            'proxy_type': 'socks5',
        }
        q.put(ip_dict)
    for i in range(20) if not google_machine_test else range(5):
        t = threading.Thread(target=get_useful_fanqiang_ip_gatherproxy, args=(q,))
        t.start()
    q.join()
    # 跑完，吧proxy文件删了
    os.remove('file/proxy_file/proxies.txt')


def get_useful_fanqiang_ip_mongo(q):
    while not q.empty():
        driver = None

        try:
            ip_dict = q.get()
            proxy_type = ip_dict['proxy_type']
            ip_with_port = ip_dict['ip_with_port']
            logger.debug("开始测试" + ip_with_port)
            resp = requests.get('https://www.baidu.com/', headers=scribe_utils.headers,
                                proxies={'http': proxy_type + (
                                    'h' if proxy_type == 'socks5' else '') + '://' + ip_with_port,
                                         'https': proxy_type + (
                                             'h' if proxy_type == 'socks5' else '') + '://' + ip_with_port},
                                timeout=10)

            if re.findall(r'robots', resp.text):
                raise scribe_utils.RobotException()

            if not google_machine_test:
                logger.debug(ip_with_port + "可用")
                modify_chrome_pac_file_and_push(ip_with_port)
            else:
                driver = scribe_utils.ready(ip_dict)
                driver.set_page_load_timeout(60)
                driver.get('http://www.google.com/')
                tags = scribe_utils.wait_and_get_elements_until_ok(driver, '#lst-ib')
                tags[0].send_keys('kkk')
                tags[0].send_keys(Keys.ENTER)
                if re.findall('我们的系统检测到您的计算机网络中存在异常流量', driver.page_source) or \
                        re.findall('Our systems have detected unusual traffic from your computer',
                                   driver.page_source):  # 证明需要机器人验证
                    driver.quit()
                    # ip_fanqiang_list.remove(ip_dict)
                    Fanqiang.delete({'ip_with_port': ip_with_port})
                    continue
                else:  # 不需要验证，可以使用
                    logger.debug(ip_with_port + "可用")
                    modify_chrome_pac_file_and_push(ip_with_port)

        except (scribe_utils.RobotException,\
               requests.exceptions.ConnectionError, requests.ReadTimeout, requests.exceptions.SSLError) as e:
            try:
                lock.acquire()
                Fanqiang.delete({'ip_with_port': ip_with_port})
            except Exception as e:
                logger.info(e)
            finally:
                lock.release()
            continue
        except exceptions.TimeoutException as e:  # 浏览器访问超时
            driver.quit()
            try:
                lock.acquire()
                Fanqiang.delete({'ip_with_port': ip_with_port})
            except Exception as e:
                logger.info(e)
            finally:
                lock.release()
            continue
        except Exception as e:
            try:
                lock.acquire()
                Fanqiang.delete({'ip_with_port': ip_with_port})
            except Exception as e:
                logger.info(e)
            finally:
                lock.release()
            if driver:
                driver.quit()
            if re.findall(r'NoneType', str(e)):
                continue
            if not isinstance(e, ValueError):
                logger.warning(traceback.format_exc())
            continue
        finally:
            q.task_done()


def get_useful_fanqiang_ip_gatherproxy(q):
    while not q.empty():
        driver = None
        try:
            ip_dict = q.get()
            proxy_type = ip_dict['proxy_type']
            ip_with_port = ip_dict['ip_with_port']
            logger.debug("开始测试" + ip_with_port)
            resp = requests.get('https://www.baidu.com/', headers=scribe_utils.headers,
                                proxies={'http': proxy_type + (
                                    'h' if proxy_type == 'socks5' else '') + '://' + ip_with_port,
                                         'https': proxy_type + (
                                             'h' if proxy_type == 'socks5' else '') + '://' + ip_with_port},
                                timeout=10)
            if re.findall(r'robots', resp.text):
                raise scribe_utils.RobotException()

            use_time = resp.elapsed.microseconds / math.pow(10, 6)
            if not google_machine_test:
                logger.debug(ip_with_port + "可用")
                try:
                    lock.acquire()
                    Fanqiang.save({'proxy_type': proxy_type, 'ip_with_port': ip_with_port,
                                   'time': use_time, 'location': scribe_utils.get_location(ip_with_port.split(':')[0])})
                except Exception as e:
                    logger.info(e)
                finally:
                    lock.release()

                    modify_chrome_pac_file_and_push(ip_with_port)

            else:
                driver = scribe_utils.ready(ip_dict)
                driver.set_page_load_timeout(60)
                driver.get('http://www.google.com/')
                tags = scribe_utils.wait_and_get_elements_until_ok(driver, '#lst-ib')
                tags[0].send_keys('kkk')
                tags[0].send_keys(Keys.ENTER)
                if re.findall('我们的系统检测到您的计算机网络中存在异常流量', driver.page_source) or \
                        re.findall('Our systems have detected unusual traffic from your computer',
                                   driver.page_source):  # 证明需要机器人验证
                    driver.quit()
                    continue
                else:  # 不需要验证，可以使用
                    logger.debug(ip_with_port + "可用")
                    # 添加到数据库
                    try:
                        lock.acquire()
                        Fanqiang.save({'proxy_type': proxy_type, 'ip_with_port': ip_with_port,
                                       'time': use_time,
                                       'location': scribe_utils.get_location(ip_with_port.split(':')[0])})
                    except Exception as e:
                        logger.info(e)
                    finally:
                        lock.release()
                    modify_chrome_pac_file_and_push(ip_with_port)
        except (requests.exceptions.ConnectionError, requests.ReadTimeout\
               , requests.exceptions.SSLError, scribe_utils.RobotException) as e:
            try:
                lock.acquire()
                Fanqiang.delete({'ip_with_port': ip_with_port})
            except Exception as e:
                logger.info(e)
            finally:
                lock.release()
            continue
        except exceptions.TimeoutException as e:  # 浏览器访问超时
            driver.quit()
            try:
                lock.acquire()
                Fanqiang.delete({'ip_with_port': ip_with_port})
            except Exception as e:
                logger.info(e)
            finally:
                lock.release()
            continue
        except Exception as e:
            if driver:
                driver.quit()
            if re.findall(r'NoneType', str(e)):
                continue
            if not isinstance(e, ValueError):
                logger.warning(traceback.format_exc())
            continue
        finally:
            q.task_done()


def modify_chrome_pac_file_and_push(ip_with_port):
    '''
    更新pac文件并提交（加锁）
    :param ip_with_port:
    :return:
    '''
    try:
        io_lock.acquire()
        global is_ok_at_least_one
        if is_ok_at_least_one:
            return
        modify_chrome_file(file_path_chrome, ip_with_port)
        modify_chrome_file(file_path_chrome_socks, ip_with_port)

        Git.git_push(file_path_chrome)
        Git.git_push(file_path_chrome_socks)

        is_ok_at_least_one = True
        return

    except Exception:
        logger.error(traceback.format_exc())
    finally:
        io_lock.release()


def modify_chrome_file(file_path, ip_with_port):
    # 替换ip和port
    new_text = ''
    with open(file_path,
              'r', encoding='utf-8') as fr:
        try:
            old_text = fr.read()
            new_text = old_text.replace(re.findall(r'(?:SOCKS |SOCKS5 )(\d+\.\d+\.\d+\.\d+:\d+)', old_text)[0],
                                        ip_with_port)
            new_text = new_text.replace(re.findall(r'(?:SOCKS |SOCKS5 )(\d+\.\d+\.\d+\.\d+:\d+)', old_text)[1],
                                        ip_with_port)
        finally:
            fr.close()

    with open(file_path,
              'w', encoding='utf-8') as fw:
        try:
            fw.write(new_text)
        finally:
            fw.close()


def merge_proxy():
    '''
    合并proxy文件
    :return:
    '''

    for root, dirs, files in os.walk("file/proxy_file"):
        logger.debug(root)  # 当前目录路径
        logger.debug(dirs)  # 当前路径下所有子目录
        logger.debug(files)  # 当前路径下所有非目录子文件
        with open(root + '/proxies.txt',
                  'a+', encoding='utf-8') as fw:
            try:
                all_ip_port_list = []
                for file_name in files:
                    if file_name == 'proxies.txt':
                        continue
                    with open(root + "/" + file_name,
                              'r', encoding='utf-8') as fr:
                        try:
                            all_ip_port_list.extend(fr.readlines())
                        finally:
                            fr.close()
                    os.remove(root + "/" + file_name)
                all_ip_port_list = list(set(all_ip_port_list))  # 去重
                fw.writelines(all_ip_port_list)
            finally:
                fw.close()


def test():
    # 初始化数据库
    client = pymongo.MongoClient('localhost', 27017)
    ips = client['ips']
    ipsData = ips['ipsData']
    ipsFanqiangData = ips['ipsFanqiangData']
    old_data = list(ipsFanqiangData.find())[-1]
    ip_fanqiang_list = old_data['ip_fanqiang_list']

    lock = threading.Lock()
    ip_port_dict_list = []

    def get_useful_ip(queue, type, fanqiang=True):
        while not queue.empty():
            try:
                ip_port = queue.get(timeout=1)
                resp = requests.get('http://www.google.com/' if fanqiang else 'http://www.baidu.com',
                                    headers=scribe_utils.headers,
                                    proxies={'http': type + (
                                        'h' if type == 'socks5' else '') + '://' + ip_port,
                                             'https': type + (
                                                 'h' if type == 'socks5' else '') + '://' + ip_port},
                                    timeout=10)
                use_time = resp.elapsed.microseconds / math.pow(10, 6)
                try:
                    lock.acquire()
                    ip_port_dict_list.append(
                        {'proxy_type': type, 'ip_with_port': ip_port,
                         'time': use_time, 'location': scribe_utils.get_location(ip_port.split(':')[0])})
                finally:
                    lock.release()
            except Exception as e:
                logger.info(e)
            finally:
                queue.task_done()

    with open('file/proxies.txt',
              'r', encoding='utf-8') as fr:
        try:
            all_ip_port_list = fr.read().split('\n')
        finally:
            fr.close()
    q = queue.Queue()
    for ip_port in all_ip_port_list:
        q.put(ip_port)
    for i in range(20):
        t = threading.Thread(target=get_useful_ip, args=(q, 'socks5', True))
        t.start()
    q.join()

    # ip_fanqiang_list = sorted(ip_fanqiang_list, key=lambda ip: ip['time'])

    # 更新数据库
    ipsFanqiangData.update_one({'_id': old_data['_id']}, {'$set': {
        'updated_at': time.strftime('%Y-%m-%d'),
        'ip_fanqiang_list': ip_fanqiang_list,
        'isFanqiang': True
    }}, upsert=True)
    client.close()


if __name__ == "__main__":
    # while True:
    #     update_surge_pac()
    #     update_chrome_pac()
    #     update_chrome_pac_by_gatherproxy()
    #     logger.debug('DONE!!!')
    #     time.sleep(3600*6)

    update_chrome_pac()
    update_chrome_pac_by_gatherproxy()
    update_surge_pac()
    logger.debug('DONE!!!')

    # ip_fanqiang_list = list(Fanqiang.query())
    # ip_fanqiang_list = [ip_port_dict['ip_with_port'] for ip_port_dict in ip_fanqiang_list if ip_port_dict['ip_with_port'].split(':')[1]]
