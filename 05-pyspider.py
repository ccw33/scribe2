#coding:utf-8
'''
https://www.jianshu.com/p/2c782eff3b9d

pip install pyspider
在终端输入pyspider启动框架，进入http://localhost:5000/
'''

import re
from pyspider.libs.base_handler import *

class Handler(BaseHandler):

    @every(minutes=24 * 60)
    def on_start(self):
        self.crawl('http://www.imdb.com/search/title?count=100&title_type=feature,tv_series,tv_movie&ref_=nv_ch_mm_1', callback=self.index_page)

    @config(age=24 * 60 * 60)
    def index_page(self, response):
        for each in response.doc('a[href^="http"]').items():
            if re.match("http://www.imdb.com/title/tt\\d+/$", each.attr.href):
                self.crawl(each.attr.href, callback=self.detail_page)
        self.crawl([x.attr.href for x in response.doc('#right a').items()], callback=self.index_page)

    @config(priority=2)
    def detail_page(self, response):
        return {
            "url": response.url,
            "title": response.doc('.header > [itemprop="name"]').text(),
            "rating": response.doc('.star-box-giga-star').text(),
            "director": [x.text() for x in response.doc('[itemprop="director"] span').items()],
        }
