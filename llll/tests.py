# make sure you installed this pkg in edit mode
from llll import sbc,python_instance,sp

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
