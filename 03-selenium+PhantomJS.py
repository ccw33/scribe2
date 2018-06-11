#coding:utf-8
'''
https://www.jianshu.com/p/520749be7377

selenium
pip install -U selenium

PhantomJS 废弃了 用headless firefox
这个不同的操作系统有各自对应的版本，这是官网的下载页面http://phantomjs.org/download.html

Headless Firefox
需要注意的点就是：
本地要有Firefox，不然报找不到载体
本地要有geckodriver，最好再配置一下环境变量
'''

import unittest
from selenium import webdriver
from bs4 import BeautifulSoup

from selenium.webdriver.chrome.options import Options



class seleniumTest(unittest.TestCase):
    def setUp(self):
        # PhantomJS废弃了
        # self.driver = webdriver.PhantomJS(executable_path='D:/phantomjs-2.1.1-windows/phantomjs-2.1.1-windows/bin/phantomjs.exe')

        fireFoxOptions = webdriver.FirefoxOptions()
        fireFoxOptions.set_headless()
        self.driver = webdriver.Firefox(executable_path='D:/geckodriver/geckodriver.exe',options=fireFoxOptions)


    def testEle(self):
        driver = self.driver
        driver.get('http://www.douyu.com/directory/all')
        soup = BeautifulSoup(driver.page_source, 'lxml')
        while True:
            titles = soup.find_all('h3', {'class': 'ellipsis'})
            nums = soup.find_all('span', {'class': 'dy-num fr'})
            for title, num in zip(titles, nums):
                print(title.get_text(), num.get_text())
            if driver.page_source.find('shark-pager-disable-next') != -1:
                break
            elem = driver.find_element_by_class_name('shark-pager-next')
            elem.click()
            soup = BeautifulSoup(driver.page_source, 'xml')

    def tearDown(self):
        print('down')

if __name__ == "__main__":
    unittest.main()
