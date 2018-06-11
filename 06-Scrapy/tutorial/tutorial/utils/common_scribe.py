# coding:utf-8

from selenium import webdriver
from selenium.webdriver.common.proxy import Proxy
from selenium.common import exceptions
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import pymongo

from . import ip_scriber

import random
import time
import logging
import re
from multiprocessing import Pool
import traceback
import functools
import pickle

ip_list = ip_scriber.get_ip_list()

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

system = 'windows'
mode = 'product'  # mode: 如果为‘debug’显示浏览器，如果为‘product’则不像是浏览器


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
    wait_and_get_elements_until_ok(driver,'[id="su"]')
    # for data in data_list:
    #     time.sleep(2)
    #     get_and_target_blank(driver, data['url'])
    # # 关闭空窗口
    # driver.switch_to.window(driver.window_handles[0])
    # close(driver)
    init_less = [data for data in data_list if not data['detail']]
    now_less = []

    for index,data in enumerate(data_list):
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
        self.driver.get(url)

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
    def click(self, selector):
        '''
        点击
        :param driver:
        :param selector:
        :return:
        '''
        self.driver.find_element_by_css_selector(selector).click()

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


def run_steps(steps, outer_driver=None,container = None):
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
    datas= []
    for step in steps['steps_detail']:

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
            getattr(ac, step['action'][0])(**step['action'][1])

            #验证是否成功
            if 'success_flag' in step and 'if_failed_action' in step:  # 如果有成功的标记success_flag
                if not wait_and_get_elements_until_ok(driver, step['success_flag']):
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
                if step['action'][0] not in ac.self_check_ations:# 如果不是自查action
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
        container['datas'] = datas
    return datas



def run_steps_list(*steps_list):
    pool = Pool()
    asy_list = []
    datas_list = []
    for index,steps in enumerate(steps_list):
        datas_list.append({'name':steps['name']})
        # pool.apply_async(run_steps, args=(steps,),kwds={'container':datas_list[index]})
        asy_list.append(pool.apply_async(run_steps, args=(steps,)))
    print('Waiting for all subprocesses done...')
    pool.close()
    pool.join()
    print('All subprocesses done.')
    for index,asy in enumerate(asy_list):
        datas_list.append({'name':steps_list[index]['name'],'datas':asy.get()})
    return datas_list


if __name__ == '__main__':
    # from my_demo import utils
    # help(utils)
    
    pass

