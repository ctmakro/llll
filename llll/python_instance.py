from .sp import Subprocess, decode_and_print_without_newline
from .sbc import sbc, env_var_name

class PythonInstance:
    def __init__(self, code, is_filename=False,):

        # retrieve source from file
        if is_filename==True:
            print('[PythonInstance] attempt to load script from',code)
            with open(code,'r') as f:
                code = f.read()

        # start a socket-based communicator in parent mode
        self.sbc = sbc()

        # retrieve the port number for the client to connect to
        port = self.sbc.port

        # start a python interpreter in a separate process
        self.process = Subprocess(
            ['python','-u'], # unbuffered output
            stdout_callback = decode_and_print_without_newline,
            stderr_callback = decode_and_print_without_newline,
            verbose = True,
            env = {env_var_name: str(port)}
        )

        precode = ''

        sigint=False

        # ignore Ctrl-C propagated from parent
        if sigint==False:
            precode+='''
import signal
def handle(number,frame):
    print('got signal',number,'(ignore)')
signal.signal(signal.SIGINT, handle)
'''

        code = precode + code

        # write the entire source code to the python interpreter
        self.process.write(code.encode('utf-8'))
        self.process.close_stdin()

        self.finished = False

    def join(self):
        print('[PythonInstance] waiting for process to finish')
        self.process.join()
        print('[PythonInstance] process finished')
        self.finished=True

    def kill(self):
        if not self.finished:
            print('[PythonInstance] trying to kill process')
            self.process.kill()
            self.process.join()

    def __del__(self):
        # self.kill()
        # del self.pbc
        del self.sbc
        del self.process

    def send(self,obj):
        return self.sbc.send(obj)
    def recv(self):
        return self.sbc.recv()

def extract_source(f):
    import inspect
    lines = inspect.getsourcelines(f)
    print("".join(lines[0]))

def test():
    code = '''
from llll import sbc
sbc = sbc()
import time
while True:
    d = sbc.recv()
    if d == 'stop':
        sbc.send('ok, stopped')
        break
    else:
        print(d)
    time.sleep(0.5)
    '''

    pi = PythonInstance(code)

    pi.send('hello')
    pi.send('world')
    pi.send('yeah!')
    pi.send('stop')
    print(pi.recv())

    import time
    time.sleep(.5)
    pi.join()
    time.sleep(.5)

if __name__ == '__main__':
    test()
