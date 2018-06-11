# coding:utf-8
import pymongo
import pickle
import re
from functools import reduce\

import git


file_path = 'E:/git-repository/blog/ccw33.github.io/file/http_surge.pac'
git_repo_path =  'E:/git-repository/blog/ccw33.github.io'

def generate_replace_text(ip_fanqiang_list):
    new_proxy_list = ["%s%s = %s,%s\n" % (ip['proxy_type'],str(index),ip['proxy_type'] if ip['proxy_type']=='http' else 'socks5',ip['ip_with_port'].replace(':',',')) for index,ip in enumerate(ip_fanqiang_list)]
    new_proxy_group = [s.split('=')[0] for s in new_proxy_list]
    return (reduce(lambda v1,v2:v1+v2,new_proxy_list),reduce(lambda v1,v2:v1+','+v2,new_proxy_group)+',')

# 修改pac文件并commit到github
def update_pac_and_push():
    client = pymongo.MongoClient('localhost', 27017)
    ips = client['ips']
    ipsFanqiangData = ips['ipsFanqiangData']
    if not list(ipsFanqiangData.find())[-1]['ip_fanqiang_list']:
        return
    ip_fanqiang_list = list(ipsFanqiangData.find())[-1]['ip_fanqiang_list']
    client.close()

    #获取repo
    repo = git.Repo(path=git_repo_path)

    # 读取文件
    old_text = ''
    new_text = ''
    with open(file_path, 'r',encoding='utf-8') as fr:
        old_text = fr.read()
        proxy_replace_text ,group_replace_text = generate_replace_text(ip_fanqiang_list)
        new_text = old_text.replace(re.findall(r'\[Proxy\]\n((?:.+\n)+)Socks1',
                                               old_text)[0], proxy_replace_text)
        new_text = new_text.replace(re.findall(r'\[Proxy Group\]\nProxy = url-test, (.+) url = http://www.google.com/generate_204\nSocks_Proxy',
                                               new_text)[0], group_replace_text)

    #修改文件
    with open(file_path, 'w',encoding='utf-8') as fw:
        fw.write(new_text)

    #git commit

    #commit
    repo.index.add([file_path.replace(git_repo_path+'/','')])
    repo.index.commit('auto update '+ file_path)
    #获取远程库origin
    remote = repo.remote()
    #提交到远程库
    remote.push()


if __name__ == "__main__":
    update_pac_and_push()