from .python_instance import PythonInstance
from .sbc import sbc

import random
import threading as th
from collections import deque

class PoolMaster:
    def __init__(self, slave, nproc, is_filename=False):
        assert nproc > 0

        self.fifo = FIFO(nproc)
        for i in range(nproc):
            self.fifo.put(PythonInstance(slave, is_filename=is_filename))

    def call(self, *a, **kw):
        pi = self.fifo.get()

        pi.send((a,kw))
        data = pi.recv()

        self.fifo.put(pi)
        return data

def PoolSlave(f):
    isbc = sbc()
    while True:
        a,kw = isbc.recv()
        isbc.send(f(*a, **kw))

class FIFO: # fifo with Semaphores
    def __init__(self, capacity, timeout=0.1):
        self.sem = th.Semaphore(0)
        self.nsem = th.Semaphore(capacity)
        self.capacity=capacity
        self.q = deque()
        self.timeout = timeout

    def put(self, stuff):
        self.nsem.acquire()
        self.q.append(stuff)
        self.sem.release()

    def get(self, *a, **k):
        while not self.sem.acquire(timeout=self.timeout):
            print('waiting for pop()...')
        stuff = self.q.popleft()
        self.nsem.release()
        return stuff

class MultithreadedGenerator:
    def __init__(self, generator, buffer_capacity=None, ncpu=None):
        if ncpu is None:
            import psutil
            ncpu = psutil.cpu_count()
            print(ncpu, 'cpu found')

        if buffer_capacity is None:
            buffer_capacity = ncpu*2

        self.fifo = FIFO(buffer_capacity)

        def worker(idx,total):
            print('({}/{}) worker thread started'.format(idx+1,total))
            while 1:
                self.put(generator())

        ts = [th.Thread(target=worker,args=(i,ncpu), daemon=True)
        for i in range(int(ncpu))]
        self.threads = ts
        [t.start() for t in ts]

    def put(self, stuff):
        self.fifo.put(stuff)

    def get(self):
        return self.fifo.get()

class MultithreadedMapper:
    def __init__(self, nthread=None):
        if nthread is None:
            import psutil
            nthread = psutil.cpu_count()
            print(nthread, 'cpu found')

        self.ififo = FIFO(nthread+2, timeout=None)
        self.ofifo = FIFO(nthread+2, timeout=None)

        def worker(idx,total):
            print('({}/{}) worker thread started'.format(idx+1,total))
            while 1:
                i,f,a = self.ififo.get()
                res = f(a)
                self.ofifo.put((i, res))

        ts = [th.Thread(target=worker,args=(i,nthread), daemon=True)
        for i in range(int(nthread))]
        self.threads = ts
        [t.start() for t in ts]

        self.nthread = nthread

    def map(self, f, arr):
        res = []
        length = len(arr)
        nt = self.nthread
        for i in range(length+nt):
            if i < length:
                self.ififo.put((i, f, arr[i]))
            if i >= nt:
                res.append(self.ofifo.get())

        res = sorted(res, key=lambda x:x[0])
        return [r[1] for r in res]
