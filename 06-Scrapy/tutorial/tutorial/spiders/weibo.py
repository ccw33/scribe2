#coding:utf-8
import scrapy
from bs4 import BeautifulSoup
from ..items import xianyuItem
from ..utils import common_scribe
import re

def method(driver):
    datas = []
    soup = BeautifulSoup(driver.page_source, 'lxml')
    # wait_and_get_elements_until_ok(driver,'.pt_ul:nth-of-type(1) > div')
    topics = soup.select('.pt_ul')[0].select('> div')
    for topic in topics:
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
            print('没有这个css:%s的处理方式' % topic.attrs['class'])

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

    return datas


def scribe_detail(driver):
    '''
    爬取子夜
    :param driver:
    :param handle:
    :param data:
    :return: 一般返回None,如果加载不出数据，会把data返回，以便再次尝试加载
    '''

    # 开始抓数据
    detail = {}
    soup = BeautifulSoup(driver.page_source, 'lxml')

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
        thumb_img_srcs = []  # if data['img_srcs'] else [img.attrs['src'] for img in soup.select('[action-type="feed_list_media_bigimg"] img')]
        media_contents = [common_scribe.add_url_prefix(
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

    return detail




class weiboSpider(scrapy.Spider):
    name = 'weibo'
    start_urls = ['https://weibo.com/?category=0']

    def parse(self, response):
        steps = {'name': '微博',
                 'steps_detail': [{'description': '打开微博',
                                   'action': ('get', {'url': 'https://weibo.com/?category=0'}),
                                   'success_flag': '[href="/?category=0"]',
                                   'if_failed_action': ('quit_and_again', {})},
                                  {'description': '点击热门',
                                   'action': ('click', {'selector': '[href="/?category=0"]'}),
                                   'success_flag': '[href="/?category=0"]',
                                   'if_failed_action': ('quit_and_again', {})},
                                  {'description': '下拉10次',
                                   'action': (
                                   'scroll', {'ok_selector': '.pt_ul:nth-of-type(1) > div', 'scroll_times': 10})},
                                  {'description': '获取热门数据',
                                   'ready': '[href="/?category=0"]',
                                   'if_not_ready_action': (
                                       'refresh',
                                       {'url': 'https://weibo.com/?category=0', 'ready_selector': '[href="/?category=0"]'}),
                                   'action': ('scribe', {'method': method,})},
                                  ]}
        datas = common_scribe.run_steps(steps)
        for data in datas[0]['detail']:
            if not data['css'] == 'UG_list_b':
                continue
            url = data['href']
            yield scrapy.Request(url,self.detail)
            return


    def detail(self, response):
        data = {}
        soup = BeautifulSoup(response.body, 'lxml')

        topics = soup.select('.pt_ul')[0].select('> div')
        for topic in topics:
            if 'UG_list_b' in topic.attrs['class'] and re.findall(r'.*article.*', topic.attrs['href']):  # 如果是文章则跳过
                continue
            print(topic.attrs['class'])
            href, img_srcs, title, transponds, comments, likes, css = ('', '', '', '', '', '', '')
            if 'UG_list_a' in topic.attrs['class']:
                href = topic.attrs['href'] if re.findall(r'https:', topic.attrs['href']) else 'https:' + topic.attrs[
                    'href']
                title = topic.select('h3')[0].text
                if topic.select('.list_nod'):
                    img_srcs = [img.attrs['src'] for img in topic.select('.list_nod')[0].select('img')]
                transponds = topic.select('.subinfo_rgt')[0].select('em:nth-of-type(2)')[0].string
                comments = topic.select('.subinfo_rgt')[1].select('em:nth-of-type(2)')[0].string
                likes = topic.select('.subinfo_rgt')[2].select('em:nth-of-type(2)')[0].string
                css = 'UG_list_a'
            elif 'UG_list_b' in topic.attrs['class']:
                href = topic.attrs['href'] if re.findall(r'https:', topic.attrs['href']) else 'https:' + topic.attrs[
                    'href']
                title = topic.select('h3')[0].text
                if topic.select('.W_piccut_v'):
                    img_srcs = [img.attrs['src'] for img in topic.select('.W_piccut_v')[0].select('img')]
                transponds = topic.select('.subinfo_rgt')[0].select('em:nth-of-type(2)')[0].string
                comments = topic.select('.subinfo_rgt')[1].select('em:nth-of-type(2)')[0].string
                likes = topic.select('.subinfo_rgt')[2].select('em:nth-of-type(2)')[0].string
                css = 'UG_list_b'
            elif 'UG_list_v2' in topic.attrs['class']:
                href = topic.attrs['href'] if re.findall(r'https:',
                                                         topic.select('> .vid')[0].attrs['href']) else 'https:' + \
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
                print('没有这个css:%s的处理方式' % topic.attrs['class'])

            if href and title and transponds and comments and likes and css:
                data.update({
                    'href': href,
                    'img_srcs': img_srcs,
                    'title': title,
                    'transponds': transponds,
                    'comments': comments,
                    'likes': likes,
                    'css': css
                })



        title = soup.select('div.content.clearfix > div.leftBox > div.col-cont.title-box > h1')
        item = xianyuItem()
        item['title'] = title[0].get_text()
        item['url'] = response.url
        return item

