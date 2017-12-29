# start and interact with a subprocess in a better-controlled way (than those available via the subprocess package).

import time
import subprocess as sp
import sys,os
import threading as th

printlock = th.Lock()
def print_without_newline(*args):
    printlock.acquire()
    args = list(map(lambda x:str(x),args))
    s = ' '.join(args)
    sys.stdout.write(s)
    sys.stdout.flush()
    printlock.release()

def decode_and_print_without_newline(bytes):
    print_without_newline(bytes.decode('utf-8'))

# an instance of subprocess
class Subprocess:
    def __init__(self,
        args,
        end_callback = None,
        stdout_callback = None,
        stderr_callback = None,
        collect_output = False,
        verbose = False,
        env = {},
    ):
        self.endcb = end_callback
        self.outcb = stdout_callback
        self.errcb = stderr_callback
        self.outcoll = collect_output
        self.verbose = verbose

        def nop(*a,**kw):
            pass

        if self.errcb is None: self.errcb = nop
        if self.endcb is None: self.endcb = nop
        if self.outcb is None: self.outcb = nop

        # if you want to collect the output into an array of bytes
        if self.outcoll == True:
            self.stdout_collected = bytearray()
            self.stderr_collected = bytearray()

        if self.verbose:
            print(
                '[run_subprocess] starting process "{}"\n'.format(' '.join(args))
            )

        # merge user specified ENV entries
        curr_env = os.environ.copy()
        curr_env.update(env)

        # instance of subprocess.Popen
        self.pop = sp.Popen(
            args,
            stdin=sp.PIPE,
            stdout=sp.PIPE,
            stderr=sp.PIPE,
            env = curr_env,
        )

        # 3 monitoring threads for the process and its stdout/stderr
        def stderr_poll():
            while True:
                err = self.pop.stderr.readline()
                self.errcb(err)
                if self.outcoll == True:
                    self.stderr_collected += err
                if self.pop.poll() is not None:
                    break

        def stdout_poll():
            while True:
                out = self.pop.stdout.readline()
                self.outcb(out)
                if self.outcoll == True:
                    self.stdout_collected += out
                if self.pop.poll() is not None:
                    break

        def process_poll():
            while True:
                if self.pop.poll() is not None:
                    # wait for the two other threads to finish..
                    if self.verbose:
                        print('[run_subprocess] joining threads 0 and 1')
                        
                    [self.threads[k].join() for k in [0,1]]

                    if self.verbose:
                        print(
                            '[run_subprocess] process "',
                            ' '.join(args),
                            '(pid {})'.format(self.pop.pid),
                            '" ended with status',
                            self.pop.returncode,
                            '\n'
                        )
                    if self.endcb is not None:
                        if self.outcoll:
                            self.endcb(
                                self.stdout_collected,
                                self.stderr_collected,
                            )
                        else:
                            self.endcb()
                    break
                else:
                    time.sleep(0.2)

        import threading as th
        t = [th.Thread(target=k, daemon=True) for k in [stdout_poll,stderr_poll,process_poll]]

        [k.start() for k in t]

        self.threads = t

    # wait for process to finish
    def join(self):
        self.threads[2].join()

    # send a kill signal
    def kill(self):
        self.pop.kill()

    def __del__(self):
        self.kill()

    # write bytes to stdin
    def write(self,bytes):
        self.pop.stdin.write(bytes)
        self.pop.stdin.flush()

    # close stdin
    def close_stdin(self):
        self.pop.stdin.close()

    def write_done(self):
        self.close_stdin()

def test_functionality():
    def end_cb(stdout,stderr):
        print('-'*30)
        print('process ended.')
        print('collected from stdout:')
        print(stdout.decode('utf-8'))
        print('collected from stderr:')
        print(stderr.decode('utf-8'))
        print('-'*30)

    s = Subprocess(
        ['python','-'],
        stdout_callback = decode_and_print_without_newline,
        stderr_callback = decode_and_print_without_newline,
        end_callback = end_cb,
        collect_output = True,
        verbose = True,
    )

    s.write('print("bitch")\nexit()\nprint("bitch")\n\n'.encode('utf-8'))
    s.write_done()
    s.join()

    s = Subprocess(
        ['ping','baidu.com'],
        end_callback = end_cb,
        collect_output = True,
        verbose = True,
    )

    time.sleep(2)
    s.kill()
    s.join()

    s = Subprocess(
        ['python','-'],
        end_callback = end_cb,
        collect_output = True,
        verbose = True,
    )

    s.write('raise NotImplementedError("okay!")\n\n'.encode('utf-8'))
    s.write_done()
    s.join()

if __name__ == '__main__':
    test_functionality()
