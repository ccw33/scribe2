# coding:utf-8
import datetime
import requests
from bs4 import BeautifulSoup
import re
import random
import time
from my_demo import ip_scriber
from selenium import webdriver
from selenium.webdriver.common.proxy import Proxy
from selenium.common import exceptions
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from multiprocessing import Pool,Manager
import threading
import logging
from logging.handlers import RotatingFileHandler
import traceback
import threading
import multiprocessing
import pymongo

'''
爬微博脚本
'''
import sys

sys.setrecursionlimit(1000000)  # 调整递归深度

# 日志
logger = logging.getLogger(__name__)
logger.setLevel(level=logging.DEBUG)
# 定义一个RotatingFileHandler，最多备份3个日志文件，每个日志文件最大1K
# rHandler = RotatingFileHandler("../log/weibo", maxBytes=1 * 1024, backupCount=3,encoding='utf-8')
rHandler = logging.FileHandler("../log/weibo", encoding='utf-8')
rHandler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
rHandler.setFormatter(formatter)
logger.addHandler(rHandler)

console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
console.setFormatter(formatter)
logger.addHandler(console)

# 初始化数据库
client = pymongo.MongoClient('localhost', 27017)
weibo = client['weibo']
indexData = weibo['indexData']
detailData = weibo['detailData']

# 初始化配置
headers = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1'}
ip_list = ip_scriber.get_ip_list()
system = 'windows'
browser = 'firefox'
each_driver_scribe_num = 5
mode = 'product'  # mode: 如果为‘debug’显示浏览器，如果为‘product’则不像是浏览器


class Cache(object):
    cache_datas=[]

def ready(proxy_ip_port=None):
    '''

    :param proxy_ip_port:
    :return:
    '''
    if system == 'windows':
        executable_path = 'D:/geckodriver/geckodriver.exe'
    elif system == 'linux':
        executable_path = '../temp_file/geckodriver'
    else:
        logger.warning('没有这个系统：%s,暂时默认为windows' % system)
        executable_path = 'D:/geckodriver/geckodriver.exe'

    fireFoxOptions = webdriver.FirefoxOptions()
    fireFoxOptions.set_headless()
    # fireFoxOptions.add_argument("--proxy-server=http://{}".format(random.choice(ip_list)))
    # driver = webdriver.Firefox( executable_path='temp_file/geckodriver',options=fireFoxOptions)
    if proxy_ip_port:
        proxy = Proxy({'httpProxy': proxy_ip_port})
    else:
        proxy = None
    if mode == 'product':
        driver = webdriver.Firefox(executable_path=executable_path, options=fireFoxOptions,
                                   proxy=proxy)
    elif mode == 'debug':
        if system == 'windows':
            binary_path = 'C:/Program Files (x86)/Mozilla Firefox/firefox.exe'
        else:
            binary_path = '/usr/bin/firefox'
        binary = FirefoxBinary(binary_path)
        driver = webdriver.Firefox(firefox_binary=binary, executable_path=executable_path, proxy=proxy)
    else:
        raise Exception('ready方法的参数里面没有这种mode：%s' % mode)
    driver.implicitly_wait(10)  # 设置寻找（包括异步加载的）element所等待的时间（如果不设置，则异步加载的element有可能会找不到）
    return driver


def close(driver):
    if len(driver.window_handles) > 1:
        driver.close()
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



def scroll_and_scribe(driver, index, datas):
    '''
    下拉异步加载，爬取新加载出来的数据
    :param driver: 原来使用的driver
    :param index: 继续爬取所使用的下表
    :param datas:  收集数据的容器
    :return:
    '''
    if index != 0:
        driver.execute_script('window.scrollTo(0,document.body.scrollHeight)')
        try:
            WebDriverWait(driver, 15).until(
                lambda driver: len(driver.find_elements_by_css_selector('.pt_ul:nth-of-type(1) > div')) > index,
                message="等待了15秒也没有加载出新的'.pt_ul:nth-of-type(1) > div'   %s" % driver.current_url)
        except Exception as e:
            logger.debug(e)
            # # 点击热门
            # re_men = wait_and_get_elements_until_ok(driver, '[href="/?category=0"]')[0]
            # re_men.click()
            return
    soup = BeautifulSoup(driver.page_source, 'lxml')
    # wait_and_get_elements_until_ok(driver,'.pt_ul:nth-of-type(1) > div')
    topics = soup.select('.pt_ul')[0].select('> div')
    new_index = len(topics)
    if new_index <= index:
        # scribe_index(driver.current_url)
        return
    for topic in topics[index:]:
        if 'UG_list_b' in topic.attrs['class'] and re.findall(r'.*article.*', topic.attrs['href']):  # 如果是文章则跳过
            continue
        print(topic.attrs['class'])
        href, img_srcs, title, transponds, comments, likes, css = ('', '', '', '', '', '', '')
        if 'UG_list_a' in topic.attrs['class']:
            href = topic.attrs['href'] if re.findall(r'https:', topic.attrs['href']) else 'https:' + topic.attrs['href']
            title = topic.select('h3')[0].text
            if topic.select('.list_nod'):
                img_srcs = [img.attrs['src'] for img in topic.select('.list_nod')[0].select('img')]
            transponds = topic.select('.subinfo_rgt')[0].select('em:nth-of-type(2)')[0].string
            comments = topic.select('.subinfo_rgt')[1].select('em:nth-of-type(2)')[0].string
            likes = topic.select('.subinfo_rgt')[2].select('em:nth-of-type(2)')[0].string
            css = 'UG_list_a'
        elif 'UG_list_b' in topic.attrs['class']:
            href = topic.attrs['href'] if re.findall(r'https:', topic.attrs['href']) else 'https:' + topic.attrs['href']
            title = topic.select('h3')[0].text
            if topic.select('.W_piccut_v'):
                img_srcs = [img.attrs['src'] for img in topic.select('.W_piccut_v')[0].select('img')]
            transponds = topic.select('.subinfo_rgt')[0].select('em:nth-of-type(2)')[0].string
            comments = topic.select('.subinfo_rgt')[1].select('em:nth-of-type(2)')[0].string
            likes = topic.select('.subinfo_rgt')[2].select('em:nth-of-type(2)')[0].string
            css = 'UG_list_b'
        elif 'UG_list_v2' in topic.attrs['class']:
            href = topic.attrs['href'] if re.findall(r'https:', topic.select('> .vid')[0].attrs['href']) else 'https:' + \
                                                                                                              topic.select(
                                                                                                                  '> .vid')[
                                                                                                                  0].attrs[
                                                                                                                  'href']
            title = topic.select('> .list_des')[0].select('h3')[0].text
            img_srcs = ['https:' + topic.select('> .vid')[0].select('[src]')[0].attrs['src']]
            # playvideo_icon=topic.select('> .vid')[0].select('.icon_playvideo')[0]
            transponds = topic.select('.subinfo_rgt')[0].select('em:nth-of-type(2)')[0].string
            comments = topic.select('.subinfo_rgt')[1].select('em:nth-of-type(2)')[0].string
            likes = topic.select('.subinfo_rgt')[2].select('em:nth-of-type(2)')[0].string
            css = 'UG_list_v2'
        elif 'UG_tips' in topic.attrs['class']:
            continue
        else:
            logger.debug('没有这个css:%s的处理方式' % topic.attrs['class'])

        if href and title and transponds and comments and likes and css:
            datas.append({
                'href': href,
                'img_srcs': img_srcs,
                'title': title,
                'transponds': transponds,
                'comments': comments,
                'likes': likes,
                'css': css
            })

    return driver, new_index, datas


def scribe_index(url):
    # 启动模拟浏览器
    driver = ready(random.choice(ip_list))
    # 打开url并确定能用
    driver.get(url)
    # 点击热门
    re_men = wait_and_get_elements_until_ok(driver, '[href="/?category=0"]')[0]
    re_men.click()
    # 下拉
    wait_and_get_elements_until_ok(driver, '[href="/?category=0"]')
    driver.execute_script('window.scrollTo(0,document.body.scrollHeight)')

    index = 0
    datas = []
    for i in range(1, 10):
        time.sleep(1)
        result = scroll_and_scribe(driver, index, datas)
        if result:
            driver, index, datas = result
        else:
            driver.quit()
            return scribe_index(url)
    driver.quit()
    print('begin writing index to mongo')
    indexData.update_one({'created_at': time.strftime('%Y-%m-%d')}, {'$set': {
        'created_at': time.strftime('%Y-%m-%d'),
        'type': 'hot',
        'datas': datas,
    }}, True)
    return datas


def scribe_detail(driver, handle, data):
    '''
    爬取子夜
    :param driver:
    :param handle:
    :param data:
    :return: 一般返回None,如果加载不出数据，会把data返回，以便再次尝试加载
    '''
    # 启动模拟浏览器
    # driver = ready(random.choice(ip_list), mode='product')
    # driver.get(data['href'])
    driver.switch_to.window(handle)
    # 先判断页面地址是否正确，如果不正确则换回正确的
    if driver.current_url != data['href']:
        driver.get(data['href'])
    # 加载想要的内容
    if not wait_and_get_elements_until_ok(driver, '[node-type="feed_list_content"]',
                                          timeout_handler=lambda: wait_and_get_elements_until_ok(driver,
                                                                                                 '.info_txt W_f14')):
        if re.findall(r'.*删除。*', driver.title):
            # 当前页面已被删除
            data['detail'] = {'error': str(driver.title)}
            close(driver)
            return
        # else:
        #     # 刷新试试
        #     driver.execute_script('location.reload()')
        #     logger.debug('没有加载到想要的东西，刷新试试：' + driver.current_url)
        #     time.sleep(5)
    driver.execute_script('window.scrollTo(0,document.body.scrollHeight)')
    if not wait_and_get_elements_until_ok(driver, '[node-type="comment_list"] [comment_id]'):
        # logger.debug('没有加载到想要的东西，刷新试试：' + driver.current_url)
        # driver.execute_script('location.reload()')
        # time.sleep(5)
        # driver.execute_script('window.scrollTo(0,document.body.scrollHeight)')
        # if not wait_and_get_elements_until_ok(driver, '[node-type="comment_list"] [comment_id]'):
        #     data['detail'] = {'error':'没有加载到想要的信息，title:' + str(driver.title)}
        #     return
        return data
    # 开始抓数据
    detail = {}
    soup = BeautifulSoup(driver.page_source, 'lxml')
    if data['css'] == 'UG_list_a':
        try:
            # UG_list_a 的爬取方法
            bozhu = {
                'name': soup.select('a.W_f14')[0].text,
                'href': 'https:' + soup.select('a.W_f14')[0].attrs['href']
            }
            content = '\n'.join([string.strip() for string in
                                 soup.select('.WB_detail')[0].select('[node-type="feed_list_content"]')[0].strings])
            thumb_img_srcs = ['https:' + img.attrs['src'] for img in
                              soup.select('.WB_expand_media_box .WB_media_view .choose_box img')]
            prefix = 'https:' + '/'.join(
                soup.select('.choose_box img')[0].attrs['src'].split('/')[:-1]) + '/'
            media_contents = [prefix + thumb.split('/')[-1] for thumb in thumb_img_srcs]
            comments = [re.match(r'.+(?=\n)', comment.text.strip()).group() for comment in
                        soup.select('[node-type="comment_list"] [comment_id]') if
                        not re.match(bozhu['name'], comment.text.strip())][:10]
            if not bozhu['name'] or not bozhu[
                'href'] or not content or not thumb_img_srcs or not media_contents or not comments:  # 数据没有加载完，递归一下
                detail = {
                    'error': '数据不全'
                }
                for k, v in {'bozhu': bozhu, 'content': content, 'thumb_img_srcs': thumb_img_srcs,
                             'media_contents': media_contents, 'comments': comments}.items():
                    if not v:
                        detail[k] = v
            else:
                detail = {
                    'bozhu': bozhu,
                    'content': content,
                    'thumb_img_srcs': thumb_img_srcs,
                    'media_contents': media_contents,
                    'comments': comments
                }
        except Exception as e:
            detail = {
                'error': traceback.format_exc()
            }

    elif data['css'] == 'UG_list_b':
        try:
            bozhu = {
                'name': soup.select('a.W_f14')[0].text,
                'href': 'https:' + soup.select('a.W_f14')[0].attrs['href']
            }
            content = '\n'.join([string.strip() for string in
                                 soup.select('.WB_detail')[0].select('[node-type="feed_list_content"]')[0].strings])
            if soup.select('.choose_box a'):  # 如果有多张图
                thumb_img_srcs = []
                media_contents = []
                for a in soup.select('.choose_box a'):
                    thumb_img_srcs.append('https:' + a.select('img')[0].attrs['src'])
                prefix = 'https:' + '/'.join(
                    soup.select('.choose_box img')[0].attrs['src'].split('/')[:-1]) + '/'
                media_contents = [prefix + thumb.split('/')[-1] for thumb in thumb_img_srcs]
            else:  # 如果没有多张图
                thumb_img_srcs = data[
                    'img_srcs']  # if data['img_srcs'] else [img.attrs['src'] for img in soup.select('[action-type="feed_list_media_bigimg"] img')]
                media_contents = [add_url_prefix(
                    soup.select('[action-type="feed_list_media_bigimg"] [src]')[0].attrs['src'])] if soup.select(
                    '[action-type="feed_list_media_bigimg"] [src]') else []

            comments = [re.match(r'.+(?=\n)', comment.text.strip()).group() for comment in
                        soup.select('[node-type="comment_list"] [comment_id]') if
                        not re.match(bozhu['name'], comment.text.strip())][:10]

            if not bozhu['name'] or not bozhu[
                'href'] or not content or not comments:
                detail = {
                    'error': '数据不全'
                }
                for k, v in {'bozhu': bozhu, 'content': content, 'thumb_img_srcs': thumb_img_srcs,
                             'media_contents': media_contents, 'comments': comments}.items():
                    if not v:
                        detail[k] = v
            else:
                detail = {
                    'bozhu': bozhu,
                    'content': content,
                    'thumb_img_srcs': thumb_img_srcs,
                    'media_contents': media_contents,
                    'comments': comments
                }
        except Exception as e:
            detail = {
                'error': traceback.format_exc()
            }
    elif data['css'] == 'UG_list_v2':
        detail = {
            'error': '没有这种css的处理方式，请及时处理-------------%s' % data['css']
        }
        try:
            bozhu = {
                'name': soup.select('.bot_name')[0].text,
                'href': 'https:' + soup.select('.bot_name')[0].parent.attrs['href']
            }
            content = soup.select('.info_txt')[0].string
            thumb_img_srcs = data['img_srcs'][0]
            media_contents = ['https:' + soup.select('.con-2 > video')[0].attrs['src']]
            comments = [re.match(r'.+(?=\n)', comment.text.strip()).group() for comment in
                        soup.select('[node-type="comment_list"] [comment_id]') if
                        not re.match(bozhu['name'], comment.text.strip())][:10]
            if not bozhu['name'] or not bozhu[
                'href'] or not content or not thumb_img_srcs or not media_contents or not comments:  # 数据没有加载完，递归一下
                detail = {
                    'error': '数据不全'
                }
                for k, v in {'bozhu': bozhu, 'content': content, 'thumb_img_srcs': thumb_img_srcs,
                             'media_contents': media_contents, 'comments': comments}.items():
                    if not v:
                        detail[k] = v
            else:
                detail = {
                    'bozhu': bozhu,
                    'content': content,
                    'thumb_img_srcs': thumb_img_srcs,
                    'media_contents': media_contents,
                    'comments': comments
                }
        except Exception as e:
            detail = {
                'error': traceback.format_exc()
            }
    else:
        logger.warning('没有这种css的处理方式，请及时处理-------------%s' % data['css'])

    data['detail'] = detail
    print('OK---------' + data['href'])
    close(driver)


def scribe_normal_detial(datas, created_at=None):

    # 爬取非视频的数据
    datas = [data for data in datas if data['css'] != 'UG_list_v2']
    # datas = last_indexData['datas']
    scribe_num = int(len(datas) / 3) if int(len(datas) / 3) else len(datas)

    # 获取热门前1/3  按转发加评论加点赞数排序
    print('准备写入数据库的datas数量为：' + str(scribe_num))
    datas = sorted(datas, key=lambda data: data['transponds'] + data['comments'] + data['likes'])[:scribe_num]

    pool = Pool()
    asy_list = []
    for i in range(int(scribe_num / each_driver_scribe_num)):
        # asy_list.append(pool.apply_async(test,))
        begin = i * each_driver_scribe_num
        end = (i + 1) * each_driver_scribe_num
        asy_list.append(pool.apply_async(scribe_detail_in_new_driver, args=(datas[begin:end],)))
    asy_list.append(pool.apply_async(scribe_detail_in_new_driver, args=(
        datas[each_driver_scribe_num * int(scribe_num / each_driver_scribe_num):scribe_num],)))
    print('Waiting for all subprocesses done...')
    pool.close()
    pool.join()
    print('All subprocesses done.')
    datas = []
    for asy in asy_list:
        for data in asy.get():
            datas.append(data)

    # threads = []
    # for i in range(int(scribe_num / each_driver_scribe_num)):
    #     t = threading.Thread(target=scribe_detail_in_new_driver,
    #                          args=(datas[i * each_driver_scribe_num:(i + 1) * each_driver_scribe_num],))
    #     threads.append(t)
    #     t.start()
    # t = threading.Thread(target=scribe_detail_in_new_driver, args=(
    # datas[each_driver_scribe_num * int(scribe_num / each_driver_scribe_num):scribe_num],))
    # threads.append(t)
    # t.start()
    # for t in threads:
    #     t.join()

    print('begin writing normal detail to mongo')
    detailData.update_one({'created_at': created_at if created_at else time.strftime('%Y-%m-%d'),
                           'detail_type': 'normal',
                           },
                          {'$set': {
                              'created_at': created_at if created_at else time.strftime('%Y-%m-%d'),
                              'type': 'hot',
                              'detail_type': 'normal',
                              'datas': datas,
                          }},
                          True)


def scribe_video_detail(datas, created_at=None):
    datas = [data for data in datas if data['css'] == 'UG_list_v2']
    # 获取热门前1/3  按转发加评论加点赞数排序
    scribe_num = int(len(datas) / 3)
    print('准备写入数据库的datas数量为：' + str(scribe_num))
    datas = sorted(datas, key=lambda data: data['transponds'] + data['comments'] + data['likes'])[:scribe_num]

    driver = ready(random.choice(ip_list))
    for data in datas:
        get_and_target_blank(driver, data['href'])
        # 先判断页面地址是否正确，如果不正确则换回正确的
        time.sleep(3)
        if driver.current_url != data['href']:
            driver.get(data['href'])
        wait_and_get_elements_until_ok(driver, '.hv-ball', timeout=15)  # 进度条出现了
        wait_and_get_elements_until_ok(driver, '.WB_h5video', timeout=15)[0].click()

        scribe_detail(driver, driver.current_window_handle, data)

    # 遍历开始仔细爬(捡漏)
    less = []  # 保存没有成功爬取的数据（由无法加载数据引起的）
    for index, handle in enumerate(driver.window_handles):
        if scribe_detail(driver, handle, datas[index]):
            less.append(datas[index])

    #   捡漏
    if less:
        scribe_less(driver, scribe_detail, less)

    # pool = Pool()
    # asy_list = []
    # for i in range(int(scribe_num / each_driver_scribe_num)):
    #     # asy_list.append(pool.apply_async(test,))
    #     begin = i * each_driver_scribe_num
    #     end = (i + 1) * each_driver_scribe_num
    #     asy_list.append(pool.apply_async(scribe_detail_in_new_driver, args=(datas[begin:end],)))
    # asy_list.append(pool.apply_async(scribe_detail_in_new_driver, args=(
    # datas[each_driver_scribe_num * int(scribe_num / each_driver_scribe_num):scribe_num],)))
    # print('Waiting for all subprocesses done...')
    # pool.close()
    # pool.join()
    # print('All subprocesses done.')
    # datas = []
    # for asy in asy_list:
    #     for data in asy.get():
    #         datas.append(data)

    print('begin writing video detail to mongo')
    detailData.update_one({'created_at': created_at if created_at else time.strftime('%Y-%m-%d'),
                           'detail_type': 'video',
                           },
                          {'$set': {
                              'created_at': created_at if created_at else time.strftime('%Y-%m-%d'),
                              'type': 'hot',
                              'detail_type': 'video',
                              'datas': datas,
                          }},
                          True)


def scribe_detail_in_new_driver(datas):
    driver = ready(random.choice(ip_list))
    time.sleep(2)
    for data in datas:
        get_and_target_blank(driver, data['href'])
        if data['css'] == 'UG_list_v2':  # 如果是视频类，则先停止视频
            # 先判断页面地址是否正确，如果不正确则换回正确的
            time.sleep(3)
            if driver.current_url != data['href']:
                driver.get(data['href'])
            if not wait_and_get_elements_until_ok(driver, '.hv-ball', timeout=15):  # 进度条出现了
                return data
            driver.find_element_by_css_selector('.WB_h5video').click()
        else:  # 如果不是视频类
            time.sleep(3)
    # 关掉空白页
    driver.switch_to.window(driver.window_handles[0])
    close(driver)
    # 遍历开始仔细爬
    less = []  # 保存没有成功爬取的数据（由无法加载数据引起的）
    for index, handle in enumerate(driver.window_handles):
        try:
            if scribe_detail(driver, handle, datas[index]):
                less.append(datas[index])
        except exceptions.JavascriptException as e:
            logger.debug(e)
            continue

    #   捡漏
    if less:
        scribe_less(driver, scribe_detail, less)
    return datas


def scribe_less(driver, scribe_function, data_list):
    '''
    最后爬取遗漏的网页
    :param driver: 有剩余网页没有爬取的driver
    :param scribe_function: 继续爬取所使用的function
    :param data_list:-->存储数据的容器集合，长度必须与driver.window_handles相同
    :return:
    '''
    less = []
    for index, handle in enumerate(driver.window_handles):
        driver.switch_to.window(handle)
        driver.get(data_list[index]['href'])
        data = scribe_function(driver, handle, data_list[index])
        if data:
            less.append(data)
    print('less:%d;data_list-less:%d' % (len(less), len(data_list) - len(less)))
    if len(less) > 0 and len(data_list) - len(less) > 0:  # 递归直到剩余空置data不在减少（即这个捡漏方法不在生效）
        scribe_less(driver, scribe_function, less)
    elif len(less) > 0:
        driver.quit()


def moni_index():
    datas = [data for data in list(indexData.find())[-1]['datas']]
    # 爬子页
    # # 获取热门前1/3  按转发加评论加点赞数排序
    scribe_num = len(datas)
    print('准备写入数据库的datas数量为：' + str(scribe_num))
    datas = sorted(datas, key=lambda data: data['transponds'] + data['comments'] + data['likes'])[:scribe_num]

    # 过滤取出 UG_list_a，UG_list_b，UG_list_v2
    # datas = [data for data in datas if data['css'] == 'UG_list_a'][:3]
    # datas = [data for data in datas if data['css'] == 'UG_list_b'][:3]
    # datas = [data for data in datas if data['css'] == 'UG_list_v2'][:3]
    asy_list = []
    pool = Pool()
    for i in range(int(scribe_num / each_driver_scribe_num)):
        # asy_list.append(pool.apply_async(test,))
        begin = i * each_driver_scribe_num
        end = (i + 1) * each_driver_scribe_num
        # asy_list.append(pool.apply_async(scribe_detail_in_new_driver, args=(datas[begin:end],)))
        pool.apply_async(scribe_detail_in_new_driver, args=(datas[begin:end],))
    print('Waiting for all subprocesses done...')
    pool.close()
    pool.join()
    print('All subprocesses done.')

    a = 1


def test():
    print('test')


def main_def():
    try:
        start = datetime.datetime.now()

        url = 'https://weibo.com/?category=0'
        scribe_index(url)

        # 获取主页已经爬到的数据
        last_indexData = list(indexData.find())[-1]

        # 爬取普通数据
        scribe_normal_detial(last_indexData['datas'])

        # # 爬取视频详情
        # scribe_video_detail(last_indexData['datas'])

        print('总共花费时间：' + str((datetime.datetime.now() - start).seconds) + '秒')
    except Exception as e:
        logger.error(traceback.format_exc())


def scribe_error():
    # datas = list(indexData.find())[-1]['datas']
    datas = list(detailData.find({'created_at': time.strftime('%Y-%m-%d'), 'detail_type': 'normal'}))[-1]['datas']
    no_detail_list = [data for data in datas if 'detail' not in data]
    detail_error_list = [data for data in datas if 'detail' in data and 'error' in data['detail']]
    print('错误率：%d/%d' % (len(detail_error_list), len(datas)))
    print('空置率：%d/%d' % (len(no_detail_list), len(datas)))

    if not detail_error_list:
        return
    driver = ready(random.choice(ip_list))
    for data in detail_error_list:
        get_and_target_blank(driver, data['href'])
        scribe_detail(driver, driver.current_window_handle, data)
    driver.quit()


def scribe_no_detail(created_at=None):
    # datas = list(indexData.find())[-1]['datas']
    datas = list(detailData.find({'created_at': time.strftime('%Y-%m-%d'), 'detail_type': 'normal'}))[-1]['datas']
    no_detail_list = [data for data in datas if 'detail' not in data]
    detail_error_list = [data for data in datas if 'detail' in data and 'error' in data['detail']]
    print('错误率：%d/%d' % (len(detail_error_list), len(datas)))
    print('空置率：%d/%d' % (len(no_detail_list), len(datas)))

    if not no_detail_list:
        return
    # # 多线程爬取方式
    # scribe_num = len(no_detail_list)
    # threads = []
    # for i in range(int(scribe_num / each_driver_scribe_num)):
    #     driver = ready(random.choice(ip_list))
    #     for data in datas[i * each_driver_scribe_num:(i + 1) * each_driver_scribe_num]:
    #         get_and_target_blank(driver, data['href'])
    #     # 关掉空白页
    #     driver.switch_to.window(driver.window_handles[0])
    #     close(driver)
    #     t = threading.Thread(target=scribe_less,
    #                          args=(driver, scribe_detail,
    #                                datas[i * each_driver_scribe_num:(i + 1) * each_driver_scribe_num],))
    #     threads.append(t)
    #     t.start()
    #
    # driver = ready(random.choice(ip_list))
    # for data in datas[each_driver_scribe_num * int(scribe_num / each_driver_scribe_num):scribe_num]:
    #     get_and_target_blank(driver, data['href'])
    # # 关掉空白页
    # driver.switch_to.window(driver.window_handles[0])
    # close(driver)
    # t = threading.Thread(target=scribe_less,
    #                      args=(driver, scribe_detail,
    #                            datas[each_driver_scribe_num * int(scribe_num / each_driver_scribe_num):scribe_num],))
    # threads.append(t)
    # t.start()
    # for t in threads:
    #     t.join()

    driver = ready(random.choice(ip_list))
    for data in no_detail_list:
        get_and_target_blank(driver, data['href'])
    # 关掉空白页
    driver.switch_to.window(driver.window_handles[0])
    close(driver)
    scribe_less(driver, scribe_detail, no_detail_list)
    print('begin writing normal detail to mongo')
    detailData.update_one({'created_at': created_at if created_at else time.strftime('%Y-%m-%d'),
                           'detail_type': 'normal',
                           },
                          {'$set': {
                              'created_at': created_at if created_at else time.strftime('%Y-%m-%d'),
                              'type': 'hot',
                              'detail_type': 'normal',
                              'datas': datas,
                          }},
                          True)


if __name__ == '__main__':
    main_def()
    # scribe_error()
    # scribe_no_detail()

# if __name__=='__main__':
#     datas = list(indexData.find())[-1]['datas']
#     no_detail_list = [data for data in datas if 'detail' not in data]
#     detail_error_list = [data for data in datas if 'detail' in data and 'error' in data['detail']]
#     print('错误率：%d/%d' % (len(detail_error_list),len(datas)))
#     print('空置率：%d/%d' % (len(no_detail_list),len(datas)))
#     v_list = [data for data in datas if data['css']=='UG_list_v2' ]
#     a = 1
