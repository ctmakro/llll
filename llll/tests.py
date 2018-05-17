# make sure you installed this pkg in edit mode
from llll import *
import time

def title(s):
    print('-'*30)
    print('*'*5, 'test', s, '*'*5)
    print('-'*30)

title('sbc')

sbc1 = sbc()
sbc2 = sbc(sbc1.port)

sbc1.write('hello'.encode('utf-8'))
print(sbc2.read().decode('utf-8'))

sbc2.write('world'.encode('utf-8'))
print(sbc1.read().decode('utf-8'))

title('sp')
sp.test_functionality()

title('python_instance')
python_instance.test()

title('fifo')
fif = FIFO(6)

for i in range(5):
    fif.put(i)
for i in range(5):
    print(fif.get())

time.sleep(0.5)

title('MultithreadedGenerator')
def garbage():
    time.sleep(.5)
    import random
    return random.random()

mg = MultithreadedGenerator(garbage,ncpu=4)
for i in range(7):
    print('mg.get() =>', mg.get())

time.sleep(0.5)

title('pooling')
code = '''
def fib(n):
    if n <= 2:
        return 1
    return fib(n-1) + fib(n-2)

from llll import PoolSlave
PoolSlave(fib)
'''
def fib(n):
    if n <= 2:
        return 1
    return fib(n-1) + fib(n-2)

print('local fibonacci')
start = time.time()
for i in range(1,33):
    print(i, fib(i))
print('time:',time.time()-start)

print('poolmaster, sequential')
pm = PoolMaster(code, 6)
import time

start = time.time()
for i in range(1,33):
    print(i, pm.call(i))
print('time:',time.time()-start)

title('MultithreadedMapper')

mm = MultithreadedMapper(nthread=6)

start = time.time()
for i,v in enumerate( mm.map(fib, list(range(1,33))) ):
    print(i+1,v)
print('time:',time.time()-start)

def fib2(n):
    return pm.call(n)

print('MultithreadedMapper + PoolMaster')
start = time.time()
for i,v in enumerate( mm.map(fib2, list(range(1,33))) ):
    print(i+1,v)
print('time:',time.time()-start)

#
# start = time.time()
# mg = MultithreadedGenerator(fib2, )
#
# for i in range(30):
#     print(i+1, pm.call(i+1))
# print('time:',time.time() - start)
