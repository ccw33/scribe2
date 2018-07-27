#encoding:utf-8

import git

class Git():
    '''
    封装私人git操作的类
    '''

    git_repo_path =  'E:/git-repository/blog/ccw33.github.io'

    def __init__(self,git_repo_path=''):
        if git_repo_path:
            self.git_repo_path = git_repo_path

    def git_push(self,file_path):
        # 获取repo
        repo = git.Repo(path=self.git_repo_path)
        # commit
        repo.index.add([file_path.replace(self.git_repo_path + '/', '')])
        repo.index.commit('auto update ' + file_path)
        # 获取远程库origin
        remote = repo.remote()
        # 提交到远程库
        remote.push()