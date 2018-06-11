#coding:utf-8
import multiprocessing
from bs4 import BeautifulSoup
import requests

def pageUrls(url):
    web_data = requests.get(url)
    soup = BeautifulSoup(web_data.text, 'lxml')
    sum = int(soup.select('span.total > em:nth-of-type(1)')[0].get_text())
    pageNum = sum/50
    return [url+'/loupan/s?p={}'.format(str(i)) for i in range(1, pageNum+2, 1)]

def detailPage(myurl):
    urls = pageUrls(myurl)
    for url in urls:
        web_data = requests.get(url)
        soup = BeautifulSoup(web_data.text, 'lxml')
        titles = soup.select('div.list-results > div.key-list > div > div.infos > div > h3 > a')
        for title in titles:
            print(url)
            print(title.get_text())
            print(title.get('href'))

def main(urls):
    pool = multiprocessing.Pool(multiprocessing.cpu_count())
    for url in urls:
        pool.apply_async(detailPage, (url, ))
    # pool.map(detailPage, urls)
    pool.close()
    pool.join()


if __name__ == "__main__":
    startUrl = 'http://tj.fang.anjuke.com/?from=navigation'
    web_data = requests.get(startUrl)
    soup = BeautifulSoup(web_data.text, 'lxml')
    urls = [url.get('href') for url in soup.select('.city-mod > dl > dd > a')]
    main(urls)
