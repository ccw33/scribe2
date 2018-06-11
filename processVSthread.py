#coding=utf-8
from multiprocessing import Pool
from threading import Thread
import time
import os
from multiprocessing import Process,Pool
import traceback


def loop():
    while True:
        pass


def sleep_in_thread(p):
    threads = [Thread(target=sleep,args=('process-%s   thread-%s' % (str(p),str(i)),),
                      name='process-%s   thread-%s' % (str(p),str(i))) for i in range(5)]
    for t in threads:
        print(t.name + ' started')
        t.start()
    for t in threads:
        t.join()
    print('process-%s done!!!' % p)

def sleep_in_sub_thread(p):
    threads = [Thread(target=sleep,args=('parent_thread-%s   child_thread-%s' % (str(p),str(i)),),
                      name='parent_thread-%s   child_thread-%s' % (str(p),str(i))) for i in range(5)]
    for t in threads:
        print(t.name + ' started')
        t.start()
    for t in threads:
        t.join()
    print('process-%s done!!!' % p)

def sleep_in_sub_process(p):
    pool = Pool()
    for i in range(4):
        pool.apply_async(sleep,args=('parent-%  child-%' % (p,i),))
    pool.close()
    pool.join()


def sleep(who):
    time.sleep(5)
    print('---------------- %s wakeup' % who)


def count_time():
    i = 1
    while True:
        time.sleep(1)
        print(i)
        i = i + 1

if __name__ == '__main__':

    # pool = []
    # for i in range(6):
    #     p = Process(target=loop)
    #     p.start()
    #     pool.append(p)
    # for p in pool:
    #     p.join()
    #
    # 计时
    # t = Thread(target=count_time)
    # t.start()

    # tloop = Thread(target=loop)

    # pool = Pool()
    # for i in range(6):
    #     # pool.apply_async(sleep_in_thread,args=(i,))
    #     pool.apply_async(sleep_in_sub_process, args=(i,))
    # pool.close()
    # pool.join()

    sleep_in_thread('主')



# if __name__ == '__main__':
#
#     # # 计时
#     # t = Thread(target=count_time)
#     # t.start()
#
#     for i in range(3):
#         t = Thread(target=sleep_in_sub_thread,args=(i,))
#         t.start()
#
#     # for i in range(10):
#     #     t = Thread(target=loop)
#     #     t.start()


