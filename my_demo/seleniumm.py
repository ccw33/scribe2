#coding:utf-8

import selenium
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from my_demo.weibo import ready


# driver = ready()
# driver.get('https://www.baidu.com')
# driver.find_element_by_css_selector('#kw').send_keys("selenium",Keys.ENTER)
#
# for handle in driver.window_handles:
#     driver.switch_to_window(handle)

from Utils import scribe_utils

driver = scribe_utils.ready()
driver