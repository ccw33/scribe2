# -*- coding:utf-8 -*-

import threading
import time
import queue


all_done=False

def worker(tName):
    print(tName,'started')
    while not all_done:
        try:
            item = q.get(timeout=2)
            print('do something')
        except queue.Empty:#如果过了2秒还没有获得新任务，回去看一下是否已经all_done
            continue
        q.task_done()
        print(tName, 'finish',str(item))
    print(tName,'done')

q = queue.Queue(6)

for i in range(3):
     t = threading.Thread(target=worker,args=('Thread'+str(i),))
     # t.daemon = True
     t.start()

for item in range(20):
    q.put(item)

q.join()

all_done=True

a = 1

